# Retrieval Algorithm Benchmark Results

Evaluation conducted over **28 candidate profiles** and **560 job listings** (15,680 ground truth relevance labels).

All confidence intervals represent **Bootstrap 95% CIs** ($B=1,000$ resamples).

## 1. Primary Strategy Comparison (In-Python & Production SQL)

| Strategy | Type | P@5 (95% CI) | P@10 (95% CI) | R@10 (95% CI) | MRR (95% CI) | NDCG@10 (95% CI) |
|---|---|---|---|---|---|---|
| **Keyword-Only** | In-Python | 0.921 [0.829, 0.986] | 0.889 [0.786, 0.975] | 0.148 [0.125, 0.172] | 0.976 [0.929, 1.000] | 0.896 [0.804, 0.971] |
| **Semantic-Only** | In-Python | 0.936 [0.850, 0.993] | 0.932 [0.854, 0.986] | 0.153 [0.132, 0.176] | 0.945 [0.859, 1.000] | 0.923 [0.836, 0.985] |
| **Hybrid Legacy SQL** | SQL Full Scan | 0.986 [0.957, 1.000] | 0.989 [0.968, 1.000] | 0.162 [0.144, 0.182] | 1.000 [1.000, 1.000] | 0.985 [0.963, 1.000] |
| **Two-Stage SQL (k=50)** | SQL Two-Stage | 0.986 [0.957, 1.000] | 0.989 [0.957, 1.000] | 0.162 [0.143, 0.183] | 1.000 [1.000, 1.000] | 0.985 [0.963, 1.000] |
| **Two-Stage SQL (k=100)** | SQL Two-Stage | 0.986 [0.957, 1.000] | 0.989 [0.968, 1.000] | 0.162 [0.144, 0.183] | 1.000 [1.000, 1.000] | 0.985 [0.960, 1.000] |
| **Two-Stage SQL (k=200)** | SQL Two-Stage | 0.986 [0.957, 1.000] | 0.989 [0.968, 1.000] | 0.162 [0.143, 0.184] | 1.000 [1.000, 1.000] | 0.985 [0.962, 1.000] |
| **Two-Stage SQL (k=500)** | SQL Two-Stage | 0.986 [0.957, 1.000] | 0.989 [0.968, 1.000] | 0.162 [0.143, 0.182] | 1.000 [1.000, 1.000] | 0.985 [0.962, 1.000] |

## 2. Two-Stage CTE vs Legacy SQL Fidelity

| Two-Stage Variant | Candidate K | Mean Top-10 Overlap | Mean Kendall's Tau (τ) | NDCG@10 (Mean) |
|---|---|---|---|---|
| **Two-Stage (k=50)** | 50 | 1.000 | 1.000 | 0.985 |
| **Two-Stage (k=100)** | 100 | 1.000 | 1.000 | 0.985 |
| **Two-Stage (k=200)** | 200 | 1.000 | 1.000 | 0.985 |
| **Two-Stage (k=500)** | 500 | 1.000 | 1.000 | 0.985 |

> **Candidate K Recommendation**: **`candidate_k = 100`** is recommended. It achieves an NDCG@10 of **0.985** (vs 0.985 for Legacy SQL) with **100.0%** top-10 item overlap and Kendall's $\tau = 1.000$.

## 3. In-Python Linear Weight Sweep (α = Vector Weight, 1 - α = Keyword Weight)

| Alpha (α) | P@5 | P@10 | R@10 | MRR | NDCG@10 |
|---|---|---|---|---|---|
| 0.0 | 0.921 | 0.889 | 0.148 | 0.976 | 0.896 |
| 0.1 | 1.000 | 1.000 | 0.164 | 1.000 | 1.000 |
| 0.2 | 1.000 | 1.000 | 0.164 | 1.000 | 1.000 |
| 0.3 | 1.000 | 1.000 | 0.164 | 1.000 | 1.000 |
| 0.4 | 1.000 | 1.000 | 0.164 | 1.000 | 1.000 |
| 0.5 | 1.000 | 1.000 | 0.164 | 1.000 | 1.000 |
| 0.6 | 1.000 | 1.000 | 0.164 | 1.000 | 0.997 |
| 0.7 | 0.986 | 0.989 | 0.162 | 1.000 | 0.985 |
| 0.8 | 0.979 | 0.971 | 0.159 | 0.976 | 0.964 |
| 0.9 | 0.950 | 0.946 | 0.155 | 0.973 | 0.943 |
| 1.0 | 0.936 | 0.932 | 0.153 | 0.945 | 0.923 |
