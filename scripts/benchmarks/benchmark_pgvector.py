#!/usr/bin/env python3
"""
Comprehensive pgvector & HNSW Performance Benchmark
Measures sequential scan vs HNSW vs hybrid query at 10,000 and 100,000 rows (N=200 queries each).
Calculates p50, p95, p99, mean, and Recall@10 against ground-truth sequential scans.
Analyzes query execution plan via EXPLAIN (ANALYZE).
"""

import os
import sys
import time
import random
import json
import numpy as np
from sqlalchemy import create_engine, text

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:password@db:5432/job_scout")
try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception:
    DB_URL = "postgresql+psycopg2://postgres:password@localhost:5435/job_scout"
    engine = create_engine(DB_URL)

VECTOR_DIM = 384
N_QUERIES = 200

def generate_random_vector():
    vec = [float(v) for v in np.random.uniform(-1.0, 1.0, VECTOR_DIM)]
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = [v / norm for v in vec]
    return f"[{','.join(f'{x:.6f}' for x in vec)}]"

def run_benchmark_for_scale(conn, num_rows: int):
    print(f"\n=======================================================")
    print(f"  BENCHMARKING SCALE: {num_rows:,} ROWS (N={N_QUERIES} queries)")
    print(f"=======================================================")
    
    table_name = f"benchmark_jobs_{num_rows}"
    
    # 1. Setup table
    print(f"[*] Creating benchmark table {table_name}...")
    conn.execute(text(f"DROP TABLE IF EXISTS {table_name};"))
    conn.execute(text(f"""
        CREATE TABLE {table_name} (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            description TEXT,
            embedding vector({VECTOR_DIM})
        );
    """))
    conn.commit()

    # 2. Populate rows in batches
    print(f"[*] Inserting {num_rows:,} mock job embeddings...")
    sample_titles = ["Senior Python Developer", "React Frontend Engineer", "DevOps Cloud Architect", "Machine Learning Engineer", "Database Specialist"]
    sample_skills = ["FastAPI", "React", "Docker", "PostgreSQL", "Kubernetes", "AWS", "TypeScript", "Python"]
    
    batch_size = 2000
    for b_start in range(0, num_rows, batch_size):
        curr_batch = min(batch_size, num_rows - b_start)
        values = []
        for _ in range(curr_batch):
            t = random.choice(sample_titles)
            d = f"Job requiring skills in {', '.join(random.sample(sample_skills, 3))}."
            v = generate_random_vector()
            values.append(f"('{t}', '{d}', '{v}')")
        insert_sql = f"INSERT INTO {table_name} (title, description, embedding) VALUES {','.join(values)};"
        conn.execute(text(insert_sql))
    conn.commit()
    print(f"[+] Inserted {num_rows:,} rows successfully.")

    # Generate query vectors beforehand
    query_vectors = [generate_random_vector() for _ in range(N_QUERIES)]

    # 3. Sequential Scan (Force enable_seqscan=on, enable_indexscan=off)
    print(f"[*] Running Sequential Scan queries (N={N_QUERIES})...")
    conn.execute(text("SET enable_seqscan = on; SET enable_indexscan = off;"))
    seq_latencies = []
    seq_ground_truth_ids = []
    
    for q_vec in query_vectors:
        t0 = time.perf_counter()
        res = conn.execute(text(f"""
            SELECT id FROM {table_name}
            ORDER BY embedding <=> '{q_vec}'
            LIMIT 10;
        """)).fetchall()
        t1 = time.perf_counter()
        seq_latencies.append((t1 - t0) * 1000.0)
        seq_ground_truth_ids.append([r[0] for r in res])

    # 4. Build HNSW Index
    print(f"[*] Building HNSW index on {table_name}...")
    index_name = f"idx_hnsw_{num_rows}"
    t0_idx = time.perf_counter()
    conn.execute(text(f"""
        CREATE INDEX {index_name} ON {table_name} 
        USING hnsw (embedding vector_cosine_ops);
    """))
    conn.commit()
    hnsw_build_time = time.perf_counter() - t0_idx
    print(f"[+] HNSW index created in {hnsw_build_time:.2f} seconds.")

    # 5. HNSW Scan (Force enable_seqscan=off, enable_indexscan=on)
    print(f"[*] Running HNSW Indexed queries (N={N_QUERIES})...")
    conn.execute(text("SET enable_seqscan = off; SET enable_indexscan = on;"))
    hnsw_latencies = []
    hnsw_retrieved_ids = []

    for q_vec in query_vectors:
        t0 = time.perf_counter()
        res = conn.execute(text(f"""
            SELECT id FROM {table_name}
            ORDER BY embedding <=> '{q_vec}'
            LIMIT 10;
        """)).fetchall()
        t1 = time.perf_counter()
        hnsw_latencies.append((t1 - t0) * 1000.0)
        hnsw_retrieved_ids.append([r[0] for r in res])

    # Calculate Recall@10
    recalls = []
    for gt, pred in zip(seq_ground_truth_ids, hnsw_retrieved_ids):
        intersection = set(gt).intersection(set(pred))
        recalls.append(len(intersection) / float(len(gt)) if len(gt) > 0 else 1.0)
    avg_recall_10 = float(np.mean(recalls))

    # 6. Hybrid Query (Vector + Keyword)
    print(f"[*] Running Hybrid queries (Vector 0.7 + Keyword 0.3) (N={N_QUERIES})...")
    hybrid_latencies = []
    test_skill_regex = r'\yPython\y'
    for q_vec in query_vectors:
        t0 = time.perf_counter()
        conn.execute(text(f"""
            SELECT id,
                   (0.7 * (1 - (embedding <=> '{q_vec}')) + 0.3 * (
                       CASE WHEN title ~* '{test_skill_regex}' THEN 2.0
                            WHEN description ~* '{test_skill_regex}' THEN 1.0
                            ELSE 0.0 END / 2.0
                   )) * 100 AS match_score
            FROM {table_name}
            ORDER BY (0.7 * (1 - (embedding <=> '{q_vec}')) + 0.3 * (
                       CASE WHEN title ~* '{test_skill_regex}' THEN 2.0
                            WHEN description ~* '{test_skill_regex}' THEN 1.0
                            ELSE 0.0 END / 2.0
                   )) DESC
            LIMIT 10;
        """)).fetchall()
        t1 = time.perf_counter()
        hybrid_latencies.append((t1 - t0) * 1000.0)

    # 7. EXPLAIN (ANALYZE) Hybrid Query to verify if HNSW is actually used
    print("[*] Running EXPLAIN (ANALYZE) on Hybrid Query...")
    explain_res = conn.execute(text(f"""
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT id
        FROM {table_name}
        ORDER BY (0.7 * (1 - (embedding <=> '{query_vectors[0]}')) + 0.3 * (
                   CASE WHEN title ~* '{test_skill_regex}' THEN 2.0
                        WHEN description ~* '{test_skill_regex}' THEN 1.0
                        ELSE 0.0 END / 2.0
               )) DESC
        LIMIT 10;
    """)).fetchall()
    explain_plan = "\n".join([r[0] for r in explain_res])
    hnsw_used_in_hybrid = index_name in explain_plan

    # Reset scan params
    conn.execute(text("SET enable_seqscan = on; SET enable_indexscan = on;"))
    
    # Cleanup table
    conn.execute(text(f"DROP TABLE IF EXISTS {table_name};"))
    conn.commit()

    def calc_stats(latencies):
        arr = np.array(latencies)
        return {
            "mean_ms": float(np.mean(arr)),
            "p50_ms": float(np.percentile(arr, 50)),
            "p95_ms": float(np.percentile(arr, 95)),
            "p99_ms": float(np.percentile(arr, 99)),
            "min_ms": float(np.min(arr)),
            "max_ms": float(np.max(arr))
        }

    return {
        "num_rows": num_rows,
        "n_queries": N_QUERIES,
        "index_build_time_s": hnsw_build_time,
        "sequential_scan": calc_stats(seq_latencies),
        "hnsw_scan": calc_stats(hnsw_latencies),
        "recall_at_10": avg_recall_10,
        "hybrid_query": calc_stats(hybrid_latencies),
        "hnsw_used_in_hybrid_query": hnsw_used_in_hybrid,
        "hybrid_explain_plan": explain_plan
    }

def main():
    with engine.connect() as conn:
        res_10k = run_benchmark_for_scale(conn, 10000)
        res_100k = run_benchmark_for_scale(conn, 100000)

    final_results = {
        "benchmark": "pgvector_hnsw_scale_evaluation",
        "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "vector_dimensions": VECTOR_DIM,
        "distance_metric": "cosine",
        "results_10k": res_10k,
        "results_100k": res_100k
    }

    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "benchmarks", "results", "pgvector_benchmark.json"))
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)

    print(f"\n[+] Saved raw benchmark results to {out_file}")
    
    # Pretty print summary table
    print("\n" + "=" * 80)
    print("PGVECTOR BENCHMARK RESULTS SUMMARY (N=200 queries)")
    print("=" * 80)
    print(f"{'Scale':<10} {'Mode':<18} {'Mean':<10} {'p50':<10} {'p95':<10} {'p99':<10} {'Recall@10':<10}")
    print("-" * 80)
    for r in [res_10k, res_100k]:
        rows_str = f"{r['num_rows']:,}"
        seq = r['sequential_scan']
        hnsw = r['hnsw_scan']
        hyb = r['hybrid_query']
        print(f"{rows_str:<10} {'Sequential':<18} {seq['mean_ms']:<10.2f} {seq['p50_ms']:<10.2f} {seq['p95_ms']:<10.2f} {seq['p99_ms']:<10.2f} {'1.000 (GT)':<10}")
        print(f"{rows_str:<10} {'HNSW':<18} {hnsw['mean_ms']:<10.2f} {hnsw['p50_ms']:<10.2f} {hnsw['p95_ms']:<10.2f} {hnsw['p99_ms']:<10.2f} {r['recall_at_10']:<10.3f}")
        print(f"{rows_str:<10} {'Hybrid (0.7/0.3)':<18} {hyb['mean_ms']:<10.2f} {hyb['p50_ms']:<10.2f} {hyb['p95_ms']:<10.2f} {hyb['p99_ms']:<10.2f} {'N/A':<10}")
        print("-" * 80)

if __name__ == "__main__":
    main()
