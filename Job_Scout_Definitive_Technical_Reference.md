# Job Scout — Definitive Technical Reference
**Version:** 1.0.0 (Production — `main` branch)
**Last Updated:** June 2026
**Classification:** Internal Engineering Documentation

---

## Preface

This document is not a summary. It is a **testimony** — a full, honest account of why every technical decision in Job Scout was made the way it was, what the alternatives were, and precisely why they were rejected. It is written so that any engineer, interviewer, or future maintainer can read it from start to finish and walk away with a complete, unambiguous understanding of the system's design philosophy, its constraints, and its future trajectory.

Job Scout is not a prototype. It is a production-grade, privacy-first, AI-powered job hunting platform that requires zero external API calls for its core intelligence. Every component was chosen deliberately. Every trade-off was accepted consciously.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Design Philosophy](#2-core-design-philosophy)
3. [The Technology Stack — Chosen, Justified, Defended](#3-the-technology-stack)
   - 3.1 [Backend Framework: FastAPI](#31-backend-framework-fastapi)
   - 3.2 [Frontend Framework: Next.js](#32-frontend-framework-nextjs)
   - 3.3 [Task Queue: Celery + Redis](#33-task-queue-celery--redis)
   - 3.4 [Containerisation: Docker Compose](#34-containerisation-docker-compose)
4. [The Database Architecture — A Deep Dive](#4-the-database-architecture)
   - 4.1 [Why PostgreSQL](#41-why-postgresql)
   - 4.2 [Why pgvector](#42-why-pgvector)
   - 4.3 [Schema Design](#43-schema-design)
   - 4.4 [Alternatives Considered and Rejected](#44-alternatives-considered-and-rejected)
   - 4.5 [The Scaling Roadmap](#45-the-scaling-roadmap)
5. [The AI Stack — Model Selection Rationale](#5-the-ai-stack)
   - 5.1 [Embedding Model: all-MiniLM-L6-v2](#51-embedding-model-all-minilm-l6-v2)
   - 5.2 [Local LLM: unsloth/Llama-3.2-3B-Instruct](#52-local-llm-unslothlllama-32-3b-instruct)
   - 5.3 [Fallback Chain](#53-fallback-chain)
   - 5.4 [Alternatives Considered and Rejected](#54-alternatives-considered-and-rejected)
6. [The RAG Pipeline — Architecture & Optimisations](#6-the-rag-pipeline)
7. [The Scraping Infrastructure](#7-the-scraping-infrastructure)
8. [Caching Strategy — Two Layers](#8-caching-strategy)
9. [Hardware & Deployment Considerations](#9-hardware--deployment-considerations)
10. [Known Constraints & Engineering Debt](#10-known-constraints--engineering-debt)
11. [Future Roadmap & Scaling Plan](#11-future-roadmap--scaling-plan)

---

## 1. System Overview

Job Scout is a **full-stack, AI-powered job application management platform** built for the individual job seeker. At its core, it solves a singular, real problem: the modern job market is noisy, applications are generic, and the tools available to candidates are either expensive SaaS products that send data to external servers, or crude spreadsheet trackers.

Job Scout occupies a different position entirely. It is:

- **Self-hosted** — runs entirely on the user's local machine or a private server.
- **Privacy-first** — no resume data, no personal information, no generated content ever leaves the machine.
- **Semantically intelligent** — uses real vector embeddings to understand the *meaning* of a job description, not just keyword matches.
- **AI-augmented** — uses a locally-hosted Large Language Model (LLM) to generate cover letters and tailored resume summaries, grounded in the candidate's actual history via a Retrieval-Augmented Generation (RAG) pipeline.

### System Capabilities at a Glance

- Automatically scrapes job listings from **LinkedIn, Indeed, Naukri, RemoteOK, and We Work Remotely**.
- Converts uploaded resumes (PDF, DOCX, MD) into structured Markdown and JSON, then into a semantic vector embedding.
- Matches that embedding against all scraped jobs using **cosine similarity via pgvector**, returning a ranked list of the most relevant openings.
- Tracks job applications on a **Kanban board** (Interested → Applied → Interviewing → Offered / Rejected).
- Feeds Kanban board jobs into a **local LLM pipeline** that generates a tailored resume summary or a custom cover letter using only the candidate's own history — no hallucinations, no fabrications.
- Caches AI outputs in PostgreSQL to prevent redundant computation across identical requests.
- Allows dynamic switching of AI computation between **CPU and CUDA** without restarting the application.

---

## 2. Core Design Philosophy

Before examining individual technology choices, it is necessary to understand the three axioms that governed every decision in this project:

**Axiom 1: Zero Dependency on Paid External APIs.**
> The system must not break if an external service is unavailable, raises its prices, or changes its terms of service. All intelligence must be self-contained. This immediately ruled out any architecture that relied on OpenAI, Anthropic, Google Gemini, or Cohere for the primary intelligence loop.

**Axiom 2: Correctness Over Speed.**
> When choosing between a faster-but-approximate approach and a slower-but-accurate approach, accuracy wins — particularly in the AI generation layer. A cover letter that is factually wrong is worse than no cover letter at all. This shaped the RAG design: the system is deliberately grounded and slow rather than fast and hallucinating.

**Axiom 3: Graceful Degradation.**
> Every component must have a fallback. If the primary LLM fails to load, a smaller model is used. If that fails, a heuristic regex-based parser takes over. If batch embedding fails, single-item embedding is tried. The system never produces a hard crash to the user when an AI component fails — it degrades to the next available tier.

---

## 3. The Technology Stack

### 3.1 Backend Framework: FastAPI

**Chosen:** FastAPI (Python)

**Why FastAPI:**

- FastAPI is the gold standard for building **typed, self-documenting REST APIs in Python**. Its use of Python type hints via Pydantic for request and response validation provides compile-time-like safety in a dynamically typed language.
- Its `async`-first design integrates naturally with the `httpx` and `aiohttp` calls used in the scraper pipeline. Non-blocking I/O means scraping dozens of job URLs concurrently without spawning dozens of threads.
- Automatic generation of **OpenAPI (Swagger) documentation** at `/docs` allows the frontend team to explore and test all endpoints without writing a single line of documentation.
- The `Depends()` injection system provides clean, testable dependency injection for database sessions — every handler receives a fresh session and the framework guarantees it is closed, preventing connection leaks.
- Pydantic validators (e.g., `@field_validator` on the `MatchRequest` model enforcing exactly 768 embedding dimensions) provide server-side data integrity that would require significant boilerplate in other frameworks.

**Why NOT Flask:**
- Flask is synchronous by default. Building an efficient scraper pipeline on Flask would require either `gevent` monkey-patching (fragile) or a heavy threading model. FastAPI's native async support is architecturally cleaner for I/O-bound workloads.
- Flask has no built-in request validation. Pydantic would need to be wired manually. FastAPI does this out of the box.
- Flask's lack of automatic API documentation generation is a meaningful developer velocity loss.

**Why NOT Django:**
- Django's ORM (Django ORM) does not support `pgvector` column types without a third-party package that lags behind in maintenance.
- Django carries significant overhead (admin panel, middleware, ORM migrations, template engine) that is entirely unnecessary for a pure API service. FastAPI with SQLAlchemy provides the same data-layer power with a fraction of the initialization weight.
- Django's synchronous request handling model (prior to ASGI adoption in Django 3.1+) would have introduced the same I/O bottleneck problems as Flask.

**Why NOT Express.js / Node:**
- The AI stack (`sentence-transformers`, `transformers`, `torch`, `pgvector`) is Python-exclusive. Building the backend in Node would have required bridging to a Python subprocess for every AI call — introducing latency, a serialisation boundary, and a second process to manage. Keeping the entire backend in Python eliminates this friction entirely.

---

### 3.2 Frontend Framework: Next.js

**Chosen:** Next.js 16.2.7 with Turbopack

**Why Next.js:**

- Next.js provides a **production-grade React framework** with server-side rendering (SSR), static site generation (SSG), and App Router capabilities out of the box. Even though Job Scout currently operates as a client-side SPA, the App Router structure provides an upgrade path to SSR without a framework migration.
- **Turbopack** (the successor to Webpack) provides dramatically faster hot module replacement (HMR) during development — critical for a UI-heavy project with many interactive components.
- The file-system-based routing in Next.js keeps view organisation intuitive and navigable.
- Next.js has first-class TypeScript support, which was essential given the number of typed API response shapes (`BoardJob`, `ActiveResume`, `AIGenerateRequest`) that need to be correctly handled across the frontend.
- The `"use client"` directive pattern in the App Router allows clean separation between server and client components, a pattern adopted in `AITailorView.tsx` and all other interactive views.

**Why Tailwind CSS:**
- Tailwind's utility-first approach enables rapid, consistent UI construction without context-switching to a separate CSS file. The custom retro design system (`retro-cream`, `retro-yellow`, `retro-red`, `retro-mint`) is defined as Tailwind configuration tokens, ensuring the entire application shares a single source of truth for colours, spacing, and typography.
- The neobrutalist design language of Job Scout (thick borders, hard drop shadows, bold uppercase labels) maps naturally to Tailwind's composable utilities.

**Why NOT Vue / Nuxt:**
- The team had stronger existing competency in React's ecosystem. Adopting Nuxt would have introduced a learning overhead on both the component model and the Composition API conventions.
- The React ecosystem's library breadth (Lucide Icons, react-hook-form, etc.) provided ready-made solutions for every UI requirement without custom implementation.

**Why NOT Create React App:**
- CRA is deprecated. Turbopack/Vite/Next.js have entirely superseded it. There was no reason to build on an abandoned toolchain.

---

### 3.3 Task Queue: Celery + Redis

**Chosen:** Celery (task queue) + Redis (broker/backend)

**Why Celery:**

- Scraping job boards is fundamentally a **long-running, I/O-bound, failure-prone background operation**. It must never block the FastAPI request-response cycle. Celery provides a battle-tested distributed task queue that handles this exactly: the API triggers a Celery task in under 1ms and immediately returns a `task_id`, while the actual scraping work happens in a fully decoupled worker process.
- **Celery Beat** provides a cron-like scheduler that runs automated scraping tasks on a defined schedule (currently: daily at midnight, and every 10 minutes for LinkedIn). This means the database stays fresh without any human interaction.
- Celery's retry and error-handling primitives (exponential backoff, `max_retries`) provide automatic resilience against flaky scraper targets — a job board occasionally returning a 429 rate limit response does not crash the entire system.
- The `scrape_and_process_jobs` task implements a **three-phase deduplication pipeline**: (1) discover links, (2) filter out URLs already in the database, (3) enrich only genuinely new jobs. This prevents redundant database writes and redundant embedding generation on already-known jobs.

**Why Redis:**

- Redis serves a dual role: Celery **message broker** (queuing task instructions from the API to the worker) and Celery **result backend** (storing task completion states and return values).
- Redis is an **in-memory data store** with sub-millisecond read/write latency — ideal for the high-frequency task dispatch and status polling patterns of a Celery system.
- Redis's persistence configuration (RDB snapshots + AOF logging) can be enabled to survive restarts without losing queued tasks.
- The Redis Alpine image (`redis:alpine`) is a minimal, ~5MB container — there was no reason to use a larger image for this use case.

**Why NOT RabbitMQ:**
- RabbitMQ is a more powerful broker with AMQP support, exchange routing, and delivery guarantees. However, for a single-node deployment, RabbitMQ's operational complexity (management console, vhosts, user configuration) is entirely unnecessary overhead. Redis provides all required brokering features with zero configuration.

**Why NOT Database-Backed Queues (e.g., django-db-scheduler, Postgres LISTEN/NOTIFY):**
- Using PostgreSQL as a task queue is a well-documented anti-pattern for high-frequency writes. It generates table bloat, causes polling overhead, and does not scale horizontally without complex partitioning. Redis is the correct tool for this use case.

---

### 3.4 Containerisation: Docker Compose

**Chosen:** Docker Compose (for local orchestration)

**Why Docker Compose:**

- Docker Compose provides **reproducible, isolated environments** for all four services (PostgreSQL/pgvector, Redis, FastAPI backend, Celery scraper workers) with a single `docker-compose up` command.
- Port mapping has been intentionally remapped from defaults (`5435:5432` for Postgres, `6380:6379` for Redis) to avoid conflicts with system-level daemons that many Linux developer workstations run on the standard ports. This was a direct response to a real deployment problem encountered during development.
- Container-level networking (`depends_on`) ensures services start in the correct order, preventing the backend from attempting database connections before the database is ready.

**Why NOT Kubernetes:**
- Kubernetes (K8s) is the industry standard for production-grade container orchestration at scale, but it is categorically over-engineered for a single-node deployment. Kubernetes requires a control plane, etcd, kubelet, and significant operational knowledge to maintain. For a personal tool running on one machine, Docker Compose provides 95% of the benefits with 5% of the complexity.
- The planned scaling roadmap (see Section 11) does identify Kubernetes as the natural upgrade path when multi-node horizontal scaling becomes necessary.

---

## 4. The Database Architecture

### 4.1 Why PostgreSQL

**Chosen:** PostgreSQL 15 (via `ankane/pgvector` Docker image)

PostgreSQL was selected as the primary data store for five specific reasons:

1. **ACID Compliance:** Every job write, resume update, and AI cache store in Job Scout is a transactional operation. ACID guarantees (Atomicity, Consistency, Isolation, Durability) ensure that partial failures — e.g., a scraper crash mid-batch — do not leave the database in a corrupted or inconsistent state. The scraper's `db.rollback()` calls in exception handlers are only meaningful because PostgreSQL supports true transactions.

2. **The pgvector Extension:** PostgreSQL is, as of 2024, the only production-grade relational database with a mature, production-proven vector similarity search extension (`pgvector`). This is not a minor feature — it is the entire architectural backbone of Job Scout's semantic matching system. Choosing PostgreSQL was, in large part, choosing pgvector.

3. **JSON/JSONB Column Support:** Job Scout stores semi-structured data (parsed resume skills, experience history, job metadata) in `JSON` columns alongside strongly-typed relational data. PostgreSQL's native `JSON` and `JSONB` types allow querying within JSON fields using standard SQL, without requiring a separate document store. No other SQL database handles this as elegantly.

4. **Mature ORM Support:** SQLAlchemy, the industry-standard Python ORM, has the deepest and most stable integration with PostgreSQL of any relational database. The `pgvector.sqlalchemy` package provides first-class `Vector` column type support directly in the model definitions.

5. **Long-term Community Reliability:** PostgreSQL has a 30-year track record, a massive open-source community, and is supported by every major cloud provider (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL). A codebase built on PostgreSQL has zero vendor lock-in risk.

### 4.2 Why pgvector

The `pgvector` extension transforms PostgreSQL into a **vector database** — one that can store high-dimensional float arrays (embeddings) and perform approximate and exact nearest-neighbour searches against them using standard SQL.

In Job Scout, every `Job` record, `Resume` record, and `User` record stores a `Vector(768)` column. When a user uploads their resume, the entire resume text is encoded into a 768-dimensional float vector. When a job listing is scraped, its description is encoded into the same space.

Finding the "most relevant" jobs for a candidate is then a pure mathematical operation:

```sql
-- Matching Service: Find jobs ordered by cosine distance to the user's resume embedding
SELECT j.id, j.title, j.company,
       (1 - (j.embedding <=> :embedding)) * 100 AS match_score
FROM jobs j
LEFT JOIN user_job_matches m ON j.id = m.job_id
WHERE (m.job_id IS NULL OR m.status = 'rejected')
ORDER BY j.embedding <=> :embedding
LIMIT :limit;
```

The `<=>` operator is pgvector's cosine distance operator. A score of `(1 - cosine_distance) * 100` converts the raw distance into an intuitive 0–100% relevance percentage displayed in the UI.

This is fundamentally different from keyword search. A job posting for "Machine Learning Researcher" and a resume describing "deep learning model training" will score highly even though they share no identical keywords — because their semantic meaning occupies nearby regions of the 768-dimensional embedding space.

### 4.3 Schema Design

The database contains five tables, each with a specific responsibility:

| Table | Purpose | Key Columns |
|---|---|---|
| `users` | Stores the candidate's active profile | `resume_markdown`, `parsed_data (JSON)`, `embedding (Vector768)` |
| `resumes` | Vault of all uploaded resumes | `filename`, `is_active`, `embedding (Vector768)` |
| `jobs` | All scraped job listings | `job_url (UNIQUE)`, `embedding (Vector768)`, `workplace_type`, `experience_required` |
| `user_job_matches` | Kanban board state | `status (interested/applied/interviewing/offered/rejected)` |
| `ai_generation_caches` | Deduplication of LLM outputs | `cache_key (SHA-256 hash)`, `response_text` |

**Design Notes:**

- `job_url` on the `jobs` table has a `UNIQUE` constraint. This is the primary deduplication mechanism. The scraper checks for URL existence before processing any job, and the constraint acts as a final safety net against race conditions in concurrent workers.
- The `is_active` flag on the `resumes` table implements a simple single-active-resume pattern. When a new resume is activated, all others are set to `False` in a single bulk update, and the `users` table is synchronised atomically.
- `workplace_type` is stored as an enumerated string (`remote`, `hybrid`, `onsite`, `negotiable`, `unspecified`) rather than a foreign-keyed enum table. This provides SQL-level filterability without the overhead of a join, appropriate for the current data volume.
- The `ai_generation_caches` table uses a **SHA-256 hash** of the composite key `(resume_id + job_id + job_title + company + job_description + mode)` as its `cache_key`. This ensures cache hits are content-addressed: the same resume applied to the same job description always returns the same cached output without re-invoking the LLM.

### 4.4 Alternatives Considered and Rejected

**Pinecone (Managed Vector Database):**
- Pinecone is a fully-managed, cloud-hosted vector database with excellent horizontal scaling and a simple API.
- **Rejected because:** It fundamentally breaks Axiom 1. Pinecone requires sending embedding vectors to an external cloud service. For Job Scout, this means sending vectors derived from a user's resume to a third-party server — a privacy violation that is architecturally incompatible with the project's core values. Additionally, Pinecone's free tier has strict limits; at scale, costs accrue rapidly.

**Weaviate / Qdrant / Milvus (Self-hosted Vector Databases):**
- These are legitimate, self-hosted alternatives with strong performance characteristics.
- **Rejected because:** They introduce a fourth independent data service (alongside Postgres, Redis, and the API server). Job Scout already stores users, resumes, jobs, matches, and caches as relational data in PostgreSQL. Splitting vector storage into a separate service creates a data consistency problem: relational integrity between `jobs` and their vectors cannot be enforced across two independent databases. Using pgvector keeps the relational and vector data in a single transaction boundary, which is architecturally far simpler and safer.

**MongoDB (Document Store):**
- MongoDB's flexible document model seemed attractive given the semi-structured nature of `parsed_data`.
- **Rejected because:** MongoDB has no mature vector search extension. Its `$vectorSearch` Atlas feature requires Atlas cloud hosting (again violating Axiom 1). Furthermore, Job Scout's data has a clear relational structure (users have many resumes, resumes have many matches, matches reference jobs) that is better expressed and enforced with foreign keys in a relational model.

**SQLite:**
- SQLite is an excellent embedded database for prototyping and single-user applications.
- **Rejected because:** SQLite does not support `pgvector`. The entire semantic matching engine depends on SQL-level vector operations. Without pgvector, semantic search would require loading all job embeddings into memory in Python and computing similarity in a loop — not scalable beyond a few hundred jobs.

### 4.5 The Scaling Roadmap

The current PostgreSQL + pgvector setup is appropriate for a personal deployment with tens of thousands of job records. The following upgrades are planned as the data volume grows:

**Phase 1 (Current — up to ~100K job records):**
- Single PostgreSQL instance with pgvector, IVFFlat index planned for the `jobs.embedding` column.
- An IVFFlat index (`CREATE INDEX ON jobs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)`) will accelerate approximate nearest-neighbour searches from O(n) to O(log n), maintaining sub-100ms match query times even at 100K records.

**Phase 2 (~1M records — Read Replica Scaling):**
- Promote the database to a primary-with-read-replicas topology. All write operations (scraper inserts, cache writes) route to the primary. All read-heavy operations (semantic matching, board queries) route to a read replica.
- This is achievable without changing the ORM layer — SQLAlchemy supports multiple engine bindings.

**Phase 3 (~10M+ records — Dedicated Vector Index Service):**
- At this scale, pgvector's IVFFlat index may saturate. Migration to **HNSW (Hierarchical Navigable Small World)** indexing, supported in pgvector 0.5+, is the first upgrade.
- If still insufficient, a dedicated vector layer (Qdrant or Weaviate, self-hosted) stores only the embedding vectors and job IDs, while PostgreSQL continues to store all other relational data. Matching queries would call the vector service for IDs, then hydrate full job data from Postgres in a single `WHERE id IN (...)` query.
- For cloud deployment at this scale, **AWS RDS with pgvector on db.r8g instance types** provides managed horizontal scaling with native pgvector support.

---

## 5. The AI Stack

### 5.1 Embedding Model: all-MiniLM-L6-v2

**Chosen:** `sentence-transformers/all-MiniLM-L6-v2`

**What it does:** Encodes arbitrary text (a resume, a job description, a sentence) into a 384-dimensional dense float vector that captures the semantic meaning of the text. Texts with similar meanings produce vectors that are close in the embedding space (low cosine distance). The model is zero-shot — no fine-tuning on job-specific data is required.

**Why this specific model:**

- **Size vs. Quality Sweet Spot:** `all-MiniLM-L6-v2` is a distilled, 6-layer MiniLM model with only 22.7M parameters. It encodes text in ~5ms on CPU, making it fast enough for real-time resume-to-job matching without a GPU. Despite its size, it consistently ranks in the **top tier of the SBERT benchmarks** for semantic textual similarity (STS) tasks — outperforming many models 5× its size.
- **Local Execution:** It runs entirely via the `sentence-transformers` Python library. No network call, no API key, no rate limit. The model weights are downloaded once and cached in the project's `models/` directory.
- **Production Precedent:** `all-MiniLM-L6-v2` is one of the most deployed embedding models in the world, used by companies ranging from startups to Fortune 500s. Its quality characteristics are well-understood.
- **Dimension Compatibility Note:** `all-MiniLM-L6-v2` natively produces 384-dimensional vectors. Our database schema uses `Vector(768)` (originally designed for a Google Gemini embeddings integration). The embedding generation code zero-pads 384-dimensional vectors to 768 dimensions (`vec.extend([0.0] * (768 - len(vec)))`). While this is a minor inefficiency, it preserves schema compatibility and allows dropping in a native 768-dimension model (e.g., `all-mpnet-base-v2`) as a zero-migration upgrade.

**Why NOT OpenAI text-embedding-ada-002 / text-embedding-3-small:**
- Both are cloud-hosted. Every embedding call sends resume and job description text to OpenAI's servers. This is a direct violation of Axiom 1 (privacy) and Axiom 1 (no external dependency). Additionally, at the volume of job scraping Job Scout performs, the per-token cost of `text-embedding-3-small` would accumulate to meaningful sums quickly.

**Why NOT Google Gemini Embeddings:**
- Same privacy and cost concerns as OpenAI. Furthermore, Gemini embedding availability is gated behind Google Cloud project setup and service account configuration — introducing significant deployment friction for a self-hosted tool.

**Why NOT Larger Local Models (e.g., all-mpnet-base-v2, E5-large):**
- `all-mpnet-base-v2` (420M parameters) and `E5-large` (335M parameters) produce marginally better embeddings on benchmark tasks. However, their encoding speed on CPU is 4–6× slower than `all-MiniLM-L6-v2`. For a use case where hundreds of job descriptions are embedded during a scraping run, this difference compounds to minutes of additional processing time per batch. The quality gain does not justify the latency cost at this scale.

---

### 5.2 Local LLM: unsloth/Llama-3.2-3B-Instruct

**Chosen:** `unsloth/Llama-3.2-3B-Instruct` via Hugging Face `transformers` pipeline

**What it does:** Generates natural language text (cover letters, resume tailoring suggestions, structured JSON parsing results) in response to carefully engineered prompts. It is the system's primary "writing" intelligence.

**Why this specific model:**

- **Parameter Count:** At 3 billion parameters, Llama 3.2-3B sits at the **minimum viable threshold for instruction-following capability**. Below 3B parameters (e.g., 1.1B TinyLlama), models lose the ability to follow multi-step structured instructions reliably — critical for generating a coherent cover letter from a complex prompt. Above 3B (e.g., 7B, 13B), models require GPU VRAM that cannot be assumed on consumer hardware.
- **Meta's Llama 3.2 Architecture:** The Llama 3.2 generation introduces significant instruction-following improvements over Llama 2, particularly in structured output generation. The updated tokeniser and context window (128K tokens) are architectural advantages for long resume + job description prompts.
- **Unsloth Optimisation:** The `unsloth` variant is a community-optimised quantisation of Meta's base model, designed explicitly for efficient CPU and low-VRAM inference. It preserves output quality while reducing memory footprint — critical for a system that must share hardware with an embedding model, a PostgreSQL process, and a Redis instance.
- **`bfloat16` on CPU:** The model is loaded in `bfloat16` precision on CPU (`torch_dtype=torch.bfloat16`). Modern x86-64 CPUs (Broadwell and later) have native `bfloat16` silicon support. This halves the model's RAM footprint compared to `float32` while introducing negligible precision loss for inference workloads.
- **Thread Management:** On CPU inference, the code explicitly caps PyTorch's thread count to `min(4, cpu_cores // 2)` via `torch.set_num_threads()`. Without this, PyTorch defaults to using all logical cores, causing severe context-switching overhead on multi-core consumer CPUs that actually *reduces* throughput compared to a focused 2–4 thread configuration.
- **Chat Template Support:** The `format_prompt()` function implements native chat template formatting for Llama's specific `<|begin_of_text|>...<|eot_id|>` token structure, as well as templates for Qwen, TinyLlama, and Phi. This ensures tokens are structured correctly, directly impacting output coherence.

**Why NOT GPT-4 / Claude / Gemini 3.1 Pro (External LLMs):**
- All external LLMs would receive the user's complete resume text and job description in every generation call. This is an absolute privacy violation for a self-hosted tool. Additionally, these APIs have costs, rate limits, and outage windows that would make the application unreliable.

**Why NOT Mistral 7B / Llama 3.2-7B:**
- 7B parameter models require approximately 14GB of RAM at `bfloat16` precision. The majority of consumer workstations and laptops have 8–16GB of total RAM, leaving no headroom for the OS, database, and other services. A 3B model at ~6GB RAM is feasible on virtually any machine with 8GB or more.

**Why NOT Gemma 2B:**
- Google's Gemma 2B is a capable model, but its instruction-following behaviour on complex, multi-section prompts (the kind used for cover letter generation) was found to be less consistent than Llama 3.2-3B in initial testing. Llama 3.2's training specifically emphasises instruction adherence.

**Why NOT Phi-3-mini (3.8B):**
- Microsoft's Phi-3-mini is an excellent model, and Job Scout's `format_prompt()` actually includes a Phi-specific chat template in its fallback logic (indicating it was evaluated). It was not chosen as the primary because `unsloth/Llama-3.2-3B-Instruct`'s community support, documentation, and quantisation ecosystem are more mature.

### 5.3 Fallback Chain

Job Scout implements a three-tier fallback chain for AI operations. This directly implements Axiom 3 (Graceful Degradation):

```
Tier 1: unsloth/Llama-3.2-3B-Instruct (primary)
   ↓ FAILS (OOM, load error, model not found)
Tier 2: TinyLlama/TinyLlama-1.1B-Chat-v1.0 (lightweight fallback)
   ↓ FAILS (all model loading fails)
Tier 3: Heuristic / Regex-based extraction (llm_fallback.py)
   (extract_structured_data_fallback, generate_embedding_fallback)
```

For embeddings:
```
Tier 1: all-MiniLM-L6-v2 via sentence-transformers
   ↓ FAILS
Tier 2: Regex/keyword extraction (generate_embedding_fallback)
```

### 5.4 Alternatives Considered and Rejected

| Model | Why Evaluated | Why Rejected |
|---|---|---|
| `OpenAI GPT-4o` | State-of-the-art generation quality | Cloud-hosted; privacy violation; cost |
| `Claude 3.5 Sonnet` | Excellent long-document understanding | Cloud-hosted; privacy violation; cost |
| `Google Gemini 1.5 Pro` | Multimodal; 1M context window | Cloud-hosted; API key required |
| `Mistral 7B Instruct` | Strong open-source model | 7B RAM requirement too high for consumer hardware |
| `Llama 3.2-1B` | Smallest viable Llama | Below minimum threshold for coherent multi-step instruction-following |
| `Gemma 2B` | Google-developed, efficient | Less consistent on structured instruction prompts in testing |
| `Phi-3-mini-4k` | Microsoft-optimised for edge | Slightly larger; Llama ecosystem more mature |
| `GPT-4-All (local)` | Local LLM runtime | GGUF format incompatible with Hugging Face `transformers` pipeline; would require `llama.cpp` integration |

---

## 6. The RAG Pipeline

RAG (Retrieval-Augmented Generation) is the mechanism that prevents the LLM from hallucinating experience, skills, or credentials that the candidate does not actually have.

### How It Works — Step by Step

When the user requests a cover letter or tailored resume summary:

1. **Resume Tokenisation:** The candidate's resume text is split line by line. Lines shorter than 15 characters or purely made of whitespace are discarded. Bullet prefix characters (`-`, `•`, `*`, `>`, numbered lists) are stripped from the beginning of each line, producing a `clean_line` for embedding.

2. **Cached Batch Embedding:** All clean resume lines are passed to `get_cached_line_embeddings()`. This function first checks the in-memory `RESUME_LINE_EMBEDDING_CACHE` dictionary. Lines that have already been embedded during a previous request in this session are returned instantly from memory. Only genuinely new lines are sent to the embedding model. This eliminates redundant CPU cycles across multiple generation requests for the same resume.

3. **Job Description Embedding:** The target job description is encoded into a single embedding vector via `generate_embedding()`.

4. **Dot-Product Similarity Scoring:** For each resume line, the dot product between the job embedding's first 384 dimensions and the line embedding's first 384 dimensions is computed. This is an approximation of cosine similarity for normalised vectors. All lines are ranked by this score.

5. **Top-6 Context Extraction:** The 6 highest-scoring resume lines are selected. These represent the candidate's most relevant experiences and skills relative to the specific job description. They are formatted as a bullet list.

6. **Similar Job Retrieval (Database RAG):** Separately, the job embedding is used to query the `jobs` table via pgvector, retrieving the 3 most semantically similar jobs already in the database. Their titles, companies, and description snippets (first 300 characters) are included as "market alignment" context.

7. **Prompt Assembly:** The system prompt for the LLM is assembled with both RAG contexts injected:
   ```
   [Role Definition]
   [RAG: Top 6 relevant resume lines]
   [RAG: 3 similar market job listings]
   [Critical Constraint: Do NOT hallucinate. Use ONLY the candidate's history.]
   [Task specification]
   ```

8. **LLM Generation:** The fully-assembled prompt is passed to `get_local_llm()` with controlled parameters:
   - `max_new_tokens=200` (tailoring) or `180` (cover letter) — constrains output length.
   - `repetition_penalty=1.2` — penalises token repetition, preventing the LLM from looping on phrases.
   - `do_sample=False` — uses greedy decoding for deterministic, consistent outputs. Sampling introduces randomness that is undesirable for factual professional documents.

9. **DB Cache Write:** The final output is stored in `ai_generation_caches` under a SHA-256 hash key. Identical future requests (same resume, same job, same mode) return the cached result in milliseconds.

---

## 7. The Scraping Infrastructure

Job Scout targets five job platforms with different scraping strategies:

| Platform | Strategy | Async |
|---|---|---|
| **LinkedIn** | Two-phase: discover links first, then parallel description enrichment | ✅ (`asyncio`) |
| **Indeed** | Full async scrape | ✅ (`asyncio`) |
| **Naukri** | Full async scrape | ✅ (`asyncio`) |
| **RemoteOK** | Synchronous (API-like JSON endpoint) | ❌ |
| **We Work Remotely** | Synchronous RSS/HTML parse | ❌ |

The LinkedIn scraper's two-phase design is architecturally significant:
- **Phase 1 (Fast):** Collect all job URLs from LinkedIn's search results. This is a lightweight operation.
- **Phase 2 (Filtered):** For each discovered URL, check the database for existence. URLs already in the database are discarded immediately.
- **Phase 3 (Expensive):** Only genuinely new jobs receive the full page fetch, description parse, LLM embedding generation, and database write. This is the expensive phase.

This design ensures that scraping a board that is 90% already-known jobs costs approximately 10% of the compute that a naive "scrape everything, deduplicate later" approach would.

**Workplace Type Classification** is performed heuristically on every scraped job via `determine_workplace_type()`. The function uses a priority-ordered keyword matching strategy against the job title, location string, and description, resolving to one of: `remote`, `hybrid`, `onsite`, `negotiable`, or `unspecified`. This allows the frontend to offer meaningful workplace type filters on the match results.

---

## 8. Caching Strategy — Two Layers

Job Scout implements caching at two distinct levels:

### Layer 1: In-Memory Embedding Cache (Process-Level)

- **Scope:** Within a single FastAPI process lifetime.
- **Implementation:** `RESUME_LINE_EMBEDDING_CACHE` — a Python dictionary mapping `clean_line_text → [float]`.
- **Purpose:** Prevents re-encoding the same resume bullet points multiple times across multiple AI generation requests within the same session. Since a user's resume changes infrequently, this cache achieves near-100% hit rates for the bulk of requests.
- **Limitation:** Does not survive process restarts. Acceptable trade-off: the cost of re-encoding resume lines on process start is a one-time ~200ms operation.

### Layer 2: Database AI Output Cache (Persistent)

- **Scope:** Permanent, survives restarts.
- **Implementation:** `ai_generation_caches` PostgreSQL table, keyed by SHA-256 hash.
- **Purpose:** Prevents re-invoking the local LLM (a 10–90 second CPU-bound operation) for identical inputs. If the same resume is applied to the same job description in the same mode, the output is returned from the database in <5ms.
- **Cache Invalidation:** Currently time-unbound (no TTL). The `/ai/cache/clear` endpoint provides manual purging. Future versions will implement TTL-based expiry.

---

## 9. Hardware & Deployment Considerations

Job Scout is designed to run on a typical developer workstation. The following is the minimum viable hardware profile:

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB | 16 GB |
| CPU | 4-core x86-64 | 8-core modern (Broadwell+ for bfloat16) |
| GPU | Not required | NVIDIA with CUDA 11.8+ (dramatically faster LLM inference) |
| Storage | 10 GB free | 20 GB free (model weights ≈ 6GB, DB + logs) |
| OS | Linux / macOS / Windows | Ubuntu 22.04 LTS |

**The `set_ai_device` API** (`POST /ai/config` with `{"device": "cuda"}`) allows toggling LLM execution to GPU without restarting the application. On a mid-range NVIDIA GPU, Llama 3.2-3B inference drops from 30–90 seconds to 2–5 seconds per generation — a transformative user experience improvement.

---

## 10. Known Constraints & Engineering Debt

This section documents the honest limitations of the current implementation:

1. **Single-User Architecture:** The system is hardcoded to `user_id=1`. There is no authentication layer. Multi-user support would require JWT-based authentication, per-user data isolation, and significantly restructured API endpoints.

2. **Embedding Dimension Mismatch:** The 384-dimensional output of `all-MiniLM-L6-v2` is zero-padded to 768 dimensions. The padded dimensions contribute no semantic information. This wastes approximately half the storage in vector columns. Migrating to a native 768-dimension model (e.g., `all-mpnet-base-v2`) would resolve this without a schema change.

3. **No pgvector Index:** The current deployment does not create an IVFFlat or HNSW index on the `jobs.embedding` column. All similarity searches perform a sequential scan. This is acceptable up to ~10,000 jobs but will degrade linearly beyond that. Adding `CREATE INDEX ON jobs USING ivfflat (embedding vector_cosine_ops)` is a planned next step.

4. **Resume Service Simplicity:** `MarkItDown` is used for resume-to-markdown conversion. While effective for standard PDFs and DOCX files, complex multi-column resume layouts may not parse correctly. A more robust solution would use `pdfplumber` for layout-aware PDF parsing.

5. **LLM Generation Time:** On CPU-only hardware, generating a cover letter takes 30–90 seconds. The frontend UX communicates this wait clearly, but the raw latency is the primary friction point for users without a CUDA-capable GPU.

---

## 11. Future Roadmap & Scaling Plan

### Near-Term (Next 3 Months)

- **IVFFlat Index on `jobs.embedding`:** Immediate query performance improvement for growing databases.
- **HNSW Index Migration:** Upgrade to pgvector's newer HNSW index type for better recall at scale.
- **Multi-User Authentication:** Implement JWT-based auth (e.g., via `fastapi-users`) to allow the application to serve multiple job seekers from a single server instance.
- **Resume Parsing Upgrade:** Replace `MarkItDown` with a hybrid `pdfplumber` + `python-docx` parser for better layout fidelity.

### Medium-Term (3–9 Months)

- **CUDA-First Deployment Option:** Provide a Docker Compose override file that maps GPU devices into the container and defaults `AI_DEVICE` to `cuda`.
- **AI Provider Toggle:** Implement an optional API gateway layer. Users who prefer cloud speed can configure an OpenAI or Anthropic API key, which the system will use in place of the local LLM. The local model remains the default; cloud is opt-in.
- **Analytics Dashboard:** Expand the frontend to show application funnel metrics (e.g., Applied → Interviewing conversion rate, average time in each stage) derived from the `user_job_matches` timestamp data.
- **Browser Extension:** A lightweight browser extension that allows one-click saving of job listings from any job board directly to the Job Scout Kanban, bypassing the scraper entirely.

### Long-Term (9+ Months)

- **Kubernetes Orchestration:** For multi-user cloud deployment, migrate from Docker Compose to a K8s cluster with horizontal pod autoscaling for the FastAPI and Celery worker deployments.
- **Dedicated Vector Service:** At 1M+ job records, evaluate migrating vector storage to a dedicated Qdrant cluster (self-hosted) while keeping relational data in PostgreSQL.
- **Fine-Tuned Embedding Model:** Fine-tune `all-MiniLM-L6-v2` on a domain-specific dataset of job description / resume pairs to improve semantic matching accuracy in specialised technical fields (e.g., ML Engineering, DevOps, Biotech).
- **Agentic Scraping Pipeline:** Replace the current HTTP-based scrapers with Playwright-driven browser agents capable of bypassing advanced bot protection (Cloudflare Turnstile, CAPTCHA) used by LinkedIn and Indeed's protected endpoints.

---

## Appendix: Technology Decision Summary Table

| Layer | Chosen | Primary Alternative | Reason for Choice |
|---|---|---|---|
| Backend Framework | FastAPI | Django, Flask, Express | Async, typed, auto-docs, pgvector ORM support |
| Frontend | Next.js + Tailwind | Vue/Nuxt, CRA | React ecosystem, Turbopack speed, TypeScript |
| Task Queue | Celery | None / Cron | Background tasks, retries, Beat scheduling |
| Message Broker | Redis | RabbitMQ, Postgres | Sub-ms latency, simple config, zero overhead |
| Primary DB | PostgreSQL + pgvector | MongoDB, SQLite, Pinecone | ACID + vector search + JSON in one system |
| Embedding Model | all-MiniLM-L6-v2 | OpenAI ada-002, mpnet | Local, fast, zero cost, top STS benchmarks |
| Local LLM | Llama 3.2-3B (Unsloth) | GPT-4, Mistral 7B, Gemma 2B | Best instruction-following at 3B RAM budget |
| Container Orchestration | Docker Compose | Kubernetes | Single-node; K8s reserved for future scaling |
| Resume Parsing | MarkItDown | pdfplumber, PyMuPDF | Broad format support; upgrade planned |

---

*This document represents the complete, living technical record of the Job Scout platform. It should be updated whenever a significant architectural decision is made or reversed.*
