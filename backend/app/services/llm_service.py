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

# 1. Local Embeddings (Fast, small, offline)
try:
    print(f"Initializing Embedding Model from {MODEL_CACHE}...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=MODEL_CACHE)
except Exception as e:
    print(f"Failed to load sentence-transformers: {e}")
    embedding_model = None

# 2. Local LLM (For Parsing)
local_llm = None
def get_local_llm():
    global local_llm
    if local_llm is None:
        print(f"Loading Local AI Model (TinyLlama) from {MODEL_CACHE}...")
        # Ensure we use a CPU pipeline, handling generation and caching locally
        local_llm = pipeline(
            "text-generation", 
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
            device="cpu",
            model_kwargs={"cache_dir": MODEL_CACHE}
        )
    return local_llm

def parse_markdown_with_llm(markdown_content: str, **kwargs):
    """
    Extracts structured data using a local LLM with TinyLlama chat formatting.
    """
    # Truncate content to 3000 chars to avoid exceeding context window (2048 tokens) of TinyLlama
    truncated_content = markdown_content[:3000] if markdown_content else ""
    
    # TinyLlama Chat Template formatting to enforce strict JSON output
    prompt = f"""<|system|>
You are a professional resume parsing assistant. Extract candidate information from the resume and respond ONLY with a valid JSON object. Do not include any explanations, introduction, markdown styling blocks, or surrounding text.
The JSON object must follow this exact structure:
{{
  "full_name": "Name",
  "email": "Email",
  "phone": "Phone number",
  "target_role": "Target role/Job title",
  "target_location": "Preferred location or 'Remote'",
  "skills": ["Skill 1", "Skill 2"],
  "experience": [
    {{"title": "Role Title", "company": "Company Name", "duration": "Duration", "description": "Short description"}}
  ],
  "education": [
    {{"degree": "Degree/Major", "institution": "School Name", "year": "Graduation Year"}}
  ]
}}</s>
<|user|>
Resume details to parse:
{truncated_content}</s>
<|assistant|>
"""
    
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
    # Truncate to 2000 chars to fit context window and prevent generation timeouts
    truncated_desc = description[:2000] if description else ""
    
    prompt = f"""<|system|>
You are a job parsing assistant. You must analyze the job description and output ONLY a single integer representing the minimum years of experience required. Do not output any other text, explanation, or units (e.g. write '3', not '3 years'). Default is 0.</s>
<|user|>
Job Description:
{truncated_desc}</s>
<|assistant|>
"""
    
    try:
        llm = get_local_llm()
        res = llm(prompt, max_new_tokens=10, return_full_text=False, clean_up_tokenization_spaces=False)
        output_text = res[0]['generated_text'].strip()
        match = re.search(r'\d+', output_text)
        return int(match.group()) if match else 0
    except Exception as e:
        print(f"Local LLM Error during experience extraction: {e}")
        return 0


