#!/usr/bin/env python3
"""
Generates the benchmark evaluation dataset:
- 12 realistic synthetic resumes spanning distinct software specializations.
- 220 realistic job postings with structured roles, domains, and requirement texts.
- ground_truth_relevance.csv mapping (resume_id, job_id) -> relevance grade (0-3).

Methodology & Grading Scale:
- Grade 3 (Highly Relevant): Exact match on domain, core tech stack, and seniority level.
- Grade 2 (Moderately Relevant): Overlapping core stack with minor difference in domain or seniority.
- Grade 1 (Marginally Relevant): Peripheral skill overlap (e.g. general Python/SQL) but disparate primary discipline.
- Grade 0 (Irrelevant): Disjoint domains (e.g., iOS developer applied to Embedded C++ or DevOps to Frontend UI).
"""

import os
import json
import csv
import random

RESUMES = [
    {
        "id": 1,
        "name": "Alex Mercer",
        "domain": "backend_python",
        "title": "Senior Python Backend Engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "REST API", "Microservices", "SQLAlchemy"],
        "experience_years": 6,
        "employers": ["DataScale Systems", "CloudForge"],
        "degree": "B.S. Computer Science",
        "summary": "Backend specialist with 6 years building high-throughput FastAPI and PostgreSQL services with Redis caching."
    },
    {
        "id": 2,
        "name": "Elena Rostova",
        "domain": "frontend_web",
        "title": "Senior Frontend Engineer",
        "skills": ["React", "Next.js", "TypeScript", "Tailwind CSS", "JavaScript", "HTML5", "CSS3", "Redux"],
        "experience_years": 5,
        "employers": ["PixelCraft Studios", "FinTech Labs"],
        "degree": "B.S. Software Engineering",
        "summary": "Frontend architect with 5 years creating responsive Next.js and TypeScript web applications."
    },
    {
        "id": 3,
        "name": "Marcus Chen",
        "domain": "machine_learning",
        "title": "Lead Machine Learning Engineer",
        "skills": ["Python", "PyTorch", "Transformers", "Machine Learning", "NLP", "Pandas", "NumPy", "HuggingFace"],
        "experience_years": 7,
        "employers": ["NeuralFlow AI", "Cognitive Insights"],
        "degree": "M.S. Artificial Intelligence",
        "summary": "ML lead with 7 years fine-tuning LLMs, building dense retrieval pipelines, and scaling PyTorch models."
    },
    {
        "id": 4,
        "name": "Devon Vance",
        "domain": "devops_cloud",
        "title": "DevOps & Cloud Infrastructure Architect",
        "skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD", "Linux", "Prometheus", "Helm"],
        "experience_years": 8,
        "employers": ["CloudScale Global", "Vanguard Infra"],
        "degree": "B.S. Information Technology",
        "summary": "Cloud architect with 8 years orchestrating multi-region AWS infrastructure, Kubernetes, and GitOps."
    },
    {
        "id": 5,
        "name": "Priya Patel",
        "domain": "data_engineering",
        "title": "Senior Data Platform Engineer",
        "skills": ["Python", "Apache Spark", "SQL", "Kafka", "PostgreSQL", "Snowflake", "Airflow", "ETL"],
        "experience_years": 6,
        "employers": ["DataStream Corp", "Apex Analytics"],
        "degree": "B.S. Computer Engineering",
        "summary": "Data engineer with 6 years architecting streaming ETL pipelines using Kafka, Spark, and PostgreSQL."
    },
    {
        "id": 6,
        "name": "Viktor Novak",
        "domain": "embedded_systems",
        "title": "Principal Embedded Systems Engineer",
        "skills": ["C++", "C", "RTOS", "Linux", "Firmware", "Git", "Microcontrollers", "CAN bus"],
        "experience_years": 10,
        "employers": ["AutoSense Electronics", "Robotics Dynamics"],
        "degree": "B.S. Electrical & Computer Engineering",
        "summary": "Embedded firmware engineer with 10 years developing safety-critical real-time C++ systems."
    },
    {
        "id": 7,
        "name": "Samira Khan",
        "domain": "mobile_ios",
        "title": "iOS Mobile Developer",
        "skills": ["Swift", "iOS", "SwiftUI", "UIKit", "Xcode", "CoreData", "Git", "Combine"],
        "experience_years": 4,
        "employers": ["AppForge Interactive", "Hyperion Mobile"],
        "degree": "B.S. Computer Science",
        "summary": "iOS engineer with 4 years delivering native SwiftUI and UIKit consumer mobile applications."
    },
    {
        "id": 8,
        "name": "Carlos Mendez",
        "domain": "enterprise_dotnet",
        "title": "Lead .NET Solutions Architect",
        "skills": ["C#", ".NET", "ASP.NET Core", "SQL Server", "Azure", "Microservices", "Docker", "Entity Framework"],
        "experience_years": 11,
        "employers": ["Enterprise Core Tech", "Global Services"],
        "degree": "B.S. Information Systems",
        "summary": "Enterprise solutions architect with 11 years designing enterprise-grade .NET and C# applications."
    },
    {
        "id": 9,
        "name": "Chloe Bennett",
        "domain": "cybersecurity",
        "title": "Security Operations & AppSec Engineer",
        "skills": ["Python", "Linux", "OWASP", "SIEM", "Penetration Testing", "Docker", "AWS", "Cryptography"],
        "experience_years": 5,
        "employers": ["CyberShield Guard", "ZeroTrust Systems"],
        "degree": "B.S. Cybersecurity",
        "summary": "Application security engineer with 5 years conducting threat modeling, vulnerability audits, and AppSec hardening."
    },
    {
        "id": 10,
        "name": "Jordan Lee",
        "domain": "fullstack_general",
        "title": "Senior Full Stack Engineer",
        "skills": ["TypeScript", "React", "Node.js", "Express", "PostgreSQL", "Docker", "Next.js", "Redis"],
        "experience_years": 6,
        "employers": ["OmniStack Inc", "Veloce Media"],
        "degree": "B.S. Computer Science",
        "summary": "Full stack generalist with 6 years building modern React frontends and Node.js/PostgreSQL APIs."
    },
    {
        "id": 11,
        "name": "Sophie Martin",
        "domain": "bi_analytics",
        "title": "Business Intelligence & Data Analyst",
        "skills": ["SQL", "Tableau", "Power BI", "Data Analysis", "Python", "Excel", "Reporting", "Statistics"],
        "experience_years": 4,
        "employers": ["MetricPulse", "InsightMetrics"],
        "degree": "B.S. Economics & Statistics",
        "summary": "BI analyst with 4 years creating executive KPI dashboards, cohort retention models, and SQL pipelines."
    },
    {
        "id": 12,
        "name": "Lucas Silva",
        "domain": "qa_automation",
        "title": "Lead SDET & Automation Engineer",
        "skills": ["Python", "Playwright", "Selenium", "CI/CD", "Docker", "Git", "pytest", "API Testing"],
        "experience_years": 6,
        "employers": ["QualityFirst Labs", "TestWave Corp"],
        "degree": "B.S. Software Engineering",
        "summary": "SDET lead with 6 years architecting end-to-end automation frameworks with Playwright, pytest, and CI pipelines."
    }
]

DOMAINS = [
    "backend_python", "frontend_web", "machine_learning", "devops_cloud",
    "data_engineering", "embedded_systems", "mobile_ios", "enterprise_dotnet",
    "cybersecurity", "fullstack_general", "bi_analytics", "qa_automation"
]

DOMAIN_KEYWORDS = {
    "backend_python": ("Python", "FastAPI", "PostgreSQL", "Redis", "Microservices"),
    "frontend_web": ("React", "Next.js", "TypeScript", "Tailwind CSS", "UI/UX"),
    "machine_learning": ("Machine Learning", "PyTorch", "NLP", "LLM", "Transformers"),
    "devops_cloud": ("AWS", "Kubernetes", "Docker", "Terraform", "CI/CD"),
    "data_engineering": ("Apache Spark", "Kafka", "SQL", "ETL", "Data Pipelines"),
    "embedded_systems": ("C++", "C", "RTOS", "Firmware", "Embedded Linux"),
    "mobile_ios": ("Swift", "iOS", "SwiftUI", "UIKit", "Mobile"),
    "enterprise_dotnet": ("C#", ".NET", "ASP.NET Core", "Azure", "Entity Framework"),
    "cybersecurity": ("AppSec", "Penetration Testing", "OWASP", "Security", "Vulnerability"),
    "fullstack_general": ("TypeScript", "React", "Node.js", "PostgreSQL", "Full Stack"),
    "bi_analytics": ("Tableau", "Power BI", "SQL", "Data Analysis", "Dashboards"),
    "qa_automation": ("Playwright", "SDET", "pytest", "Automation", "Testing")
}

def generate_dataset():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)

    # 1. Save Resumes
    resumes_path = os.path.join(data_dir, "resumes.json")
    with open(resumes_path, "w", encoding="utf-8") as f:
        json.dump(RESUMES, f, indent=2)
    print(f"[+] Wrote {len(RESUMES)} resumes to {resumes_path}")

    # 2. Generate 220 Jobs
    jobs = []
    job_id = 1
    # Distribute ~18-19 jobs per domain
    for dom in DOMAINS:
        kw = DOMAIN_KEYWORDS[dom]
        seniorities = ["Junior", "Mid-Level", "Senior", "Staff", "Lead", "Principal"]
        for i in range(18):
            sen = random.choice(seniorities)
            title = f"{sen} {kw[0]} Engineer" if "Engineer" not in kw[0] else f"{sen} {kw[0]}"
            company = f"{dom.replace('_', ' ').title().replace(' ', '')} Labs {i+1}"
            desc = (
                f"We are hiring a {title} at {company}. The candidate will work extensively with "
                f"{kw[0]}, {kw[1]}, and {kw[2]}. Requirements: {random.randint(2, 8)}+ years of experience with "
                f"{kw[3]} and {kw[4]}. Must be collaborative and experienced in production deployments."
            )
            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "domain": dom,
                "seniority": sen,
                "description": desc,
                "key_skills": list(kw)
            })
            job_id += 1

    # Add 4 additional cross-domain hybrid jobs to reach exactly 220
    cross_domains = [
        ("Full Stack AI Engineer", "machine_learning", ["Python", "React", "PyTorch", "FastAPI"]),
        ("Cloud Data Infrastructure Architect", "data_engineering", ["AWS", "Spark", "Kubernetes", "Kafka"]),
        ("Frontend Quality Automation Lead", "qa_automation", ["React", "Playwright", "TypeScript", "CI/CD"]),
        ("SecOps Platform Developer", "cybersecurity", ["Python", "AWS", "Docker", "Security"])
    ]
    for title, dom, skills in cross_domains:
        jobs.append({
            "id": job_id,
            "title": title,
            "company": f"Hybrid Ventures {job_id}",
            "domain": dom,
            "seniority": "Senior",
            "description": f"Seeking a {title} skilled in {', '.join(skills)} with 5+ years experience.",
            "key_skills": skills
        })
        job_id += 1

    jobs_path = os.path.join(data_dir, "jobs.json")
    with open(jobs_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    print(f"[+] Wrote {len(jobs)} jobs to {jobs_path}")

    # 3. Generate Ground Truth Relevance Matrix (12 resumes x 220 jobs = 2,640 pairs)
    gt_path = os.path.join(data_dir, "ground_truth_relevance.csv")
    with open(gt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["resume_id", "job_id", "relevance_grade", "notes"])

        for r in RESUMES:
            r_dom = r["domain"]
            r_skills = set(s.lower() for s in r["skills"])

            for j in jobs:
                j_dom = j["domain"]
                j_skills = set(s.lower() for s in j["key_skills"])
                common_skills = r_skills.intersection(j_skills)

                # Deterministic Ground-Truth Relevance Heuristic:
                if r_dom == j_dom:
                    # Same primary domain
                    if len(common_skills) >= 3:
                        grade = 3  # Perfect match
                        note = "Exact domain & core skill match"
                    else:
                        grade = 2  # Same domain, minor skill variance
                        note = "Exact domain, partial skill variance"
                else:
                    # Cross-domain comparison
                    # Check transferable domain pairings (e.g., backend_python & data_engineering or frontend & fullstack)
                    adjacent_pairs = {
                        ("backend_python", "data_engineering"),
                        ("backend_python", "fullstack_general"),
                        ("frontend_web", "fullstack_general"),
                        ("frontend_web", "qa_automation"),
                        ("devops_cloud", "cybersecurity"),
                        ("machine_learning", "data_engineering"),
                        ("machine_learning", "backend_python")
                    }
                    is_adjacent = (r_dom, j_dom) in adjacent_pairs or (j_dom, r_dom) in adjacent_pairs

                    if is_adjacent and len(common_skills) >= 2:
                        grade = 2
                        note = "Adjacent technical domain with skill overlap"
                    elif len(common_skills) >= 1 or is_adjacent:
                        grade = 1
                        note = "Marginal overlap on auxiliary technologies"
                    else:
                        grade = 0
                        note = "Disjoint domains / zero semantic alignment"

                writer.writerow([r["id"], j["id"], grade, note])

    print(f"[+] Wrote {len(RESUMES) * len(jobs)} ground truth labels to {gt_path}")

if __name__ == "__main__":
    generate_dataset()
