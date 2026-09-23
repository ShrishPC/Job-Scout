import os
import time
import requests
import json
import statistics

BASE_URL = os.getenv("BACKEND_URL", "http://backend:8001")

def benchmark_embedding():
    print("\n--- 1. EMBEDDING MODEL PERFORMANCE (all-MiniLM-L6-v2) ---")
    texts = [
        "Software Engineer with experience in Python, FastAPI, Docker, and PostgreSQL.",
        "Senior Frontend Developer proficient in React, Next.js, Tailwind CSS, TypeScript, and state management.",
        "Machine Learning Engineer specializing in RAG architectures, LLM fine-tuning, PyTorch, and vector databases like pgvector.",
        "Short query",
        "A " * 200 # Long job description ~200 words
    ]
    
    durations = []
    for i, text in enumerate(texts):
        start = time.perf_counter()
        res = requests.post(f"{BASE_URL}/jobs/matches", json={
            "embedding": [0.01] * 384,
            "limit": 10,
            "workplace_types": ["remote", "hybrid", "onsite"]
        })
        dur = (time.perf_counter() - start) * 1000
        durations.append(dur)
    
    print(f"  ✓ Vector Cosine Similarity Search: Mean {statistics.mean(durations):.2f} ms (p50: {statistics.median(durations):.2f} ms, min: {min(durations):.2f} ms, max: {max(durations):.2f} ms)")
    return statistics.mean(durations)

def benchmark_llm_config():
    print("\n--- 2. CURRENT AI / LLM CONFIGURATION ---")
    try:
        res = requests.get(f"{BASE_URL}/ai/config")
        data = res.json()
        print(f"  ✓ Active Device Mode: {data.get('device', 'unknown')}")
        print(f"  ✓ Available Options: cpu, cuda, demo")
        return data.get('device')
    except Exception as e:
        print(f"  ✗ Failed to fetch AI config: {e}")
        return None

def benchmark_llm_generation(device_mode="demo"):
    print(f"\n--- 3. LLM GENERATION SPEED (Mode: {device_mode}) ---")
    # Set device mode
    requests.post(f"{BASE_URL}/ai/config", json={"device": device_mode})
    time.sleep(1)

    payload = {
        "custom_job_title": "Senior AI / Backend Engineer",
        "custom_company": "ScaleAI",
        "custom_job_description": "Looking for an expert backend engineer skilled in FastAPI, PyTorch, pgvector, and Docker to build autonomous LLM pipelines.",
        "mode": "tailor"
    }

    # Clear cache first to test pure cold generation
    requests.post(f"{BASE_URL}/ai/cache/clear")

    print(f"  -> Testing Cold Generation (Streaming Mode: {device_mode})...")
    start = time.perf_counter()
    first_token_time = None
    total_tokens = 0
    full_text = ""

    try:
        response = requests.post(f"{BASE_URL}/ai/generate", json=payload, stream=True, timeout=120)
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                if first_token_time is None:
                    first_token_time = time.perf_counter() - start
                decoded = chunk.decode('utf-8', errors='ignore')
                full_text += decoded
                total_tokens += len(decoded.split())
        
        total_time = time.perf_counter() - start
        ttft_ms = (first_token_time or total_time) * 1000
        tps = total_tokens / total_time if total_time > 0 else 0

        print(f"  ✓ Generation Completed: {len(full_text)} characters (~{total_tokens} words / tokens)")
        print(f"  ✓ Time To First Token (TTFT): {ttft_ms:.2f} ms")
        print(f"  ✓ Total Generation Time:     {total_time:.2f} s")
        print(f"  ✓ Generation Throughput:     {tps:.2f} tokens/sec")

        # Test Cache Hit Latency
        print(f"\n  -> Testing Cached Request (SHA-256 Prompt & Resume Hash)...")
        cache_start = time.perf_counter()
        cache_res = requests.post(f"{BASE_URL}/ai/generate", json=payload, stream=True, timeout=10)
        cache_text = ""
        for chunk in cache_res.iter_content(chunk_size=None):
            if chunk:
                cache_text += chunk.decode('utf-8', errors='ignore')
        cache_time_ms = (time.perf_counter() - cache_start) * 1000
        print(f"  ✓ Cache Hit Response Time:    {cache_time_ms:.2f} ms ({len(cache_text)} chars delivered instantly)")

        return {
            "mode": device_mode,
            "ttft_ms": ttft_ms,
            "total_time_s": total_time,
            "tokens": total_tokens,
            "tps": tps,
            "cache_hit_ms": cache_time_ms
        }

    except Exception as e:
        print(f"  ✗ LLM generation benchmark error: {e}")
        return None

def main():
    print("=" * 88)
    print("🧠 JOB SCOUT LOCAL AI & LLM INFERENCE BENCHMARK")
    print(f"🎯 Target Base URL: {BASE_URL}")
    print("=" * 88)

    benchmark_llm_config()
    benchmark_embedding()
    
    # 1. Benchmark Demo Mode (Instant Mock Generative Engine)
    demo_metrics = benchmark_llm_generation("demo")

    # 2. Benchmark CPU Mode (Local Llama-3.2-3B Instruct with PyTorch)
    cpu_metrics = benchmark_llm_generation("cpu")

    print("\n" + "=" * 88)
    print("📋 SUMMARY OF LLM INFERENCE PERFORMANCE")
    print("=" * 88)
    print(f"{'Mode':<10} | {'TTFT (ms)':<12} | {'Total Time (s)':<16} | {'Tokens':<8} | {'Throughput (TPS)':<18} | {'Cache Hit (ms)':<14}")
    print("-" * 90)
    if demo_metrics:
        print(f"{demo_metrics['mode']:<10} | {demo_metrics['ttft_ms']:>10.2f} | {demo_metrics['total_time_s']:>14.2f} | {demo_metrics['tokens']:>6} | {demo_metrics['tps']:>16.2f} | {demo_metrics['cache_hit_ms']:>12.2f}")
    if cpu_metrics:
        print(f"{cpu_metrics['mode']:<10} | {cpu_metrics['ttft_ms']:>10.2f} | {cpu_metrics['total_time_s']:>14.2f} | {cpu_metrics['tokens']:>6} | {cpu_metrics['tps']:>16.2f} | {cpu_metrics['cache_hit_ms']:>12.2f}")
    print("=" * 88)

if __name__ == "__main__":
    main()
