# Retrieval & Generation Evaluation Suite

This directory contains the empirical evaluation dataset, methodology disclosures, and reproducible benchmark harnesses for Job Scout's retrieval ranking algorithms and local text generation factuality.

---

## 1. Ground-Truth Dataset Provenance & Methodology Disclosures

### A. Initial Synthetic Baseline (2,640 Labels - Saturated & Circular)
The initial evaluation suite utilized 12 candidate profiles and 220 synthetic job postings (`2,640 pairs`). 
> [!WARNING]
> **Methodology Disclosure & Circularity Limitation**:
> In the initial 2,640-pair dataset, ground-truth relevance grades (0 to 3) were generated via programmatic rules calculating the intersection between the candidate's skill set and the job's listed skills (`common_skills = r_skills.intersection(j_skills)`). 
> Because Job Scout's keyword ranking algorithm scores jobs by counting exact skill occurrences in titles and descriptions, **evaluating keyword retrieval against labels derived from skill intersections produced artificial saturation and circular confirmation**. On that synthetic dataset, keyword-only search scored $P@5 = 1.000$ and $NDCG@10 = 0.963$ simply because the scoring code and ground truth shared the exact same vocabulary.

---

### B. Hard & Discriminating Evaluation Benchmark (15,680 Labels)
To eliminate circularity and provide a rigorous, discriminating benchmark, we generated an expanded dataset in `data/generate_hard_dataset.py`:
- **28 Diverse Candidate Resumes (`data/resumes.json`)**: Spanning 14 distinct software engineering specializations (Backend Python, Frontend React, ML/AI, DevOps, Data Engineering, Embedded Systems, iOS, .NET, Cybersecurity, Full-Stack, BI/Analytics, QA Automation, Systems Rust, Android Kotlin, Go Distributed, SRE, GenAI/RAG, Low-Latency C++, Enterprise Java, Data Science).
- **560 Job Postings (`data/jobs.json`)**: Systematically divided into five distinct categories:
  1. **Canonical Engineering Postings (240 jobs)**: Direct domain and tech stack matches ($Grade = 3$).
  2. **Paraphrased / Synonymous Postings (80 jobs)**: Identical domain and problem scope, but written with **zero keyword overlap** (e.g., *"predictive modelling / statistical inference / neural representations"* for ML; *"declarative IaC / cluster scheduling manifests"* for DevOps; *"asynchronous event loops / relational persistence layers"* for Python Backend). In this subset, naive keyword search fails ($Score \approx 0.0$), while semantic embeddings correctly capture high relevance ($Grade = 3$).
  3. **Keyword Distractor Postings (80 jobs)**: High keyword density on engineering terms, but representing **completely wrong or non-engineering roles** (e.g. *Technical Recruiter sourcing Python/FastAPI engineers*, *Enterprise Account Executive selling Kubernetes licenses*, *Course Instructor teaching Playwright*, *Executive Assistant to VP of ML*). Naive keyword search naively ranks these at the top, whereas semantic search and hybrid reranking correctly penalize them ($Grade = 0$).
  4. **Adjacent Cross-Domain Technical Roles (80 jobs)**: Transferable engineering disciplines (e.g., Data Platform $\leftrightarrow$ Backend, SRE $\leftrightarrow$ DevOps) ($Grade = 2$ or $1$).
  5. **Disjoint Non-Engineering Postings (80 jobs)**: Chefs, civil engineers, accountants, nurses, paralegals ($Grade = 0$).

- **Independent Ground Truth (`data/ground_truth_relevance.csv`)**:
  Ground truth grades (0–3) are assigned strictly according to **role taxonomy and engineering candidate qualifications**, completely independent of keyword matching counts or vector distance scores.

---

## 2. Evaluation Scripts & Metrics

### A. Retrieval Evaluation (`evaluate_retrieval.py`)
Computes top-$k$ ranking performance across three primary modes:
1. **Keyword-Only Retrieval**: Exact substring matching and title weighting ($2.0\times$ title, $1.0\times$ description).
2. **Semantic-Only Retrieval**: Cosine similarity via `all-MiniLM-L6-v2` dense embeddings.
3. **Production Hybrid ($\alpha = 0.7$)**: Linear combination:
   $$\text{Score} = 100 \times [0.7 \times (1 - \text{cosine\_dist}) + 0.3 \times \text{keyword\_score}]$$
4. **Weight Sweep ($\alpha \in [0.0, 1.0]$)**: Systematic sweep in $0.1$ increments.

**Reported Ranking Metrics (with Bootstrap 95% CIs, $B=1,000$):**
- **Precision@5 ($P@5$)** and **Precision@10 ($P@10$)**
- **Recall@10 ($R@10$)**
- **Mean Reciprocal Rank ($MRR$)**
- **Normalized Discounted Cumulative Gain at 10 ($NDCG@10$)**

### B. Factual Grounding & Hallucination Audit (`evaluate_generation.py`)
Evaluates the factual fidelity of AI-tailored resume bullets and cover letters against source resume text:
- Verifies named tech skills, past employers, degree titles, and numeric metrics against ground-truth resume entities.
- Calculates the `unsupported_claim_rate` (hallucinations per generation).
- Compares `unsloth/Llama-3.2-3B-Instruct` versus `TinyLlama-1.1B-Chat-v1.0`.
- Outputs blind qualitative review samples to `results/generation_samples_review.csv` (28 pairs, 56 outputs with blank human evaluation columns).
