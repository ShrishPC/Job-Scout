"""
Generation Quality & Factual Grounding Evaluation
Evaluates Llama-3.2-3B vs TinyLlama-1.1B on 20 resume-job pairs.
Measures:
  - Factual grounding (hallucination / unsupported claim rate)
  - Latency & tokens per second on CPU
  - Formatting instruction compliance (Summary + exactly 3 bullets)
  - Output length (chars, words, tokens)
Outputs:
  - evaluation/results/generation_eval.json
  - evaluation/results/generation_samples_review.csv (with blank 'human_rating' column)
  - evaluation/results/generation_summary.md
"""

import os
import sys
import json
import time
import re
import csv
from pathlib import Path
import torch

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True, parents=True)

MODEL_CACHE = os.getenv("MODEL_CACHE_DIR", "/models")

COMMON_TECH_POOL = [
    "Python", "FastAPI", "Django", "Flask", "React", "Next.js", "TypeScript", "JavaScript",
    "Node.js", "Express", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "CI/CD", "GitHub Actions", "Git", "REST API", "GraphQL", "gRPC",
    "Kafka", "RabbitMQ", "Celery", "PyTorch", "TensorFlow", "Scikit-Learn", "HuggingFace",
    "LangChain", "LlamaIndex", "pgvector", "Microservices", "Linux", "Java", "Spring Boot",
    "C++", "Rust", "Go", "Golang", "Tailwind CSS", "Redux", "SQL", "Terraform", "Ansible",
    "Elasticsearch", "Spark", "Airflow", "Hadoop", "Snowflake", "BigQuery", "GraphQL"
]


def load_dataset():
    with open(DATA_DIR / "resumes.json", "r", encoding="utf-8") as f:
        resumes = json.load(f)
    with open(DATA_DIR / "jobs.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)
    
    # Load ground truth labels
    labels = []
    with open(DATA_DIR / "ground_truth_relevance.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels.append({
                "resume_id": int(row["resume_id"]),
                "job_id": int(row["job_id"]),
                "grade": int(row["relevance_grade"])
            })

    resume_map = {r["id"]: r for r in resumes}
    job_map = {j["id"]: j for j in jobs}

    # Select 20 pairs with high relevance (grade >= 2)
    pairs = []
    # Take 2 relevant jobs for first 8 resumes, 1 for remaining 4 = 20 pairs
    for r_id in range(1, 13):
        r_labels = [l for l in labels if l["resume_id"] == r_id and l["grade"] >= 2]
        count_to_take = 2 if r_id <= 8 else 1
        for match in r_labels[:count_to_take]:
            pairs.append((resume_map[r_id], job_map[match["job_id"]]))
            if len(pairs) == 20:
                break
        if len(pairs) == 20:
            break

    return pairs


def build_resume_text(r: dict) -> str:
    skills_str = ", ".join(r.get("skills", []))
    employers = ", ".join(r.get("employers", ["Enterprise Corp"]))
    return (
        f"{r['name']}\n"
        f"Title: {r['title']}\n"
        f"Education: {r.get('degree', 'B.S. in Computer Science')}\n"
        f"Experience: {r.get('experience_years', 5)} years at {employers}\n"
        f"Core Skills: {skills_str}\n\n"
        f"Summary:\n{r.get('summary', '')}\n\n"
        f"Work History:\n"
        f"- Engineered robust software at {employers.split(',')[0]} leveraging {', '.join(r.get('skills', [])[:3])}.\n"
        f"- Led cross-functional initiatives improving test coverage and system throughput."
    )


def extract_bullets(text: str) -> list[str]:
    bullets = []
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        # Match markdown bullets or numbered bullets
        m = re.match(r"^[\*\-\•\d+\.]\s*(.+)$", stripped)
        if m:
            bullet_body = m.group(1).strip()
            if len(bullet_body) > 15:  # avoid heading fragments
                bullets.append(bullet_body)
    return bullets


def analyze_factual_grounding(bullet: str, resume: dict, full_resume_text: str) -> dict:
    """
    Checks if technical claims, tools, or skills in the bullet point exist in the input resume.
    """
    candidate_skills_lower = {s.lower() for s in resume.get("skills", [])}
    candidate_skills_lower.add(resume.get("title", "").lower())
    resume_text_lower = full_resume_text.lower()

    # Identify tech terms mentioned in this bullet
    bullet_lower = bullet.lower()
    mentioned_techs = []
    for tech in COMMON_TECH_POOL:
        # Check boundary match
        pattern = r"\b" + re.escape(tech.lower()) + r"\b"
        if re.search(pattern, bullet_lower):
            mentioned_techs.append(tech)

    # Check which mentioned techs are completely absent from candidate's resume
    unsupported_techs = []
    for tech in mentioned_techs:
        t_low = tech.lower()
        if t_low not in candidate_skills_lower and t_low not in resume_text_lower:
            unsupported_techs.append(tech)

    is_unsupported = len(unsupported_techs) > 0
    return {
        "is_unsupported": is_unsupported,
        "unsupported_techs": unsupported_techs,
        "mentioned_techs": mentioned_techs
    }


def evaluate_models(pairs: list):
    from transformers import pipeline

    torch.set_num_threads(4)

    models_to_test = [
        {
            "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "short_name": "TinyLlama-1.1B-Chat",
            "tag_style": "tinyllama"
        },
        {
            "name": "unsloth/Llama-3.2-3B-Instruct",
            "short_name": "Llama-3.2-3B-Instruct",
            "tag_style": "llama"
        }
    ]

    all_results = {}
    csv_rows = []
    sample_id = 1

    # Open CSV early for incremental writing
    csv_path = RESULTS_DIR / "generation_samples_review.csv"
    csv_fieldnames = [
        "sample_id", "model_name", "resume_id", "candidate_name", "job_id",
        "job_title", "latency_seconds", "bullet_count", "unsupported_claims_detected",
        "format_compliant", "generated_output", "human_rating"
    ]
    csv_file = open(csv_path, "w", encoding="utf-8", newline="")
    csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fieldnames)
    csv_writer.writeheader()
    csv_file.flush()

    import gc

    for m_cfg in models_to_test:
        model_name = m_cfg["name"]
        short_name = m_cfg["short_name"]
        tag_style = m_cfg["tag_style"]

        print(f"\n=======================================================")
        print(f"[*] Loading model: {short_name} on CPU...")
        t_load_start = time.perf_counter()

        pipe = pipeline(
            "text-generation",
            model=model_name,
            model_kwargs={
                "cache_dir": MODEL_CACHE,
                "torch_dtype": torch.bfloat16,
                "low_cpu_mem_usage": True
            },
            device=-1
        )
        print(f"[+] Loaded in {time.perf_counter() - t_load_start:.2f}s")

        model_eval_records = []

        for pair_idx, (resume, job) in enumerate(pairs, 1):
            resume_text = build_resume_text(resume)
            job_desc = job["description"]
            job_title = job["title"]

            system_prompt = (
                f"You are an expert resume coach and recruiter. Analyze the candidate's resume and the job description for the {job_title} role.\n"
                f"CRITICAL: Do NOT invent, assume, or hallucinate any facts, metrics, projects, dates, or credentials. Use ONLY the candidate's actual history from the provided resume text.\n\n"
                f"Tasks to perform:\n"
                f"1. Write a tailored 'Professional Summary' (2-3 sentences) from the candidate's perspective ('I'). Begin directly with impact and core credentials, aligning with the job description keywords. Avoid clichés like 'Highly motivated professional'.\n"
                f"2. Suggest exactly 3 bullet points for experience. Each bullet point MUST showcase measurable results or metrics based on the candidate's history, align with required job skills, and use strong action verbs (e.g. Optimized, Automated, Spearheaded).\n"
                f"Respond ONLY with: 1) the summary, and 2) the bullet point suggestions. Do not add intro/outro remarks or conversational filler."
            )
            user_prompt = f"Candidate Resume:\n{resume_text}\n\nJob Description:\n{job_desc}"

            if tag_style == "llama":
                prompt = (
                    f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
                    f"{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
                    f"{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
                )
            else:
                prompt = (
                    f"<|system|>\n{system_prompt}</s>\n"
                    f"<|user|>\n{user_prompt}</s>\n"
                    f"<|assistant|>\n"
                )

            t0 = time.perf_counter()
            out = pipe(
                prompt,
                max_new_tokens=60,
                return_full_text=False,
                repetition_penalty=1.15,
                do_sample=False
            )
            latency = time.perf_counter() - t0
            raw_generated = out[0]["generated_text"].strip()

            # Analyze output
            bullets = extract_bullets(raw_generated)
            bullet_analyses = [analyze_factual_grounding(b, resume, resume_text) for b in bullets]
            unsupported_count = sum(1 for a in bullet_analyses if a["is_unsupported"])
            unsupported_rate = unsupported_count / max(1, len(bullets))

            has_summary = "summary" in raw_generated.lower() or len(raw_generated.split("\n\n")[0]) > 40
            format_compliant = has_summary and (len(bullets) == 3)

            char_len = len(raw_generated)
            word_len = len(raw_generated.split())
            token_est = word_len * 1.3
            tokens_per_sec = token_est / max(0.001, latency)

            record = {
                "sample_id": sample_id,
                "model": short_name,
                "resume_id": resume["id"],
                "candidate_name": resume["name"],
                "job_id": job["id"],
                "job_title": job_title,
                "latency_seconds": round(latency, 2),
                "tokens_per_second": round(tokens_per_sec, 1),
                "char_length": char_len,
                "word_length": word_len,
                "bullet_count": len(bullets),
                "unsupported_claim_count": unsupported_count,
                "unsupported_claim_rate": round(unsupported_rate, 3),
                "format_compliant": format_compliant,
                "generated_output": raw_generated,
                "unsupported_details": [a["unsupported_techs"] for a in bullet_analyses if a["is_unsupported"]]
            }
            model_eval_records.append(record)

            # CSV row for manual grading
            csv_row = {
                "sample_id": sample_id,
                "model_name": short_name,
                "resume_id": resume["id"],
                "candidate_name": resume["name"],
                "job_id": job["id"],
                "job_title": job_title,
                "latency_seconds": round(latency, 2),
                "bullet_count": len(bullets),
                "unsupported_claims_detected": unsupported_count,
                "format_compliant": "YES" if format_compliant else "NO",
                "generated_output": raw_generated.replace("\n", " \\n "),
                "human_rating": ""  # Blank for manual university grading
            }
            csv_rows.append(csv_row)
            csv_writer.writerow(csv_row)
            csv_file.flush()

            print(f"  [{pair_idx:02d}/20] {short_name} | Latency: {latency:.2f}s | Bullets: {len(bullets)} | Unsupported: {unsupported_count} | Compliant: {format_compliant}")
            sample_id += 1

        all_results[short_name] = {
            "model_name": model_name,
            "sample_count": len(model_eval_records),
            "mean_latency_s": round(sum(r["latency_seconds"] for r in model_eval_records) / len(model_eval_records), 2),
            "mean_tokens_per_s": round(sum(r["tokens_per_second"] for r in model_eval_records) / len(model_eval_records), 1),
            "mean_char_length": round(sum(r["char_length"] for r in model_eval_records) / len(model_eval_records), 1),
            "mean_word_length": round(sum(r["word_length"] for r in model_eval_records) / len(model_eval_records), 1),
            "format_compliance_rate": round(sum(1 for r in model_eval_records if r["format_compliant"]) / len(model_eval_records), 3),
            "mean_unsupported_claim_rate": round(sum(r["unsupported_claim_rate"] for r in model_eval_records) / len(model_eval_records), 3),
            "total_unsupported_claims": sum(r["unsupported_claim_count"] for r in model_eval_records),
            "records": model_eval_records
        }

        # Explicit garbage collection between models
        del pipe
        gc.collect()

    csv_file.close()

    # Save JSON results
    json_path = RESULTS_DIR / "generation_eval.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[+] Saved detailed evaluation to {json_path}")
    print(f"[+] Saved manual review sheet with blank human_rating to {csv_path}")

    # Generate Markdown Summary
    md_content = f"""# LLM Generation Quality & Factual Grounding Evaluation

Evaluation conducted across **20 candidate resume and job posting pairs** comparing **Llama-3.2-3B-Instruct** and **TinyLlama-1.1B-Chat** on local CPU execution.

## 1. Summary Comparison

| Metric | Llama-3.2-3B-Instruct | TinyLlama-1.1B-Chat | Delta / Notes |
|---|---|---|---|
| **Parameters** | 3.2 Billion | 1.1 Billion | 2.9x capacity difference |
| **Mean Latency (CPU)** | {all_results['Llama-3.2-3B-Instruct']['mean_latency_s']}s | {all_results['TinyLlama-1.1B-Chat']['mean_latency_s']}s | TinyLlama is faster on CPU |
| **Throughput (Tokens/s)** | {all_results['Llama-3.2-3B-Instruct']['mean_tokens_per_s']} tok/s | {all_results['TinyLlama-1.1B-Chat']['mean_tokens_per_s']} tok/s | Thread-clamped (4 threads) |
| **Avg Word Count** | {all_results['Llama-3.2-3B-Instruct']['mean_word_length']} words | {all_results['TinyLlama-1.1B-Chat']['mean_word_length']} words | Concise tailoring length |
| **Format Compliance** | {all_results['Llama-3.2-3B-Instruct']['format_compliance_rate'] * 100:.1f}% | {all_results['TinyLlama-1.1B-Chat']['format_compliance_rate'] * 100:.1f}% | Summary + exact 3 bullets constraint |
| **Unsupported Claim Rate** | {all_results['Llama-3.2-3B-Instruct']['mean_unsupported_claim_rate'] * 100:.1f}% | {all_results['TinyLlama-1.1B-Chat']['mean_unsupported_claim_rate'] * 100:.1f}% | Unanchored tech/facts in bullets |
| **Total Unsupported Claims** | {all_results['Llama-3.2-3B-Instruct']['total_unsupported_claims']} / {sum(r['bullet_count'] for r in all_results['Llama-3.2-3B-Instruct']['records'])} | {all_results['TinyLlama-1.1B-Chat']['total_unsupported_claims']} / {sum(r['bullet_count'] for r in all_results['TinyLlama-1.1B-Chat']['records'])} | Lower is better |

## 2. Methodology & Factual Grounding Verification
1. **Prompt Template**: Strict zero-hallucination constraint instructing the model: *"Do NOT invent, assume, or hallucinate any facts, metrics, projects, dates, or credentials. Use ONLY the candidate's actual history."*
2. **Unsupported Claim Extraction**: Evaluated candidate bullet points against ground-truth resume skills and text. Bullets introducing frameworks, tools, or libraries absent from the candidate profile were flagged.
3. **Manual Verification Sheet**: Generated `evaluation/results/generation_samples_review.csv` containing all 40 outputs alongside a blank `human_rating` column for independent academic review.
"""
    summary_path = RESULTS_DIR / "generation_summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[+] Saved human-readable summary to {summary_path}")


if __name__ == "__main__":
    pairs = load_dataset()
    print(f"[+] Loaded {len(pairs)} evaluation pairs for generation testing.")
    evaluate_models(pairs)
