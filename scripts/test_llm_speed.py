import time
import sys
from app.services.llm_service import generate_tailored_resume_stream

dummy_resume = """
John Doe
Software Engineer
Experience: 5 years building Python and Node.js backends.
Skills: Python, FastAPI, Docker, PostgreSQL.
"""
dummy_job = """
Looking for a Senior Backend Engineer.
Must have experience with Python, API design, and containerization.
"""

print("Initializing local LLM on CPU...")
start_init = time.time()
stream = generate_tailored_resume_stream(
    resume_text=dummy_resume,
    job_title="Senior Backend Engineer",
    job_desc=dummy_job,
    company="TechCorp",
    rag_context=""
)
init_time = time.time() - start_init
print(f"Model Initialization / Warmup Time: {init_time:.2f} seconds\n")
print("Streaming response:")

start_gen = time.time()
token_count = 0
try:
    for token in stream:
        sys.stdout.write(token)
        sys.stdout.flush()
        token_count += 1
except Exception as e:
    print(f"\nError during generation: {e}")
    
end_gen = time.time()
gen_time = end_gen - start_gen

print(f"\n\n--- STATS ---")
print(f"Total time generating: {gen_time:.2f} seconds")
print(f"Tokens/chunks received: {token_count}")
if gen_time > 0:
    print(f"Speed: {(token_count / gen_time):.2f} chunks per second")

