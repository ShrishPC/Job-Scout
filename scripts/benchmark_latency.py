import os
import time
import requests
import json
import statistics

BASE_URL = os.getenv("BACKEND_URL", "http://backend:8001")
SAMPLE_COUNT = 10

def benchmark_endpoint(name: str, method: str, path: str, payload=None, headers=None):
    durations = []
    status_codes = []
    
    url = f"{BASE_URL}{path}"
    
    # Warmup request
    try:
        if method == "GET":
            requests.get(url, headers=headers)
        elif method == "POST":
            requests.post(url, json=payload, headers=headers)
    except Exception:
        pass

    for _ in range(SAMPLE_COUNT):
        start = time.perf_counter()
        if method == "GET":
            resp = requests.get(url, headers=headers)
        elif method == "POST":
            resp = requests.post(url, json=payload, headers=headers)
        duration_ms = (time.perf_counter() - start) * 1000
        durations.append(duration_ms)
        status_codes.append(resp.status_code)

    avg = statistics.mean(durations)
    p50 = statistics.median(durations)
    p95 = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations)
    min_t = min(durations)
    max_t = max(durations)
    status_ok = all(s in (200, 201) for s in status_codes)

    return {
        "name": name,
        "method": method,
        "path": path,
        "avg_ms": avg,
        "p50_ms": p50,
        "p95_ms": p95,
        "min_ms": min_t,
        "max_ms": max_t,
        "status_ok": status_ok,
        "status_code": status_codes[0]
    }

def main():
    print("=" * 88)
    print("⚡ JOB SCOUT API PERFORMANCE & LATENCY BENCHMARK")
    print(f"🎯 Target Base URL: {BASE_URL} (Samples per endpoint: {SAMPLE_COUNT})")
    print("=" * 88)

    # 1. Root / Health
    r1 = benchmark_endpoint("Root & Healthcheck", "GET", "/")

    # 2. User Profile Sync
    r2 = benchmark_endpoint("Startup Profile Sync", "GET", "/user")

    # 3. Resume Vault List
    r3 = benchmark_endpoint("Resume Vault Listing", "GET", "/resumes")

    # 4. Kanban Pipeline Board
    r4 = benchmark_endpoint("Job Tracker Board", "GET", "/jobs/board")

    # 5. Hybrid RAG Vector Matching
    dummy_embedding = [0.05] * 384
    r5 = benchmark_endpoint(
        "HNSW Vector Matching", 
        "POST", 
        "/jobs/matches", 
        payload={"embedding": dummy_embedding, "limit": 12, "workplace_types": ["remote", "hybrid", "onsite"]}
    )

    # 6. ATS Match & Gap Diagnostic
    ats_payload = {
        "resume_text": "Experienced Full Stack Software Engineer with expertise in Python, FastAPI, React, TypeScript, Docker, Kubernetes, PostgreSQL, Redis, and PyTorch.",
        "job_title": "Senior Full Stack Engineer",
        "company": "NextGen AI",
        "job_description": "We are seeking a Senior Full Stack Engineer with strong experience in Python, FastAPI, React, PostgreSQL, Docker, Redis, and vector search. Must have 5+ years experience building scalable microservices and REST APIs."
    }
    r6 = benchmark_endpoint("ATS Diagnostic Rubric", "POST", "/ai/ats-analyze", payload=ats_payload)

    # Fetch real ats_data once for export benchmarks
    ats_res = requests.post(f"{BASE_URL}/ai/ats-analyze", json=ats_payload).json()

    # 7. ATS Report PDF Export
    export_payload = {
        "ats_data": ats_res,
        "format": "pdf",
        "candidate_name": "Shrish Prasad Chakraborty"
    }
    r7 = benchmark_endpoint("ATS Report PDF Export", "POST", "/export/ats-report", payload=export_payload)

    # 8. ATS Report DOCX Export
    export_docx_payload = dict(export_payload, format="docx")
    r8 = benchmark_endpoint("ATS Report DOCX Export", "POST", "/export/ats-report", payload=export_docx_payload)

    results = [r1, r2, r3, r4, r5, r6, r7, r8]

    print(f"{'Endpoint':<26} | {'Method':<6} | {'Status':<8} | {'Avg (ms)':<9} | {'p50 (ms)':<9} | {'Min (ms)':<9} | {'Max (ms)':<9}")
    print("-" * 90)
    for r in results:
        status_label = f"HTTP {r['status_code']}" if r['status_ok'] else f"ERR {r['status_code']}"
        print(f"{r['name']:<26} | {r['method']:<6} | {status_label:<8} | {r['avg_ms']:>8.2f}  | {r['p50_ms']:>8.2f}  | {r['min_ms']:>8.2f}  | {r['max_ms']:>8.2f}")
    print("=" * 90)

if __name__ == "__main__":
    main()
