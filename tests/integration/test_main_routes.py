import pytest
import io
import fitz
import docx
from app.models.models import Job, Resume, User, UserJobMatch, AIGenerationCache
from app.services.llm_service import generate_embedding

def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Job Scout" in res.json()["message"]

def test_jobs_board_and_interest(client, db_session):
    # Create test job directly in DB with unique URL
    import uuid
    uniq_url = f"https://example.com/job/cloud-eng-{uuid.uuid4().hex[:8]}"
    job = Job(
        title="Senior Cloud Engineer",
        company="CloudScale Inc",
        location="Remote",
        job_url=uniq_url,
        description="Kubernetes, Terraform, AWS, Docker infrastructure.",
        workplace_type="Remote",
        embedding=generate_embedding("Senior Cloud Engineer Kubernetes Terraform AWS Docker")
    )
    db_session.add(job)
    db_session.commit()


    # 1. Mark interest
    interest_res = client.post("/jobs/interest", json={
        "job_id": job.id,
        "status": "interested"
    })
    assert interest_res.status_code == 200
    assert interest_res.json()["status"] == "success"

    # 2. Get Kanban Board
    board_res = client.get("/jobs/board")
    assert board_res.status_code == 200
    board = board_res.json()
    assert any(item["id"] == job.id and item["status"] == "interested" for item in board)

    # 3. Matches endpoint
    match_payload = {
        "embedding": generate_embedding("Senior Cloud Engineer"),
        "limit": 5,
        "skip": 0,
        "workplace_types": ["Remote"]
    }
    match_res = client.post("/jobs/matches", json=match_payload)
    assert match_res.status_code == 200
    assert len(match_res.json()) >= 1

def test_resumes_crud_and_activation(client, db_session):
    # Upload markdown resume via /resume/parse
    resume_content = (
        "# Devon Vance\n"
        "Email: devon@example.com\n"
        "Phone: 555-0192\n"
        "Skills: AWS, Terraform, Docker, Kubernetes\n"
        "Experience: 8 years in DevOps and cloud engineering."
    )
    files = {
        "file": ("devon_resume.md", io.BytesIO(resume_content.encode("utf-8")), "text/markdown")
    }
    upload_res = client.post("/resume/parse", files=files)
    assert upload_res.status_code == 200
    resume_data = upload_res.json()
    assert "id" in resume_data
    assert resume_data["id"] is not None


    # List Resumes
    list_res = client.get("/resumes")
    assert list_res.status_code == 200
    resumes = list_res.json()
    assert len(resumes) >= 1
    resume_id = resumes[0]["id"]

    # Active resume check
    active_res = client.get("/resume/active")
    assert active_res.status_code == 200

    # Activate Resume
    act_res = client.post(f"/resumes/{resume_id}/activate")
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "success"

    # Fetch User Profile to confirm sync
    user_res = client.get("/user")
    assert user_res.status_code == 200
    assert user_res.json()["has_profile"] is True

    # Export vault resume
    export_res = client.get(f"/resumes/{resume_id}/export?format=pdf")
    assert export_res.status_code == 200
    assert export_res.content.startswith(b"%PDF")

    # Delete Resume
    del_res = client.delete(f"/resumes/{resume_id}")
    assert del_res.status_code == 200

def test_ai_config_endpoint(client):
    # Get config
    get_res = client.get("/ai/config")
    assert get_res.status_code == 200
    config_data = get_res.json()
    assert "device" in config_data

    # Set config to demo mode
    set_res = client.post("/ai/config", json={"device": "demo"})
    assert set_res.status_code == 200
    assert set_res.json()["status"] == "success"
    assert set_res.json()["device"] == "demo"

    # Set config to cpu
    set_cpu = client.post("/ai/config", json={"device": "cpu"})
    assert set_cpu.status_code == 200
    assert set_cpu.json()["device"] == "cpu"

def test_export_document_endpoint(client):
    payload = {
        "title": "Tailored Application",
        "content": "# Summary\nTailored for Python and Redis roles.\n\n- Spearheaded microservices.",
        "mode": "tailor",
        "format": "docx",
        "candidate_name": "Marcus Chen",
        "candidate_email": "marcus@example.com"
    }
    # Test DOCX
    docx_res = client.post("/export/document", json=payload)
    assert docx_res.status_code == 200
    assert docx_res.content.startswith(b"PK\x03\x04")

    # Test PDF
    payload["format"] = "pdf"
    pdf_res = client.post("/export/document", json=payload)
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF")

    # Test TXT
    payload["format"] = "txt"
    txt_res = client.post("/export/document", json=payload)
    assert txt_res.status_code == 200
    assert b"Tailored for Python" in txt_res.content

def test_ats_analyze_and_export_report(client, db_session):
    resume = (
        "Elena Rostova\n"
        "Senior React Engineer with 6 years experience in Next.js, TypeScript, Tailwind, and Jest.\n"
        "Optimized frontend bundle size by 35% and improved LCP by 200ms."
    )
    job_desc = "Seeking React Developer with TypeScript, Next.js, and automated testing experience."
    
    # 1. Run ATS Analyze
    analyze_res = client.post("/ai/ats-analyze", json={
        "resume_text": resume,
        "job_title": "React Developer",
        "job_description": job_desc,
        "company": "FrontEnd Co."
    })
    assert analyze_res.status_code == 200
    ats_data = analyze_res.json()
    assert "overall_score" in ats_data
    assert ats_data["overall_score"] > 40.0

    # 2. Export ATS Report
    export_payload = {
        "ats_data": ats_data,
        "format": "pdf",
        "candidate_name": "Elena Rostova"
    }
    report_res = client.post("/export/ats-report", json=export_payload)
    assert report_res.status_code == 200
    assert report_res.content.startswith(b"%PDF")

def test_admin_cache_clear(client, db_session):
    # Add an entry to cache with unique key
    import uuid
    uniq_key = f"test_cache_{uuid.uuid4().hex}"
    cache = AIGenerationCache(cache_key=uniq_key, response_text="cached output")
    db_session.add(cache)
    db_session.commit()

    # Clear cache via /ai/cache/clear
    res = client.post("/ai/cache/clear")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # Confirm cache is cleared
    remaining = db_session.query(AIGenerationCache).filter(AIGenerationCache.cache_key == uniq_key).first()
    assert remaining is None

def test_admin_stats(client):
    headers = {"X-Admin-Key": "jobscout_admin_k3y_2026"}
    res = client.get("/api/admin/stats", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert "total_jobs" in stats
    assert "system_cpu_usage_percent" in stats

def test_ai_refine_route(client):
    res = client.post("/ai/refine", json={
        "current_text": "Experienced software developer with strong skills in Python.",
        "instruction": "Make it more executive and concise"
    })
    assert res.status_code == 200
    assert len(res.text) > 0

def test_ai_research_route(client, db_session):
    import uuid
    company_name = f"TestCorp_{uuid.uuid4().hex[:6]}"
    cache_entry = AIGenerationCache(cache_key=f"company_research_{company_name.lower().replace(' ', '_')}", response_text="TestCorp builds cloud platforms.")
    db_session.add(cache_entry)
    db_session.commit()

    res = client.post("/ai/research", json={"company": company_name})
    assert res.status_code == 200
    assert len(res.text) > 0

def test_ai_config_routes(client):
    # GET config
    get_res = client.get("/ai/config")
    assert get_res.status_code == 200
    assert "device" in get_res.json()

    # POST config valid demo
    demo_res = client.post("/ai/config", json={"device": "demo"})
    assert demo_res.status_code == 200
    assert demo_res.json()["device"] == "demo"

    # POST config valid cpu
    cpu_res = client.post("/ai/config", json={"device": "cpu"})
    assert cpu_res.status_code == 200
    assert cpu_res.json()["device"] == "cpu"

    # POST config invalid
    err_res = client.post("/ai/config", json={"device": "quantum"})
    assert err_res.status_code in [400, 422]

def test_export_document_formats(client):
    # Test TXT
    txt_res = client.post("/ai/export", json={
        "content": "Professional Summary\nSoftware Engineer with experience.",
        "mode": "tailor",
        "format": "txt"
    })
    assert txt_res.status_code == 200
    assert "attachment" in txt_res.headers.get("content-disposition", "")

    # Test DOCX
    docx_res = client.post("/ai/export", json={
        "content": "Professional Summary\nSoftware Engineer with experience.",
        "mode": "cover_letter",
        "format": "docx",
        "candidate_name": "Alex Mercer",
        "company": "TechCorp"
    })
    assert docx_res.status_code == 200
    assert len(docx_res.content) > 100

    # Test PDF
    pdf_res = client.post("/ai/export", json={
        "content": "Professional Summary\nSoftware Engineer with experience.",
        "mode": "tailor",
        "format": "pdf"
    })
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF")

def test_export_ats_report_formats(client):
    sample_ats = {
        "overall_score": 85.0,
        "job_title": "Python Developer",
        "company": "Tech Corp",
        "summary": "High alignment candidate.",
        "matched_skills": ["Python", "FastAPI"],
        "missing_critical_skills": ["Docker"],
        "score_breakdown": {
            "hard_skills": {"score": 80.0, "weight": 40},
            "experience_level": {"score": 90.0, "weight": 20}
        }
    }
    # DOCX format
    docx_res = client.post("/export/ats-report", json={
        "ats_data": sample_ats,
        "format": "docx",
        "candidate_name": "Devon Vance"
    })
    assert docx_res.status_code == 200
    assert len(docx_res.content) > 100

    # TXT format
    txt_res = client.post("/export/ats-report", json={
        "ats_data": sample_ats,
        "format": "txt",
        "candidate_name": "Devon Vance"
    })
    assert txt_res.status_code == 200
    assert b"ATS Diagnostic Report" in txt_res.content or len(txt_res.content) > 0

def test_vault_resume_export(client, db_session):
    import uuid
    uniq_url = f"https://example.com/job/test-{uuid.uuid4().hex[:6]}"
    resume = Resume(
        filename=f"test_export_{uuid.uuid4().hex[:6]}.pdf",
        resume_markdown="# Candidate Profile\nSkills: Python, FastAPI\nExperience: 5 years",
        parsed_data={"full_name": "Test Candidate", "skills": ["Python", "FastAPI"]},
        is_active=True
    )
    db_session.add(resume)
    db_session.commit()

    # Export PDF
    pdf_res = client.get(f"/resumes/{resume.id}/export?format=pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF")

    # Export DOCX
    docx_res = client.get(f"/resumes/{resume.id}/export?format=docx")
    assert docx_res.status_code == 200
    assert len(docx_res.content) > 100

    # Delete resume
    del_res = client.delete(f"/resumes/{resume.id}")
    assert del_res.status_code == 200

def test_scrape_trigger_and_task_status(client, monkeypatch):
    class MockTask:
        id = "mock-task-id-12345"
    monkeypatch.setattr("app.main.celery_app.send_task", lambda *a, **kw: MockTask())
    
    # Test /jobs/scrape POST
    res = client.post("/jobs/scrape", json={"keyword": "Python Developer", "location": "Remote", "limit": 5, "source": "linkedin"})
    assert res.status_code == 200
    assert "task_ids" in res.json()
    assert res.json()["task_ids"] == ["mock-task-id-12345"]

    # Test /tasks/{task_id} GET
    t_res = client.get("/tasks/mock-task-id-12345")
    assert t_res.status_code == 200
    assert "state" in t_res.json()

    # Test /tasks/batch-status POST
    b_res = client.post("/tasks/batch-status", json={"task_ids": ["mock-task-id-12345"]})
    assert b_res.status_code == 200
    assert "tasks" in b_res.json()

def test_resume_upload_and_parse_endpoint(client, db_session):
    content = b"Candidate Name: Devon Vance\nTitle: Senior Python Engineer\nSkills: Python, FastAPI, Docker\nExperience: 5 years at TechCorp."
    files = {"file": ("test_resume.txt", content, "text/plain")}
    res = client.post("/resume/parse", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "parsed_json" in data
    assert "id" in data

def test_get_user_profile_and_activate(client, db_session):
    # GET user profile
    u_res = client.get("/user")
    assert u_res.status_code == 200

    # Add resume and activate
    import uuid
    res_obj = Resume(
        filename=f"activate_test_{uuid.uuid4().hex[:6]}.pdf",
        resume_markdown="# Active Dev\nSkills: Python",
        parsed_data={"full_name": "Active Dev", "skills": ["Python"]},
        is_active=False
    )
    db_session.add(res_obj)
    db_session.commit()

    act_res = client.post(f"/resumes/{res_obj.id}/activate")
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "success"


