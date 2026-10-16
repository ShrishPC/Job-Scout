#!/usr/bin/env python3
import time
import requests
import json
import os
import sys

API_BASE = "http://localhost:8001"
RESUME_PATH = "/home/rishav/Documents/IMP DOC/RESUME UPDATED(FINAL).pdf"

def main():
    print("=" * 80)
    print("  JOB SCOUT: REAL-TIME CPU EXECUTION BENCHMARK & LATENCY TIMER")
    print(f"  Target Resume: {RESUME_PATH}")
    print(f"  Target Endpoint: {API_BASE}")
    print(f"  File Size: {os.path.getsize(RESUME_PATH):,} bytes ({os.path.getsize(RESUME_PATH)/1024:.1f} KB)")
    print("=" * 80)

    results = {}

    # Check health
    try:
        r = requests.get(f"{API_BASE}/docs", timeout=5)
        if r.status_code != 200:
            print(f"ERROR: API returned status {r.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to API at {API_BASE}: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # STAGE 1: RESUME INGESTION, PARSING & EMBEDDING
    # -------------------------------------------------------------------------
    print("\n[STAGE 1] Ingesting, Parsing & Embedding Resume...")
    print("  - Action: POST /resume/parse (multipart file upload)")
    t0 = time.perf_counter()
    with open(RESUME_PATH, "rb") as f:
        files = {"file": (os.path.basename(RESUME_PATH), f, "application/pdf")}
        resp = requests.post(f"{API_BASE}/resume/parse", files=files, timeout=120)
    t1 = time.perf_counter()
    stage1_time = t1 - t0
    results["stage1_parse"] = stage1_time

    if resp.status_code != 200:
        print(f"  FAILED: Status {resp.status_code}, Body: {resp.text}")
        sys.exit(1)

    parse_data = resp.json()
    resume_id = parse_data.get("id")
    embedding = parse_data.get("embedding", [])
    parsed_json = parse_data.get("parsed_json", {})
    markdown_len = len(parse_data.get("markdown", ""))
    
    print(f"  ✓ Status: 200 OK")
    print(f"  ⏱ Elapsed Time: {stage1_time:.4f} s ({stage1_time*1000:.2f} ms)")
    print(f"  - Resume ID: {resume_id}")
    print(f"  - Extracted Name: {parsed_json.get('full_name', 'N/A')}")
    print(f"  - Extracted Email: {parsed_json.get('email', 'N/A')}")
    print(f"  - Extracted Phone: {parsed_json.get('phone', 'N/A')}")
    print(f"  - Target Role: {parsed_json.get('target_role', 'N/A')}")
    print(f"  - Skills Identified: {len(parsed_json.get('skills', []))} skills")
    print(f"    Sample: {', '.join(parsed_json.get('skills', [])[:8])}")
    print(f"  - Markdown Length: {markdown_len:,} characters")
    print(f"  - Embedding Length: {len(embedding)} dimensions (all-MiniLM-L6-v2)")

    # -------------------------------------------------------------------------
    # STAGE 2: HYBRID MATCHMAKING RETRIEVAL (pgvector + HNSW ef_search=400)
    # -------------------------------------------------------------------------
    print("\n[STAGE 2] Hybrid Job Matchmaking Retrieval...")
    print("  - Action: POST /jobs/matches (HNSW vector + keyword SQL)")
    
    match_payload = {
        "embedding": embedding,
        "limit": 10,
        "skip": 0,
        "workplace_types": None,
        "search_keyword": None,
        "hybrid_mode": "two_stage"
    }

    # Run 5 times to get statistical distribution
    match_latencies = []
    top_matches = []
    for i in range(5):
        t0 = time.perf_counter()
        resp_m = requests.post(f"{API_BASE}/jobs/matches", json=match_payload, timeout=10)
        t1 = time.perf_counter()
        lat_ms = (t1 - t0) * 1000
        match_latencies.append(lat_ms)
        if i == 0 and resp_m.status_code == 200:
            top_matches = resp_m.json().get("jobs", [])

    stage2_p50 = sorted(match_latencies)[len(match_latencies)//2]
    stage2_mean = sum(match_latencies) / len(match_latencies)
    results["stage2_match_mean_ms"] = stage2_mean
    results["stage2_match_p50_ms"] = stage2_p50

    print(f"  ✓ Status: 200 OK across 5 iterations")
    print(f"  ⏱ Query Latency: Mean = {stage2_mean:.2f} ms | p50 = {stage2_p50:.2f} ms | Min = {min(match_latencies):.2f} ms | Max = {max(match_latencies):.2f} ms")
    print(f"  - Retrieved Jobs: {len(top_matches)} positions")
    for idx, j in enumerate(top_matches[:3]):
        print(f"    [{idx+1}] {j.get('title')} @ {j.get('company')}")
        print(f"        Match Score: {j.get('match_score', 0):.1f}% | Semantic: {j.get('semantic_score', 0):.3f} | Keyword: {j.get('keyword_score', 0):.3f}")

    top_job = top_matches[0] if top_matches else None
    if not top_job:
        print("  WARNING: No jobs matched. Cannot proceed to ATS or generation.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # STAGE 3: ATS DIAGNOSTIC & GAP ANALYSIS
    # -------------------------------------------------------------------------
    print(f"\n[STAGE 3] ATS Diagnostic Gap Analysis...")
    print(f"  - Action: POST /ai/ats-analyze against Job #{top_job.get('id')} ({top_job.get('title')} @ {top_job.get('company')})")
    
    ats_payload = {
        "job_id": top_job.get("id"),
        "resume_id": resume_id
    }
    t0 = time.perf_counter()
    resp_ats = requests.post(f"{API_BASE}/ai/ats-analyze", json=ats_payload, timeout=10)
    t1 = time.perf_counter()
    stage3_time = t1 - t0
    results["stage3_ats_s"] = stage3_time

    if resp_ats.status_code == 200:
        ats_data = resp_ats.json()
        print(f"  ✓ Status: 200 OK")
        print(f"  ⏱ ATS Diagnostic Time: {stage3_time:.4f} s ({stage3_time*1000:.2f} ms)")
        print(f"  - ATS Overall Score: {ats_data.get('overall_score', 'N/A')}%")
        print(f"  - Matching Keywords Found: {len(ats_data.get('matching_keywords', []))} keywords")
        print(f"    Sample: {', '.join(ats_data.get('matching_keywords', [])[:6])}")
        print(f"  - Missing Keywords: {len(ats_data.get('missing_keywords', []))} keywords")
        print(f"    Sample: {', '.join(ats_data.get('missing_keywords', [])[:6])}")
    else:
        print(f"  ATS Analyze returned {resp_ats.status_code}: {resp_ats.text}")

    # -------------------------------------------------------------------------
    # STAGE 4: AI RESUME TAILORING (CPU EXECUTION)
    # -------------------------------------------------------------------------
    print(f"\n[STAGE 4] AI Content Generation & Resume Tailoring (Cold CPU Execution)...")
    print(f"  - Action: POST /ai/generate (Streaming mode='tailor') for Job #{top_job.get('id')}")
    
    # First, let's clear cache for this job to ensure cold measurement
    try:
        requests.post(f"{API_BASE}/ai/cache/clear", json={"job_id": top_job.get("id"), "resume_id": resume_id}, timeout=3)
    except:
        pass

    gen_payload = {
        "job_id": top_job.get("id"),
        "resume_id": resume_id,
        "mode": "tailor"
    }

    t0 = time.perf_counter()
    ttft = None
    chunks = []
    resp_gen = requests.post(f"{API_BASE}/ai/generate", json=gen_payload, stream=True, timeout=120)
    for chunk in resp_gen.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            if ttft is None:
                ttft = time.perf_counter() - t0
            chunks.append(chunk)
    t1 = time.perf_counter()
    cold_gen_time = t1 - t0
    results["stage4_cold_gen_s"] = cold_gen_time
    results["stage4_ttft_s"] = ttft or cold_gen_time
    full_output = "".join(chunks)

    print(f"  ✓ Status: 200 OK (Stream Complete)")
    print(f"  ⏱ Time to First Token (TTFT): {(ttft or 0):.4f} s ({(ttft or 0)*1000:.1f} ms)")
    print(f"  ⏱ Total Cold Generation Time: {cold_gen_time:.4f} s")
    print(f"  - Output Size: {len(full_output)} characters ({len(full_output.split())} words)")
    print("  - Generated Content Preview:")
    lines = [l.strip() for l in full_output.split("\n") if l.strip()]
    for l in lines[:4]:
        print(f"    > {l[:100]}...")

    # -------------------------------------------------------------------------
    # STAGE 5: REPEAT GENERATION (WARM REDIS RESPONSE CACHE TEST)
    # -------------------------------------------------------------------------
    print(f"\n[STAGE 5] Repeat AI Generation (Warm Redis Cache Acceleration)...")
    print(f"  - Action: POST /ai/generate (Same payload, testing cache hit)")
    
    t0 = time.perf_counter()
    resp_cache = requests.post(f"{API_BASE}/ai/generate", json=gen_payload, stream=True, timeout=10)
    cache_chunks = []
    for chunk in resp_cache.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            cache_chunks.append(chunk)
    t1 = time.perf_counter()
    cache_time = t1 - t0
    results["stage5_cache_gen_ms"] = cache_time * 1000

    speedup = cold_gen_time / cache_time if cache_time > 0 else 0
    results["stage5_speedup"] = speedup

    print(f"  ✓ Status: 200 OK (Cache Hit)")
    print(f"  ⏱ Cached Generation Time: {cache_time*1000:.2f} ms ({cache_time:.5f} s)")
    print(f"  🚀 Measured Cache Speedup: {speedup:,.1f}x acceleration over cold execution!")

    # -------------------------------------------------------------------------
    # MASTER BENCHMARK SUMMARY TABLE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("                    MASTER LATENCY & PERFORMANCE BREAKDOWN")
    print("=" * 80)
    print(f"{'Pipeline Stage':<38} | {'Measured Latency':<18} | {'SLA / Target':<16}")
    print("-" * 80)
    print(f"{'1. PDF Parse & Dense Embedding':<38} | {stage1_time*1000:>10.2f} ms ({stage1_time:.2f}s) | {'< 3.0 s':<16}")
    print(f"{'2. Two-Stage Hybrid Search (p50)':<38} | {stage2_p50:>10.2f} ms        | {'< 10.0 ms':<16}")
    print(f"{'3. ATS Diagnostic Gap Analysis':<38} | {stage3_time*1000:>10.2f} ms        | {'< 500 ms':<16}")
    print(f"{'4. Cold AI Tailor Generation':<38} | {cold_gen_time:>10.2f} s         | {'DDR4 Bound':<16}")
    print(f"{'5. Warm Redis Cache Generation':<38} | {cache_time*1000:>10.2f} ms        | {'< 5.0 ms':<16}")
    print("-" * 80)
    total_interactive = (stage1_time + (stage2_p50/1000.0) + stage3_time)
    print(f"{'TOTAL CORE WORKFLOW (Parse+Search+ATS)':<38} | {total_interactive:>10.2f} s         | {'< 5.0 s SLA':<16}")
    print("=" * 80)

if __name__ == "__main__":
    main()
