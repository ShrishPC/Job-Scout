import pytest
import hashlib
from app.models.models import Resume, User, Job, AIGenerationCache
from app.core.config import settings

def test_int_03_and_04_ai_generate_streaming_and_caching(client, db_session, monkeypatch):
    """
    INT-03: /ai/generate streams chunks (multiple chunks arrive, content-type text/plain).
    INT-04: /ai/generate caches: second identical call returns from AIGenerationCache.
    """
    # 1. Ensure active resume exists
    active_resume = db_session.query(Resume).filter(Resume.is_active == True).first()
    if not active_resume:
        active_resume = Resume(
            filename="test_active.md",
            resume_markdown="Professional Software Engineer with 5 years experience in Python and FastAPI.",
            is_active=True,
            embedding=[0.02] * 384
        )
        db_session.add(active_resume)
        db_session.commit()
        db_session.refresh(active_resume)

    # Enable DEMO_MODE for lightning-fast deterministic token generation
    monkeypatch.setattr(settings, "DEMO_MODE", True)

    payload = {
        "mode": "tailor",
        "custom_job_description": "Seeking Python Backend Architect with experience in microservices and PostgreSQL.",
        "custom_job_title": "Backend Architect",
        "custom_company": "Test Company"
    }

    # Clean existing cache for this exact input
    inputs_str = f"resume_{active_resume.id}_job_custom_{payload['custom_job_title']}_{payload['custom_company']}_{payload['custom_job_description']}_{payload['mode']}"
    expected_cache_key = hashlib.sha256(inputs_str.encode('utf-8')).hexdigest()
    db_session.query(AIGenerationCache).filter(AIGenerationCache.cache_key == expected_cache_key).delete()
    db_session.commit()

    # FIRST CALL (Cold - generates stream and populates cache)
    res_cold = client.post("/ai/generate", json=payload)
    assert res_cold.status_code == 200
    assert "text/plain" in res_cold.headers["content-type"]
    cold_content = res_cold.text
    assert len(cold_content) > 20

    # Verify cache entry was persisted in PostgreSQL
    cached_row = db_session.query(AIGenerationCache).filter(AIGenerationCache.cache_key == expected_cache_key).first()
    assert cached_row is not None
    assert cached_row.response_text.strip() == cold_content.strip()

    # SECOND CALL (Warm - cached hit)
    res_cached = client.post("/ai/generate", json=payload)
    assert res_cached.status_code == 200
    assert "text/plain" in res_cached.headers["content-type"]
    assert res_cached.text.strip() == cold_content.strip()

    # Cleanup
    db_session.query(AIGenerationCache).filter(AIGenerationCache.cache_key == expected_cache_key).delete()
    db_session.commit()
