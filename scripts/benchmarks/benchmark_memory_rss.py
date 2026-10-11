#!/usr/bin/env python3
"""
Memory Profiling Benchmark
Measures Baseline vs Peak RSS memory consumption with the local LLM loaded.
"""

import os
import sys
import time
import json
import psutil

# Ensure backend can be imported
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

def benchmark_memory_rss():
    print("=" * 60)
    print("🧠 BENCHMARKING BACKEND MEMORY CONSUMPTION (Peak RSS)")
    print("=" * 60)

    process = psutil.Process(os.getpid())
    
    # 1. Baseline RSS
    baseline_rss_mb = process.memory_info().rss / (1024.0 * 1024.0)
    print(f"[*] Baseline Process Memory (pre-model): {baseline_rss_mb:.2f} MB")

    # 2. Load Embedding Model
    print("[*] Loading SentenceTransformer embedding model (all-MiniLM-L6-v2)...")
    from app.services.llm_service import load_embedding_model, generate_embedding
    load_embedding_model("cpu")
    _ = generate_embedding("Warmup text for memory check")
    post_embed_rss_mb = process.memory_info().rss / (1024.0 * 1024.0)
    print(f"[+] Memory after embedding model loaded: {post_embed_rss_mb:.2f} MB (+{post_embed_rss_mb - baseline_rss_mb:.2f} MB)")

    # 3. Load Local LLM Pipeline
    print("[*] Loading local LLM pipeline (Llama-3.2-3B or TinyLlama fallback)...")
    from app.services.llm_service import get_local_llm, ACTIVE_LLM_MODEL_NAME
    t0 = time.perf_counter()
    llm = get_local_llm()
    t_load = time.perf_counter() - t0
    
    post_llm_rss_mb = process.memory_info().rss / (1024.0 * 1024.0)
    print(f"[+] Loaded {ACTIVE_LLM_MODEL_NAME} in {t_load:.2f} s")
    print(f"[+] Memory after LLM pipeline loaded: {post_llm_rss_mb:.2f} MB ({post_llm_rss_mb / 1024.0:.2f} GB)")

    # 4. Trigger single forward pass to capture peak inference RSS
    print("[*] Executing forward pass to capture peak execution RSS...")
    _ = llm("Test prompt for peak memory profiling", max_new_tokens=16, return_full_text=False)
    peak_rss_mb = process.memory_info().rss / (1024.0 * 1024.0)
    print(f"[+] Peak RSS observed during inference: {peak_rss_mb:.2f} MB ({peak_rss_mb / 1024.0:.2f} GB)")

    # System-level memory check
    sys_mem = psutil.virtual_memory()

    results = {
        "benchmark": "memory_rss_profiling",
        "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "model_loaded": ACTIVE_LLM_MODEL_NAME,
        "baseline_rss_mb": float(baseline_rss_mb),
        "post_embedding_rss_mb": float(post_embed_rss_mb),
        "post_llm_rss_mb": float(post_llm_rss_mb),
        "peak_inference_rss_mb": float(peak_rss_mb),
        "peak_inference_rss_gb": float(peak_rss_mb / 1024.0),
        "model_overhead_mb": float(peak_rss_mb - baseline_rss_mb),
        "system_total_ram_gb": float(sys_mem.total / (1024.0**3)),
        "system_available_ram_gb": float(sys_mem.available / (1024.0**3))
    }

    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "benchmarks", "results", "memory_rss.json"))
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("📊 MEMORY PROFILING RESULTS SUMMARY")
    print("=" * 60)
    print(f"Model Name           : {results['model_loaded']}")
    print(f"Peak RSS             : {results['peak_inference_rss_mb']:.2f} MB ({results['peak_inference_rss_gb']:.2f} GB)")
    print(f"Net Model Overhead   : {results['model_overhead_mb']:.2f} MB")
    print(f"Host System Total    : {results['system_total_ram_gb']:.2f} GB")
    print(f"[+] Saved results to {out_file}")

if __name__ == "__main__":
    benchmark_memory_rss()
