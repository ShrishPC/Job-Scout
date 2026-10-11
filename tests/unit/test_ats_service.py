import pytest
from app.services.ats_service import (
    normalize_skill,
    extract_all_known_skills,
    calculate_metric_density,
    calculate_experience_depth,
    analyze_resume_ats_match,
    SKILL_TAXONOMY,
    SYNONYMS,
)

def test_normalize_skill():
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("postgres") == "postgresql"
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill("ReactJS") == "react"
    assert normalize_skill("unknown_tool") == "unknown_tool"

def test_extract_all_known_skills():
    sample_text = (
        "Experienced Python and C++ developer with FastAPI, PostgreSQL, and Docker. "
        "Also worked with React, Kubernetes (k8s), and PyTorch for machine learning."
    )
    skills = extract_all_known_skills(sample_text)
    
    assert "python" in skills
    assert "c++" in skills
    assert "fastapi" in skills
    assert "postgresql" in skills
    assert "docker" in skills
    assert "react" in skills
    assert "kubernetes" in skills  # k8s normalized to kubernetes
    assert "pytorch" in skills
    
    assert skills["python"]["count"] >= 1
    assert skills["python"]["category"] == "Languages"
    assert skills["c++"]["count"] >= 1

def test_calculate_metric_density():
    resume_with_metrics = (
        "- Architected high-throughput API reducing latency by 45% across 12 services.\n"
        "- Optimized PostgreSQL queries saving $12,000 monthly in cloud hosting.\n"
        "- Scaled user platform to 2M monthly active users with 99.99% uptime.\n"
        "- Automated deployment pipelines using Docker, accelerating release cycle by 3x."
    )
    res = calculate_metric_density(resume_with_metrics)
    assert res["score"] > 5.0
    assert res["metric_bullets_count"] >= 3
    assert res["action_verb_count"] >= 3
    assert res["total_bullets_analyzed"] == 4

    resume_without_metrics = (
        "Responsible for writing code and attending team standup meetings every day.\n"
        "Helped team members with bug fixes and code maintenance."
    )
    res_low = calculate_metric_density(resume_without_metrics)
    assert res_low["score"] < res["score"]

def test_calculate_experience_depth():
    strong_exp = (
        "Senior Backend Architect with 8 years of experience in production environments. "
        "Spearheaded distributed systems, microservices infrastructure, and scalability initiatives. "
        "Mentored junior developers and led CI/CD security audits."
    )
    res = calculate_experience_depth(strong_exp, "Senior Backend Architect")
    assert res["score"] >= 12.0
    assert res["estimated_years"] == 8
    assert "production" in res["production_signals_found"]
    assert "microservices" in res["production_signals_found"]

    entry_exp = "Junior Developer with passion for coding and learning new libraries."
    res_entry = calculate_experience_depth(entry_exp, "Junior Developer")
    assert res_entry["score"] < res["score"]
    assert res_entry["estimated_years"] == 0

def test_analyze_resume_ats_match(db_session):
    resume = (
        "Senior Python Engineer with 6 years experience building FastAPI backends, "
        "PostgreSQL databases, Redis caching, and Docker containerization. "
        "Optimized database queries reducing p99 latency by 40% and handled 500k requests/min."
    )
    job_title = "Senior Python Developer"
    job_desc = (
        "Looking for a Senior Python Developer with expertise in FastAPI, PostgreSQL, "
        "and Redis. Experience with Docker and Kubernetes required. Must have experience optimizing APIs."
    )
    
    result = analyze_resume_ats_match(resume, job_title, job_desc, company="TestCorp", db=db_session)
    
    assert "overall_score" in result
    assert result["overall_score"] > 50.0
    assert "keyword_matrix" in result
    assert "category_scores" in result
    assert "GOOD MATCH" in result["rating_label"] or "MATCH" in result["rating_label"]
    
    matched_names = [s["name"].lower() for s in result["keyword_matrix"]["matched_skills"]]
    assert any("python" in m for m in matched_names)
    assert any("fastapi" in m for m in matched_names)
    assert any("postgresql" in m for m in matched_names)
    
    # Check cache hit on repeated call
    cached_result = analyze_resume_ats_match(resume, job_title, job_desc, company="TestCorp", db=db_session)
    assert cached_result["overall_score"] == result["overall_score"]

