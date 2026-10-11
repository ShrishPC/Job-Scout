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

