import os
import json
import re
from app.services.llm_fallback import extract_structured_data_fallback, generate_embedding_fallback
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Optimized Local Model Storage (Ensures portability across machines)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_CACHE = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODEL_CACHE, exist_ok=True)

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
PARSER_LLM_MODEL_NAME = os.getenv("PARSER_LLM_MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# 1. Local Embeddings (Fast, small, offline)
try:
    print(f"Initializing Embedding Model ({EMBEDDING_MODEL_NAME}) from {MODEL_CACHE}...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, cache_folder=MODEL_CACHE)
except Exception as e:
    print(f"Failed to load sentence-transformers model {EMBEDDING_MODEL_NAME}: {e}")
    try:
        print("Attempting fallback initialization with all-MiniLM-L6-v2...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=MODEL_CACHE)
    except Exception as fallback_err:
        print(f"Fallback model failed: {fallback_err}")
        embedding_model = None

# 2. Local LLM (For Parsing)
local_llm = None
def get_local_llm():
    global local_llm
    if local_llm is None:
        print(f"Loading Local AI Model ({PARSER_LLM_MODEL_NAME}) from {MODEL_CACHE}...")
        try:
            local_llm = pipeline(
                "text-generation", 
                model=PARSER_LLM_MODEL_NAME, 
                device="cpu",
                model_kwargs={"cache_dir": MODEL_CACHE}
            )
        except Exception as e:
            print(f"Failed to load {PARSER_LLM_MODEL_NAME}: {e}")
            print("Attempting fallback to TinyLlama/TinyLlama-1.1B-Chat-v1.0...")
            local_llm = pipeline(
                "text-generation", 
                model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
                device="cpu",
                model_kwargs={"cache_dir": MODEL_CACHE}
            )
    return local_llm

def format_prompt(system_prompt: str, user_prompt: str) -> str:
    model_lower = PARSER_LLM_MODEL_NAME.lower()
    if "qwen" in model_lower:
        return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
    elif "tinyllama" in model_lower:
        return f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_prompt}</s>\n<|assistant|>\n"
    elif "phi" in model_lower:
        return f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{user_prompt}<|end|>\n<|assistant|>\n"
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

def extract_experience_from_job(description: str, **kwargs):
    """
    Uses local LLM to extract the minimum years of experience required.
    """
    truncated_desc = description[:2000] if description else ""
    
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


