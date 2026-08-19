import os
import re
import math
import hashlib
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sentence_transformers import util

from app.models.models import AIGenerationCache
from app.services.llm_service import (
    get_embedding_model,
    format_prompt,
    get_local_llm,
)
from app.core.config import settings

# ==============================================================================
# Comprehensive Skill Dictionary & Taxonomy
# ==============================================================================

SKILL_TAXONOMY = {
    "Languages": [
        "python", "javascript", "typescript", "golang", "go", "rust", "java", "c++", "c#",
        "ruby", "php", "swift", "kotlin", "scala", "sql", "html", "css", "bash", "shell",
        "r", "dart", "c", "elixir", "clojure"
    ],
    "Frontend": [
        "react", "next.js", "nextjs", "vue", "vue.js", "nuxt", "angular", "svelte", "tailwind",
        "tailwindcss", "redux", "zustand", "graphql", "webpack", "vite", "remix", "html5",
        "css3", "sass", "bootstrap", "shadcn", "material ui", "chakra ui", "three.js"
    ],
    "Backend & APIs": [
        "node.js", "nodejs", "express", "fastapi", "django", "flask", "nestjs", "spring boot",
        "gin", "actix", "ruby on rails", "asp.net", "grpc", "rest api", "restful api",
        "microservices", "celery", "graphql", "websockets", "socket.io", "trpc"
    ],
    "Databases & Caching": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "cassandra",
        "dynamodb", "elasticsearch", "neo4j", "supabase", "pgvector", "firebase",
        "cockroachdb", "couchdb", "mariadb", "snowflake", "bigquery"
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "gcp", "google cloud", "azure", "docker", "kubernetes",
        "k8s", "terraform", "ansible", "ci/cd", "github actions", "jenkins", "helm",
        "prometheus", "grafana", "linux", "serverless", "aws lambda", "nginx", "datadog",
        "cloudflare", "ec2", "s3", "ecs", "eks"
    ],
    "AI & Data Science": [
        "pytorch", "tensorflow", "transformers", "huggingface", "langchain", "llamaindex",
        "scikit-learn", "pandas", "numpy", "nlp", "llms", "vector database", "rag",
        "computer vision", "opencv", "deep learning", "machine learning", "ollama", "onnx"
    ],
    "Testing & Quality": [
        "jest", "cypress", "playwright", "pytest", "mocha", "junit", "unit testing",
        "integration testing", "e2e testing", "tdd", "selenium"
    ],
    "System Design & Architecture": [
        "distributed systems", "high availability", "scalability", "caching",
        "event-driven architecture", "kafka", "rabbitmq", "message queues", "system design",
        "oauth", "jwt", "load balancing", "api gateway", "concurrency"
    ],
    "Methodology & Soft Skills": [
        "agile", "scrum", "kanban", "jira", "code review", "mentorship", "cross-functional",
        "stakeholder management", "leadership", "collaboration", "problem solving"
    ]
}

# Synonym Normalization Map
SYNONYMS = {
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "psql": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "nextjs": "next.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "aws": "amazon web services",
    "gcp": "google cloud",
    "golang": "go",
    "tailwind": "tailwindcss",
    "ml": "machine learning",
    "dl": "deep learning"
}

ACTION_VERBS = [
    "spearheaded", "architected", "engineered", "optimized", "developed", "built", "implemented",
    "accelerated", "designed", "deployed", "scaled", "automated", "streamlined", "orchestrated",
    "championed", "delivered", "reduced", "increased", "enhanced", "resolved", "migrated"
]

METRIC_PATTERNS = [
    r'\b\d+%\b',               # 40%
    r'\$[\d,]+(?:\.\d+)?\b',   # $50,000
    r'\b\d+(?:\.\d+)?x\b',     # 10x
    r'\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b', # 200ms, 3 years
    r'\b\d+\+\b',              # 100+
    r'\b\d+k\b',               # 50k
    r'\b\d+m\b',               # 2M
]

# ==============================================================================
# Helper Functions
# ==============================================================================

def normalize_skill(term: str) -> str:
    cleaned = term.strip().lower()
    return SYNONYMS.get(cleaned, cleaned)

def extract_all_known_skills(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts all known technical and domain skills from a block of text
    with occurrences, categorization, and normalized naming.
    """
    found_skills = {}
    lower_text = text.lower()
    
    for category, skill_list in SKILL_TAXONOMY.items():
        for skill in skill_list:
            norm = normalize_skill(skill)
            # Match boundary for alphanumeric words
            if re.match(r'^[a-zA-Z0-9\s\-]+$', skill):
                pattern = r'\b' + re.escape(skill) + r'\b'
            else:
                pattern = re.escape(skill)
                
            matches = list(re.finditer(pattern, lower_text))
            if matches:
                count = len(matches)
                if norm not in found_skills or found_skills[norm]["count"] < count:
                    found_skills[norm] = {
                        "name": skill.title() if len(skill) > 3 else skill.upper(),
                        "normalized": norm,
                        "category": category,
                        "count": count
                    }
    return found_skills

def calculate_metric_density(resume_text: str) -> Dict[str, Any]:
    """
    Measures quantifiable metrics and strong action verbs in resume bullets.
    """
    lines = [line.strip() for line in resume_text.split('\n') if line.strip().startswith(('-', '*', '•')) or len(line.strip()) > 30]
    if not lines:
        lines = [line.strip() for line in resume_text.split('\n') if len(line.strip()) > 20]
        
    total_bullets = max(len(lines), 1)
    metrics_count = 0
    action_verb_count = 0
    
    for line in lines:
        lower_line = line.lower()
        has_metric = any(re.search(p, line, re.IGNORECASE) for p in METRIC_PATTERNS)
        has_action = any(re.search(r'\b' + re.escape(v) + r'\b', lower_line) for v in ACTION_VERBS)
        
        if has_metric:
            metrics_count += 1
        if has_action:
            action_verb_count += 1
            
    metric_pct = round((metrics_count / total_bullets) * 100, 1)
    action_pct = round((action_verb_count / total_bullets) * 100, 1)
    
    # Score out of 10 points
    score = min(10.0, (metric_pct * 0.05) + (action_pct * 0.05))
    return {
        "score": round(score, 1),
        "max": 10,
        "total_bullets_analyzed": total_bullets,
        "metric_bullets_count": metrics_count,
        "metric_percentage": metric_pct,
        "action_verb_count": action_verb_count,
        "action_percentage": action_pct
    }

def calculate_experience_depth(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Evaluates production depth, seniority signals, and work history scope.
    """
    lower_resume = resume_text.lower()
    
    production_terms = [
        "production", "architected", "deployed", "enterprise", "scalability", "leadership",
        "spearheaded", "mentored", "microservices", "infrastructure", "high availability",
        "ci/cd", "security", "distributed systems", "database optimization"
    ]
    
    found_production = [term for term in production_terms if term in lower_resume]
    
    # Check for experience years pattern
    years_matches = re.findall(r'(\d+)\+?\s*(?:years|yrs)\s*(?:of)?\s*experience', lower_resume)
    exp_years = max([int(y) for y in years_matches], default=0) if years_matches else 0
    
    # Score out of 20 points
    base_score = min(12.0, len(found_production) * 1.5)
    exp_score = min(8.0, exp_years * 1.5 if exp_years > 0 else 4.0)
    total_exp_score = round(min(20.0, base_score + exp_score), 1)
    
    return {
        "score": total_exp_score,
        "max": 20,
        "estimated_years": exp_years,
        "production_signals_found": found_production
    }

# ==============================================================================
# Main ATS Scoring Engine
# ==============================================================================

def analyze_resume_ats_match(
    resume_text: str,
    job_title: str,
    job_description: str,
    company: str = "Target Company",
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Performs comprehensive hybrid ATS evaluation comparing a resume against a target job.
    Combines deterministic keyword gap analysis, semantic embedding cosine alignment,
    and HackerRank-inspired category rubrics.
    """
    cache_key = f"ats_eval_{hashlib.sha256((resume_text[:1000] + job_description[:1000]).encode('utf-8')).hexdigest()}"
    
    # 1. Check DB Cache
    if db:
        cached = db.query(AIGenerationCache).filter(AIGenerationCache.cache_key == cache_key).first()
        if cached:
            try:
                import json
                return json.loads(cached.response_text)
            except Exception:
                pass

    # 2. Extract Skills from Resume and Job Description
    resume_skills = extract_all_known_skills(resume_text)
    jd_skills = extract_all_known_skills(job_description + " " + job_title)
    
    matched_skills = []
    missing_skills = []
    
    # Identify Matched and Missing Skills
    for norm_skill, info in jd_skills.items():
        if norm_skill in resume_skills:
            matched_skills.append({
                "name": info["name"],
                "category": info["category"],
                "resume_count": resume_skills[norm_skill]["count"],
                "jd_count": info["count"],
                "importance": "critical" if info["count"] > 1 or norm_skill in job_title.lower() else "recommended"
            })
        else:
            is_critical = (
                info["count"] >= 2 or
                norm_skill in job_title.lower() or
                bool(re.search(r'(?:required|must have|requirements)[\s\S]{0,150}' + re.escape(info["name"]), job_description, re.IGNORECASE))
            )
            missing_skills.append({
                "name": info["name"],
                "category": info["category"],
                "jd_count": info["count"],
                "importance": "critical" if is_critical else "recommended"
            })
            
    # Sort missing skills: critical first
    missing_skills.sort(key=lambda s: (0 if s["importance"] == "critical" else 1, -s["jd_count"]))
    matched_skills.sort(key=lambda s: -s["jd_count"])

    # 3. Technical Skills Score (Max 40 points)
    total_jd_skills = max(len(jd_skills), 1)
    matched_count = len(matched_skills)
    skill_coverage_ratio = matched_count / total_jd_skills
    skills_score = round(min(40.0, skill_coverage_ratio * 40.0), 1)

    # 4. Semantic Alignment Score via Embeddings (Max 30 points)
    try:
        model = get_embedding_model()
        emb_resume = model.encode(resume_text[:2500], convert_to_tensor=True)
        emb_jd = model.encode(job_description[:2000], convert_to_tensor=True)
        cosine_sim = float(util.cos_sim(emb_resume, emb_jd)[0][0])
        # Map cosine similarity (typically 0.3 - 0.9) to 0-30 scale
        norm_sim = max(0.0, min(1.0, (cosine_sim - 0.25) / 0.65))
        semantic_score = round(norm_sim * 30.0, 1)
    except Exception as e:
        print(f"Embedding calculation warning in ATS: {e}")
        semantic_score = round(skills_score * 0.75, 1)

    # 5. Experience Depth (Max 20 points) & Impact Density (Max 10 points)
    exp_data = calculate_experience_depth(resume_text, job_description)
    metric_data = calculate_metric_density(resume_text)

    # 6. Overall Composite Score (0-100%)
    overall_score = round(min(100.0, skills_score + semantic_score + exp_data["score"] + metric_data["score"]), 1)

    # Score Rating & Color Code
    if overall_score >= 80:
        rating_label = "STRONG MATCH"
        rating_color = "green"
        summary_verdict = "Your resume demonstrates high alignment with the core requirements. Ready for submission with minor fine-tuning."
    elif overall_score >= 60:
        rating_label = "GOOD MATCH (OPTIMIZE)"
        rating_color = "yellow"
        summary_verdict = "Solid foundational match, but critical technical skills or tools mentioned in the job description are missing from your resume."
    else:
        rating_label = "SIGNIFICANT GAPS"
        rating_color = "red"
        summary_verdict = "Key qualification and stack gaps detected. We recommend tailoring your bullet points before applying."

    # 7. Actionable Recommendations & Tailored Bullet Suggestions
    recommendations = []
    top_missing_names = [s["name"] for s in missing_skills[:4]]
    
    if top_missing_names:
        recommendations.append(f"Incorporate missing core skills: {', '.join(top_missing_names)} into your experience bullets.")
        
    if metric_data["metric_percentage"] < 40:
        recommendations.append("Increase metric density: Only " + str(metric_data["metric_percentage"]) + "% of your bullets contain measurable metrics (%, $, scale).")
        
    if metric_data["action_percentage"] < 60:
        recommendations.append("Strengthen bullet openers: Use high-impact verbs (e.g., 'Architected', 'Spearheaded', 'Optimized').")
        
    if not recommendations:
        recommendations.append("Resume formatting and keyword distribution are strong. Highlight domain-specific achievements during interviews.")

    # 8. Suggested Bullet Fix
    suggested_bullet_rewrite = ""
    if top_missing_names:
        primary_gap = top_missing_names[0]
        suggested_bullet_rewrite = f"Architected and deployed high-throughput backend services utilizing {primary_gap} and PostgreSQL, reducing query latency by 35% and improving uptime to 99.9%."

    result = {
        "overall_score": overall_score,
        "rating_label": rating_label,
        "rating_color": rating_color,
        "summary_verdict": summary_verdict,
        "job_title": job_title,
        "company": company,
        "category_scores": {
            "technical_skills": {
                "score": skills_score,
                "max": 40,
                "label": "Technical Stack Fit"
            },
            "semantic_alignment": {
                "score": semantic_score,
                "max": 30,
                "label": "Role & Domain Alignment"
            },
            "experience_depth": {
                "score": exp_data["score"],
                "max": 20,
                "label": "Production & Experience Depth"
            },
            "metric_density": {
                "score": metric_data["score"],
                "max": 10,
                "label": "Impact & Action Verbs"
            }
        },
        "keyword_matrix": {
            "matched_count": len(matched_skills),
            "missing_count": len(missing_skills),
            "total_jd_keywords": len(jd_skills),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        },
        "formatting_checks": {
            "total_bullets": metric_data["total_bullets_analyzed"],
            "metric_percentage": metric_data["metric_percentage"],
            "action_verb_percentage": metric_data["action_percentage"],
            "estimated_years_experience": exp_data["estimated_years"]
        },
        "recommendations": recommendations,
        "suggested_bullet_rewrite": suggested_bullet_rewrite
    }

    # 9. Save to Cache
    if db:
        try:
            import json
            new_cache = AIGenerationCache(cache_key=cache_key, response_text=json.dumps(result))
            db.add(new_cache)
            db.commit()
        except Exception as cache_err:
            print(f"Error saving ATS cache: {cache_err}")

    return result
