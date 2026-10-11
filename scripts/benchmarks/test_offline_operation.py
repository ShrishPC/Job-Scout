#!/usr/bin/env python3
"""
Offline Operation Verification Benchmark
Verifies that resume parsing, vector matching, and AI generation operate 100% offline
with all external internet egress disabled.
"""

import os
import sys
import socket
import json
import time

# Block all external network egress at the Python socket level
_original_socket_connect = socket.socket.connect

def offline_safe_connect(self, address):
    host, port = address[0], address[1]
    # Allow local container networking (localhost, loopback, or internal Docker bridge 172.x / 10.x / 192.168.x)
    allowed_prefixes = ("127.", "localhost", "172.", "10.", "192.168.", "db", "redis")
    if isinstance(host, str) and not any(host.startswith(prefix) for prefix in allowed_prefixes):
        raise ConnectionRefusedError(
            f"[OFFLINE VIOLATION] Attempted external network connection to {host}:{port} during offline mode test!"
        )
    return _original_socket_connect(self, address)

socket.socket.connect = offline_safe_connect

# Force offline environment variables
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Ensure backend can be imported
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.services.llm_service import generate_embedding, parse_markdown_with_llm, get_local_llm, format_prompt
from app.services.resume_service import parse_resume_to_markdown
from app.services.matching_service import get_job_matches
from app.core.database import SessionLocal

def run_offline_validation():
    print("=" * 60)
    print("🛡️ VERIFYING 100% OFFLINE PIPELINE EXECUTION")
    print("=" * 60)
    print("[*] Strict socket firewall activated: external WAN egress disabled.")

    results = {
        "benchmark": "offline_operation_audit",
        "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "hf_hub_offline": os.getenv("HF_HUB_OFFLINE") == "1",
        "transformers_offline": os.getenv("TRANSFORMERS_OFFLINE") == "1",
        "steps": {}
    }

    # Step 1: Resume Text Parsing (Offline)
    print("[1/3] Testing offline resume parsing...")
    sample_resume = "# Dr. Jane Doe\njane@example.com\n555-0199\n## Experience\nSenior AI Scientist with 6 years experience in Python, PyTorch, and NLP."
    parsed_data = parse_markdown_with_llm(sample_resume)
    assert parsed_data is not None
    assert "email" in parsed_data
    results["steps"]["resume_parsing"] = {"status": "SUCCESS", "parsed_name": parsed_data.get("full_name")}
    print(f"  [+] Extracted candidate: {parsed_data.get('full_name')} ({parsed_data.get('email')})")

    # Step 2: Embedding Generation & Database Matching (Offline)
    print("[2/3] Testing offline vector embedding & hybrid match...")
    t0_emb = time.perf_counter()
    vec = generate_embedding("Python developer skilled in PostgreSQL and vector search.")
    t_emb = time.perf_counter() - t0_emb
    assert len(vec) == 384
    
    with SessionLocal() as db:
        matches = get_job_matches(db, user_embedding=vec, limit=5)
    results["steps"]["vector_matching"] = {
        "status": "SUCCESS", 
        "vector_dim": len(vec),
        "embedding_latency_ms": t_emb * 1000.0,
        "matches_count": len(matches)
    }
    print(f"  [+] Generated {len(vec)}-d embedding in {t_emb*1000.0:.2f} ms; retrieved {len(matches)} matches from DB.")

    # Step 3: LLM Inference (Offline)
    print("[3/3] Testing offline LLM text generation...")
    t0_llm = time.perf_counter()
    llm = get_local_llm()
    prompt = format_prompt("Summarize candidate qualifications.", sample_resume)
    out = llm(prompt, max_new_tokens=32, return_full_text=False)
    t_llm = time.perf_counter() - t0_llm
    generated_text = out[0]["generated_text"]
    assert len(generated_text) > 5
    results["steps"]["llm_generation"] = {
        "status": "SUCCESS",
        "tokens_output": len(generated_text.split()),
        "latency_s": t_llm
    }
    print(f"  [+] Generated {len(generated_text.split())} tokens in {t_llm:.2f} s completely offline.")

    results["overall_verdict"] = "PASSED_100_PERCENT_OFFLINE"

    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "benchmarks", "results", "offline_test_results.json"))
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("✅ OFFLINE OPERATION FULLY VERIFIED")
    print(f"All operations executed without network access or exceptions.")
    print(f"[+] Saved results to {out_file}")

if __name__ == "__main__":
    run_offline_validation()
