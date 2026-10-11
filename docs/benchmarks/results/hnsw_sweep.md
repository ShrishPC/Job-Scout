# HNSW Parameter Sweep & Two-Stage Query Benchmark Report

## 1. Methodology & Root Cause Analysis of Previous Low Recall

- **Root Cause of Prior Result**: The prior audit utilized uniform random vectors generated via `np.random.uniform(-1, 1)` and pgvector's default `hnsw.ef_search = 40`. In high dimensions (384-d), uniform spherical vectors have uniform distance distributions without topological clusters, leading HNSW graphs to explore non-representative paths and yield low recall (0.331 at 10k, 0.064 at 100k).
- **Methodology for This Benchmark**: Encoded real job descriptions using `all-MiniLM-L6-v2` (384 dimensions) and replicated them to 10,000 and 100,000 rows by applying small Gaussian perturbations ($\sigma = 0.01$) to simulate natural dense semantic clusters. Evaluated ground truth exact nearest neighbors across $N=200$ realistic queries via full Sequential Scans.

## 2. Scale: 10,000 Rows (N=200 Queries)

### Sequential Scan (Ground Truth Baseline)
- **Mean**: 4.17 ms
- **p50**: 3.85 ms
- **p95**: 6.83 ms
- **p99**: 8.97 ms

### HNSW Parameter Grid Sweep

| m | ef_construction | ef_search | Build Time (s) | Recall@10 | Mean Latency (ms) | p50 (ms) | p95 (ms) |
|---|---|---|---|---|---|---|---|
| 16 | 64 | 40 | 1.66s | 0.8985 | 0.48 ms | 0.47 ms | 0.59 ms |
| 16 | 64 | 100 | 1.66s | 0.9145 | 0.6 ms | 0.58 ms | 0.79 ms |
| 16 | 64 | 200 | 1.66s | 0.9220 | 0.85 ms | 0.74 ms | 1.42 ms |
| 16 | 64 | 400 | 1.66s | 0.9220 | 1.33 ms | 1.26 ms | 1.89 ms |
| 16 | 128 | 40 | 2.48s | 0.8795 | 0.64 ms | 0.66 ms | 0.78 ms |
| 16 | 128 | 100 | 2.48s | 0.9275 | 0.99 ms | 0.98 ms | 1.25 ms |
| 16 | 128 | 200 | 2.48s | 0.9400 | 1.05 ms | 0.97 ms | 1.52 ms |
| 16 | 128 | 400 | 2.48s | 1.0000 **>= 0.95** | 1.76 ms | 1.62 ms | 2.65 ms |
| 16 | 200 | 40 | 3.48s | 0.9750 **>= 0.95** | 0.68 ms | 0.67 ms | 0.9 ms |
| 16 | 200 | 100 | 3.48s | 0.9875 **>= 0.95** | 0.84 ms | 0.82 ms | 1.02 ms |
| 16 | 200 | 200 | 3.48s | 0.9950 **>= 0.95** | 0.98 ms | 0.95 ms | 1.31 ms |
| 16 | 200 | 400 | 3.48s | 1.0000 **>= 0.95** | 1.45 ms | 1.39 ms | 1.92 ms |
| 32 | 64 | 40 | 4.4s | 0.9475 | 0.71 ms | 0.6 ms | 1.28 ms |
| 32 | 64 | 100 | 4.4s | 0.9885 **>= 0.95** | 0.84 ms | 0.8 ms | 1.21 ms |
| 32 | 64 | 200 | 4.4s | 0.9910 **>= 0.95** | 1.55 ms | 1.43 ms | 2.47 ms |
| 32 | 64 | 400 | 4.4s | 0.9915 **>= 0.95** | 2.08 ms | 1.92 ms | 2.81 ms |
| 32 | 128 | 40 | 5.95s | 0.9910 **>= 0.95** | 0.53 ms | 0.51 ms | 0.63 ms |
| 32 | 128 | 100 | 5.95s | 0.9950 **>= 0.95** | 0.71 ms | 0.7 ms | 0.83 ms |
| 32 | 128 | 200 | 5.95s | 1.0000 **>= 0.95** | 1.23 ms | 1.09 ms | 1.78 ms |
| 32 | 128 | 400 | 5.95s | 1.0000 **>= 0.95** | 1.95 ms | 1.85 ms | 2.7 ms |
| 32 | 200 | 40 | 7.13s | 0.9465 | 0.72 ms | 0.72 ms | 0.9 ms |
| 32 | 200 | 100 | 7.13s | 0.9600 **>= 0.95** | 0.99 ms | 0.96 ms | 1.23 ms |
| 32 | 200 | 200 | 7.13s | 0.9950 **>= 0.95** | 1.29 ms | 1.24 ms | 1.72 ms |
| 32 | 200 | 400 | 7.13s | 1.0000 **>= 0.95** | 1.87 ms | 1.64 ms | 2.96 ms |

## 2. Scale: 100,000 Rows (N=200 Queries)

### Sequential Scan (Ground Truth Baseline)
- **Mean**: 41.33 ms
- **p50**: 40.15 ms
- **p95**: 44.79 ms
- **p99**: 68.93 ms

### HNSW Parameter Grid Sweep

| m | ef_construction | ef_search | Build Time (s) | Recall@10 | Mean Latency (ms) | p50 (ms) | p95 (ms) |
|---|---|---|---|---|---|---|---|
| 16 | 64 | 40 | 88.73s | 0.4680 | 1.06 ms | 0.9 ms | 1.84 ms |
| 16 | 64 | 100 | 88.73s | 0.6325 | 1.21 ms | 1.08 ms | 2.16 ms |
| 16 | 64 | 200 | 88.73s | 0.8380 | 1.9 ms | 1.73 ms | 3.26 ms |
| 16 | 64 | 400 | 88.73s | 0.8825 | 2.66 ms | 2.51 ms | 4.16 ms |
| 16 | 128 | 40 | 104.99s | 0.5800 | 1.2 ms | 1.06 ms | 1.98 ms |
| 16 | 128 | 100 | 104.99s | 0.8255 | 1.45 ms | 1.32 ms | 2.38 ms |
| 16 | 128 | 200 | 104.99s | 0.9130 | 2.11 ms | 1.98 ms | 3.39 ms |
| 16 | 128 | 400 | 104.99s | 0.9565 **>= 0.95** | 2.88 ms | 2.7 ms | 4.59 ms |
| 16 | 200 | 40 | 120.55s | 0.6875 | 1.44 ms | 1.2 ms | 3.02 ms |
| 16 | 200 | 100 | 120.55s | 0.8530 | 1.65 ms | 1.52 ms | 2.76 ms |
| 16 | 200 | 200 | 120.55s | 0.9170 | 2.19 ms | 2.1 ms | 3.3 ms |
| 16 | 200 | 400 | 120.55s | 0.9260 | 2.89 ms | 2.77 ms | 4.55 ms |
| 32 | 64 | 40 | 249.68s | 0.5290 | 1.19 ms | 0.88 ms | 2.41 ms |
| 32 | 64 | 100 | 249.68s | 0.6900 | 1.41 ms | 1.28 ms | 2.3 ms |
| 32 | 64 | 200 | 249.68s | 0.8190 | 2.12 ms | 1.95 ms | 3.42 ms |
| 32 | 64 | 400 | 249.68s | 0.8560 | 3.49 ms | 3.37 ms | 5.42 ms |
| 32 | 128 | 40 | 275.21s | 0.7195 | 1.5 ms | 1.25 ms | 3.05 ms |
| 32 | 128 | 100 | 275.21s | 0.8945 | 1.96 ms | 1.86 ms | 3.05 ms |
| 32 | 128 | 200 | 275.21s | 0.9435 | 2.77 ms | 2.62 ms | 4.1 ms |
| 32 | 128 | 400 | 275.21s | 0.9820 **>= 0.95** | 3.69 ms | 3.49 ms | 5.41 ms |
| 32 | 200 | 40 | 310.98s | 0.8075 | 1.79 ms | 1.6 ms | 3.3 ms |
| 32 | 200 | 100 | 310.98s | 0.9285 | 2.08 ms | 2.02 ms | 3.3 ms |
| 32 | 200 | 200 | 310.98s | 0.9820 **>= 0.95** | 2.48 ms | 2.42 ms | 3.81 ms |
| 32 | 200 | 400 | 310.98s | 0.9835 **>= 0.95** | 3.28 ms | 3.14 ms | 4.87 ms |

## 3. Two-Stage CTE Query vs Single-Stage Legacy Benchmark

| Scale | Metric | Single-Stage Legacy | Two-Stage CTE | Speedup / Agreement |
|---|---|---|---|---|
| 10,000 | Mean Latency | 44.55 ms | 1.35 ms | **33.1x Faster** |
| 10,000 | p50 Latency | 44.2 ms | 1.36 ms | - |
| 10,000 | p95 Latency | 45.77 ms | 1.5 ms | - |
| 10,000 | Top-10 Overlap | - | - | **90.00%** |
| 10,000 | Kendall Tau | - | - | **0.9000** |
| 100,000 | Mean Latency | 130.6 ms | 2.45 ms | **53.3x Faster** |
| 100,000 | p50 Latency | 128.54 ms | 2.43 ms | - |
| 100,000 | p95 Latency | 136.55 ms | 3.74 ms | - |
| 100,000 | Top-10 Overlap | - | - | **68.20%** |
| 100,000 | Kendall Tau | - | - | **0.8200** |

## 4. Execution Plan Proof (EXPLAIN ANALYZE)

### Single-Stage Legacy Plan Snippet:
```
Limit  (cost=10000003191.10..10000003191.12 rows=10 width=536) (actual time=80.419..80.421 rows=10 loops=1)
  Buffers: shared hit=2500
  ->  Sort  (cost=10000003191.10..10000003216.10 rows=10000 width=536) (actual time=11.858..11.859 rows=10 loops=1)
        Sort Key: ((('0.7'::double precision * ('1'::double precision - (embedding <=> '[-0.062124,0.020283,0.05627,0.039476,-0.061742,-0.11746,0.033125,0.060208,-0.082439,-0.024095,-0.089886,-0.050773,0.00963,0.028035,0.005713,0.056952,-0.012579,-0
```

### Two-Stage CTE Plan Snippet:
```
Limit  (cost=192.26..192.29 rows=10 width=536) (actual time=0.618..0.620 rows=10 loops=1)
  Buffers: shared hit=630
  ->  Sort  (cost=192.26..192.51 rows=100 width=536) (actual time=0.618..0.618 rows=10 loops=1)
        Sort Key: ((('0.7'::double precision * candidates.vector_sim) + ((0.3 * CASE WHEN ((candidates.title)::text ~~* '%python%'::text) THEN 1.0 ELSE 0.0 END))::double precision)) DESC
        Sort Method: top-N heapsort  Memory: 25kB
        Buffers: shared hit=630
        ->  Subquer
```
