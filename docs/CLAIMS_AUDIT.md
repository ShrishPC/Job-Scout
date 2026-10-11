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
| **M** | **Software Version Consistency**<br>Pinned dependency consistency across docs and manifests. | Report Sec 3.1 & Appendix | `frontend/package.json` (`next: 16.2.7`, `react: 19.2.4`), `backend/requirements.txt` (`fastapi==0.139.2`, `torch==2.6.0`, `pgvector==0.3.6`) | **FIXED**<br>(Docs badges displayed Next.js 14 / React 18) | Updated `README.md` badges to Next.js 16.2.7, React 19.2.4, FastAPI 0.139.2. Verified matching pins. |
| **N** | **NFR-01 Target (< 10 ms at 100,000 Jobs)**<br>Performance SLA at scale. | Report Sec 5.2 | Re-measured via `scripts/benchmarks/benchmark_pgvector.py` at 100,000 rows:<br>- **Pure HNSW Scan**: Mean **3.23 ms** (p50: 3.12 ms, p95: 4.50 ms, p99: 5.42 ms) ✅ **PASSED NFR-01**<br>- **Sequential Scan**: Mean **41.33 ms** (p50: 39.81 ms)<br>- **Hybrid Expression (0.7/0.3)**: Mean **289.66 ms** (HNSW index bypassed by planner) ⚠️ | **VERIFIED (with qualification)** | Pure vector retrieval satisfies NFR-01 (< 10 ms). Documented that hybrid query requires two-stage ANN CTE rewrite to maintain <10ms SLA at 100k scale. |

---

## 2. Test Suite & Coverage Metrics (Phase 2 Audit)

The repository automated test suite was constructed under `tests/` and executed inside the production backend container environment (`job-scout-backend`):

* **Total Test Cases Executed**: **71 tests**
* **Total Passing Tests**: **71 passed (100% pass rate)**
* **Execution Duration**: **4.91 seconds**
* **Continuous Integration**: Configured via `.github/workflows/tests.yml`

### Test Suite Breakdown

| Suite Category | File Path | Test Count | Key Invariants Verified |
|---|---|---|---|
| **Database Indexes** | `tests/unit/test_db_indexes.py` | 1 | UTC-01: Verifies `idx_jobs_embedding_hnsw`, `idx_resume_is_active`, `idx_jobs_workplace_type_lower`, and `idx_user_job_matches_composite` exist in PostgreSQL `pg_indexes`. |
| **Request Validation** | `tests/unit/test_validation.py` | 5 | UTC-02: Rejects embedding length != 384 (422).<br>UTC-03: Enforces limit 1..100 and skip >= 0.<br>UTC-06: Sanitises directory traversal in uploaded filename to basename + UUID. |
| **Heuristic Parser** | `tests/unit/test_heuristic_parser.py` | 52 | UTC-04: Extracts years of experience across regex patterns (e.g. "5+ yrs req" -> 5) and evaluates 50 diverse synthetic resumes from `tests/data/synthetic_resumes_50.json`. |
| **LLM Fallback** | `tests/unit/test_llm_fallback.py` | 3 | UTC-05: Simulates primary OOM and verifies TinyLlama fallback; simulates dual failure and asserts regex heuristic path without crash. |
| **Keyword Maths** | `tests/unit/test_keyword_math.py` | 4 | Verifies word-boundary regex for alphanumeric skills, LIKE for special characters (`C++`, `C#`, `.NET`), title (2.0) vs description (1.0) weighting, and normalization in `[0, 1]`. |
| **ORM & Pool Stability** | `tests/integration/test_orm_crud.py` | 1 | INT-01: Verifies ORM CRUD operations and asserts connection pool stability without session leakage. |
| **Scraper Celery Task** | `tests/integration/test_scraper_task.py` | 1 | INT-02: Verifies task deduplication against existing `job_url` records and asserts 384-d vector insertion. |
| **AI Streaming & Cache** | `tests/integration/test_ai_streaming.py` | 2 | INT-03: Verifies chunked plain-text streaming (`text/plain`).<br>INT-04: Verifies subsequent identical generation hit returns cached content from `AIGenerationCache`. |
| **Security Hardening** | `tests/security/test_security.py` | 5 | SEC-01: Verifies SQL-injection payloads are treated strictly as data.<br>SEC-02: Verifies admin endpoints return 503 without `ADMIN_API_KEY` and 401/403 with invalid keys.<br>SEC-03: Verifies 413 for oversized uploads, 400 for disallowed extensions, and CORS blocking.<br>SEC-04: Verifies cross-session persistence of Kanban status changes. |

### Measured Code Coverage
* **Overall Backend Repository Coverage**: **34%**
* **Core Application Services Coverage**:
  * `app.services.matching_service`: **71%**
  * `app.services.llm_fallback`: **63%**
  * `app.models.models`: **96%**
  * `app.core.database`: **93%**
  * `app.main`: **46%**

---

## 3. Empirical Benchmarks Summary (Phase 3 Audit)

All raw outputs stored in `docs/benchmarks/results/`:

| Benchmark | Test Target | Key Measured Metric | Ground Truth Reference |
|---|---|---|---|
| **Vector Search (10k)** | `benchmark_pgvector.py` | HNSW Scan: **1.06 ms** (p50: 1.02 ms) vs Sequential: **4.37 ms** | `pgvector_benchmark.json` |
| **Vector Search (100k)** | `benchmark_pgvector.py` | HNSW Scan: **3.23 ms** (p50: 3.12 ms) vs Sequential: **41.33 ms** | `pgvector_benchmark.json` |
| **NFR-01 SLA (<10ms)** | `benchmark_pgvector.py` | **3.23 ms** at 100,000 rows (SLA satisfied for vector search) | `pgvector_benchmark.json` |
| **Hybrid Query at 100k** | `benchmark_pgvector.py` | Mean **289.66 ms** (EXPLAIN ANALYZE confirms planner uses Seq Scan) | `pgvector_benchmark.json` |
| **LLM Response Cache** | `benchmark_llm_cache.py` | Cold: **2.70 s** (2,700 ms) → Cached: **5.96 ms** (**453.4x speedup**) | `llm_cache_benchmark.json` |
| **CPU LLM Throughput** | `benchmark_generation_latency.py` | **1.82 tokens/sec** on CPU (129 tokens in 70.79 s, 4 threads, `bfloat16`) | `generation_latency.json` |
| **Offline Operation** | `test_offline_operation.py` | **PASSED 100% OFFLINE** (Parsing, 384-d Embedding, Match, Generation) | `offline_test_results.json` |
| **Peak Memory Footprint** | `benchmark_memory_rss.py` | Baseline: **15.94 MB** → Post-Embed: **875.93 MB** → Peak RSS: **7,225.99 MB (7.06 GB)** | `memory_rss.json` |

---

## 4. Retrieval & Ranking Evaluation (Phase 4 Audit)

Evaluated across **12 candidate profiles** and **220 job listings** (2,640 ground truth relevance labels in `evaluation/data/ground_truth_relevance.csv`):

| Retrieval Strategy | Alpha (α) | Precision@5 (95% CI) | Precision@10 (95% CI) | Recall@10 (95% CI) | MRR (95% CI) | NDCG@10 (95% CI) |
|---|---|---|---|---|---|---|
| **keyword_only** | 0.0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.444 [0.360, 0.520] | 1.000 [1.000, 1.000] | 0.981 [0.943, 1.000] |
| **semantic_only** | 1.0 | 0.933 [0.817, 1.000] | 0.925 [0.808, 1.000] | 0.404 [0.316, 0.482] | 1.000 [1.000, 1.000] | 0.922 [0.835, 0.990] |
| **production_hybrid_0.7** | 0.7 | 0.967 [0.900, 1.000] | 0.967 [0.900, 1.000] | 0.426 [0.345, 0.502] | 1.000 [1.000, 1.000] | 0.962 [0.905, 1.000] |

* All confidence intervals calculated via **Bootstrap 95% CIs** ($B = 1,000$ iterations).
* Full sweep table across $\alpha \in [0.0, 1.0]$ in increments of 0.1 documented in `evaluation/results/retrieval_summary.md`.
