#!/usr/bin/env python3
"""
Generates the Hard & Discriminating Evaluation Benchmark:
- 28 diverse candidate profiles spanning 14 technical domains
- 560 job listings containing:
    1. Canonical Relevant Matches (same domain, core tech stack) -> Grade 3
    2. Paraphrased / Synonymous Matches (identical domain & seniority, but using semantic paraphrasing with NO keyword overlap, e.g. "predictive modelling / statistical inference" vs "machine learning", "container orchestration / declarative IaC" vs "Kubernetes / Terraform", "relational datastores / high-concurrency microservices" vs "PostgreSQL / FastAPI") -> Grade 3 or 2
    3. Keyword Distractors (high keyword overlap with auxiliary tools, but wrong role/domain, e.g. Technical Recruiter, Account Executive, Technical Writer, Sales Engineer) -> Grade 0 or 1
    4. Adjacent Domain Positions (e.g. Data Engineering <-> Backend Python, SRE <-> DevOps) -> Grade 1 or 2
    5. Disjoint Domain Postings -> Grade 0
- Independent Ground Truth Relevance Matrix:
    Ground-truth labels are assigned via structural role taxonomy and candidate qualification criteria,
    COMPLETELY INDEPENDENT of keyword matching points or scoring logic.
"""

import os
import json
import csv
import shutil

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# 28 Detailed Candidate Resumes (>= 25)
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
        "title": "Senior .NET Core Architect",
        "skills": [".NET", "C#", "ASP.NET Core", "SQL Server", "Azure", "Entity Framework", "Microservices", "RabbitMQ"],
        "experience_years": 9,
        "employers": ["OmniCorp Financial", "Meridian Solutions"],
        "degree": "B.S. Information Systems",
        "summary": "Enterprise architect with 9 years designing distributed C# .NET microservices on Microsoft Azure."
    },
    {
        "id": 9,
        "name": "Amina Diallo",
        "domain": "cybersecurity",
        "title": "Application Security Engineer",
        "skills": ["Python", "Linux", "Application Security", "Penetration Testing", "OWASP", "SIEM", "Cryptography", "Git"],
        "experience_years": 5,
        "employers": ["CyberDefend Labs", "Sentinel Security"],
        "degree": "B.S. Cybersecurity",
        "summary": "AppSec specialist with 5 years securing containerized web APIs, performing code reviews, and threat modeling."
    },
    {
        "id": 10,
        "name": "Jordan Lee",
        "domain": "fullstack_general",
        "title": "Full Stack Software Engineer",
        "skills": ["TypeScript", "React", "Node.js", "Express", "PostgreSQL", "Docker", "REST API", "Tailwind CSS"],
        "experience_years": 4,
        "employers": ["Veloce Web Systems", "Beacon Tech"],
        "degree": "B.S. Software Development",
        "summary": "Full-stack builder with 4 years deploying end-to-end web applications with Node.js, React, and PostgreSQL."
    },
    {
        "id": 11,
        "name": "Rachel Goldberg",
        "domain": "bi_analytics",
        "title": "Senior BI & Analytics Specialist",
        "skills": ["SQL", "Python", "Tableau", "Power BI", "Data Modeling", "Excel", "Data Analysis", "Snowflake"],
        "experience_years": 6,
        "employers": ["Strategic Insights", "OmniMetrics"],
        "degree": "B.A. Economics & Statistics",
        "summary": "Analytics lead with 6 years building executive dashboards, SQL aggregations, and cohort retention models."
    },
    {
        "id": 12,
        "name": "Taro Tanaka",
        "domain": "qa_automation",
        "title": "Lead QA Automation Engineer",
        "skills": ["Python", "Playwright", "Selenium", "CI/CD", "Docker", "PyTest", "API Testing", "Git"],
        "experience_years": 7,
        "employers": ["QualityFirst Soft", "TestMatrix Labs"],
        "degree": "B.S. Computer Engineering",
        "summary": "QA lead with 7 years architecting automated regression pipelines using Python, Playwright, and PyTest."
    },
    {
        "id": 13,
        "name": "Dmitri Volkov",
        "domain": "systems_rust",
        "title": "Rust Systems Software Engineer",
        "skills": ["Rust", "Tokio", "Concurrency", "Linux", "gRPC", "Systems Programming", "Distributed Systems", "Git"],
        "experience_years": 5,
        "employers": ["HyperDrive Storage", "KernelScale"],
        "degree": "B.S. Computer Engineering",
        "summary": "Low-level systems programmer with 5 years writing high-throughput asynchronous storage engines in Rust."
    },
    {
        "id": 14,
        "name": "Chloe Bennett",
        "domain": "mobile_android",
        "title": "Senior Android Engineer",
        "skills": ["Kotlin", "Android", "Jetpack Compose", "Coroutines", "Dagger Hilt", "Room", "Gradle", "Git"],
        "experience_years": 6,
        "employers": ["MobilityHQ", "PulseMobile"],
        "degree": "B.S. Computer Science",
        "summary": "Android developer with 6 years building reactive Jetpack Compose mobile experiences with Kotlin Coroutines."
    },
    {
        "id": 15,
        "name": "Karthik Subramanian",
        "domain": "distributed_go",
        "title": "Senior Go Distributed Systems Engineer",
        "skills": ["Go", "Golang", "gRPC", "Kubernetes", "Docker", "Distributed Systems", "Prometheus", "PostgreSQL"],
        "experience_years": 6,
        "employers": ["MicroMesh Networks", "StreamGlobal"],
        "degree": "B.Tech Computer Science",
        "summary": "Go engineer with 6 years writing low-latency microservices, gRPC protocols, and resilient distributed systems."
    },
    {
        "id": 16,
        "name": "Sarah Jenkins",
        "domain": "cloud_sre",
        "title": "Site Reliability Engineer (SRE)",
        "skills": ["Linux", "Kubernetes", "Prometheus", "Grafana", "Python", "Terraform", "Incident Management", "AWS"],
        "experience_years": 7,
        "employers": ["UptimeForge", "GlobalPay Tech"],
        "degree": "B.S. Computer Networks",
        "summary": "SRE with 7 years implementing SLO/SLAs, multi-region observability, and automated chaos testing."
    },
    {
        "id": 17,
        "name": "Zackary Taylor",
        "domain": "nlp_genai",
        "title": "GenAI & RAG Solutions Engineer",
        "skills": ["Python", "LangChain", "LlamaIndex", "pgvector", "PyTorch", "HuggingFace", "Vector Search", "RAG"],
        "experience_years": 4,
        "employers": ["LexiconAI", "CognitiveSearch"],
        "degree": "M.S. Data Science",
        "summary": "GenAI specialist with 4 years building retrieval-augmented generation (RAG) engines and vector search pipelines."
    },
    {
        "id": 18,
        "name": "Lars Lindqvist",
        "domain": "low_latency_cpp",
        "title": "Staff Low-Latency C++ Engineer",
        "skills": ["C++", "Linux", "Socket Programming", "Multi-threading", "Memory Management", "Algorithms", "Git", "C"],
        "experience_years": 11,
        "employers": ["Apex Quant Trading", "Citadel Markets"],
        "degree": "M.S. Applied Mathematics",
        "summary": "Quantitative systems developer with 11 years optimizing kernel bypass networking and nanosecond order matching engines."
    },
    {
        "id": 19,
        "name": "Fatima Zahra",
        "domain": "enterprise_java",
        "title": "Principal Java Spring Boot Engineer",
        "skills": ["Java", "Spring Boot", "Microservices", "Kafka", "PostgreSQL", "Docker", "Kubernetes", "Hibernate"],
        "experience_years": 10,
        "employers": ["Financiere Globale", "Enterprise Transit"],
        "degree": "M.S. Computer Science",
        "summary": "Java architect with 10 years designing mission-critical enterprise banking platforms using Spring Boot and Kafka."
    },
    {
        "id": 20,
        "name": "Gabriel Santos",
        "domain": "data_science",
        "title": "Staff Data Scientist",
        "skills": ["Python", "Pandas", "Scikit-Learn", "Machine Learning", "SQL", "Statistics", "NumPy", "Matplotlib"],
        "experience_years": 8,
        "employers": ["BioAnalytics Lab", "HealthPulse"],
        "degree": "Ph.D. Biostatistics",
        "summary": "Data scientist with 8 years building predictive survival models, randomized clinical trial analytics, and causal inference."
    },
    {
        "id": 21,
        "name": "Ananya Sharma",
        "domain": "mlops_platform",
        "title": "Senior MLOps Platform Engineer",
        "skills": ["Python", "Kubeflow", "MLflow", "Docker", "Kubernetes", "AWS", "CI/CD", "PyTorch"],
        "experience_years": 5,
        "employers": ["ModelScale Systems", "InferenceGrid"],
        "degree": "B.S. Information Technology",
        "summary": "MLOps engineer with 5 years establishing continuous training workflows, feature stores, and automated model deployment."
    },
    {
        "id": 22,
        "name": "Brian O'Connor",
        "domain": "dba_postgresql",
        "title": "Senior PostgreSQL Database Administrator",
        "skills": ["PostgreSQL", "SQL", "Database Administration", "Linux", "Performance Tuning", "Replication", "Bash", "Backup"],
        "experience_years": 9,
        "employers": ["DataVault Managed Services", "CoreCloud DB"],
        "degree": "B.S. Database Systems",
        "summary": "PostgreSQL DBA with 9 years managing terabyte-scale clusters, WAL replication, and query optimization."
    },
    {
        "id": 23,
        "name": "Maya Lin",
        "domain": "frontend_web",
        "title": "Frontend UI/UX Systems Specialist",
        "skills": ["React", "TypeScript", "Tailwind CSS", "HTML5", "CSS3", "Design Systems", "JavaScript", "Figma"],
        "experience_years": 5,
        "employers": ["Starlight Design", "Echo Web"],
        "degree": "B.A. Digital Media Design",
        "summary": "Frontend developer focusing on accessible component libraries, Tailwind tokens, and responsive web animations."
    },
    {
        "id": 24,
        "name": "Henrik Sorensen",
        "domain": "cloud_security",
        "title": "Cloud Security Architect",
        "skills": ["AWS", "Azure", "Terraform", "Security", "IAM", "Compliance", "Linux", "Kubernetes"],
        "experience_years": 8,
        "employers": ["Nordic Shield Cyber", "EuroCloud Sec"],
        "degree": "B.S. Computer Information Systems",
        "summary": "Cloud security architect designing Zero-Trust architectures, IAM policies, and automated CSPM audits."
    },
    {
        "id": 25,
        "name": "Mei-Ling Wu",
        "domain": "backend_python",
        "title": "Python API & Platform Developer",
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Celery", "REST API", "Docker"],
        "experience_years": 4,
        "employers": ["TechBridge Digital", "SaaSStream"],
        "degree": "B.S. Software Engineering",
        "summary": "Python engineer with 4 years building asynchronous background workers with Celery and REST APIs with FastAPI."
    },
    {
        "id": 26,
        "name": "Mateo Rossi",
        "domain": "mobile_react_native",
        "title": "Cross-Platform Mobile Engineer",
        "skills": ["React Native", "TypeScript", "JavaScript", "iOS", "Android", "Redux", "REST API", "Git"],
        "experience_years": 5,
        "employers": ["AppHive Studios", "OmniMobile"],
        "degree": "B.S. Computer Applications",
        "summary": "Mobile engineer with 5 years shipping cross-platform iOS and Android apps with React Native."
    },
    {
        "id": 27,
        "name": "Lucas Dubois",
        "domain": "blockchain_web3",
        "title": "Smart Contract & Protocol Engineer",
        "skills": ["Solidity", "Rust", "Ethereum", "Smart Contracts", "Cryptography", "Git", "Linux", "Web3"],
        "experience_years": 4,
        "employers": ["DecentralChain", "TokenMatrix"],
        "degree": "M.S. Cryptography",
        "summary": "Web3 engineer specializing in audited Solidity smart contracts, DeFi liquidity protocols, and zero-knowledge proofs."
    },
    {
        "id": 28,
        "name": "Olga Ivanova",
        "domain": "bioinformatics",
        "title": "Bioinformatics Pipeline Engineer",
        "skills": ["Python", "Nextflow", "Linux", "Bash", "Docker", "Data Analysis", "Git", "SQL"],
        "experience_years": 6,
        "employers": ["GenomeSeq Analytics", "BioCore Labs"],
        "degree": "Ph.D. Bioinformatics",
        "summary": "Computational biologist with 6 years developing reproducible Nextflow and Python pipelines for high-throughput DNA sequencing."
    }
]

def generate_hard_dataset():
    print("=" * 60)
    print("🚀 GENERATING HARD & DISCRIMINATING EVALUATION BENCHMARK")
    print("=" * 60)

    # 1. Save Resumes
    resumes_path = os.path.join(DATA_DIR, "resumes.json")
    with open(resumes_path, "w", encoding="utf-8") as f:
        json.dump(RESUMES, f, indent=2)
    print(f"[+] Wrote {len(RESUMES)} candidate resumes to {resumes_path}")

    # 2. Build 560 Job Descriptions
    jobs = []
    job_id = 1

    # Domain definitions and vocabularies
    DOMAINS = [
        "backend_python", "frontend_web", "machine_learning", "devops_cloud",
        "data_engineering", "embedded_systems", "mobile_ios", "enterprise_dotnet",
        "cybersecurity", "fullstack_general", "bi_analytics", "qa_automation",
        "systems_rust", "mobile_android", "distributed_go", "cloud_sre",
        "nlp_genai", "low_latency_cpp", "enterprise_java", "data_science"
    ]

    # Category 1: Standard Canonical Matches (20 domains x 12 jobs = 240 jobs)
    domain_canonical_specs = {
        "backend_python": ("Python Backend Engineer", ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"]),
        "frontend_web": ("Senior Frontend Developer", ["React", "Next.js", "TypeScript", "Tailwind CSS", "JavaScript"]),
        "machine_learning": ("Machine Learning Engineer", ["Python", "PyTorch", "Transformers", "NLP", "Machine Learning"]),
        "devops_cloud": ("DevOps & Cloud Engineer", ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD"]),
        "data_engineering": ("Data Platform Engineer", ["Python", "Apache Spark", "Kafka", "PostgreSQL", "Airflow"]),
        "embedded_systems": ("Embedded Firmware Engineer", ["C++", "C", "RTOS", "Linux", "Firmware"]),
        "mobile_ios": ("iOS Mobile Application Developer", ["Swift", "iOS", "SwiftUI", "UIKit", "Xcode"]),
        "enterprise_dotnet": ("Senior .NET Core Architect", [".NET", "C#", "ASP.NET Core", "SQL Server", "Azure"]),
        "cybersecurity": ("Application Security Engineer", ["Python", "Linux", "Application Security", "Penetration Testing", "OWASP"]),
        "fullstack_general": ("Full Stack Web Developer", ["TypeScript", "React", "Node.js", "Express", "PostgreSQL"]),
        "bi_analytics": ("Business Intelligence Analyst", ["SQL", "Tableau", "Power BI", "Data Modeling", "Python"]),
        "qa_automation": ("Software Quality Engineer", ["Python", "Playwright", "Selenium", "PyTest", "CI/CD"]),
        "systems_rust": ("Rust Systems Software Engineer", ["Rust", "Tokio", "Concurrency", "Linux", "gRPC"]),
        "mobile_android": ("Android Mobile Developer", ["Kotlin", "Android", "Jetpack Compose", "Coroutines", "Room"]),
        "distributed_go": ("Go Distributed Systems Engineer", ["Go", "Golang", "gRPC", "Kubernetes", "Microservices"]),
        "cloud_sre": ("Site Reliability Engineer", ["Linux", "Kubernetes", "Prometheus", "Grafana", "Terraform"]),
        "nlp_genai": ("GenAI & LLM Solutions Engineer", ["Python", "LangChain", "LlamaIndex", "pgvector", "RAG"]),
        "low_latency_cpp": ("Low-Latency C++ Engineer", ["C++", "Linux", "Socket Programming", "Multi-threading", "C"]),
        "enterprise_java": ("Enterprise Java Architect", ["Java", "Spring Boot", "Microservices", "Kafka", "PostgreSQL"]),
        "data_science": ("Staff Data Scientist", ["Python", "Pandas", "Scikit-Learn", "Machine Learning", "Statistics"])
    }

    seniorities = ["Junior", "Mid-Level", "Senior", "Lead", "Staff", "Principal"]

    for dom, (base_title, core_skills) in domain_canonical_specs.items():
        for i in range(12):
            sen = seniorities[i % len(seniorities)]
            title = f"{sen} {base_title}" if sen not in base_title else base_title
            desc = (
                f"We are seeking a talented {title} to join our engineering organization. "
                f"The ideal candidate will have strong experience with {', '.join(core_skills[:3])}, "
                f"along with hands-on proficiency in {core_skills[3]} and {core_skills[4]}. "
                f"You will design scalable services, collaborate with product teams, and write clean, tested code."
            )
            jobs.append({
                "id": job_id,
                "title": title,
                "company": f"TechCorp {dom.title()} {job_id}",
                "domain": dom,
                "category": "canonical",
                "seniority": sen,
                "description": desc,
                "key_skills": core_skills
            })
            job_id += 1

    # Category 2: Paraphrased / Synonymous Matches (80 jobs)
    # ZERO canonical keyword overlap, but IDENTICAL domain and engineering intent!
    paraphrase_templates = [
        # (domain, title, description, skills_used_conceptually)
        (
            "machine_learning",
            "Predictive Modeling & Statistical Inference Specialist",
            "Seeking an applied algorithmic researcher to design deep neural representations, "
            "gradient optimization workflows, and probabilistic sequence architectures for high-dimensional inference. "
            "Strong mathematical foundations and computational graph frameworks required.",
            ["statistical modeling", "deep neural networks", "gradient optimization"]
        ),
        (
            "backend_python",
            "Asynchronous HTTP Services & Relational Datastore Architect",
            "Looking for an architect to build resilient web application interfaces, high-concurrency event loops, "
            "and transactional relational schemas with distributed in-memory caching layers.",
            ["asynchronous web framework", "relational persistence", "in-memory caching"]
        ),
        (
            "devops_cloud",
            "Infrastructure as Code & Container Orchestration Specialist",
            "Join our platform crew to automate cloud provisioning, declarative resource manifests, "
            "cluster scheduling engines, and automated continuous deployment verification pipelines.",
            ["declarative infrastructure", "cluster scheduling", "continuous deployment"]
        ),
        (
            "frontend_web",
            "Client-Side Interface & Reactive View Architect",
            "Build next-generation single page browser client applications using component hierarchies, "
            "type-checked client scripting, responsive utility styling, and state management graphs.",
            ["component architectures", "type-checked client scripting", "responsive web design"]
        ),
        (
            "embedded_systems",
            "Low-Level Bare Metal & Microcontroller Firmware Developer",
            "Responsible for deterministic real-time executive loops, peripheral register manipulation, "
            "memory-constrained target boards, and hardware protocol bus communication.",
            ["bare metal programming", "real-time executive", "peripheral bus communication"]
        ),
        (
            "mobile_ios",
            "Native Apple Mobile Experience Developer",
            "Craft fluid touch-first consumer mobile applications for iOS devices using modern declarative view syntax, "
            "reactive data bindings, local persistent device datastores, and Apple platform standards.",
            ["declarative mobile views", "reactive data binding", "device local storage"]
        ),
        (
            "data_engineering",
            "Distributed Event Streaming & Analytical Lakehouse Architect",
            "Orchestrate high-throughput distributed commit logs, large-scale columnar analytical partitions, "
            "and scheduled batch graph transformations for downstream enterprise consumers.",
            ["distributed commit logs", "columnar storage", "batch data workflows"]
        ),
        (
            "systems_rust",
            "Memory-Safe Concurrent Systems Programmer",
            "Engineer safe, zero-cost abstraction low-level network daemons with strict compile-time ownership guarantees, "
            "asynchronous task reactors, and high-performance socket polling.",
            ["zero-cost abstractions", "ownership semantics", "asynchronous reactors"]
        )
    ]

    for p_dom, p_title, p_desc, p_skills in paraphrase_templates:
        for i in range(10):
            jobs.append({
                "id": job_id,
                "title": f"{p_title} ({i+1})",
                "company": f"Paraphrase Venture {job_id}",
                "domain": p_dom,
                "category": "paraphrase_synonym",
                "seniority": "Senior",
                "description": p_desc + f" Position requires 4+ years in {p_skills[0]} and {p_skills[1]}.",
                "key_skills": p_skills
            })
            job_id += 1

    # Category 3: Keyword Distractors (80 jobs)
    # High exact keyword overlap with resume terms, but WRONG ROLE / NON-ENGINEERING!
    distractor_templates = [
        # (title, skills_borrowed, desc, actual_discipline)
        (
            "Technical Talent Recruiter - Python & FastAPI Sourcing",
            ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "Seeking an energetic Technical Recruiter to screen candidate resumes for Python and FastAPI engineering positions. "
            "You will source senior backend engineers with PostgreSQL and Docker experience, coordinate interview loops, and negotiate offers.",
            "recruiting_hr"
        ),
        (
            "Enterprise Account Executive - Kubernetes & Cloud Platforms",
            ["AWS", "Kubernetes", "Docker", "Terraform"],
            "Drive enterprise sales quotas for our Kubernetes and AWS infrastructure SaaS platform. "
            "Meet with CTOs to demonstrate Docker container optimization and Terraform cost-cutting benefits. No coding required.",
            "sales_executive"
        ),
        (
            "Technical Documentation Specialist - React & Next.js Frameworks",
            ["React", "Next.js", "TypeScript", "Tailwind CSS"],
            "Write public-facing developer tutorials, API documentation, and changelogs for our React and Next.js open source tools. "
            "Collaborate with marketing and design to produce clean TypeScript markdown guides.",
            "technical_writing"
        ),
        (
            "Sales Development Representative - Big Data & Apache Kafka",
            ["Kafka", "Spark", "PostgreSQL", "Snowflake"],
            "Cold call enterprise data leaders to pitch our Apache Kafka and Spark acceleration tools. "
            "Qualify leads who currently query PostgreSQL or Snowflake databases.",
            "sales_sdr"
        ),
        (
            "Executive Administrative Assistant - Cloud & AI Engineering",
            ["Python", "PyTorch", "AWS", "Machine Learning"],
            "Provide executive support to the VP of Machine Learning. Maintain calendars, book travel to PyTorch and AWS summits, "
            "and expense Python developer equipment.",
            "administrative"
        ),
        (
            "IT Procurement & Licensing Coordinator (Docker & Azure)",
            [".NET", "C#", "Azure", "Docker"],
            "Manage enterprise software vendor agreements for Azure subscriptions, Docker container licenses, and Microsoft .NET toolkits. "
            "Negotiate volume discounts and track renewals.",
            "procurement"
        ),
        (
            "Product Marketing Manager - Embedded Systems & C++",
            ["C++", "Linux", "RTOS", "Firmware"],
            "Develop product positioning, whitepapers, and launch webinars for our automotive C++ and RTOS firmware testing product suite. "
            "Attend international consumer electronics conferences.",
            "marketing"
        ),
        (
            "Course Instructor & Lab Assistant - QA & Web Testing",
            ["Playwright", "Selenium", "Python", "PyTest"],
            "Grade student homework assignments, demonstrate Playwright and Selenium basics on Zoom, and maintain course Discord for QA testing students.",
            "education"
        )
    ]

    for d_title, d_skills, d_desc, d_disc in distractor_templates:
        for i in range(10):
            jobs.append({
                "id": job_id,
                "title": f"{d_title} ({i+1})",
                "company": f"Distractor Corp {job_id}",
                "domain": d_disc,
                "category": "keyword_distractor",
                "seniority": "Mid-Level",
                "description": d_desc,
                "key_skills": d_skills
            })
            job_id += 1

    # Category 4: Adjacent Cross-Domain Technical Roles (80 jobs)
    adjacent_templates = [
        ("data_engineering", "Data Infrastructure SRE", ["Python", "Kubernetes", "Kafka", "Linux", "Docker"]),
        ("backend_python", "Data Services Platform Engineer", ["Python", "FastAPI", "SQL", "PostgreSQL", "Spark"]),
        ("frontend_web", "Fullstack UI Integrator", ["React", "TypeScript", "Node.js", "REST API", "Tailwind CSS"]),
        ("devops_cloud", "Cloud Security Systems Engineer", ["AWS", "Terraform", "Security", "Linux", "Docker"]),
        ("machine_learning", "Data Platform ML Integrator", ["Python", "PyTorch", "Spark", "SQL", "Docker"]),
        ("enterprise_java", "Backend Services & Event Engineer", ["Java", "Kafka", "PostgreSQL", "Docker", "Microservices"]),
        ("qa_automation", "Fullstack Test Automation Developer", ["Python", "TypeScript", "Playwright", "CI/CD", "Docker"]),
        ("distributed_go", "Cloud Infrastructure Go Engineer", ["Go", "Kubernetes", "Docker", "Linux", "gRPC"])
    ]

    for a_dom, a_title, a_skills in adjacent_templates:
        for i in range(10):
            jobs.append({
                "id": job_id,
                "title": f"{a_title} ({i+1})",
                "company": f"Adjacent Enterprises {job_id}",
                "domain": a_dom,
                "category": "adjacent_cross_domain",
                "seniority": "Senior",
                "description": f"Exciting hybrid opportunity for a {a_title} possessing experience with {', '.join(a_skills)}.",
                "key_skills": a_skills
            })
            job_id += 1

    # Category 5: Disjoint Domain Postings (80 jobs to make 560 total)
    disjoint_templates = [
        ("hospitality", "Executive Pastry Chef", ["Pastry", "Baking", "Culinary", "Menu Planning", "Food Safety"], "High-end restaurant seeking executive pastry chef."),
        ("construction", "Civil Structural Project Engineer", ["AutoCAD", "Concrete", "Structural Engineering", "Building Codes", "Site Inspection"], "Manage commercial construction sites and structural blueprints."),
        ("finance_tax", "Senior Corporate Tax Accountant", ["Tax Compliance", "GAAP", "Auditing", "IRS", "Financial Reporting"], "Prepare federal and multi-state corporate tax filings."),
        ("healthcare", "Clinical Research Nurse Coordinator", ["Patient Care", "Clinical Trials", "GCP", "Phlebotomy", "Protocol Compliance"], "Coordinate oncology drug trials and patient monitoring."),
        ("legal", "Corporate Intellectual Property Paralegal", ["Patent Filing", "Trademark", "Legal Research", "Contract Review", "USPTO"], "Draft patent prosecution forms and manage IP trademark docket."),
        ("logistics", "Freight Logistics & Fleet Dispatcher", ["Route Planning", "DOT Compliance", "Fleet Management", "Dispatch", "Supply Chain"], "Coordinate interstate trucking freight movements and load dispatch."),
        ("real_estate", "Commercial Real Estate Leasing Broker", ["Tenant Representation", "Lease Negotiation", "Property Valuation", "Cold Calling", "Closing"], "Represent landlords in commercial class-A office leasing."),
        ("education", "Elementary School Science Teacher", ["Curriculum Development", "Classroom Management", "STEM", "Lesson Planning", "Student Assessment"], "Teach 4th grade STEM curriculum and laboratory experiments.")
    ]

    for d_dom, d_title, d_skills, d_desc in disjoint_templates:
        for i in range(10):
            jobs.append({
                "id": job_id,
                "title": f"{d_title} ({i+1})",
                "company": f"Disjoint Global {job_id}",
                "domain": d_dom,
                "category": "disjoint_irrelevant",
                "seniority": "Senior",
                "description": f"{d_desc} Seeking candidates with expertise in {', '.join(d_skills[:3])}.",
                "key_skills": d_skills
            })
            job_id += 1

    jobs_path = os.path.join(DATA_DIR, "jobs.json")
    with open(jobs_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    print(f"[+] Wrote {len(jobs)} jobs to {jobs_path}")

    # 3. Generate Independent Ground Truth Relevance Matrix
    # 28 Resumes x 560 Jobs = 15,680 pairs
    # Explicit Human/Ontology Taxonomy Rules:
    # - Grade 3 (Highly Relevant):
    #     * Canonical match on same primary domain
    #     * Paraphrase match on same primary domain
    # - Grade 2 (Moderately Relevant):
    #     * Adjacent domain engineering position with high transferable skill alignment
    # - Grade 1 (Marginally Relevant):
    #     * Cross-domain technical with minor auxiliary overlap (e.g. SRE vs Developer)
    # - Grade 0 (Irrelevant):
    #     * Keyword Distractors (Recruiter, Sales, Admin, IT Procurement - completely wrong role!)
    #     * Disjoint non-engineering jobs
    #     * Unrelated engineering disciplines

    gt_path = os.path.join(DATA_DIR, "ground_truth_relevance.csv")
    with open(gt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["resume_id", "job_id", "relevance_grade", "notes"])

        adjacent_matrix = {
            "backend_python": {"data_engineering", "fullstack_general", "nlp_genai", "distributed_go"},
            "frontend_web": {"fullstack_general", "qa_automation", "mobile_react_native"},
            "machine_learning": {"nlp_genai", "data_science", "mlops_platform", "backend_python"},
            "devops_cloud": {"cloud_sre", "cloud_security", "distributed_go"},
            "data_engineering": {"backend_python", "machine_learning", "dba_postgresql", "bi_analytics"},
            "embedded_systems": {"low_latency_cpp", "systems_rust"},
            "mobile_ios": {"mobile_android", "mobile_react_native"},
            "mobile_android": {"mobile_ios", "mobile_react_native"},
            "enterprise_dotnet": {"enterprise_java", "fullstack_general"},
            "cybersecurity": {"cloud_security", "devops_cloud"},
            "fullstack_general": {"frontend_web", "backend_python", "mobile_react_native"},
            "bi_analytics": {"data_science", "data_engineering"},
            "qa_automation": {"frontend_web", "backend_python"},
            "systems_rust": {"low_latency_cpp", "embedded_systems", "distributed_go"},
            "distributed_go": {"systems_rust", "cloud_sre", "backend_python"},
            "cloud_sre": {"devops_cloud", "distributed_go"},
            "nlp_genai": {"machine_learning", "backend_python", "data_science"},
            "low_latency_cpp": {"systems_rust", "embedded_systems"},
            "enterprise_java": {"enterprise_dotnet", "backend_python"},
            "data_science": {"machine_learning", "bi_analytics", "bioinformatics"},
            "mlops_platform": {"machine_learning", "devops_cloud"},
            "dba_postgresql": {"data_engineering", "backend_python"},
            "cloud_security": {"cybersecurity", "devops_cloud"},
            "mobile_react_native": {"frontend_web", "mobile_ios", "mobile_android"},
            "blockchain_web3": {"systems_rust", "backend_python"},
            "bioinformatics": {"data_science", "backend_python"}
        }

        total_pairs = 0
        grade_counts = {0: 0, 1: 0, 2: 0, 3: 0}

        for r in RESUMES:
            r_dom = r["domain"]

            for j in jobs:
                j_dom = j["domain"]
                cat = j["category"]

                # Category-driven ground truth assignment
                if cat == "keyword_distractor":
                    # KEYWORD DISTRACTOR: Non-engineering position that happens to borrow tech buzzwords.
                    # Even if resume contains words in job, this is an unqualified or non-engineering mismatch!
                    if "Technical Writing" in j["title"] and r_dom in ("frontend_web", "backend_python"):
                        grade = 1  # Marginally relevant auxiliary role
                    else:
                        grade = 0  # Completely irrelevant role
                    note = f"Keyword distractor ({cat}) - non-engineering mismatch"

                elif cat == "disjoint_irrelevant":
                    grade = 0
                    note = "Disjoint non-engineering industry"

                elif cat in ("canonical", "paraphrase_synonym"):
                    if r_dom == j_dom:
                        grade = 3  # Perfect domain & role alignment
                        note = f"Primary domain target ({cat})"
                    elif j_dom in adjacent_matrix.get(r_dom, set()):
                        grade = 2  # Adjacent domain
                        note = f"Adjacent engineering domain ({cat})"
                    else:
                        grade = 0  # Unrelated engineering discipline
                        note = "Mismatched engineering discipline"

                elif cat == "adjacent_cross_domain":
                    if r_dom == j_dom:
                        grade = 3
                        note = "Primary domain target (adjacent_cross_domain)"
                    elif j_dom in adjacent_matrix.get(r_dom, set()):
                        grade = 2
                        note = "Adjacent engineering discipline match"
                    else:
                        grade = 1 if r_dom in ("fullstack_general", "devops_cloud") else 0
                        note = "Marginal auxiliary or mismatched domain"

                else:
                    grade = 0
                    note = "Default irrelevant"

                writer.writerow([r["id"], j["id"], grade, note])
                total_pairs += 1
                grade_counts[grade] += 1

    print(f"[+] Wrote {total_pairs} ground truth labels to {gt_path}")
    print(f"[+] Grade distribution: Grade 3: {grade_counts[3]}, Grade 2: {grade_counts[2]}, Grade 1: {grade_counts[1]}, Grade 0: {grade_counts[0]}")

if __name__ == "__main__":
    generate_hard_dataset()
