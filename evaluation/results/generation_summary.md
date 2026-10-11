# LLM Generation Quality & Factual Grounding Evaluation

Evaluation conducted across **28 candidate resume and job posting pairs** (56 outputs) comparing **Llama-3.2-3B-Instruct** and **TinyLlama-1.1B-Chat** on local CPU execution (8 threads).

## 1. Summary Comparison

| Metric | Llama-3.2-3B-Instruct | TinyLlama-1.1B-Chat | Delta / Notes |
|---|---|---|---|
| **Parameters** | 3.2 Billion | 1.1 Billion | 2.9x capacity difference |
| **Mean Latency (CPU)** | 54.42s | 20.63s | TinyLlama is faster on CPU |
| **Throughput (Tokens/s)** | 1.7 tok/s | 3.2 tok/s | Clamped to 8 CPU threads |
| **Avg Word Count** | 72.8 words | 51.5 words | Concise tailoring length |
| **Format Compliance** | 28/28 (100.0%) | 28/28 (100.0%) | Summary: + exactly 3 bullets constraint |
| **Bullets Checked** | 84 | 84 | Exactly 3 bullets x 28 pairs |
| **Unsupported Claims (Count)** | 8 / 84 | 25 / 84 | Lower is better |
| **Per-Bullet Unsupported Rate** | 9.5% (8/84) | 29.8% (25/84) | Percentage and count match |

## 2. Methodology & Factual Grounding Verification
1. **Output Format Enforcement**: Tightened prompt with constrained post-processing guaranteeing reliable output: `"Summary:"` header followed by candidate summary, and exactly three achievement bullets (`- `).
2. **Unsupported Claim Extraction**: Evaluated candidate bullet points against ground-truth resume skills and text. Bullets introducing frameworks, tools, or libraries absent from the candidate profile were flagged.
3. **Manual Verification Sheet**: Generated `evaluation/results/generation_samples_review.csv` containing all 56 outputs alongside a blank `human_rating` column for independent academic review.
