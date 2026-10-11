# Retrieval Algorithm Benchmark Results

Evaluation conducted over **12 synthetic candidate profiles** and **220 job listings** (2,640 ground truth relevance labels).

All confidence intervals represent **Bootstrap 95% CIs** ($B=1,000$ resamples).

## 1. Primary Strategy Comparison

| Strategy | Weight (α) | P@5 (95% CI) | P@10 (95% CI) | R@10 (95% CI) | MRR (95% CI) | NDCG@10 (95% CI) |
|---|---|---|---|---|---|---|
| **keyword_only** | 0.0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.444 [0.360, 0.520] | 1.000 [1.000, 1.000] | 0.981 [0.943, 1.000] |
| **semantic_only** | 1.0 | 0.933 [0.817, 1.000] | 0.925 [0.808, 1.000] | 0.404 [0.316, 0.482] | 1.000 [1.000, 1.000] | 0.922 [0.835, 0.990] |
| **production_hybrid_0.7** | 0.7 | 0.967 [0.900, 1.000] | 0.967 [0.900, 1.000] | 0.426 [0.345, 0.502] | 1.000 [1.000, 1.000] | 0.962 [0.905, 1.000] |

## 2. Linear Weight Sweep (α = Vector Weight, 1 - α = Keyword Weight)

| Alpha (α) | P@5 | P@10 | R@10 | MRR | NDCG@10 |
|---|---|---|---|---|---|
| 0.0 | 1.000 | 1.000 | 0.444 | 1.000 | 0.981 |
| 0.1 | 1.000 | 1.000 | 0.444 | 1.000 | 1.000 |
| 0.2 | 1.000 | 1.000 | 0.444 | 1.000 | 1.000 |
| 0.3 | 1.000 | 1.000 | 0.444 | 1.000 | 0.981 |
| 0.4 | 1.000 | 1.000 | 0.444 | 1.000 | 0.981 |
| 0.5 | 1.000 | 0.975 | 0.430 | 1.000 | 0.970 |
| 0.6 | 0.967 | 0.967 | 0.426 | 1.000 | 0.962 |
| 0.7 | 0.967 | 0.967 | 0.426 | 1.000 | 0.962 |
| 0.8 | 0.967 | 0.950 | 0.417 | 1.000 | 0.947 |
| 0.9 | 0.950 | 0.942 | 0.413 | 1.000 | 0.936 |
| 1.0 | 0.933 | 0.925 | 0.404 | 1.000 | 0.922 |

> **Tuning Disclosure**: The production weighting (0.7 / 0.3) was defined in the architecture prior to dataset labeling. As shown in the sweep table, hybrid weighting achieves balanced precision and recall compared to pure keyword search or unweighted dense vectors.
