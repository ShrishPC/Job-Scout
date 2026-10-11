import pytest
from app.services.llm_service import (
    format_prompt,
    extract_candidate_insights,
    generate_dynamic_tailored_resume,
    generate_dynamic_cover_letter,
    extract_experience_heuristics,
    extract_experience_from_job,
    generate_embedding,
    generate_embeddings_batch,
    get_cached_line_embeddings,
    retrieve_rag_context,
    generate_tailored_resume_service,
    generate_cover_letter_service,
    generate_tailored_resume_stream,
    generate_cover_letter_stream,
    research_company_stream,
    parse_markdown_with_llm,
    set_ai_device,
)
from app.models.models import Job, AIGenerationCache

def test_format_prompt():
    p = format_prompt("You are an assistant.", "Candidate information.")
    assert "You are an assistant." in p
    assert "Candidate information." in p

def test_extract_candidate_insights():
    resume = (
        "# Alex Mercer\n"
        "Email: alex@example.com\n"
        "Skills: Python, FastAPI, Docker, PostgreSQL, Redis, Kubernetes\n"
        "Senior Software Engineer with 6 years experience."
    )
    job_desc = "Seeking a Backend Engineer skilled in Python, FastAPI, Docker, and AWS."
    insights = extract_candidate_insights(resume, job_desc)
    assert insights["name"] == "Alex Mercer"
    assert "Python" in insights["matched_skills"]
    assert "FastAPI" in insights["matched_skills"]
    assert "Docker" in insights["matched_skills"]
    assert len(insights["candidate_skills"]) >= 2

def test_generate_dynamic_tailored_resume():
    resume = "Alex Mercer. Skills: Python, FastAPI, PostgreSQL. 5 years experience."
    job_desc = "Looking for Senior Python Developer with FastAPI and PostgreSQL expertise."
    tailored = generate_dynamic_tailored_resume(resume, "Senior Python Developer", "InnovateTech", job_desc)
    assert "Results-driven Senior Python Developer" in tailored
    assert "InnovateTech" in tailored
    assert "**Suggested Bullets:**" in tailored
    assert "- Architected and deployed" in tailored

def test_generate_dynamic_cover_letter():
    resume = "# Samira Khan\nSkills: Python, Docker, AWS. 4 years experience."
    job_desc = "Backend Engineer skilled in Python and AWS."
    letter = generate_dynamic_cover_letter(resume, "Backend Engineer", "MobileApp Inc.", job_desc)
    assert "Dear Hiring Manager," in letter
    assert "MobileApp Inc." in letter
    assert "Samira Khan" in letter

def test_extract_experience_heuristics():
    assert extract_experience_heuristics("Requires 5+ years of software development experience") == 5
    assert extract_experience_heuristics("Minimum 3 yrs in cloud architecture") == 3
    assert extract_experience_heuristics("No specific duration mentioned") is None

def test_extract_experience_from_job():
    assert extract_experience_from_job("Requires 4+ years of Python") == 4
    assert extract_experience_from_job("No experience mentioned", use_llm=False) == 0
    assert extract_experience_from_job("", use_llm=False) == 0

def test_generate_embedding_and_batch():
    emb = generate_embedding("Senior Software Architect")
    assert isinstance(emb, list)
    assert len(emb) == 384
    
    batch = generate_embeddings_batch(["Python Developer", "React Frontend"])
    assert len(batch) == 2
    assert len(batch[0]) == 384
    assert len(batch[1]) == 384

def test_get_cached_line_embeddings():
    lines = ["Developed scalable backend services", "Deployed Kubernetes clusters"]
    embeddings = get_cached_line_embeddings(lines)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    cached = get_cached_line_embeddings(lines)
    assert len(cached) == 2
    assert cached[0] == embeddings[0]

def test_retrieve_rag_context(db_session):
    import uuid
    uniq_url = f"https://example.com/job/data-eng-{uuid.uuid4().hex[:8]}"
    job = Job(
        title="Staff Data Engineer",
        company="DataStream Corp",
        job_url=uniq_url,
        description="Build scalable ETL pipelines with Python, Kafka, and Snowflake.",
        embedding=generate_embedding("Staff Data Engineer ETL pipelines Python Kafka Snowflake")
    )
    db_session.add(job)
    db_session.commit()

    resume = "Data Engineer with 5 years experience in Python and ETL pipelines."
    job_desc = "Build pipelines with Kafka and Python."
    ctx = retrieve_rag_context(resume, job_desc, db=db_session)
    assert isinstance(ctx, str)
    assert len(ctx) > 0

def test_generate_tailored_resume_and_cover_letter_service(db_session, monkeypatch):
    resume = "Marcus Vance. Skills: Python, Docker, PostgreSQL. 4 years experience."
    job_desc = "Looking for Python Engineer."

    mock_pipeline = lambda prompt, **kwargs: [{"generated_text": "Tailored Summary: Proven Python developer."}]
    monkeypatch.setattr("app.services.llm_service.get_local_llm", lambda *a, **kw: mock_pipeline)
    
    tailored = generate_tailored_resume_service(resume, "Python Engineer", job_desc, db=db_session)
    assert isinstance(tailored, str)
    assert "Tailored Summary" in tailored

    letter = generate_cover_letter_service(resume, "Python Engineer", "TestCo", job_desc, db=db_session)
    assert isinstance(letter, str)
    assert len(letter) > 0

def test_generate_streams_in_demo_mode():
    import app.services.llm_service as llm_svc
    llm_svc.AI_DEVICE = "demo"
    llm_svc.settings.DEMO_MODE = True

    resume = "Alex Mercer. Skills: Python, FastAPI."
    job_desc = "Python Backend Developer."
    
    stream = generate_tailored_resume_stream(resume, "Python Developer", job_desc, company="Acme")
    chunks = list(stream)
    full_text = "".join(chunks)
    assert len(chunks) > 0
    assert "Acme" in full_text

    cl_stream = generate_cover_letter_stream(resume, "Python Developer", "Acme", job_desc)
    cl_chunks = list(cl_stream)
    assert len(cl_chunks) > 0
    assert "Dear Hiring Manager," in "".join(cl_chunks)

def test_research_company_stream(db_session):
    # Prepopulate cache so it tests the streaming cached path without hitting external DuckDuckGo network
    cache = AIGenerationCache(cache_key="company_research_acme_corp", response_text="Acme Corp is a high-tech engineering platform.")
    db_session.add(cache)
    db_session.commit()

    stream = research_company_stream("Acme Corp", db=db_session)
    chunks = list(stream)
    assert len(chunks) > 0
    assert "Acme Corp" in "".join(chunks)

def test_refine_stream_demo_mode():
    import app.services.llm_service as llm_svc
    from app.services.llm_service import refine_stream
    llm_svc.AI_DEVICE = "demo"
    llm_svc.settings.DEMO_MODE = True

    shortened = list(refine_stream("Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.", "Make it shorter"))
    assert len(shortened) > 0

    metric_refined = list(refine_stream("Improved latency by 38% and scaled 10x.", "Add more metrics"))
    assert "52%" in "".join(metric_refined)

    exec_refined = list(refine_stream("Results-driven engineer Specializing in microservices.", "More executive tone"))
    assert "Strategic and visionary" in "".join(exec_refined)

def test_parse_markdown_with_llm():
    from app.core.config import settings
    settings.DEMO_MODE = True
    parsed = parse_markdown_with_llm("# Candidate Name\nSkills: Python")
    assert "full_name" in parsed
    assert "skills" in parsed

def test_set_ai_device():
    set_ai_device("cpu")

