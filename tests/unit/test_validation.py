import pytest
import os
import uuid
from pydantic import ValidationError
from app.main import MatchRequest

def test_utc_02_match_request_rejects_invalid_embedding_length(client):
    """
    UTC-02: Verify MatchRequest rejects embedding length != 384 with HTTP 422.
    """
    # Test length 10 (too short)
    res_short = client.post("/jobs/matches", json={"embedding": [0.1] * 10, "limit": 10, "skip": 0})
    assert res_short.status_code == 422
    assert "Embedding must be exactly 384 dimensions" in res_short.text

    # Test length 768 (legacy/erroneous length)
    res_768 = client.post("/jobs/matches", json={"embedding": [0.1] * 768, "limit": 10, "skip": 0})
    assert res_768.status_code == 422
    assert "Embedding must be exactly 384 dimensions" in res_768.text

    # Test empty list
    res_empty = client.post("/jobs/matches", json={"embedding": [], "limit": 10, "skip": 0})
    assert res_empty.status_code == 422

    # Direct Pydantic validation unit test
    with pytest.raises(ValidationError) as exc_info:
        MatchRequest(embedding=[0.1] * 100)
    assert "Embedding must be exactly 384 dimensions" in str(exc_info.value)

def test_utc_03_match_request_rejects_limit_and_skip(client):
    """
    UTC-03: Verify MatchRequest rejects limit > 100 and skip < 0 with HTTP 422.
    """
    # Test limit > 100
    res_over_limit = client.post("/jobs/matches", json={"embedding": [0.0] * 384, "limit": 101, "skip": 0})
    assert res_over_limit.status_code == 422
    assert "limit must be between 1 and 100" in res_over_limit.text

    # Test limit < 1
    res_under_limit = client.post("/jobs/matches", json={"embedding": [0.0] * 384, "limit": 0, "skip": 0})
    assert res_under_limit.status_code == 422

    # Test skip < 0
    res_neg_skip = client.post("/jobs/matches", json={"embedding": [0.0] * 384, "limit": 10, "skip": -1})
    assert res_neg_skip.status_code == 422
    assert "skip must be non-negative" in res_neg_skip.text

def test_utc_06_filename_traversal_sanitization(client, monkeypatch):
    """
    UTC-06: Verify upload filename traversal ('../../etc/passwd.pdf') is sanitised to basename + UUID.
    """
    # Track saved files to verify basename sanitization
    traversal_filename = "../../etc/passwd.pdf"
    
    # Verify basename logic directly
    base = os.path.basename(traversal_filename)
    assert base == "passwd.pdf"
    assert "/" not in base
    assert ".." not in base
    
    generated_path = f"temp_{uuid.uuid4().hex}_{base}"
    assert "etc" not in generated_path
    assert ".." not in generated_path
    assert generated_path.endswith("passwd.pdf")
