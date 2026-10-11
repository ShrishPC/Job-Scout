# LLM Generation Quality & Factual Grounding Evaluation

Evaluation conducted across **20 candidate resume and job posting pairs** comparing **Llama-3.2-3B-Instruct** and **TinyLlama-1.1B-Chat** on local CPU execution.

## 1. Summary Comparison

| Metric | Llama-3.2-3B-Instruct | TinyLlama-1.1B-Chat | Delta / Notes |
|---|---|---|---|
| **Parameters** | 3.2 Billion | 1.1 Billion | 2.9x capacity difference |
| **Mean Latency (CPU)** | 105.37s | 39.19s | TinyLlama is faster on CPU |
| **Throughput (Tokens/s)** | 0.7 tok/s | 1.3 tok/s | Thread-clamped (4 threads) |
| **Avg Word Count** | 49.2 words | 36.3 words | Concise tailoring length |
| **Format Compliance** | 0.0% | 3.6% | Summary + exact 3 bullets constraint |
| **Unsupported Claim Rate** | 0.0% | 3.6% | Unanchored tech/facts in bullets |
| **Total Unsupported Claims** | 0 / 29 | 2 / 10 | Lower is better |

## 2. Methodology & Factual Grounding Verification
1. **Prompt Template**: Strict zero-hallucination constraint instructing the model: *"Do NOT invent, assume, or hallucinate any facts, metrics, projects, dates, or credentials. Use ONLY the candidate's actual history."*
2. **Unsupported Claim Extraction**: Evaluated candidate bullet points against ground-truth resume skills and text. Bullets introducing frameworks, tools, or libraries absent from the candidate profile were flagged.
3. **Manual Verification Sheet**: Generated `evaluation/results/generation_samples_review.csv` containing all 40 outputs alongside a blank `human_rating` column for independent academic review.
