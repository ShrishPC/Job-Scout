# Empirical System Performance Benchmarks

This report documents reproducible, empirical benchmarks executed on the Job Scout stack. All values reported below were directly measured from automated benchmark runs with raw JSON outputs stored in this directory.

> [!NOTE]
> **Exploratory Phase 1 Baseline**: This document records initial exploratory baseline benchmarks on default, uncalibrated parameters (e.g. pgvector default $ef\_search=40$, where recall was 0.064) and outlines the proposed two-stage CTE architecture.
> For production-calibrated benchmarks and empirical grid sweeps, see [`hnsw_sweep.md`](file:///home/rishav/job-scout/docs/benchmarks/results/hnsw_sweep.md) ($ef\_search=400$ achieving recall 0.9565) and [`ef_search_api_benchmark.md`](file:///home/rishav/job-scout/docs/benchmarks/results/ef_search_api_benchmark.md) (production two-stage API benchmark achieving 9.08 ms at 100k rows).

---

## 1. Test Environment & System Specifications

| Parameter | Measured Specification |
|---|---|
| **Date of Execution** | 2026-10-11 13:26:42 UTC |
| **CPU Model** | 12th Gen Intel(R) Core(TM) i7-1255U (12 logical threads) |
| **System RAM** | Mem:            15Gi       4.7Gi       1.7Gi       402Mi       9.7Gi        10Gi |
| **GPU Acceleration** | None (100% CPU inference) |
| **Operating System / Kernel** | Linux Fedora (7.2.8-200.fc44.x86_64) |
| **Docker Engine Version** | Docker version 29.8.1, build 4a63305 |
| **Git Commit Hash** | `4b200bd82580a0a14389f4858ec7f37a1ad4873d` |

---

## 2. pgvector & HNSW Search Latency (N=200 Queries)

Evaluated across both **10,000** and **100,000** job embedding rows (384-dimensional `all-MiniLM-L6-v2` cosine embeddings):

### A. 10,000 Row Scale
- **Sequential Scan Mean**: 4.37 ms (p50: 4.13 ms, p95: 5.66 ms, p99: 6.07 ms)
- **HNSW Index Scan Mean**: 1.06 ms (p50: 1.02 ms, p95: 1.51 ms, p99: 1.71 ms)
- **HNSW Recall@10 (vs Exact Ground Truth)**: 0.331
- **Speedup Factor**: 4.1x faster

### B. 100,000 Row Scale (NFR-01 Audit)
- **Sequential Scan Mean**: 41.33 ms (p50: 39.81 ms, p95: 53.44 ms, p99: 77.74 ms)
- **HNSW Index Scan Mean**: 3.23 ms (p50: 3.12 ms, p95: 4.50 ms, p99: 5.42 ms)
- **HNSW Recall@10 (vs Exact Ground Truth)**: 0.064

### C. Hybrid Query Execution Analysis (EXPLAIN ANALYZE)
- **Hybrid Query Mean (10k)**: 72.45 ms
- **Hybrid Query Mean (100k)**: 289.66 ms
- **HNSW Index Usage in Hybrid Query**: NOT USED (Sequential Scan forced by computed ORDER BY expression)

> **Architectural Observation & Proposed Rewrite**:
> When PostgreSQL evaluates `ORDER BY (0.7 * (1 - (embedding <=> :q)) + 0.3 * keyword_score) DESC`, the query planner cannot utilize the HNSW index directly because the ordering expression combines both vector distance and scalar keyword score. To achieve index-accelerated hybrid retrieval, the query should be rewritten into a two-stage Common Table Expression (CTE):
> 1. Stage 1 (ANN Filter): `WITH candidates AS (SELECT id, title, description, embedding FROM jobs ORDER BY embedding <=> :q LIMIT 100)` (uses HNSW index in <10ms).
> 2. Stage 2 (Scalar Re-ranking): Compute the keyword score and composite rank strictly over the top 100 candidates.

---

## 3. LLM Caching: Cold vs Cached Latency

Measured across 5 paired repetitions for tailored resume generation:

- **Cold Generation Latency (Mean)**: 2.70 s (2700.00 ms)
- **AIGenerationCache Latency (Mean)**: 5.96 ms
- **Speedup Factor**: 453.4x faster

---

## 4. Local LLM Generation Throughput

- **Active Model**: `unsloth/Llama-3.2-3B-Instruct`
- **Execution Device**: `cpu` (10 threads, dtype: `torch.bfloat16`)
- **Tokens Generated**: 129 tokens
- **Total Latency**: 70.79 s
- **Throughput**: 1.82 tokens/second

---

## 5. Offline Operation Audit

- **Environment Flags**: `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`
- **Socket Firewall**: External WAN egress blocked at socket level.
- **Audit Verdict**: `PASSED_100_PERCENT_OFFLINE`
- **Resume Parsing**: SUCCESS
- **384-d Embedding & Hybrid Matching**: SUCCESS (145.55 ms)
- **Local Generation**: SUCCESS

---

## 6. Memory Footprint (Peak RSS)

- **Baseline Process RSS**: 15.94 MB
- **Post-Embedding Model RSS**: 875.93 MB
- **Peak Execution RSS (Inference)**: 7225.99 MB (7.06 GB)
- **Net Model Overhead**: 7210.05 MB
