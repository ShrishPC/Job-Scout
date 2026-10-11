# Retrieval & Generation Evaluation Suite

This directory contains the empirical evaluation dataset and benchmarks for Job Scout's retrieval ranking algorithms and local text generation factuality.

---

## 1. Dataset Methodology & Ground-Truth Labeling

The evaluation dataset comprises:
- **12 Candidate Profiles (`data/resumes.json`)**: Realistic synthetic resumes spanning 12 distinct software engineering and data disciplines (Python Backend, Frontend React/Next.js, Machine Learning, DevOps/Cloud, Data Engineering, Embedded C++, iOS Mobile, Enterprise .NET, Cybersecurity, Full-Stack, BI/Analytics, QA Automation).
- **220 Job Postings (`data/jobs.json`)**: Realistic job descriptions distributed across all 12 disciplines with varying seniority levels (Junior to Principal).
- **2,640 Graded Relevance Annotations (`data/ground_truth_relevance.csv`)**: Evaluates every `(resume_id, job_id)` pair on a 4-point graded relevance scale:

### Graded Relevance Rubric:
- **Grade 3 (Highly Relevant)**: Exact match on primary domain, core tech stack, and seniority requirements.
- **Grade 2 (Moderately Relevant)**: Same primary domain with minor technology variance, or adjacent domain with strong transferable overlap (e.g., Python Backend $\leftrightarrow$ Data Engineering, Frontend $\leftrightarrow$ Full Stack).
- **Grade 1 (Marginally Relevant)**: Minimal auxiliary overlap (e.g. general SQL/Git familiarity) with mismatched core discipline.
- **Grade 0 (Irrelevant)**: Disjoint disciplines (e.g. iOS Swift developer applied to Embedded C++ or DevOps applied to Frontend CSS).

### Label Provenance & Disclosure:
- **Provenance**: The labels were produced via deterministic programmatic rubric mapping technology co-occurrence and domain adjacency matrices, followed by manual audit of edge-case pairings.
- **Human Review Status**: 2,640 pairs were automatically assigned initial grades; 100 sample pairings were manually verified. A random sample of 20 LLM generation outputs is exported to `evaluation/results/generation_samples_review.csv` with a blank `human_rating` column reserved for blind human qualitative grading.

---

## 2. Evaluation Scripts

### A. Retrieval Quality (`evaluate_retrieval.py`)
Compares retrieval effectiveness across:
1. **Keyword-Only Retrieval**: Exact substring & title weighting.
2. **Semantic-Only Retrieval**: Cosine similarity via `all-MiniLM-L6-v2`.
3. **Production Hybrid (0.7 / 0.3)**: Weighted combination ($0.7 \times \text{Cosine} + 0.3 \times \text{Keyword}$).
4. **Alpha Weight Sweep**: Systematic sweep of $\alpha \in [0.0, 1.0]$ in increments of $0.1$.

**Reported Metrics (with Bootstrap 95% Confidence Intervals, B=1000):**
- Precision@5 ($P@5$) & Precision@10 ($P@10$)
- Recall@10 ($R@10$)
- Mean Reciprocal Rank ($MRR$)
- Normalized Discounted Cumulative Gain at 10 ($NDCG@10$)

### B. Factual Grounding & Unsupported-Claim Rate (`evaluate_generation.py`)
Evaluates the factual fidelity of generated application materials against source candidate resumes:
- Automatically scans generated output for named skills, employers, degree titles, and numeric metrics.
- Flags any entity not grounded in the source resume (`unsupported_claim_rate`).
- Compares hallucination rates of `unsloth/Llama-3.2-3B-Instruct` versus `TinyLlama-1.1B-Chat-v1.0`.
