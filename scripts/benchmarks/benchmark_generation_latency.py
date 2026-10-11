#!/usr/bin/env python3
"""
LLM Generation Latency & Throughput Benchmark
Measures tokens/sec, total generation time, CPU thread allocation, and precision dtype.
"""

import os
import sys
import time
import json
import torch

# Ensure backend can be imported
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.services.llm_service import get_local_llm, ACTIVE_LLM_MODEL_NAME, format_prompt

def benchmark_generation():
    print("=" * 60)
    print("🚀 BENCHMARKING LOCAL LLM INFERENCE LATENCY & THROUGHPUT")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    initial_threads = torch.get_num_threads()
    dtype = str(torch.float16 if device == "cuda" else torch.bfloat16)

    print(f"Device: {device.upper()}")
    print(f"Initial thread count: {initial_threads}")
    print(f"Precision dtype: {dtype}")

    # Load LLM
    print("[*] Loading local LLM pipeline...")
    t0_load = time.perf_counter()
    llm = get_local_llm()
    t_load = time.perf_counter() - t0_load
    clamped_threads = torch.get_num_threads()
    print(f"[+] Loaded {ACTIVE_LLM_MODEL_NAME} in {t_load:.2f} s")
    print(f"[+] Thread allocation: Initial={initial_threads} -> Clamped for inference={clamped_threads}")


    test_prompt = format_prompt(
        "You are an ATS resume optimization assistant. Write 3 impactful bullet points for a Python developer.",
        "Candidate with 5 years experience in FastAPI and PostgreSQL."
    )

    max_tokens = 128
    print(f"[*] Running generation with max_new_tokens={max_tokens}...")
    
    t0_gen = time.perf_counter()
    output = llm(
        test_prompt,
        max_new_tokens=max_tokens,
        return_full_text=False,
        clean_up_tokenization_spaces=False
    )
    t_gen = time.perf_counter() - t0_gen
    generated_text = output[0]["generated_text"]

    # Approximate token count by word/subword heuristic
    # (or via tokenizer if accessible)
    tokenizer = getattr(llm, "tokenizer", None)
    if tokenizer:
        token_count = len(tokenizer.encode(generated_text))
    else:
        token_count = len(generated_text.split())

    tokens_per_sec = token_count / t_gen if t_gen > 0 else 0.0

    results = {
        "benchmark": "llm_generation_throughput",
        "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "model": ACTIVE_LLM_MODEL_NAME,
        "device": device,
        "cuda_available": torch.cuda.is_available(),
        "initial_thread_count": initial_threads,
        "cpu_thread_count": clamped_threads,
        "torch_dtype": dtype,
        "max_new_tokens_requested": max_tokens,
        "tokens_generated": token_count,
        "total_latency_seconds": float(t_gen),
        "tokens_per_second": float(tokens_per_sec),
        "sample_output_preview": generated_text[:200]
    }

    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "benchmarks", "results", "generation_latency.json"))
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("📊 GENERATION THROUGHPUT RESULTS")
    print("=" * 60)
    print(f"Model Name        : {results['model']}")
    print(f"Device / Threads  : {device} (Initial: {initial_threads}, Clamped: {clamped_threads} threads, {dtype})")
    print(f"Tokens Generated  : {token_count} tokens")
    print(f"Total Time        : {t_gen:.2f} s")
    print(f"Throughput        : {tokens_per_sec:.2f} tokens/sec")
    print(f"[+] Saved results to {out_file}")

if __name__ == "__main__":
    benchmark_generation()
