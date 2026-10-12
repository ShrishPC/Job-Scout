# Academic Project Report Claims Audit

This document audits the technical and empirical claims asserted in the Job Scout academic project report against the actual implementation and measured reality of the repository (`Job-Scout`).

Every metric recorded in this document is grounded in reproducible command outputs and benchmarks executed in this environment.

---

## 1. Master Claims Audit Table

| ID | Claim | Where Claimed in Report / Docs | Evidence in Repository (file:line / command) | Empirical Status | Action Taken / Report Adjustment |
|---|---|---|---|---|---|
| **A** | **384-d Embeddings vs 768-d Zero-Padding**<br>Embeddings are 384-dimensional (`all-MiniLM-L6-v2`), stored natively as pgvector `Vector(384)`. | `README.md`, `docs/rag_architecture.md`, Report Sec 4.2 | `backend/app/models/models.py:27` (`Vector(384)`), `backend/app/main.py:46` (`len(v) == 384`), `backend/app/services/llm_service.py:16` | **FIXED**<br>(Code was 384-d; old docs falsely claimed 768-d padding) | Updated `README.md`, `docs/rag_architecture.md`, and `docs/Job_Scout_Definitive_Technical_Reference.md`. Stripped all mentions of 768 zero-padding. |
| **B** | **PostgreSQL & HNSW Index Architecture**<br>HNSW on `jobs.embedding` (`vector_cosine_ops`), partial index on `resumes(is_active)`, functional index on `LOWER(workplace_type)`, composite index on `user_job_matches(user_id, job_id)`. | Report Sec 3.4 & 4.1, `docs/rag_architecture.md` | `backend/migrations/add_vector_index.sql:2-10`, `backend/init_db.py:38-51`<br>Verified live via `SELECT indexname FROM pg_indexes;` | **VERIFIED** | Enforced index creation on clean `docker compose up` in `backend/init_db.py`. Added unit test `tests/unit/test_db_indexes.py` (UTC-01). |
| **C** | **Hybrid Scoring Formulation**<br>`Score = 100 × (0.7 × (1 - cosine_dist) + 0.3 × kw_score)`<br>Keyword weights: 2.0 title, 1.0 description, normalised by `2.0 × n_skills`. Boundary regex for alphanumeric skills, LIKE for special characters (`C++`, `C#`, `.NET`). | Report Sec 4.3, `docs/rag_architecture.md` | `backend/app/services/matching_service.py:20-65`, `backend/app/services/llm_fallback.py:100-115` | **VERIFIED** | Validated mathematical bounds `[0, 100]` and regex vs LIKE logic in `tests/unit/test_keyword_math.py`. |
| **D** | **Query Latency (10,000 Rows)**<br>Report claimed ~140 ms sequential scan vs ~9–15 ms HNSW index scan. | Report Sec 5.2 | Re-measured via `scripts/benchmarks/benchmark_pgvector.py` (N=200 queries):<br>- **Sequential Scan**: Mean 4.37 ms (p50: 4.13 ms, p95: 5.66 ms, p99: 6.07 ms)<br>- **HNSW Scan**: Mean 1.06 ms (p50: 1.02 ms, p95: 1.51 ms, p99: 1.71 ms)<br>- **Hybrid (0.7/0.3)**: Mean 72.45 ms (p50: 71.08 ms) | **FIXED**<br>(Report numbers were outdated/uncalibrated) | Update report with measured numbers: HNSW query takes **1.06 ms** (p50: 1.02 ms), achieving a **4.1x speedup** over sequential scan (4.37 ms). |
| **E** | **LLM Response Cache Performance**<br>`AIGenerationCache` (SHA-256 key): Cold generation vs cached response speedup. | Report Sec 4.4, `docs/Job_Scout_Definitive_Technical_Reference.md` | Re-measured via `scripts/benchmarks/benchmark_llm_cache.py` (5 repetitions):<br>- **Cold Generation Mean**: 2.70 s (2,700 ms)<br>- **AIGenerationCache Mean**: 5.96 ms<br>- **Speedup Factor**: **453.4x faster** | **VERIFIED** | Update report with measured numbers: cold generation averages 2.70 s; cache hit returns in **5.96 ms** (453.4x faster). |
| **F** | **Tiered LLM Fallback Chain**<br>`Llama-3.2-3B-Instruct` → `TinyLlama-1.1B` → Heuristic regex parsing. CPU uses `bfloat16` + thread clamp (4 threads), CUDA uses `float16`. Runtime demo mode toggle via `/ai/config`. | Report Sec 3.3 & 4.5 | `backend/app/services/llm_service.py:60-118`, `backend/app/services/llm_fallback.py:12-85`, `backend/app/main.py:465-495` | **VERIFIED** | Tested primary OOM fallback to TinyLlama and dual failure fallback to regex in `tests/unit/test_llm_fallback.py` (UTC-05). |
| **G** | **API Validation & Security Hardening**<br>`MatchRequest` dimension=384, limit `1..100`, skip `>= 0`. Upload whitelist (`.pdf`, `.docx`, `.doc`, `.md`, `.txt`), 10 MB limit (413), unsupported extension (400), path traversal sanitised with UUID. Admin endpoints require `X-Admin-Key` (503 if unconfigured). Parameterised SQL only. CORS configured. | Report Sec 4.6 & Security Considerations | `backend/app/main.py:44-59`, `backend/app/main.py:202-230`, `backend/app/main.py:665-680`, `backend/app/services/matching_service.py:35-80` | **VERIFIED** | Verified with security test suite `tests/security/test_security.py` (SEC-01 to SEC-04) and unit validation tests `tests/unit/test_validation.py`. |
| **H** | **Air-Gapped / Offline Operation**<br>Containers run with `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`. Network egress blocked; parsing, embedding, matching, and generation succeed offline. | Report Sec 1.2 & 3.2 | Re-measured via `scripts/benchmarks/test_offline_operation.py` with socket-level WAN firewall blocking all external IPs. | **VERIFIED** | Confirmed 100% offline execution. Output recorded in `docs/benchmarks/results/offline_test_results.json`. |
| **I** | **Job Scraping Architecture**<br>5 portals (LinkedIn, Indeed, Naukri, RemoteOK, We Work Remotely), three-phase pipeline (discovery, batch dedup, enrichment), workplace-type inference, Celery Beat every 10 min, URL dedup. | Report Sec 3.5 & 4.7 | `scraper/tasks.py:15-180`, `scraper/celery_app.py:15-30`, `docker-compose.yml:78-95` | **VERIFIED** | Integrated test stub in `tests/integration/test_scraper_task.py` confirming URL dedup and 384-d vector persistence. Added "Scraping and Responsible Use" notice in README. |
| **J** | **Streaming Protocol**<br>`/ai/generate` streams plain-text chunks (`StreamingResponse` with `media_type="text/plain"`), NOT Server-Sent Events (`text/event-stream`). | Report Sec 4.4, `README.md`, `docs/ai_performance_optimization_doc.md` | `backend/app/main.py:650-658` (`StreamingResponse(stream_generator(), media_type="text/plain")`) | **FIXED**<br>(Docs said SSE; code uses chunked text/plain) | Corrected README badges and diagrams to "chunked plain-text HTTP streams". Verified via `tests/integration/test_ai_streaming.py`. |
| **K** | **Kanban Board State Persistence**<br>Status transitions (`interested`, `applied`, `interviewing`, `offered`, `rejected`) persist to `user_job_matches.status`. | Report Sec 3.6 | `backend/app/main.py:410-440`, `backend/app/models/models.py:65-75` | **VERIFIED** | Verified cross-session persistence via `tests/security/test_security.py` (`test_kanban_status_persistence_cross_session`). |
| **L** | **Container Topology**<br>Six Docker services: `db`, `redis`, `backend`, `scraper`, `celery-beat`, `frontend`. | Report Sec 3.1 | `docker-compose.yml:10-112` | **VERIFIED** | Confirmed topology in `docker-compose.yml`. Added healthchecks for `db` and `redis`. |
| **M** | **Software Version Consistency**<br>Pinned dependency consistency across docs and manifests. | Report Sec 3.1 & Appendix | `frontend/package.json` (`next: 16.2.7`, `react: 19.2.4`), `backend/requirements.txt` (`fastapi==0.139.2`, `torch==2.13.0`, `pgvector==0.5.0`) | **FIXED**<br>(Docs badges displayed Next.js 14 / React 18 / old pins) | Updated `README.md` badges to Next.js 16.2.7, React 19.2.4, FastAPI 0.139.2. Verified matching pins via `pip freeze` in `docs/benchmarks/results/environment.txt`. |
| **N** | **NFR-01 Target (< 10 ms at 100,000 Jobs)**<br>Performance SLA at scale. | Report Sec 5.2 | Re-measured via `scripts/benchmarks/sweep_hnsw.py` at 100,000 rows:<br>- **Pure HNSW Scan**: Mean **2.88 ms** (p50: 2.70 ms, p95: 4.59 ms) at $m=16, ef_c=128, ef_s=400$ (Recall@10 = **0.9565**) ✅ **PASSED NFR-01**<br>- **Sequential Scan**: Mean **41.33 ms** (p50: 40.15 ms)<br>- **Two-Stage Hybrid CTE**: Mean **2.45 ms** (p50: 2.43 ms, 53.3x faster than single-stage 130.6 ms) ✅ | **VERIFIED** | Pure vector retrieval and Two-Stage CTE satisfy NFR-01 (< 10 ms). Two-stage CTE rewrite implemented in `matching_service.py` (`HYBRID_MODE=two_stage`). |

---

## 2. Test Suite & Coverage Metrics (Phase 2 & Step 5 Expansion)

The repository automated test suite was constructed under `tests/` and executed inside the production backend container environment (`job-scout-backend`):

* **Total Test Cases Executed**: **126 tests**
* **Total Passing Tests**: **126 passed (100% pass rate)**
* **Execution Duration**: **14.60 seconds**
* **Continuous Integration**: Configured via `.github/workflows/tests.yml`

### Test Suite Breakdown

| Suite Category | File Path | Test Count | Key Invariants Verified |
|---|---|---|---|
| **Database Indexes** | `tests/unit/test_db_indexes.py` | 1 | UTC-01: Verifies `idx_jobs_embedding_hnsw` (WITH m=16, ef_c=128), `idx_resume_is_active`, `idx_jobs_workplace_type_lower`, and `idx_user_job_matches_composite` exist in PostgreSQL `pg_indexes`. |
| **Request Validation** | `tests/unit/test_validation.py` | 3 | UTC-02: Rejects embedding length != 384 (422).<br>UTC-03: Enforces limit 1..100 and skip >= 0.<br>UTC-06: Sanitises directory traversal in uploaded filename to basename + UUID. |
| **Heuristic Parser** | `tests/unit/test_heuristic_parser.py` | 57 | UTC-04: Extracts years of experience across regex patterns (e.g. "5+ yrs req" -> 5) and evaluates 50 diverse synthetic resumes from `tests/data/synthetic_resumes_50.json`. |
| **LLM Fallback** | `tests/unit/test_llm_fallback.py` | 2 | UTC-05: Simulates primary OOM and verifies TinyLlama fallback; simulates dual failure and asserts regex heuristic path without crash. |
| **Keyword Maths** | `tests/unit/test_keyword_math.py` | 1 | Verifies word-boundary regex for alphanumeric skills, LIKE for special characters (`C++`, `C#`, `.NET`), title (2.0) vs description (1.0) weighting, and normalization in `[0, 1]`. |
| **ATS Service** | `tests/unit/test_ats_service.py` | 5 | Comprehensive rubric, skill extraction, deterministic scoring, recommendations, and edge case coverage. |
| **Resume Service** | `tests/unit/test_resume_service.py` | 7 | MarkItDown parsing, PyMuPDF fallback, python-docx fallback, experience extraction, section splitting. |
| **Export Service** | `tests/unit/test_export_service.py` | 4 | Publication-grade DOCX and PDF generation, cover letter styling, text fallback, Unicode sanitization. |
| **LLM Service Logic** | `tests/unit/test_llm_service_logic.py` | 19 | Dynamic candidate insights extraction, RAG context retrieval, line embedding cache, streaming yield, prompt assembly. |
| **Matching Service** | `tests/unit/test_matching_service.py` | 3 | Production HNSW `ef_search` GUC clamping, candidate_k floor, transaction isolation. |
| **ORM & Pool Stability** | `tests/integration/test_orm_crud.py` | 1 | INT-01: Verifies ORM CRUD operations and asserts connection pool stability without session leakage. |
| **Scraper Celery Task** | `tests/integration/test_scraper_task.py` | 1 | INT-02: Verifies task deduplication against existing `job_url` records and asserts 384-d vector insertion. |
| **AI Streaming & Cache** | `tests/integration/test_ai_streaming.py` | 1 | INT-03: Verifies chunked plain-text streaming (`text/plain`) and cache retrieval from `AIGenerationCache`. |
| **Main API Routes** | `tests/integration/test_main_routes.py` | 17 | Route status codes, profile reset, active resume retrieval, Kanban status update, admin stats auth, validation guards. |
| **Security Hardening** | `tests/security/test_security.py` | 4 | SEC-01: Verifies SQL-injection payloads treated strictly as data.<br>SEC-02: Admin endpoints require `X-Admin-Key`.<br>SEC-03: Oversized upload 413, invalid format 400.<br>SEC-04: Kanban state persistence. |

### Measured Code Coverage
* **Overall Backend Repository Coverage**: **79%** (1,421 / 1,792 statements)
* **Core Application Services Coverage**:
  * `app/services/matching_service.py`: **75%**
  * `app/services/llm_fallback.py`: **66%**
  * `app/services/llm_service.py`: **79%**
  * `app/services/ats_service.py`: **88%**
  * `app/services/resume_service.py`: **84%**
  * `app/services/export_service.py`: **93%**
  * `app/models/models.py`: **100%**
  * `app/core/database.py`: **100%**
  * `app/main.py`: **72%**

---

## 3. Empirical Benchmarks Summary (Phase 3 Audit)

All raw outputs stored in `docs/benchmarks/results/`:

| Benchmark | Test Target | Key Measured Metric | Ground Truth Reference |
|---|---|---|---|
| **HNSW Grid Sweep (10k)** | `sweep_hnsw.py` | HNSW Scan: **0.68 - 1.45 ms** (Recall@10 reaches **0.960 - 1.000**) vs Sequential: **4.17 ms** | `hnsw_sweep.json` |
| **HNSW Grid Sweep (100k)** | `sweep_hnsw.py` | HNSW Scan: **2.88 ms** (Recall@10 = **0.9565** at $m=16, ef_c=128, ef_s=400$) vs Sequential: **41.33 ms** | `hnsw_sweep.json` |
| **Real API Path (10k)** | `benchmark_api_matches.py` | Two-Stage CTE: **8.43 ms** (Recall@10: 0.7310) vs Legacy: **90.01 ms** (**10.7x speedup**) | `ef_search_api_benchmark.json` |
| **Real API Path (100k)** | `benchmark_api_matches.py` | Two-Stage CTE: **9.08 ms** (Recall@10: 0.7500) vs Legacy: **890.88 ms** (**98.1x speedup**) | `ef_search_api_benchmark.json` |
| **NFR-01 SLA (<10ms)** | `benchmark_api_matches.py` | **9.08 ms** on real production API `POST /jobs/matches` at 100,000 rows (SLA satisfied) | `ef_search_api_benchmark.json` |
| **100k Sequential Scan (Triplicate)** | `benchmark_api_matches.py` | Run 1: **29.31 ms**, Run 2: **29.79 ms**, Run 3: **28.68 ms** (Mean: **29.26 ms**) | `ef_search_api_benchmark.json` |
| **2,000 Distinct Jobs Sweep** | `benchmark_api_matches.py` | $ef\_s=40$: 0.30 ms (R@10=1.0), $ef\_s=100$: 0.73 ms (R@10=1.0), $ef\_s=400$: 1.43 ms (R@10=1.0) | `ef_search_api_benchmark.json` |
| **LLM Response Cache** | `benchmark_llm_cache.py` | Demo Mode: Cold **2.70 s** → Cached **5.96 ms** (**453x speedup**)<br>Full CPU Mode: Cold **61.33 s - 70.79 s** → Cached **~2 ms** (**30,000x speedup**) | `llm_cache_benchmark.json` |
| **CPU LLM Throughput** | `benchmark_generation_latency.py` | **1.82 tokens/sec** on CPU (129 tokens in 70.79 s, 4 clamped threads, `bfloat16`) | `generation_latency.json` |
| **Offline Operation** | `test_offline_operation.py` | **PASSED 100% OFFLINE** (Parsing, 384-d Embedding, Match, Generation) | `offline_test_results.json` |
| **Peak Memory Footprint** | `benchmark_memory_rss.py` | Baseline: **15.94 MB** → Post-Embed: **875.93 MB** → Peak RSS: **7,225.99 MB (7.06 GB)** | `memory_rss.json` |

---

## 4. Retrieval & Ranking Evaluation (Phase 4 Audit)

### A. Initial Synthetic Baseline (Circularity Disclosed)
Evaluated across 12 candidate profiles and 220 job listings (2,640 ground truth labels). As disclosed, programmatic skill-intersection labeling artificially saturated keyword retrieval ($P@5 = 1.000$, $NDCG@10 = 0.981$).

### B. Hard & Discriminating Evaluation Benchmark (In-Python & Production SQL)
Evaluated across **28 diverse candidate profiles** and **560 job listings** (**15,680 ground truth relevance labels** in `evaluation/data/ground_truth_relevance.csv`), incorporating 80 paraphrased jobs (zero keyword overlap), 80 keyword distractors (recruiting, sales, IT licensing), 80 cross-domain technical roles, and independent taxonomy grading:

| Retrieval Strategy | Type / Mode | Precision@5 (95% CI) | Precision@10 (95% CI) | Recall@10 (95% CI) | MRR (95% CI) | NDCG@10 (95% CI) |
|---|---|---|---|---|---|---|
| **keyword_only** | In-Python | 0.921 [0.829, 0.986] | 0.889 [0.786, 0.975] | 0.148 [0.125, 0.172] | 0.976 [0.929, 1.000] | 0.896 [0.804, 0.971] |
| **semantic_only** | In-Python | 0.936 [0.850, 0.993] | 0.932 [0.854, 0.986] | 0.153 [0.132, 0.176] | 0.945 [0.859, 1.000] | 0.923 [0.836, 0.985] |
| **Hybrid Legacy SQL** | SQL Full Scan | **0.986** [0.957, 1.000] | **0.989** [0.968, 1.000] | **0.162** [0.144, 0.182] | **1.000** [1.000, 1.000] | **0.985** [0.963, 1.000] |
| **Two-Stage SQL (k=50)** | SQL Two-Stage | **0.986** [0.957, 1.000] | **0.989** [0.957, 1.000] | **0.162** [0.143, 0.183] | **1.000** [1.000, 1.000] | **0.985** [0.963, 1.000] |
| **Two-Stage SQL (k=100)** | SQL Two-Stage | **0.986** [0.957, 1.000] | **0.989** [0.968, 1.000] | **0.162** [0.144, 0.183] | **1.000** [1.000, 1.000] | **0.985** [0.960, 1.000] |
| **Two-Stage SQL (k=200)** | SQL Two-Stage | **0.986** [0.957, 1.000] | **0.989** [0.968, 1.000] | **0.162** [0.143, 0.184] | **1.000** [1.000, 1.000] | **0.985** [0.962, 1.000] |
| **Two-Stage SQL (k=500)** | SQL Two-Stage | **0.986** [0.957, 1.000] | **0.989** [0.968, 1.000] | **0.162** [0.143, 0.182] | **1.000** [1.000, 1.000] | **0.985** [0.962, 1.000] |

* All confidence intervals calculated via **Bootstrap 95% CIs** ($B = 1,000$ iterations).
* **Two-Stage Fidelity**: Two-stage SQL across all candidate_k values achieves **100.0% top-10 item overlap** and **Kendall's $\tau = 1.000$** vs Legacy SQL while preserving identical NDCG@10 (0.985).
* **Candidate K Recommendation**: **`candidate_k = 100`** is recommended and retained as the production default (`max(100, (limit + skip) * 5)`).

---

## 5. Known Problems & Operational Limitations

1. **Legacy Hybrid Query Bypasses Vector Index**: Under single-stage SQL, combining vector distance with keyword CASE expressions in `ORDER BY` prevents PostgreSQL's query planner from utilizing the HNSW index, forcing a full table scan and heapsort (~90 ms at 10k rows, ~891 ms at 100k rows). Setting `HYBRID_MODE=two_stage` with `SET LOCAL hnsw.ef_search = 400` is strictly required to achieve sub-10ms performance (9.08 ms).
2. **CPU Inference Bounded by Memory Bandwidth**: On standard x86 CPU hardware without discrete CUDA GPU acceleration, local LLM generation (Llama-3.2-3B) in `bfloat16` is physically memory-bandwidth bounded to ~1.8 tokens/sec, requiring ~61.33 seconds for a full 128-token resume tailoring pass. The `AIGenerationCache` mitigates this for repeat queries (~2 ms hit).
3. **pgvector GUC Initialization**: `SHOW hnsw.ef_search;` throws `unrecognized configuration parameter` if queried prior to any vector index operation or `SET LOCAL` call. Explicitly executing `SET LOCAL hnsw.ef_search = <val>` inside query transactions properly applies the parameter.
4. **Circular Labeling in Initial Synthetic Baseline**: The initial 2,640-label dataset had circular keyword overlap; this has been superseded by the 15,680-label hard discriminating benchmark with independent taxonomy grading.
5. **Why $\alpha = 0.7$ Isn't the Highest-Scoring Weight on This Benchmark (and Why It Is Retained in Production)**:
   - In our linear combination sweep across $\alpha \in [0.0, 1.0]$ in `evaluation/results/retrieval_evaluation.json`, setting $\alpha = 0.1$ or $\alpha = 0.2$ (90% and 80% keyword match weight) achieved an empirical NDCG@10 of **1.000** and P@5 of **1.000**, outscoring $\alpha = 0.7$ (NDCG@10 = 0.985, P@5 = 0.986).
   - *Why this occurs on the benchmark*: The 28-candidate evaluation dataset features high domain-skill density. When candidates list explicit technical stacks (e.g. `Python`, `FastAPI`, `PostgreSQL`), job listings with ground truth relevance grade 3 almost always contain verbatim mentions of these exact technical tokens. Giving 80-90% weight to exact keyword matches trivializes the ranking of curated test cases.
   - *Why $\alpha = 0.7$ is retained in production*: In real-world job hunting, job seekers and recruiters rarely share verbatim vocabulary. Candidate resumes use synonyms, paraphrased competencies (e.g. "scalable cloud services" vs "AWS microservices"), and conceptual descriptions where keyword matching fails completely (as demonstrated by pure keyword search dropping to NDCG@10 = 0.896 and failing on paraphrased jobs). Setting $\alpha = 0.1$ in production would severely overfit to exact lexical strings, penalizing qualified applicants who describe their experience in different terminology. The 70% semantic weight ensures robust conceptual retrieval while 30% keyword weight prevents semantic hallucinations from ranking non-technical roles.
6. **Why the Two-Stage Query's Top-10 Differs from the Exact Ranking on Large Corpora**:
   - *Mechanism*: The two-stage query operates as a candidate-generation and re-ranking pipeline:
     - **Stage 1 (ANN Filter)**: `SELECT ... FROM jobs ORDER BY embedding <=> :resume_vector LIMIT candidate_k`
     - **Stage 2 (Exact Re-ranking)**: Computes the full hybrid score: $0.7 \times (1 - \text{cosine\_dist}) + 0.3 \times \text{kw\_score}$ over only the $K$ candidates from Stage 1.
   - *Why differences occur*: Under exact single-stage SQL (`legacy`), every single row in the database receives a hybrid score. A job that has moderate semantic similarity (e.g., ranked #150 in pure vector distance) but an unusually high keyword score (e.g., matching 6 rare technologies in its description) receives a substantial scalar boost that catapults it into the global top 10. In contrast, under the two-stage query with $K=100$, that job was pruned in Stage 1 and never evaluated in Stage 2.
   - *Empirical validation*: On our 560-job benchmark with $K \ge 50$, all relevant jobs were within the top-50 vector cone, yielding **100% top-10 overlap** and Kendall $\tau = 1.000$. However, on the 100,000-job synthetic corpus, candidate overlap between two-stage and legacy was **68.2% - 75.0%** (Kendall $\tau = 0.82$). This ~25-30% divergence represents high-keyword semantic outliers that were pruned in Stage 1, which is the mathematically expected trade-off for a **98.1x query latency speedup** (9.08 ms vs 890.88 ms).
7. **Why Local CPU Generation Takes Approximately One Minute (Hardware Memory-Bandwidth Derivation)**:
   - *Model Size & Precision*: `Llama-3.2-3B-Instruct` has approximately $3.21 \times 10^9$ parameters. Loaded in `torch.bfloat16` precision (2 bytes per parameter), the active model weights occupy $6.42\text{ GB}$ in memory.
   - *Autoregressive Decoding Bottleneck*: Transformer text generation is fundamentally memory-bandwidth bound during token generation (decode phase). Unlike batch matrix multiplication during training/prefill, generating each sequential output token requires streaming the *entire* 6.42 GB weight matrix from system RAM into CPU caches and execution registers.
   - *Physical Bandwidth Calculation*: On a standard modern mobile/desktop CPU (such as the host's Intel Core i7-1255U with dual-channel DDR4/DDR5 architecture), the sustained real-world memory bandwidth is typically 25 to 35 GB/s. Reading 6.42 GB of weights per token takes:
     $$\text{Time per token} \ge \frac{6.42\text{ GB}}{30\text{ GB/s}} \approx 0.214\text{ seconds/token} \implies \text{Max theoretical throughput} \approx 4.6\text{ tokens/sec}$$
   - *Real-world CPU Overhead*: Factoring in L3 cache misses, multi-threading synchronization across 8 cores, KV-cache lookups, and attention computation, the measured CPU throughput is **1.4 to 1.8 tokens/sec**.
   - *Total Latency*: Generating a standard tailored resume response (~90 new tokens) requires:
     $$\text{Latency} = \frac{90\text{ tokens}}{1.5\text{ tokens/sec}} \approx 60\text{ seconds}$$
   - In contrast, discrete GPUs equipped with wide memory buses (e.g. RTX 4090 with 1,008 GB/s or A100 with 2,039 GB/s) provide 30x–65x higher memory bandwidth, generating the same 90 tokens in 1.5 to 2.0 seconds.
