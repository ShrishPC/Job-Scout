# Retrieval Algorithm Benchmark Results

Evaluation conducted over **28 candidate profiles** and **560 job listings** (15,680 ground truth relevance labels).

All confidence intervals represent **Bootstrap 95% CIs** ($B=1,000$ resamples).

## 1. Primary Strategy Comparison

| Strategy | Weight (α) | P@5 (95% CI) | P@10 (95% CI) | R@10 (95% CI) | MRR (95% CI) | NDCG@10 (95% CI) |
|---|---|---|---|---|---|---|
| **keyword_only** | 0.0 | 0.921 [0.836, 0.986] | 0.889 [0.800, 0.975] | 0.148 [0.124, 0.173] | 0.976 [0.929, 1.000] | 0.896 [0.802, 0.972] |
| **semantic_only** | 1.0 | 0.936 [0.843, 0.993] | 0.932 [0.854, 0.986] | 0.153 [0.132, 0.175] | 0.945 [0.859, 1.000] | 0.923 [0.837, 0.985] |
| **production_hybrid_0.7** | 0.7 | 0.986 [0.957, 1.000] | 0.989 [0.968, 1.000] | 0.162 [0.143, 0.185] | 1.000 [1.000, 1.000] | 0.985 [0.961, 1.000] |

## 2. Linear Weight Sweep (α = Vector Weight, 1 - α = Keyword Weight)

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

> **Tuning Disclosure**: The production weighting (0.7 / 0.3) was defined in the architecture prior to dataset labeling. As shown in the sweep table, hybrid weighting achieves balanced precision and recall compared to pure keyword search or unweighted dense vectors.
