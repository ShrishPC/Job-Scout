#!/usr/bin/env python3
"""
LLM Cache Latency Benchmark
Measures Cold generation time vs AIGenerationCache response time
across 5 repetitions on CPU.
"""

import os
import sys
import time
import json
import hashlib
import requests
from sqlalchemy import create_engine, text

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8001")
DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:password@localhost:5435/job_scout")

def benchmark_llm_caching():
    print("=" * 60)
    print("🚀 BENCHMARKING AI GENERATION CACHING (Cold vs Warm)")
    print("=" * 60)

    # Clean existing caches to ensure pure cold runs
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE ai_generation_caches;"))
            conn.commit()
            print("[+] Cleared ai_generation_caches for fresh cold measurements.")
    except Exception as e:
        print(f"[!] Warning: Could not truncate cache table via DB: {e}")

    # Test payload
    payload = {
        "mode": "tailor",
        "custom_job_title": "Senior Distributed Systems Architect",
        "custom_company": "ScalePlatform Inc.",
        "custom_job_description": (
            "Seeking an experienced Distributed Systems Architect with 8+ years experience in Python, "
            "PostgreSQL, Redis, and high-concurrency microservices. Responsible for designing fault-tolerant "
            "event streams, caching architectures, and database scalability patterns."
        )
    }

    cold_latencies_ms = []
    cached_latencies_ms = []

    print("\n[*] Running 5 Cold vs Cached Measurement Pairs...")

    for rep in range(1, 6):
        # Vary prompt slightly for each pair to test 5 distinct cold requests
        rep_payload = dict(payload)
        rep_payload["custom_job_title"] = f"Senior Distributed Systems Architect (Cohort {rep})"

        # 1. Cold Request
        print(f"[{rep}/5] Timing Cold Request...", end="", flush=True)
        t0 = time.perf_counter()
        res_cold = requests.post(f"{API_BASE}/ai/generate", json=rep_payload, stream=True)
        cold_text = ""
        for chunk in res_cold.iter_content(chunk_size=128):
            if chunk:
                cold_text += chunk.decode('utf-8', errors='ignore')
        t1 = time.perf_counter()
        cold_ms = (t1 - t0) * 1000.0
        cold_latencies_ms.append(cold_ms)
        print(f" -> Done in {cold_ms:.2f} ms ({cold_ms/1000.0:.2f} s)")

        # 2. Warm Request (Identical payload, should hit AIGenerationCache)
        print(f"[{rep}/5] Timing Cached Request...", end="", flush=True)
        t0_cached = time.perf_counter()
        res_cached = requests.post(f"{API_BASE}/ai/generate", json=rep_payload, stream=True)
        cached_text = ""
        for chunk in res_cached.iter_content(chunk_size=128):
            if chunk:
                cached_text += chunk.decode('utf-8', errors='ignore')
        t1_cached = time.perf_counter()
        cached_ms = (t1_cached - t0_cached) * 1000.0
        cached_latencies_ms.append(cached_ms)
        print(f" -> Done in {cached_ms:.2f} ms")

    import numpy as np
    results = {
        "benchmark": "llm_caching_evaluation",
        "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "repetitions": 5,
        "cold_latencies_ms": cold_latencies_ms,
        "cached_latencies_ms": cached_latencies_ms,
        "cold_stats": {
            "mean_s": float(np.mean(cold_latencies_ms) / 1000.0),
            "mean_ms": float(np.mean(cold_latencies_ms)),
            "min_ms": float(np.min(cold_latencies_ms)),
            "max_ms": float(np.max(cold_latencies_ms))
        },
        "cached_stats": {
            "mean_ms": float(np.mean(cached_latencies_ms)),
            "min_ms": float(np.min(cached_latencies_ms)),
            "max_ms": float(np.max(cached_latencies_ms))
        },
        "speedup_factor": float(np.mean(cold_latencies_ms) / np.mean(cached_latencies_ms))
    }

    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "benchmarks", "results", "llm_cache_benchmark.json"))
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("📊 LLM CACHE BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Average Cold Generation : {results['cold_stats']['mean_s']:.2f} s ({results['cold_stats']['mean_ms']:.2f} ms)")
    print(f"Average Cached Latency  : {results['cached_stats']['mean_ms']:.2f} ms")
    print(f"Cache Speedup Factor    : {results['speedup_factor']:.1f}x faster")
    print(f"[+] Saved raw data to {out_file}")

if __name__ == "__main__":
    benchmark_llm_caching()
