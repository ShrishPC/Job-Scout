import os
import sys

# Add backend to path so we can import the models safely
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

def download():
    print("🚀 Pre-downloading Local AI Models for Job Scout...")
    
    # Define models directory path
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    MODEL_CACHE = os.path.join(PROJECT_ROOT, "models")
    os.makedirs(MODEL_CACHE, exist_ok=True)
    
    print(f"📁 Cache folder set to: {MODEL_CACHE}")
    
    # 1. Read model configurations from environment
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    PARSER_LLM_MODEL_NAME = os.getenv("PARSER_LLM_MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    
    # 2. Download sentence-transformers model (Embedding)
    try:
        from sentence_transformers import SentenceTransformer
        print(f"\n📥 Downloading SentenceTransformer ('{EMBEDDING_MODEL_NAME}')...")
        _ = SentenceTransformer(EMBEDDING_MODEL_NAME, cache_folder=MODEL_CACHE)
        print(f"✅ SentenceTransformer model '{EMBEDDING_MODEL_NAME}' downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download SentenceTransformer '{EMBEDDING_MODEL_NAME}': {e}")
        
    # 3. Download LLM parser model (LLM Parsing)
    try:
        from transformers import pipeline
        print(f"\n📥 Downloading Local LLM ('{PARSER_LLM_MODEL_NAME}')...")
        _ = pipeline(
            "text-generation", 
            model=PARSER_LLM_MODEL_NAME, 
            device="cpu",
            model_kwargs={"cache_dir": MODEL_CACHE}
        )
        print(f"✅ Local LLM model '{PARSER_LLM_MODEL_NAME}' downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download Local LLM '{PARSER_LLM_MODEL_NAME}': {e}")

    print("\n🎉 Local models are fully cached and ready to use offline!")

if __name__ == "__main__":
    download()
