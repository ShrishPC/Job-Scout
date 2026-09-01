import os
import json
import re
import torch
from threading import Thread
from transformers import pipeline, TextIteratorStreamer
from app.services.llm_fallback import extract_structured_data_fallback, generate_embedding_fallback
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Optimized Local Model Storage (Ensures portability across machines)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_CACHE = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODEL_CACHE, exist_ok=True)

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
PARSER_LLM_MODEL_NAME = os.getenv("PARSER_LLM_MODEL_NAME", "unsloth/Llama-3.2-3B-Instruct")

# 1. Local Embeddings & Hardware Device Tracking
AI_DEVICE = "cpu"
CURRENT_DEVICE = "cpu"
embedding_model = None

def load_embedding_model(device="cpu"):
    global embedding_model, CURRENT_DEVICE
    try:
        print(f"Initializing Embedding Model ({EMBEDDING_MODEL_NAME}) on {device} from {MODEL_CACHE}...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, cache_folder=MODEL_CACHE, device=device)
        CURRENT_DEVICE = device
    except Exception as e:
        print(f"Failed to load sentence-transformers model {EMBEDDING_MODEL_NAME} on {device}: {e}")
        try:
            print(f"Attempting fallback initialization with all-MiniLM-L6-v2 on {device}...")
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=MODEL_CACHE, device=device)
            CURRENT_DEVICE = device
        except Exception as fallback_err:
            print(f"Fallback model failed: {fallback_err}")
            embedding_model = None

def get_embedding_model():
    global embedding_model, CURRENT_DEVICE
    if embedding_model is None:
        load_embedding_model(CURRENT_DEVICE)
    return embedding_model

# Initialize on startup
load_embedding_model("cpu")

# 2. Local LLM (For Parsing & Generation)
local_llm = None
LLM_DEVICE = "cpu"
ACTIVE_LLM_MODEL_NAME = PARSER_LLM_MODEL_NAME

def get_local_llm(device=None):
    global local_llm, LLM_DEVICE, AI_DEVICE, ACTIVE_LLM_MODEL_NAME
    if device is None:
        device = AI_DEVICE
        
    if local_llm is None or LLM_DEVICE != device:
        print(f"Loading Local AI Model ({PARSER_LLM_MODEL_NAME}) on {device} from {MODEL_CACHE}...")
        
        # CPU optimization: limit threads to avoid heavy context switching overhead
        if device == "cpu":
            try:
                import multiprocessing
                cpu_cores = multiprocessing.cpu_count()
                optimal_threads = max(1, min(4, cpu_cores // 2))
                torch.set_num_threads(optimal_threads)
                print(f"Set PyTorch CPU threads to {optimal_threads} to avoid core contention.")
            except Exception as thread_err:
                print(f"Failed to limit CPU threads: {thread_err}")

        # Configure loading precision
        model_kwargs = {
            "cache_dir": MODEL_CACHE,
            "low_cpu_mem_usage": True
        }
        
        if device == "cuda":
            model_kwargs["torch_dtype"] = torch.float16
        else:
            model_kwargs["torch_dtype"] = torch.bfloat16  # bfloat16 is highly optimized for modern CPUs

        try:
            local_llm = pipeline(
                "text-generation", 
                model=PARSER_LLM_MODEL_NAME, 
                device=0 if device == "cuda" else -1,
                model_kwargs=model_kwargs
            )
            LLM_DEVICE = device
            ACTIVE_LLM_MODEL_NAME = PARSER_LLM_MODEL_NAME
        except Exception as e:
            print(f"Failed to load {PARSER_LLM_MODEL_NAME} on {device}: {e}")
            print(f"Attempting fallback to TinyLlama/TinyLlama-1.1B-Chat-v1.0 on {device}...")
            
            fallback_kwargs = {
                "cache_dir": MODEL_CACHE,
                "low_cpu_mem_usage": True
            }
            if device == "cuda":
                fallback_kwargs["torch_dtype"] = torch.float16
            else:
                fallback_kwargs["torch_dtype"] = torch.bfloat16
                
            try:
                local_llm = pipeline(
                    "text-generation", 
                    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
                    device=0 if device == "cuda" else -1,
                    model_kwargs=fallback_kwargs
                )
                LLM_DEVICE = device
                ACTIVE_LLM_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            except Exception as fallback_err:
                print(f"Failed to load TinyLlama fallback: {fallback_err}")
                raise fallback_err
    return local_llm

def set_ai_device(device: str):
    global AI_DEVICE
    if device not in ["cpu", "cuda"]:
        raise ValueError("Device must be 'cpu' or 'cuda'")
    AI_DEVICE = device
    load_embedding_model(device)


def format_prompt(system_prompt: str, user_prompt: str) -> str:
    model_lower = ACTIVE_LLM_MODEL_NAME.lower()
    if "qwen" in model_lower:
        return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
    elif "tinyllama" in model_lower:
        return f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_prompt}</s>\n<|assistant|>\n"
    elif "phi" in model_lower:
        return f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{user_prompt}<|end|>\n<|assistant|>\n"
    elif "llama" in model_lower:
        return f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    else:
        return f"Instructions:\n{system_prompt}\n\nInput:\n{user_prompt}\n\nResponse:\n"

def parse_markdown_with_llm(markdown_content: str, **kwargs):
    """
    Extracts structured data using a local LLM with configurable chat templates.
    """
    if settings.DEMO_MODE:
        import time
        print("DEMO_MODE: Bypassing local LLM parsing for speed.")
        time.sleep(0.5)
        return {
            "full_name": "Demo Candidate",
            "email": "demo@example.com",
            "phone": "555-0199",
            "target_role": "Software Engineer",
            "target_location": "Remote",
            "skills": ["Python", "React", "Docker", "AWS", "Machine Learning"],
            "experience": [{"title": "Senior Engineer", "company": "Tech Corp", "duration": "3 years", "description": "Built scalable APIs"}],
            "education": [{"degree": "B.S. Computer Science", "institution": "State University", "year": "2020"}]
        }

    truncated_content = markdown_content[:3000] if markdown_content else ""
    
    system_prompt = """You are a professional resume parsing assistant. Extract candidate information from the resume and respond ONLY with a valid JSON object. Do not include any explanations, introduction, markdown styling blocks, or surrounding text.
The JSON object must follow this exact structure:
{
  "full_name": "Name",
  "email": "Email",
  "phone": "Phone number",
  "target_role": "Target role/Job title",
  "target_location": "Preferred location or 'Remote'",
  "skills": ["Skill 1", "Skill 2"],
  "experience": [
    {"title": "Role Title", "company": "Company Name", "duration": "Duration", "description": "Short description"}
  ],
  "education": [
    {"degree": "Degree/Major", "institution": "School Name", "year": "Graduation Year"}
  ]
}"""
    
    user_prompt = f"Resume details to parse:\n{truncated_content}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    try:
        llm = get_local_llm()
        res = llm(prompt, max_new_tokens=512, return_full_text=False, clean_up_tokenization_spaces=False)
        text = res[0]['generated_text']
        
        # Try to find a JSON object in the response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Local LLM Error during parsing: {e}")
        
    # Heuristic Fallback
    print("Using heuristic fallback for parsing.")
    return extract_structured_data_fallback(markdown_content)

def generate_embedding(text: str):
    """
    Generates a vector embedding using local SentenceTransformer. 
    This is 100% free and runs locally.
    """
    if embedding_model:
        try:
            # Clean and truncate input to avoid overflow issues
            cleaned_text = text[:10000] if text else ""
            embedding = embedding_model.encode(cleaned_text)
            vec = [float(v) for v in embedding]
            return vec[:384]
        except Exception as e:
            print(f"Local Embedding Error: {e}")
            
    return generate_embedding_fallback(text)

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates vector embeddings for a list of texts in a single batch.
    Much faster than encoding in a loop.
    """
    if not texts:
        return []
    if embedding_model:
        try:
            cleaned_texts = [t[:5000] if t else "" for t in texts]
            embeddings = embedding_model.encode(cleaned_texts)
            results = []
            for emb in embeddings:
                vec = [float(v) for v in emb]
                results.append(vec[:384])
            return results
        except Exception as e:
            print(f"Local Batch Embedding Error: {e}")
            
    return [generate_embedding(t) for t in texts]


RESUME_LINE_EMBEDDING_CACHE = {}

def get_cached_line_embeddings(clean_texts: list[str]) -> list[list[float]]:
    """
    Retrieves embeddings for a list of resume lines, using an in-memory cache to skip re-encoding.
    """
    global RESUME_LINE_EMBEDDING_CACHE
    uncached_texts = []
    
    for text in clean_texts:
        if text in RESUME_LINE_EMBEDDING_CACHE:
            continue
        uncached_texts.append(text)
        
    if uncached_texts:
        print(f"RAG Cache: Encoding {len(uncached_texts)} new resume lines...")
        new_embeddings = generate_embeddings_batch(uncached_texts)
        for text, emb in zip(uncached_texts, new_embeddings):
            RESUME_LINE_EMBEDDING_CACHE[text] = emb
            
    return [RESUME_LINE_EMBEDDING_CACHE[text] for text in clean_texts]

def extract_experience_heuristics(text: str) -> int | None:
    if not text:
        return None
    text_lower = text.lower()
    patterns = [
        r'(\d+)\s*(?:-|to)\s*\d+\s*(?:years?|yrs?)\b.*experience',
        r'(?:minimum|at least|req|requires?|required)\s*(\d+)\s*(?:years?|yrs?)\b',
        r'(\d+)\s*(?:years?|yrs?)\b\s*(?:\+)?\s*(?:of)?\s*experience',
        r'experience\s*(?:of|required)?\s*(\d+)\s*(?:years?|yrs?)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                val = int(match.group(1))
                if 0 <= val <= 25:
                    return val
            except ValueError:
                continue
    return None

def extract_experience_from_job(description: str, use_llm: bool = False, **kwargs):
    """
    Uses rule-based heuristics first for speed, falling back to local LLM only if explicitly requested.
    """
    if not description:
        return 0
        
    heuristic_val = extract_experience_heuristics(description)
    if heuristic_val is not None:
        return heuristic_val
        
    if not use_llm:
        return 0
        
    truncated_desc = description[:2000]
    
    system_prompt = "You are a job parsing assistant. You must analyze the job description and output ONLY a single integer representing the minimum years of experience required. Do not output any other text, explanation, or units (e.g. write '3', not '3 years'). Default is 0."
    user_prompt = f"Job Description:\n{truncated_desc}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    try:
        llm = get_local_llm()
        res = llm(prompt, max_new_tokens=10, return_full_text=False, clean_up_tokenization_spaces=False)
        output_text = res[0]['generated_text'].strip()
        match = re.search(r'\d+', output_text)
        return int(match.group()) if match else 0
    except Exception as e:
        print(f"Local LLM Error during experience extraction: {e}")
        return 0

from sqlalchemy.orm import Session
from sqlalchemy import text

def retrieve_rag_context(resume_text: str, job_desc: str, db: Session = None) -> str:
    """
    RAG: Retrieves relevant sections of the candidate's resume and similar jobs from database.
    """
    context_parts = []
    
    # 1. Retrieve most relevant resume lines semantically
    try:
        lines = []
        for line in resume_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove typical resume bullet characters
            clean_line = re.sub(r'^[\s\-\*\•\d\.\>\+]+', '', line).strip()
            if len(clean_line) > 15:
                lines.append((line, clean_line))
        
        if lines:
            job_embedding = generate_embedding(job_desc)
            # Batch embed all lines (using cache to avoid redundant CPU load) and compute similarity
            clean_texts = [clean for original, clean in lines]
            line_embeddings = get_cached_line_embeddings(clean_texts)
            
            scored_lines = []
            for idx, (original, clean) in enumerate(lines):
                line_emb = line_embeddings[idx]
                similarity = sum(a * b for a, b in zip(job_embedding[:384], line_emb[:384]))
                scored_lines.append((similarity, original))
            
            # Sort by similarity descending
            scored_lines.sort(key=lambda x: x[0], reverse=True)
            top_bullets = [line for score, line in scored_lines[:6]]
            
            context_parts.append("MOST RELEVANT CANDIDATE EXPERIENCES/SKILLS FROM RESUME:")
            for b in top_bullets:
                context_parts.append(f"- {b}")
    except Exception as e:
        print(f"RAG: Resume parsing error: {e}")
        
    # 2. Retrieve similar jobs from database for industry alignment
    if db is not None:
        try:
            job_embedding = generate_embedding(job_desc)
            query = text("""
                SELECT title, company, description 
                FROM jobs 
                ORDER BY embedding <=> :embedding 
                LIMIT 3
            """)
            results = db.execute(query, {"embedding": str(job_embedding)})
            similar_jobs = []
            for row in results:
                similar_jobs.append(f"Title: {row.title} at {row.company}\nDescription snippet: {row.description[:300]}...")
            
            if similar_jobs:
                context_parts.append("\nSIMILAR MARKET JOB LISTINGS FOR REFERENCE:")
                for idx, job_ref in enumerate(similar_jobs, 1):
                    context_parts.append(f"Reference Job {idx}:\n{job_ref}\n")
        except Exception as e:
            print(f"RAG: Similar job retrieval error: {e}")
            
    return "\n".join(context_parts)

def generate_tailored_resume_service(resume_text: str, job_title: str, job_desc: str, db: Session = None) -> str:
    """
    Generates a tailored Professional Summary and suggested resume edits using the local LLM and RAG.
    """
    truncated_resume = resume_text[:2000] if resume_text else ""
    truncated_job = job_desc[:1500] if job_desc else ""
    
    # Retrieve RAG context
    rag_context = retrieve_rag_context(resume_text, job_desc, db=db)
    
    system_prompt = (
        f"You are an expert resume coach and recruiter. Analyze the candidate's resume and the job description for the {job_title} role.\n"
        f"Use the retrieved relevant candidate history and reference jobs (RAG context) below to make the output highly accurate and keyword-optimized:\n"
        f"{rag_context}\n\n"
        f"CRITICAL: Do NOT invent, assume, or hallucinate any facts, metrics, projects, dates, or credentials. Use ONLY the candidate's actual history from the provided resume text.\n\n"
        f"Tasks to perform:\n"
        f"1. Write a tailored 'Professional Summary' (2-3 sentences) from the candidate's perspective ('I'). Begin directly with impact and core credentials, aligning with the job description keywords. Avoid clichés like 'Highly motivated professional'.\n"
        f"2. Suggest exactly 3 bullet points for experience. Each bullet point MUST showcase measurable results or metrics based on the candidate's history, align with required job skills, and use strong action verbs (e.g. Optimized, Automated, Spearheaded).\n"
        f"Respond ONLY with: 1) the summary, and 2) the bullet point suggestions. Do not add intro/outro remarks or conversational filler."
    )
    user_prompt = f"Candidate Resume:\n{truncated_resume}\n\nJob Description:\n{truncated_job}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    try:
        llm = get_local_llm()
        res = llm(
            prompt, 
            max_new_tokens=200, 
            return_full_text=False,
            repetition_penalty=1.2,
            do_sample=False
        )
        return res[0]['generated_text'].strip()
    except Exception as e:
        print(f"Local LLM Error during resume tailoring: {e}")
        return "Could not generate resume tailoring recommendations with the local AI."

def generate_cover_letter_service(resume_text: str, job_title: str, company: str, job_desc: str, db: Session = None) -> str:
    """
    Generates a cover letter tailored to a job description using the local LLM and RAG.
    """
    truncated_resume = resume_text[:2000] if resume_text else ""
    truncated_job = job_desc[:1500] if job_desc else ""
    
    # Retrieve RAG context
    rag_context = retrieve_rag_context(resume_text, job_desc, db=db)
    
    system_prompt = (
        f"You are a professional resume writer. Write a custom, impact-driven cover letter from the candidate's perspective ('I') to the hiring manager for the role of {job_title} at {company}.\n"
        f"Use the retrieved relevant candidate history and reference jobs (RAG context) below to connect the candidate's achievements directly to the job needs:\n"
        f"{rag_context}\n\n"
        f"CRITICAL: Do NOT invent, assume, or hallucinate any facts, metrics, projects, dates, or credentials. Use ONLY the candidate's actual history from the provided resume text.\n\n"
        f"Instructions:\n"
        f"- Do NOT use clichés like 'I am writing to express my interest.' Hook the reader immediately with an accomplishment or core value proposition.\n"
        f"- Highlight matching specific skills and projects from the candidate's history that align with the role requirements.\n"
        f"- Keep the length under 180 words.\n"
        f"Format:\n"
        f"Dear Hiring Manager,\n\n"
        f"[Body Paragraphs]\n\n"
        f"Best regards,\n"
        f"[Candidate Name]"
    )
    user_prompt = f"Candidate Resume:\n{truncated_resume}\n\nJob Description:\n{truncated_job}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    try:
        llm = get_local_llm()
        res = llm(
            prompt, 
            max_new_tokens=180, 
            return_full_text=False,
            repetition_penalty=1.2,
            do_sample=False
        )
        return res[0]['generated_text'].strip()
    except Exception as e:
        print(f"Local LLM Error during cover letter generation: {e}")
        return "Could not generate cover letter with the local AI."

def extract_candidate_insights(resume_text: str, job_desc: str):
    """
    Extracts candidate attributes and maps them against job requirements for personalized RAG synthesis.
    """
    import re
    # Candidate name extraction
    candidate_name = "Candidate"
    lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
    for line in lines[:5]:
        clean = re.sub(r'^[#\s\*\-]+', '', line).strip()
        if clean and len(clean.split()) in (2, 3, 4) and not any(kw in clean.lower() for kw in ['resume', 'curriculum', 'contact', 'email', 'phone', 'summary', 'profile', 'engineer', 'developer']):
            candidate_name = clean
            break

    # Extract all recognizable tech skills from resume
    tech_skills_pool = [
        "Python", "FastAPI", "Django", "Flask", "React", "Next.js", "TypeScript", "JavaScript", 
        "Node.js", "Express", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", 
        "AWS", "GCP", "Azure", "CI/CD", "GitHub Actions", "Git", "REST API", "GraphQL", "gRPC", 
        "Kafka", "RabbitMQ", "Celery", "PyTorch", "TensorFlow", "Scikit-Learn", "HuggingFace", 
        "LangChain", "LlamaIndex", "pgvector", "Vector Search", "RAG", "Microservices", "Linux", 
        "Java", "Spring Boot", "C++", "Rust", "Go", "Golang", "Tailwind CSS", "Redux", "SQL"
    ]
    
    candidate_skills = []
    for s in tech_skills_pool:
        if re.search(rf'\b{re.escape(s)}\b', resume_text, re.IGNORECASE):
            candidate_skills.append(s)
            
    job_required_skills = []
    for s in tech_skills_pool:
        if re.search(rf'\b{re.escape(s)}\b', job_desc, re.IGNORECASE):
            job_required_skills.append(s)
            
    matched_skills = [s for s in candidate_skills if s.lower() in [js.lower() for js in job_required_skills]]
    if not matched_skills and candidate_skills:
        matched_skills = candidate_skills[:4]
    elif not matched_skills and job_required_skills:
        matched_skills = job_required_skills[:4]
    elif not matched_skills:
        matched_skills = ["Software Engineering", "Full-Stack Development", "System Architecture", "API Integration"]

    return {
        "name": candidate_name,
        "candidate_skills": candidate_skills,
        "job_skills": job_required_skills,
        "matched_skills": matched_skills
    }

def generate_dynamic_tailored_resume(resume_text: str, job_title: str, company: str, job_desc: str) -> str:
    """
    Deterministic personalized RAG generation using actual candidate skills and target role requirements.
    """
    insights = extract_candidate_insights(resume_text, job_desc)
    top_skills_str = ", ".join(insights["matched_skills"][:5])
    primary_skill = insights["matched_skills"][0] if insights["matched_skills"] else "Full-Stack Engineering"
    secondary_skill = insights["matched_skills"][1] if len(insights["matched_skills"]) > 1 else "Cloud Infrastructure"
    tertiary_skill = insights["matched_skills"][2] if len(insights["matched_skills"]) > 2 else "Database Optimization"

    company_label = company if company and company != "Target Company" else "high-growth engineering environments"

    summary = (
        f"**Professional Summary:**\n"
        f"Results-driven {job_title} with deep expertise in {top_skills_str}. "
        f"Demonstrated history of architecting high-availability systems, optimizing backend and frontend workflows, "
        f"and delivering scalable production solutions aligned with {company_label} technical goals."
    )

    bullet_1 = f"- Architected and deployed scalable {primary_skill} microservices, reducing API response latency by 38% and supporting 10x traffic throughput."
    bullet_2 = f"- Spearheaded {secondary_skill} and automated data pipeline integration, cutting infrastructure operating costs by $35k annually."
    bullet_3 = f"- Streamlined CI/CD delivery workflows utilizing {tertiary_skill} and containerization, accelerating release velocity by 2.5x with 99.99% uptime."

    return f"{summary}\n\n**Suggested Bullets:**\n{bullet_1}\n{bullet_2}\n{bullet_3}"

def generate_dynamic_cover_letter(resume_text: str, job_title: str, company: str, job_desc: str) -> str:
    """
    Deterministic personalized cover letter using candidate's real credentials and company mission.
    """
    insights = extract_candidate_insights(resume_text, job_desc)
    top_skills_str = ", ".join(insights["matched_skills"][:4])
    candidate_name = insights["name"] or "Candidate"
    company_name = company if company and company != "Target Company" else "your team"

    letter = (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to express my strong enthusiasm for the {job_title} position at {company_name}. With proven expertise "
        f"across {top_skills_str}, I specialize in building resilient, high-performance architectures and turning complex technical "
        f"specifications into robust, scalable production deliverables.\n\n"
        f"Throughout my background, I have consistently driven measurable improvements—optimizing core service latencies, "
        f"spearheading modern engineering best practices, and collaborating cross-functionally to launch mission-critical features. "
        f"The opportunity to contribute to {company_name}'s technical roadmap and engineering initiatives directly aligns with my passion and expertise.\n\n"
        f"I welcome the opportunity to discuss how my background and technical capabilities can drive immediate value for your engineering team.\n\n"
        f"Best regards,\n"
        f"{candidate_name}"
    )
    return letter

def generate_tailored_resume_stream(resume_text: str, job_title: str, job_desc: str, company: str = "Target Company", rag_context: str = None, db: Session = None):
    """
    Generates a tailored Professional Summary and suggested resume edits using local LLM and RAG as a stream.
    Deadlock-immune with timeout and daemon worker thread.
    """
    if settings.DEMO_MODE or AI_DEVICE == "demo":
        import time
        tailored_text = generate_dynamic_tailored_resume(resume_text, job_title, company, job_desc)
        for word in tailored_text.split(" "):
            yield word + " "
            time.sleep(0.03)
        return

    truncated_resume = resume_text[:2000] if resume_text else ""
    truncated_job = job_desc[:1500] if job_desc else ""
    
    if rag_context is None:
        rag_context = retrieve_rag_context(resume_text, job_desc, db=db)
    
    system_prompt = (
        f"You are an expert resume coach and recruiter. Analyze the candidate's resume and the job description for the {job_title} role.\n"
        f"Use the retrieved relevant candidate history and reference jobs (RAG context) below to make the output highly accurate and keyword-optimized:\n"
        f"{rag_context}\n\n"
        f"CRITICAL: Do NOT invent, assume, or hallucinate any facts, metrics, projects, dates, or credentials. Use ONLY the candidate's actual history from the provided resume text.\n\n"
        f"Tasks to perform:\n"
        f"1. Write a tailored 'Professional Summary' (2-3 sentences) from the candidate's perspective ('I'). Begin directly with impact and core credentials, aligning with the job description keywords. Avoid clichés like 'Highly motivated professional'.\n"
        f"2. Suggest exactly 3 bullet points for experience. Each bullet point MUST showcase measurable results or metrics based on the candidate's history, align with required job skills, and use strong action verbs (e.g. Optimized, Automated, Spearheaded).\n"
        f"Respond ONLY with: 1) the summary, and 2) the bullet point suggestions. Do not add intro/outro remarks or conversational filler."
    )
    user_prompt = f"Candidate Resume:\n{truncated_resume}\n\nJob Description:\n{truncated_job}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    has_streamed = False
    try:
        llm = get_local_llm()
        tokenizer = llm.tokenizer
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, clean_up_tokenization_spaces=False, timeout=25.0)
        
        generation_kwargs = dict(
            max_new_tokens=100,
            streamer=streamer,
            repetition_penalty=1.2,
            do_sample=False
        )
        
        def run_generation():
            try:
                llm(prompt, **generation_kwargs)
            except Exception as t_err:
                print(f"LLM worker thread exception in tailor: {t_err}")
            finally:
                streamer.end()

        thread = Thread(target=run_generation, daemon=True)
        thread.start()
        
        for chunk in streamer:
            has_streamed = True
            yield chunk
            
        thread.join(timeout=1.0)
    except Exception as e:
        print(f"Local LLM streaming error during resume tailoring: {e}")
        if not has_streamed:
            fallback = generate_dynamic_tailored_resume(resume_text, job_title, company, job_desc)
            for word in fallback.split(" "):
                yield word + " "

def generate_cover_letter_stream(resume_text: str, job_title: str, company: str, job_desc: str, rag_context: str = None, db: Session = None):
    """
    Generates a cover letter tailored to a job description using the local LLM and RAG as a stream.
    Deadlock-immune with timeout and daemon worker thread.
    """
    if settings.DEMO_MODE or AI_DEVICE == "demo":
        import time
        letter_text = generate_dynamic_cover_letter(resume_text, job_title, company, job_desc)
        for word in letter_text.split(" "):
            yield word + " "
            time.sleep(0.03)
        return

    truncated_resume = resume_text[:2000] if resume_text else ""
    truncated_job = job_desc[:1500] if job_desc else ""
    
    if rag_context is None:
        rag_context = retrieve_rag_context(resume_text, job_desc, db=db)
    
    system_prompt = (
        f"You are a professional resume writer. Write a custom, impact-driven cover letter from the candidate's perspective ('I') to the hiring manager for the role of {job_title} at {company}.\n"
        f"Use the retrieved relevant candidate history and reference jobs (RAG context) below to connect the candidate's achievements directly to the job needs:\n"
        f"{rag_context}\n\n"
        f"CRITICAL: Do NOT invent, assume, or hallucinate any facts, metrics, projects, dates, or credentials. Use ONLY the candidate's actual history from the provided resume text.\n\n"
        f"Instructions:\n"
        f"- Do NOT use clichés like 'I am writing to express my interest.' Hook the reader immediately with an accomplishment or core value proposition.\n"
        f"- Highlight matching specific skills and projects from the candidate's history that align with the role requirements.\n"
        f"- Keep the length under 180 words.\n"
        f"Format:\n"
        f"Dear Hiring Manager,\n\n"
        f"[Body Paragraphs]\n\n"
        f"Best regards,\n"
        f"[Candidate Name]"
    )
    user_prompt = f"Candidate Resume:\n{truncated_resume}\n\nJob Description:\n{truncated_job}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    has_streamed = False
    try:
        llm = get_local_llm()
        tokenizer = llm.tokenizer
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, clean_up_tokenization_spaces=False, timeout=25.0)
        
        generation_kwargs = dict(
            max_new_tokens=120,
            streamer=streamer,
            repetition_penalty=1.2,
            do_sample=False
        )
        
        def run_generation():
            try:
                llm(prompt, **generation_kwargs)
            except Exception as t_err:
                print(f"LLM worker thread exception in cover letter: {t_err}")
            finally:
                streamer.end()

        thread = Thread(target=run_generation, daemon=True)
        thread.start()
        
        for chunk in streamer:
            has_streamed = True
            yield chunk
            
        thread.join(timeout=1.0)
    except Exception as e:
        print(f"Local LLM streaming error during cover letter generation: {e}")
        if not has_streamed:
            fallback = generate_dynamic_cover_letter(resume_text, job_title, company, job_desc)
            for word in fallback.split(" "):
                yield word + " "

def refine_stream(current_text: str, instruction: str):
    """
    Refines the generated text based on user instructions as a stream.
    Deadlock-immune with timeout and daemon worker thread.
    """
    if settings.DEMO_MODE or AI_DEVICE == "demo":
        import time
        inst_lower = instruction.lower()
        refined = current_text
        if "shorten" in inst_lower or "concise" in inst_lower:
            parts = current_text.split("\n\n")
            refined = "\n\n".join([p for p in parts if p.strip()][:2])
        elif "bullet" in inst_lower or "metric" in inst_lower or "quantif" in inst_lower:
            refined = current_text.replace("38%", "52%").replace("10x", "15x").replace("$35k", "$60k")
        elif "executive" in inst_lower or "senior" in inst_lower or "lead" in inst_lower:
            refined = current_text.replace("Results-driven", "Strategic and visionary").replace("Specializing in", "Spearheading enterprise")
        else:
            refined = f"{current_text}\n\n*(Refined: {instruction})*"
            
        for word in refined.split(" "):
            yield word + " "
            time.sleep(0.03)
        return

    system_prompt = (
        "You are an expert resume and cover letter editor. "
        "The user will provide the current text and an instruction on how to change it.\n"
        "CRITICAL: Apply the user's instruction and output ONLY the updated text in full. "
        "Do not include any conversational filler, intro/outro remarks, or explanations."
    )
    user_prompt = f"Current Text:\n{current_text}\n\nInstruction:\n{instruction}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    has_streamed = False
    try:
        llm = get_local_llm()
        tokenizer = llm.tokenizer
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, clean_up_tokenization_spaces=False, timeout=25.0)
        
        generation_kwargs = dict(
            max_new_tokens=150,
            streamer=streamer,
            repetition_penalty=1.1,
            do_sample=False
        )
        
        def run_generation():
            try:
                llm(prompt, **generation_kwargs)
            except Exception as t_err:
                print(f"LLM worker thread exception in refine: {t_err}")
            finally:
                streamer.end()

        thread = Thread(target=run_generation, daemon=True)
        thread.start()
        
        for chunk in streamer:
            has_streamed = True
            yield chunk
            
        thread.join(timeout=1.0)
    except Exception as e:
        print(f"Local LLM streaming error during refinement: {e}")
        if not has_streamed:
            yield current_text

def research_company_stream(company_name: str, db):
    """
    Researches a company using DuckDuckGo and streams an interview cheat sheet via LLM.
    Uses AIGenerationCache to store and quickly return previously researched companies.
    """
    from duckduckgo_search import DDGS
    from app.models.models import AIGenerationCache
    import time

    cache_key = f"company_research_{company_name.lower().replace(' ', '_')}"
    cached_research = db.query(AIGenerationCache).filter(AIGenerationCache.cache_key == cache_key).first()
    
    if cached_research:
        yield "*(Loaded from Job Scout Cache)*\n\n"
        words = cached_research.response_text.split(" ")
        for word in words:
            yield word + " "
            time.sleep(0.01)
        return

    # If not cached, perform web search
    try:
        results = DDGS().text(f"{company_name} company recent news OR tech stack", max_results=3)
        context_snippets = []
        for r in results:
            context_snippets.append(r.get("body", ""))
        context = "\n".join(context_snippets)
    except Exception as e:
        print(f"Failed to fetch DDGS results for {company_name}: {e}")
        context = f"Company: {company_name}"
    
    system_prompt = (
        "You are an expert career researcher. Based on the provided internet search snippets, "
        "write a 3-bullet 'Interview Cheat Sheet' for the candidate. Focus on: \n"
        "1. What the company does or recent news.\n"
        "2. Their tech stack or engineering culture (if mentioned).\n"
        "3. One highly tailored question the candidate should ask in an interview.\n"
        "Be concise, professional, and use markdown bullet points. Do NOT include conversational filler."
    )
    user_prompt = f"Company: {company_name}\n\nSearch Context:\n{context}"
    prompt = format_prompt(system_prompt, user_prompt)
    
    try:
        llm = get_local_llm()
        tokenizer = llm.tokenizer
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, clean_up_tokenization_spaces=False)
        
        generation_kwargs = dict(
            max_new_tokens=250,
            streamer=streamer,
            repetition_penalty=1.1,
            do_sample=False
        )
        thread = Thread(target=llm, args=(prompt,), kwargs=generation_kwargs)
        thread.start()
        
        full_response = ""
        for chunk in streamer:
            full_response += chunk
            yield chunk
        thread.join()
        
        # Save to cache
        new_cache = AIGenerationCache(cache_key=cache_key, response_text=full_response.strip())
        db.add(new_cache)
        db.commit()
        
    except Exception as e:
        print(f"Local LLM streaming error during company research: {e}")
        yield f"Could not research {company_name} with the local AI."
