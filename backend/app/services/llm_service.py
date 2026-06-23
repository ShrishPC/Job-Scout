import os
import json
import re
import torch
from app.services.llm_fallback import extract_structured_data_fallback, generate_embedding_fallback
from sentence_transformers import SentenceTransformer
from transformers import pipeline

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
            
            # Pad 384d to 768d to match our existing DB schema safely.
            if len(vec) < 768:
                vec.extend([0.0] * (768 - len(vec)))
            return vec[:768]
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
                if len(vec) < 768:
                    vec.extend([0.0] * (768 - len(vec)))
                results.append(vec[:768])
            return results
        except Exception as e:
            print(f"Local Batch Embedding Error: {e}")
            
    return [generate_embedding(t) for t in texts]

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
            # Batch embed all lines and compute similarity
            clean_texts = [clean for original, clean in lines]
            line_embeddings = generate_embeddings_batch(clean_texts)
            
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



