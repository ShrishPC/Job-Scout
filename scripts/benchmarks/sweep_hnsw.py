#!/usr/bin/env python3
"""
HNSW Parameter Sweep & Two-Stage Hybrid Query Benchmark
Measures:
1. Exact sequential scan ground truth (N=200 queries).
2. HNSW sweep across:
   - m in {16, 32}
   - ef_construction in {64, 128, 200}
   - hnsw.ef_search in {40, 100, 200, 400}
   at 10,000 and 100,000 rows with real all-MiniLM-L6-v2 embeddings.
3. Legacy single-stage vs Two-Stage CTE query comparison:
   - Latency (mean, p50, p95)
   - EXPLAIN (ANALYZE) query execution plan
   - Overlap@10 and Kendall's tau rank correlation
Outputs saved to docs/benchmarks/results/hnsw_sweep.json and .md.
"""

import os
import sys
import time
import json
import math
import random
import numpy as np
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:password@localhost:5435/job_scout")
try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception:
    DB_URL = "postgresql+psycopg2://postgres:password@db:5432/job_scout"
    engine = create_engine(DB_URL)

VECTOR_DIM = 384
N_QUERIES = 200
M_VALS = [16, 32]
EF_C_VALS = [64, 128, 200]
EF_S_VALS = [40, 100, 200, 400]

def kendall_tau(list1, list2):
    """Computes Kendall tau rank correlation on shared elements."""
    common = [x for x in list1 if x in list2]
    if len(common) < 2:
        return 0.0
    rank1 = {item: i for i, item in enumerate(list1)}
    rank2 = {item: i for i, item in enumerate(list2)}
    concordant, discordant = 0, 0
    items = list(common)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            order1 = rank1[a] < rank1[b]
            order2 = rank2[a] < rank2[b]
            if order1 == order2:
                concordant += 1
            else:
                discordant += 1
    total = concordant + discordant
    return (concordant - discordant) / total if total > 0 else 0.0

def load_real_base_embeddings():
    print("[*] Loading real job descriptions and generating base embeddings...")
    model_cache = "/models" if os.path.exists("/models") else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
    model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=model_cache)

    jobs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "evaluation", "data", "jobs.json"))
    if os.path.exists(jobs_path):
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)
            texts = [j["title"] + " " + j.get("description", "") for j in jobs_data]
    else:
        sample_roles = [
            "Senior Python Backend Engineer FastAPI PostgreSQL Redis microservices Docker",
            "Frontend Engineer React Next.js TypeScript Tailwind UI component architecture",
            "Machine Learning Engineer PyTorch Transformers NLP HuggingFace dense retrieval",
            "DevOps Cloud Architect AWS Kubernetes Terraform CI/CD Docker Linux Helm",
            "Data Platform Engineer Apache Spark Kafka Snowflake ETL Python pipeline",
            "Embedded Systems Engineer C++ Linux RTOS ARM firmware CAN bus hardware",
            "iOS Mobile Developer Swift SwiftUI UIKit CoreData Combine mobile architecture",
            ".NET Solutions Architect C# ASP.NET Core Azure SQL Server microservices",
            "Cybersecurity Incident Responder SIEM SOC network security Python penetration",
            "Full Stack Software Engineer React Node.js Express MongoDB REST API TypeScript"
        ]
        texts = sample_roles * 22

    base_embs = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    print(f"[+] Encoded {len(base_embs)} real base embeddings with all-MiniLM-L6-v2.")

    # Generate 200 real query vectors
    query_texts = [
        f"Experienced software specialist with expertise in {random.choice(texts)[:60]}"
        for _ in range(N_QUERIES)
    ]
    query_embs = model.encode(query_texts, show_progress_bar=False, normalize_embeddings=True)
    return base_embs, query_embs

def run_benchmark():
    base_embs, query_embs = load_real_base_embeddings()
    scales = [10000, 100000]
    
    full_results = {
        "benchmark_metadata": {
            "date": "2026-10-11",
            "embedding_model": "all-MiniLM-L6-v2 (384-d)",
            "vector_distribution": "Real job text replicated with small Gaussian noise (sigma=0.01) on unit hypersphere",
            "n_queries": N_QUERIES,
            "scales": scales,
            "m_values": M_VALS,
            "ef_construction_values": EF_C_VALS,
            "ef_search_values": EF_S_VALS
        },
        "results_by_scale": {},
        "two_stage_comparison": {}
    }

    with engine.connect() as conn:
        for num_rows in scales:
            print(f"\n{'='*70}\n🚀 RUNNING HNSW BENCHMARK AT {num_rows:,} ROWS\n{'='*70}")
            table_name = f"benchmark_hnsw_sweep_{num_rows}"

            # 1. Create and populate table
            print(f"[*] Setting up table {table_name}...")
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
            conn.execute(text(f"""
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255),
                    description TEXT,
                    workplace_type VARCHAR(50),
                    embedding vector(384)
                );
            """))
            conn.commit()

            print(f"[*] Inserting {num_rows:,} synthetic real-domain vectors...")
            batch_size = 5000
            n_base = len(base_embs)
            for b in range(0, num_rows, batch_size):
                curr_size = min(batch_size, num_rows - b)
                rows = []
                for i in range(curr_size):
                    base_idx = (b + i) % n_base
                    # Add small noise and re-normalize to keep on real semantic manifold
                    noise = np.random.normal(0, 0.01, VECTOR_DIM)
                    vec = base_embs[base_idx] + noise
                    vec = vec / np.linalg.norm(vec)
                    vec_str = f"[{','.join(f'{x:.6f}' for x in vec)}]"
                    rows.append(f"('Engineer Role {b+i}', 'Requirements in Python, Docker, SQL.', 'Remote', '{vec_str}')")
                conn.execute(text(f"INSERT INTO {table_name} (title, description, workplace_type, embedding) VALUES {','.join(rows)};"))
            conn.commit()
            print(f"[+] Inserted {num_rows:,} rows.")

            # 2. Sequential Scan Ground Truth (N=200 queries)
            print(f"[*] Measuring Sequential Scan ground truth (N={N_QUERIES})...")
            conn.execute(text("SET enable_seqscan = on; SET enable_indexscan = off;"))
            seq_latencies = []
            ground_truth = []

            for q in query_embs:
                q_str = f"[{','.join(f'{x:.6f}' for x in q)}]"
                t0 = time.perf_counter()
                res = conn.execute(text(f"""
                    SELECT id FROM {table_name}
                    ORDER BY embedding <=> '{q_str}'
                    LIMIT 10;
                """)).fetchall()
                t1 = time.perf_counter()
                seq_latencies.append((t1 - t0) * 1000.0)
                ground_truth.append([r[0] for r in res])

            seq_summary = {
                "mean_ms": round(float(np.mean(seq_latencies)), 2),
                "p50_ms": round(float(np.median(seq_latencies)), 2),
                "p95_ms": round(float(np.percentile(seq_latencies, 95)), 2),
                "p99_ms": round(float(np.percentile(seq_latencies, 99)), 2),
                "min_ms": round(float(np.min(seq_latencies)), 2),
                "max_ms": round(float(np.max(seq_latencies)), 2)
            }
            print(f"[+] Sequential scan mean: {seq_summary['mean_ms']} ms | p50: {seq_summary['p50_ms']} ms | p95: {seq_summary['p95_ms']} ms")

            # 3. Parameter Sweep
            scale_sweep = {
                "sequential_scan": seq_summary,
                "hnsw_configurations": []
            }

            for m in M_VALS:
                for ef_c in EF_C_VALS:
                    idx_name = f"idx_hnsw_m{m}_efc{ef_c}_{num_rows}"
                    print(f"\n[*] Building HNSW index WITH (m = {m}, ef_construction = {ef_c})...")
                    conn.execute(text(f"DROP INDEX IF EXISTS {idx_name};"))
                    conn.commit()

                    t0_build = time.perf_counter()
                    conn.execute(text(f"""
                        CREATE INDEX {idx_name} ON {table_name} 
                        USING hnsw (embedding vector_cosine_ops)
                        WITH (m = {m}, ef_construction = {ef_c});
                    """))
                    conn.commit()
                    build_time_s = round(time.perf_counter() - t0_build, 2)
                    print(f"[+] Built {idx_name} in {build_time_s} s.")

                    conn.execute(text("SET enable_seqscan = off; SET enable_indexscan = on;"))

                    for ef_s in EF_S_VALS:
                        conn.execute(text(f"SET hnsw.ef_search = {ef_s};"))
                        latencies = []
                        recalls = []

                        for q_idx, q in enumerate(query_embs):
                            q_str = f"[{','.join(f'{x:.6f}' for x in q)}]"
                            t0 = time.perf_counter()
                            res = conn.execute(text(f"""
                                SELECT id FROM {table_name}
                                ORDER BY embedding <=> '{q_str}'
                                LIMIT 10;
                            """)).fetchall()
                            t1 = time.perf_counter()
                            latencies.append((t1 - t0) * 1000.0)

                            retrieved = [r[0] for r in res]
                            gt = ground_truth[q_idx]
                            hits = len(set(retrieved).intersection(set(gt)))
                            recalls.append(hits / 10.0)

                        config_entry = {
                            "m": m,
                            "ef_construction": ef_c,
                            "ef_search": ef_s,
                            "build_time_seconds": build_time_s,
                            "recall_at_10": round(float(np.mean(recalls)), 4),
                            "mean_latency_ms": round(float(np.mean(latencies)), 2),
                            "p50_latency_ms": round(float(np.median(latencies)), 2),
                            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
                            "p99_latency_ms": round(float(np.percentile(latencies, 99)), 2)
                        }
                        scale_sweep["hnsw_configurations"].append(config_entry)
                        print(f"    -> m={m:2d}, ef_c={ef_c:3d}, ef_s={ef_s:3d} | Recall@10: {config_entry['recall_at_10']:.4f} | Mean: {config_entry['mean_latency_ms']:.2f} ms | p95: {config_entry['p95_latency_ms']:.2f} ms")

                    conn.execute(text(f"DROP INDEX IF EXISTS {idx_name};"))
                    conn.commit()

            full_results["results_by_scale"][str(num_rows)] = scale_sweep

            # 4. Two-Stage vs Legacy Hybrid Comparison at this scale
            print(f"\n[*] Benchmarking Single-Stage Legacy vs Two-Stage CTE at {num_rows:,} rows...")
            # Recreate recommended index
            best_m = 16
            best_efc = 128
            rec_idx = f"idx_recommended_{num_rows}"
            conn.execute(text(f"""
                CREATE INDEX {rec_idx} ON {table_name} 
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = {best_m}, ef_construction = {best_efc});
            """))
            conn.commit()
            conn.execute(text("SET hnsw.ef_search = 100;"))

            q_test = query_embs[0]
            q_str = f"[{','.join(f'{x:.6f}' for x in q_test)}]"

            # Query A: Single-stage Legacy
            legacy_sql = f"""
                SELECT id, title,
                       (0.7 * (1 - (embedding <=> '{q_str}')) + 0.3 * (CASE WHEN title ILIKE '%python%' THEN 1.0 ELSE 0.0 END)) * 100 as match_score
                FROM {table_name}
                ORDER BY (0.7 * (1 - (embedding <=> '{q_str}')) + 0.3 * (CASE WHEN title ILIKE '%python%' THEN 1.0 ELSE 0.0 END)) DESC
                LIMIT 10;
            """

            # Query B: Two-Stage CTE
            two_stage_sql = f"""
                WITH candidates AS (
                    SELECT id, title, embedding,
                           (1 - (embedding <=> '{q_str}')) as vector_sim
                    FROM {table_name}
                    ORDER BY embedding <=> '{q_str}'
                    LIMIT 100
                )
                SELECT id, title,
                       (0.7 * vector_sim + 0.3 * (CASE WHEN title ILIKE '%python%' THEN 1.0 ELSE 0.0 END)) * 100 as match_score
                FROM candidates
                ORDER BY (0.7 * vector_sim + 0.3 * (CASE WHEN title ILIKE '%python%' THEN 1.0 ELSE 0.0 END)) DESC
                LIMIT 10;
            """

            # Measure EXPLAIN ANALYZE
            explain_legacy = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS) {legacy_sql}")).fetchall()
            explain_two_stage = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS) {two_stage_sql}")).fetchall()

            plan_legacy = "\n".join(r[0] for r in explain_legacy)
            plan_two_stage = "\n".join(r[0] for r in explain_two_stage)

            # Measure latencies and rank agreement across 50 sample queries
            legacy_latencies = []
            two_stage_latencies = []
            overlaps = []
            taus = []

            for q in query_embs[:50]:
                q_s = f"[{','.join(f'{x:.6f}' for x in q)}]"

                l_sql = f"""
                    SELECT id FROM {table_name}
                    ORDER BY (0.7 * (1 - (embedding <=> '{q_s}')) + 0.3 * (CASE WHEN title ILIKE '%python%' THEN 1.0 ELSE 0.0 END)) DESC
                    LIMIT 10;
                """
                ts_sql = f"""
                    WITH candidates AS (
                        SELECT id, title, embedding, (1 - (embedding <=> '{q_s}')) as vector_sim
                        FROM {table_name}
                        ORDER BY embedding <=> '{q_s}'
                        LIMIT 100
                    )

                    SELECT id FROM candidates
                    ORDER BY (0.7 * vector_sim + 0.3 * (CASE WHEN title ILIKE '%python%' THEN 1.0 ELSE 0.0 END)) DESC
                    LIMIT 10;
                """

                t0 = time.perf_counter()
                r_leg = [r[0] for r in conn.execute(text(l_sql)).fetchall()]
                legacy_latencies.append((time.perf_counter() - t0) * 1000.0)

                t0 = time.perf_counter()
                r_ts = [r[0] for r in conn.execute(text(ts_sql)).fetchall()]
                two_stage_latencies.append((time.perf_counter() - t0) * 1000.0)

                overlap = len(set(r_leg).intersection(set(r_ts))) / 10.0
                overlaps.append(overlap)
                taus.append(kendall_tau(r_leg, r_ts))

            comp_result = {
                "legacy_mean_ms": round(float(np.mean(legacy_latencies)), 2),
                "legacy_p50_ms": round(float(np.median(legacy_latencies)), 2),
                "legacy_p95_ms": round(float(np.percentile(legacy_latencies, 95)), 2),
                "two_stage_mean_ms": round(float(np.mean(two_stage_latencies)), 2),
                "two_stage_p50_ms": round(float(np.median(two_stage_latencies)), 2),
                "two_stage_p95_ms": round(float(np.percentile(two_stage_latencies, 95)), 2),
                "speedup_factor": round(float(np.mean(legacy_latencies) / max(0.01, np.mean(two_stage_latencies))), 1),
                "mean_top10_overlap": round(float(np.mean(overlaps)), 4),
                "mean_kendall_tau": round(float(np.mean(taus)), 4),
                "explain_plan_legacy_snippet": plan_legacy[:500],
                "explain_plan_two_stage_snippet": plan_two_stage[:500]
            }
            full_results["two_stage_comparison"][str(num_rows)] = comp_result
            print(f"[+] Scale {num_rows:,}: Legacy mean={comp_result['legacy_mean_ms']}ms vs Two-Stage mean={comp_result['two_stage_mean_ms']}ms (Speedup: {comp_result['speedup_factor']}x) | Overlap@10: {comp_result['mean_top10_overlap']:.2%} | Kendall Tau: {comp_result['mean_kendall_tau']:.4f}")

            conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
            conn.commit()

    # Save to JSON
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "benchmarks", "results", "hnsw_sweep.json"))
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)
    print(f"\n[+] Saved full benchmark results to {json_path}")

    # Generate Markdown Report
    md_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "benchmarks", "results", "hnsw_sweep.md"))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# HNSW Parameter Sweep & Two-Stage Query Benchmark Report\n\n")
        f.write("## 1. Methodology & Root Cause Analysis of Previous Low Recall\n\n")
        f.write("- **Root Cause of Prior Result**: The prior audit utilized uniform random vectors generated via `np.random.uniform(-1, 1)` and pgvector's default `hnsw.ef_search = 40`. In high dimensions (384-d), uniform spherical vectors have uniform distance distributions without topological clusters, leading HNSW graphs to explore non-representative paths and yield low recall (0.331 at 10k, 0.064 at 100k).\n")
        f.write("- **Methodology for This Benchmark**: Encoded real job descriptions using `all-MiniLM-L6-v2` (384 dimensions) and replicated them to 10,000 and 100,000 rows by applying small Gaussian perturbations ($\sigma = 0.01$) to simulate natural dense semantic clusters. Evaluated ground truth exact nearest neighbors across $N=200$ realistic queries via full Sequential Scans.\n\n")

        for scale in [10000, 100000]:
            f.write(f"## 2. Scale: {scale:,} Rows (N=200 Queries)\n\n")
            data = full_results["results_by_scale"][str(scale)]
            seq = data["sequential_scan"]
            f.write(f"### Sequential Scan (Ground Truth Baseline)\n")
            f.write(f"- **Mean**: {seq['mean_ms']} ms\n")
            f.write(f"- **p50**: {seq['p50_ms']} ms\n")
            f.write(f"- **p95**: {seq['p95_ms']} ms\n")
            f.write(f"- **p99**: {seq['p99_ms']} ms\n\n")

            f.write("### HNSW Parameter Grid Sweep\n\n")
            f.write("| m | ef_construction | ef_search | Build Time (s) | Recall@10 | Mean Latency (ms) | p50 (ms) | p95 (ms) |\n")
            f.write("|---|---|---|---|---|---|---|---|\n")
            for c in data["hnsw_configurations"]:
                rec_flag = " **>= 0.95**" if c["recall_at_10"] >= 0.95 else ""
                f.write(f"| {c['m']} | {c['ef_construction']} | {c['ef_search']} | {c['build_time_seconds']}s | {c['recall_at_10']:.4f}{rec_flag} | {c['mean_latency_ms']} ms | {c['p50_latency_ms']} ms | {c['p95_latency_ms']} ms |\n")
            f.write("\n")

        f.write("## 3. Two-Stage CTE Query vs Single-Stage Legacy Benchmark\n\n")
        f.write("| Scale | Metric | Single-Stage Legacy | Two-Stage CTE | Speedup / Agreement |\n")
        f.write("|---|---|---|---|---|\n")
        for scale in [10000, 100000]:
            comp = full_results["two_stage_comparison"][str(scale)]
            f.write(f"| {scale:,} | Mean Latency | {comp['legacy_mean_ms']} ms | {comp['two_stage_mean_ms']} ms | **{comp['speedup_factor']}x Faster** |\n")
            f.write(f"| {scale:,} | p50 Latency | {comp['legacy_p50_ms']} ms | {comp['two_stage_p50_ms']} ms | - |\n")
            f.write(f"| {scale:,} | p95 Latency | {comp['legacy_p95_ms']} ms | {comp['two_stage_p95_ms']} ms | - |\n")
            f.write(f"| {scale:,} | Top-10 Overlap | - | - | **{comp['mean_top10_overlap']:.2%}** |\n")
            f.write(f"| {scale:,} | Kendall Tau | - | - | **{comp['mean_kendall_tau']:.4f}** |\n")

        f.write("\n## 4. Execution Plan Proof (EXPLAIN ANALYZE)\n\n")
        f.write("### Single-Stage Legacy Plan Snippet:\n```\n")
        f.write(full_results["two_stage_comparison"]["10000"]["explain_plan_legacy_snippet"] + "\n```\n\n")
        f.write("### Two-Stage CTE Plan Snippet:\n```\n")
        f.write(full_results["two_stage_comparison"]["10000"]["explain_plan_two_stage_snippet"] + "\n```\n")

    print(f"[+] Saved markdown report to {md_path}")

if __name__ == "__main__":
    run_benchmark()
