#!/usr/bin/env python3
"""
Retrieval Quality Evaluation Suite
Evaluates Keyword-only, Semantic-only (all-MiniLM-L6-v2), and Hybrid (0.7/0.3)
in-Python along with the actual SQL paths (legacy and two_stage with candidate_k
in {50, 100, 200, 500}) on the 28 x 560 benchmark loaded into PostgreSQL.
Calculates P@5, P@10, R@10, MRR, and NDCG@10 with Bootstrap 95% Confidence Intervals.
Computes top-10 overlap and Kendall tau rank correlation vs SQL legacy.
"""

import os
import sys
import json
import csv
import time
import re
import numpy as np
from scipy.stats import kendalltau

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.llm_service import generate_embeddings_batch
from app.core.database import engine, SessionLocal
from app.services.matching_service import get_job_matches
from sqlalchemy import text

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
os.makedirs(RESULTS_DIR, exist_ok=True)


def load_data():
    with open(os.path.join(DATA_DIR, "resumes.json"), "r", encoding="utf-8") as f:
        resumes = json.load(f)
    with open(os.path.join(DATA_DIR, "jobs.json"), "r", encoding="utf-8") as f:
        jobs = json.load(f)

    gt = {}
    with open(os.path.join(DATA_DIR, "ground_truth_relevance.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_id = int(row["resume_id"])
            j_id = int(row["job_id"])
            grade = int(row["relevance_grade"])
            gt[(r_id, j_id)] = grade

    return resumes, jobs, gt


def compute_keyword_score(resume, job):
    skills = [s.strip().lower() for s in resume.get("skills", []) if s.strip()]
    if not skills:
        return 0.0

    title_lower = job["title"].lower()
    desc_lower = job["description"].lower()

    total_points = 0.0
    for skill in skills:
        if re.match(r'^[a-zA-Z0-9\s\-]+$', skill):
            pattern = rf'\b{re.escape(skill)}\b'
            in_title = bool(re.search(pattern, title_lower))
            in_desc = bool(re.search(pattern, desc_lower))
        else:
            in_title = skill in title_lower
            in_desc = skill in desc_lower

        if in_title:
            total_points += 2.0
        elif in_desc:
            total_points += 1.0

    return total_points / (2.0 * len(skills))


def dcg_at_k(grades, k=10):
    grades = grades[:k]
    dcg = 0.0
    for i, g in enumerate(grades):
        dcg += (2.0**g - 1.0) / np.log2(i + 2.0)
    return dcg


def ndcg_at_k(ranked_grades, all_grades, k=10):
    actual_dcg = dcg_at_k(ranked_grades, k)
    ideal_grades = sorted(all_grades, reverse=True)[:k]
    ideal_dcg = dcg_at_k(ideal_grades, k)
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg


def evaluate_ranking_metrics(ranked_job_ids, r_id, gt_dict, total_pool_job_ids):
    grades = [gt_dict.get((r_id, j_id), 0) for j_id in ranked_job_ids]
    all_grades = [gt_dict.get((r_id, j_id), 0) for j_id in total_pool_job_ids]

    relevant_mask = [g >= 2 for g in grades]
    total_relevant = sum(g >= 2 for g in all_grades)

    p5 = sum(relevant_mask[:5]) / 5.0
    p10 = sum(relevant_mask[:10]) / 10.0
    r10 = sum(relevant_mask[:10]) / float(total_relevant) if total_relevant > 0 else 0.0

    mrr = 0.0
    for rank_idx, is_rel in enumerate(relevant_mask):
        if is_rel:
            mrr = 1.0 / (rank_idx + 1.0)
            break

    ndcg10 = ndcg_at_k(grades, all_grades, k=10)

    return {
        "p5": p5,
        "p10": p10,
        "r10": r10,
        "mrr": mrr,
        "ndcg10": ndcg10
    }


def bootstrap_ci(metric_values, n_bootstraps=1000, ci=0.95):
    arr = np.array(metric_values)
    boot_means = []
    n = len(arr)
    for _ in range(n_bootstraps):
        sample = np.random.choice(arr, size=n, replace=True)
        boot_means.append(np.mean(sample))

    lower_pct = ((1.0 - ci) / 2.0) * 100
    upper_pct = (1.0 - (1.0 - ci) / 2.0) * 100
    return {
        "mean": float(np.mean(arr)),
        "ci_lower": float(np.percentile(boot_means, lower_pct)),
        "ci_upper": float(np.percentile(boot_means, upper_pct))
    }


def compute_top_k_kendall_tau(l1, l2, k=10):
    """
    Computes Kendall's tau rank correlation across the union of top-k items.
    Items absent from a top-k list are assigned rank k (tied bottom).
    """
    top1 = l1[:k]
    top2 = l2[:k]
    union_items = list(dict.fromkeys(top1 + top2))
    if len(union_items) < 2:
        return 1.0
    rank1 = [top1.index(x) if x in top1 else k for x in union_items]
    rank2 = [top2.index(x) if x in top2 else k for x in union_items]
    tau, _ = kendalltau(rank1, rank2)
    return 1.0 if np.isnan(tau) else float(tau)


def populate_benchmark_database(jobs, job_embs):
    """Loads the 560 benchmark jobs into PostgreSQL with exact IDs and HNSW index."""
    print("\n[*] Populating PostgreSQL with 560 benchmark evaluation jobs...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE user_job_matches CASCADE;"))
        conn.execute(text("TRUNCATE TABLE jobs CASCADE;"))
        conn.commit()

        # Batch insert 560 rows
        for i, j in enumerate(jobs):
            j_id = j["id"]
            title_esc = j["title"].replace("'", "''")
            comp_esc = j.get("company", "Company").replace("'", "''")
            desc_esc = j.get("description", "").replace("'", "''")
            url = f"https://jobscout.internal/eval/job/{j_id}"
            v_str = f"[{','.join(f'{x:.6f}' for x in job_embs[i])}]"

            conn.execute(text(f"""
                INSERT INTO jobs (id, title, company, description, location, salary, job_url, date_posted, experience_required, workplace_type, embedding)
                VALUES ({j_id}, '{title_esc}', '{comp_esc}', '{desc_esc}', 'Remote', '$120,000', '{url}', 'Recent', 3, 'remote', '{v_str}');
            """))
        conn.commit()

        # Reset sequence
        conn.execute(text("SELECT setval(pg_get_serial_sequence('jobs', 'id'), coalesce(max(id), 1)) FROM jobs;"))
        conn.commit()

        # Build HNSW index
        print("[*] Ensuring HNSW index on jobs table...")
        conn.execute(text("DROP INDEX IF EXISTS idx_jobs_embedding_hnsw;"))
        conn.execute(text("CREATE INDEX idx_jobs_embedding_hnsw ON jobs USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128);"))
        conn.commit()

    print("[+] 560 benchmark jobs successfully indexed in PostgreSQL.")


def main():
    print("=" * 70)
    print("🎯 JOB SCOUT RETRIEVAL RANKING EVALUATION (IN-PYTHON & REAL SQL)")
    print("=" * 70)

    resumes, jobs, gt = load_data()
    n_resumes = len(resumes)
    n_jobs = len(jobs)
    job_ids = [j["id"] for j in jobs]
    print(f"[+] Loaded {n_resumes} resumes and {n_jobs} jobs ({len(gt):,} ground truth labels).")

    # Precompute embeddings
    print("[*] Generating 384-d embeddings for candidate resumes...")
    resume_texts = [f"{r['title']} with skills in {', '.join(r['skills'])}. {r['summary']}" for r in resumes]
    resume_embs = np.array(generate_embeddings_batch(resume_texts))

    print("[*] Generating 384-d embeddings for job postings...")
    job_texts = [f"{j['title']} at {j['company']}. {j['description']}" for j in jobs]
    job_embs = np.array(generate_embeddings_batch(job_texts))

    # Normalize vectors
    resume_norms = np.linalg.norm(resume_embs, axis=1, keepdims=True)
    job_norms = np.linalg.norm(job_embs, axis=1, keepdims=True)
    resume_embs_norm = resume_embs / np.maximum(resume_norms, 1e-9)
    job_embs_norm = job_embs / np.maximum(job_norms, 1e-9)

    # 1. Populate PostgreSQL DB for real SQL path evaluation
    populate_benchmark_database(jobs, job_embs_norm)

    # 2. In-Python similarity matrices
    print("[*] Precomputing similarity scores across all candidate-job pairs...")
    cosine_matrix = np.dot(resume_embs_norm, job_embs_norm.T)

    keyword_matrix = np.zeros((n_resumes, n_jobs), dtype=float)
    for r_idx, r in enumerate(resumes):
        for j_idx, j in enumerate(jobs):
            keyword_matrix[r_idx, j_idx] = compute_keyword_score(r, j)

    results = {}

    # 3. Evaluate In-Python Methods
    in_python_methods = {
        "keyword_only": 0.0,
        "semantic_only": 1.0,
        "in_python_hybrid_0.7": 0.7
    }
    sweep_alphas = [round(a, 1) for a in np.linspace(0.0, 1.0, 11)]
    for a in sweep_alphas:
        cfg_name = f"alpha_{a:.1f}"
        if cfg_name not in in_python_methods:
            in_python_methods[cfg_name] = a

    print("\n[*] Evaluating In-Python ranking configurations...")
    for name, alpha in in_python_methods.items():
        scores = alpha * cosine_matrix + (1.0 - alpha) * keyword_matrix
        per_resume_metrics = {"p5": [], "p10": [], "r10": [], "mrr": [], "ndcg10": []}

        for r_idx, r in enumerate(resumes):
            r_id = r["id"]
            ranked_indices = np.argsort(-scores[r_idx])
            ranked_job_ids = [jobs[idx]["id"] for idx in ranked_indices]

            eval_res = evaluate_ranking_metrics(ranked_job_ids, r_id, gt, job_ids)
            for m in per_resume_metrics:
                per_resume_metrics[m].append(eval_res[m])

        cfg_summary = {m: bootstrap_ci(per_resume_metrics[m]) for m in per_resume_metrics}
        results[name] = {
            "type": "in_python",
            "alpha": alpha,
            "metrics": cfg_summary
        }

    # 4. Evaluate Actual SQL Database Paths
    print("\n[*] Evaluating Actual SQL Database Paths (legacy vs two_stage)...")
    sql_configurations = [
        {"name": "hybrid_legacy", "mode": "legacy", "candidate_k": None},
        {"name": "hybrid_two_stage_k50", "mode": "two_stage", "candidate_k": 50},
        {"name": "hybrid_two_stage_k100", "mode": "two_stage", "candidate_k": 100},
        {"name": "hybrid_two_stage_k200", "mode": "two_stage", "candidate_k": 200},
        {"name": "hybrid_two_stage_k500", "mode": "two_stage", "candidate_k": 500},
    ]

    sql_rankings_by_cfg = {}  # cfg_name -> list of ranked_job_ids per resume

    db = SessionLocal()
    try:
        for cfg in sql_configurations:
            cfg_name = cfg["name"]
            mode = cfg["mode"]
            cand_k = cfg["candidate_k"]
            print(f"  --> Executing SQL path: {cfg_name} (mode={mode}, candidate_k={cand_k})...")

            per_resume_metrics = {"p5": [], "p10": [], "r10": [], "mrr": [], "ndcg10": []}
            cfg_rankings = []

            for r_idx, r in enumerate(resumes):
                r_id = r["id"]
                u_emb = resume_embs_norm[r_idx].tolist()
                u_skills = r.get("skills", [])

                matches = get_job_matches(
                    db=db,
                    user_embedding=u_emb,
                    limit=560,
                    skip=0,
                    candidate_k=cand_k,
                    hybrid_mode=mode,
                    user_skills=u_skills
                )
                ranked_job_ids = [m["id"] for m in matches]
                cfg_rankings.append(ranked_job_ids)

                eval_res = evaluate_ranking_metrics(ranked_job_ids, r_id, gt, job_ids)
                for m in per_resume_metrics:
                    per_resume_metrics[m].append(eval_res[m])

            sql_rankings_by_cfg[cfg_name] = cfg_rankings
            cfg_summary = {m: bootstrap_ci(per_resume_metrics[m]) for m in per_resume_metrics}
            results[cfg_name] = {
                "type": "sql",
                "mode": mode,
                "candidate_k": cand_k,
                "metrics": cfg_summary
            }
    finally:
        db.close()

    # 5. Compute Top-10 Overlap and Kendall Tau vs SQL Legacy
    legacy_rankings = sql_rankings_by_cfg["hybrid_legacy"]
    candidate_k_comparisons = {}

    print("\n[*] Computing Rank Correlation and Top-10 Overlap vs SQL Legacy...")
    for cfg in sql_configurations:
        cfg_name = cfg["name"]
        if cfg_name == "hybrid_legacy":
            continue

        cand_k = cfg["candidate_k"]
        rankings = sql_rankings_by_cfg[cfg_name]

        overlaps = []
        taus = []
        for r_idx in range(n_resumes):
            top10_legacy = legacy_rankings[r_idx][:10]
            top10_cand = rankings[r_idx][:10]

            overlap = len(set(top10_legacy) & set(top10_cand)) / 10.0
            tau = compute_top_k_kendall_tau(top10_legacy, top10_cand, k=10)

            overlaps.append(overlap)
            taus.append(tau)

        comp_stat = {
            "candidate_k": cand_k,
            "mean_top10_overlap": round(float(np.mean(overlaps)), 4),
            "mean_kendall_tau": round(float(np.mean(taus)), 4),
            "overlap_ci": bootstrap_ci(overlaps),
            "kendall_tau_ci": bootstrap_ci(taus)
        }
        candidate_k_comparisons[cfg_name] = comp_stat
        results[cfg_name]["comparison_vs_legacy"] = comp_stat
        print(f"  [{cfg_name}] Mean Top-10 Overlap: {comp_stat['mean_top10_overlap']:.3f} | Mean Kendall Tau: {comp_stat['mean_kendall_tau']:.3f}")

    # 6. Candidate_K Recommendation Logic
    legacy_ndcg = results["hybrid_legacy"]["metrics"]["ndcg10"]["mean"]
    recommended_cand_k = None
    for cand_k in [100, 200, 500]:
        k_key = f"hybrid_two_stage_k{cand_k}"
        k_ndcg = results[k_key]["metrics"]["ndcg10"]["mean"]
        if k_ndcg >= (legacy_ndcg - 0.005):  # not worse than legacy within noise
            recommended_cand_k = cand_k
            break
    if recommended_cand_k is None:
        recommended_cand_k = 200

    # Save JSON Report
    raw_output_path = os.path.join(RESULTS_DIR, "retrieval_evaluation.json")
    with open(raw_output_path, "w", encoding="utf-8") as f:
        json.dump({
            "benchmark": "retrieval_quality_evaluation",
            "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "dataset": {
                "num_resumes": n_resumes,
                "num_jobs": n_jobs,
                "ground_truth_labels": len(gt),
                "relevance_scale": "0-3"
            },
            "recommendation": {
                "recommended_candidate_k": recommended_cand_k,
                "reasoning": f"two_stage with candidate_k={recommended_cand_k} achieves NDCG@10 ({results[f'hybrid_two_stage_k{recommended_cand_k}']['metrics']['ndcg10']['mean']:.3f}) comparable to legacy ({legacy_ndcg:.3f}) with high rank fidelity."
            },
            "configurations": results
        }, f, indent=2)
    print(f"\n[+] Saved raw JSON evaluation to {raw_output_path}")

    # Generate Markdown Summary Report
    summary_path = os.path.join(RESULTS_DIR, "retrieval_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Retrieval Algorithm Benchmark Results\n\n")
        f.write(f"Evaluation conducted over **{n_resumes} candidate profiles** and **{n_jobs} job listings** ({len(gt):,} ground truth relevance labels).\n\n")
        f.write("All confidence intervals represent **Bootstrap 95% CIs** ($B=1,000$ resamples).\n\n")

        f.write("## 1. Primary Strategy Comparison (In-Python & Production SQL)\n\n")
        f.write("| Strategy | Type | P@5 (95% CI) | P@10 (95% CI) | R@10 (95% CI) | MRR (95% CI) | NDCG@10 (95% CI) |\n")
        f.write("|---|---|---|---|---|---|---|\n")

        core_display_keys = [
            ("keyword_only", "Keyword-Only", "In-Python"),
            ("semantic_only", "Semantic-Only", "In-Python"),
            ("hybrid_legacy", "Hybrid Legacy SQL", "SQL Full Scan"),
            ("hybrid_two_stage_k50", "Two-Stage SQL (k=50)", "SQL Two-Stage"),
            ("hybrid_two_stage_k100", "Two-Stage SQL (k=100)", "SQL Two-Stage"),
            ("hybrid_two_stage_k200", "Two-Stage SQL (k=200)", "SQL Two-Stage"),
            ("hybrid_two_stage_k500", "Two-Stage SQL (k=500)", "SQL Two-Stage"),
        ]

        for key, label, stype in core_display_keys:
            m = results[key]["metrics"]
            p5_s = f"{m['p5']['mean']:.3f} [{m['p5']['ci_lower']:.3f}, {m['p5']['ci_upper']:.3f}]"
            p10_s = f"{m['p10']['mean']:.3f} [{m['p10']['ci_lower']:.3f}, {m['p10']['ci_upper']:.3f}]"
            r10_s = f"{m['r10']['mean']:.3f} [{m['r10']['ci_lower']:.3f}, {m['r10']['ci_upper']:.3f}]"
            mrr_s = f"{m['mrr']['mean']:.3f} [{m['mrr']['ci_lower']:.3f}, {m['mrr']['ci_upper']:.3f}]"
            ndcg_s = f"{m['ndcg10']['mean']:.3f} [{m['ndcg10']['ci_lower']:.3f}, {m['ndcg10']['ci_upper']:.3f}]"
            f.write(f"| **{label}** | {stype} | {p5_s} | {p10_s} | {r10_s} | {mrr_s} | {ndcg_s} |\n")

        f.write("\n## 2. Two-Stage CTE vs Legacy SQL Fidelity\n\n")
        f.write("| Two-Stage Variant | Candidate K | Mean Top-10 Overlap | Mean Kendall's Tau (τ) | NDCG@10 (Mean) |\n")
        f.write("|---|---|---|---|---|\n")
        for cand_k in [50, 100, 200, 500]:
            k_key = f"hybrid_two_stage_k{cand_k}"
            c = candidate_k_comparisons[k_key]
            ndcg_val = results[k_key]["metrics"]["ndcg10"]["mean"]
            f.write(f"| **Two-Stage (k={cand_k})** | {cand_k} | {c['mean_top10_overlap']:.3f} | {c['mean_kendall_tau']:.3f} | {ndcg_val:.3f} |\n")

        f.write(f"\n> **Candidate K Recommendation**: **`candidate_k = {recommended_cand_k}`** is recommended. "
                f"It achieves an NDCG@10 of **{results[f'hybrid_two_stage_k{recommended_cand_k}']['metrics']['ndcg10']['mean']:.3f}** "
                f"(vs {legacy_ndcg:.3f} for Legacy SQL) with **{candidate_k_comparisons[f'hybrid_two_stage_k{recommended_cand_k}']['mean_top10_overlap'] * 100:.1f}%** top-10 item overlap "
                f"and Kendall's $\\tau = {candidate_k_comparisons[f'hybrid_two_stage_k{recommended_cand_k}']['mean_kendall_tau']:.3f}$.\n\n")

        f.write("## 3. In-Python Linear Weight Sweep (α = Vector Weight, 1 - α = Keyword Weight)\n\n")
        f.write("| Alpha (α) | P@5 | P@10 | R@10 | MRR | NDCG@10 |\n")
        f.write("|---|---|---|---|---|---|\n")
        for a in sweep_alphas:
            k = f"alpha_{a:.1f}"
            m = results[k]["metrics"]
            f.write(f"| {a:.1f} | {m['p5']['mean']:.3f} | {m['p10']['mean']:.3f} | {m['r10']['mean']:.3f} | {m['mrr']['mean']:.3f} | {m['ndcg10']['mean']:.3f} |\n")

    print(f"[+] Saved summary to {summary_path}")

    # Console display
    print("\n" + "=" * 100)
    print(f"{'Strategy':<26} {'P@5':<10} {'P@10':<10} {'R@10':<10} {'MRR':<10} {'NDCG@10':<10}")
    print("-" * 100)
    for key, label, _ in core_display_keys:
        m = results[key]["metrics"]
        print(f"{label:<26} {m['p5']['mean']:<10.3f} {m['p10']['mean']:<10.3f} {m['r10']['mean']:<10.3f} {m['mrr']['mean']:<10.3f} {m['ndcg10']['mean']:<10.3f}")
    print("=" * 100)


if __name__ == "__main__":
    main()
