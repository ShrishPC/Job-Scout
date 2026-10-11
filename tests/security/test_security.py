import pytest
import io
import os
from app.models.models import Job, UserJobMatch, User
from app.core.config import settings

def test_sec_01_sql_injection_treated_as_data(client, db_session):
    """
    SEC-01: Verify SQL injection payloads in search_keyword and skills are safely parameterized.
    """
    # Malicious search keyword payload
    injection_kw = "' OR '1'='1' --; DROP TABLE jobs;"
    payload = {
        "embedding": [0.0] * 384,
        "limit": 5,
        "skip": 0,
        "search_keyword": injection_kw
    }
    
    # Should execute safely without database error or syntax exception
    response = client.post("/jobs/matches", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_sec_02_admin_endpoint_authorization(client, monkeypatch):
    """
    SEC-02: Admin endpoints return 503 when ADMIN_API_KEY is unset and 403 when key is wrong.
    """
    # 1. Unset key -> 503
    monkeypatch.setenv("ADMIN_API_KEY", "")
    res_unset = client.get("/api/admin/stats")
    assert res_unset.status_code == 503
    assert "Admin API key not configured" in res_unset.text

    # 2. Configured key with wrong X-Admin-Key -> 403
    monkeypatch.setenv("ADMIN_API_KEY", "correct_secret_key_123")
    res_wrong = client.get("/api/admin/stats", headers={"X-Admin-Key": "wrong_key"})
    assert res_wrong.status_code == 403
    assert "Invalid or missing Admin API Key" in res_wrong.text

    # 3. Configured key with valid X-Admin-Key -> 200
    res_valid = client.get("/api/admin/stats", headers={"X-Admin-Key": "correct_secret_key_123"})
    assert res_valid.status_code == 200

def test_sec_03_upload_validation_and_cors(client):
    """
    SEC-03: Oversized upload -> 413, wrong extension -> 400, CORS blocks unauthorized origin.
    """
    # 1. Unsupported extension (.exe) -> 400
    bad_file = io.BytesIO(b"dummy binary")
    res_bad_ext = client.post(
        "/resume/parse", 
        files={"file": ("malicious.exe", bad_file, "application/octet-stream")}
    )
    assert res_bad_ext.status_code == 400
    assert "Unsupported file type" in res_bad_ext.text

    # 2. Oversized upload (> 10MB) -> 413
    big_file = io.BytesIO(b"0" * (10 * 1024 * 1024 + 1024))
    res_oversize = client.post(
        "/resume/parse", 
        files={"file": ("huge_resume.pdf", big_file, "application/pdf")}
    )
    assert res_oversize.status_code == 413
    assert "File too large" in res_oversize.text

    # 3. CORS check: non-whitelisted origin
    res_cors = client.get("/", headers={"Origin": "http://unauthorized-attacker-site.com"})
    allow_origin = res_cors.headers.get("access-control-allow-origin")
    assert allow_origin != "http://unauthorized-attacker-site.com"

def test_sec_04_kanban_status_persistence(client, db_session):
    """
    SEC-04: Kanban status change persists across a new session.
    """
    # Ensure job exists
    job = db_session.query(Job).first()
    if not job:
        job = Job(title="Kanban Test Job", company="Kanban Corp", job_url="https://example.com/kanban-1", embedding=[0.0] * 384)
        db_session.add(job)
        db_session.commit()

    # Move to 'applied'
    res_applied = client.post("/jobs/interest", json={"job_id": job.id, "status": "applied"})
    assert res_applied.status_code == 200

    # Query from a clean board retrieval
    board = client.get("/jobs/board").json()
    matched_entry = next((item for item in board if item["id"] == job.id), None)
    assert matched_entry is not None
    assert matched_entry["status"] == "applied"

    # Move to 'interviewing'
    res_interview = client.post("/jobs/interest", json={"job_id": job.id, "status": "interviewing"})
    assert res_interview.status_code == 200

    board_updated = client.get("/jobs/board").json()
    matched_updated = next((item for item in board_updated if item["id"] == job.id), None)
    assert matched_updated is not None
    assert matched_updated["status"] == "interviewing"
