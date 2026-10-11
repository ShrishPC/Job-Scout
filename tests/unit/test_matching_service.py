import os
import pytest
from unittest.mock import MagicMock
from sqlalchemy import text
from app.services.matching_service import get_job_matches
from app.core.database import SessionLocal


def test_matching_service_applies_ef_search_setting(monkeypatch):
    """
    Verifies that get_job_matches sets SET LOCAL hnsw.ef_search
    with the value from HNSW_EF_SEARCH (default 400).
    """
    monkeypatch.setenv("HNSW_EF_SEARCH", "400")
    monkeypatch.setenv("HYBRID_MODE", "two_stage")

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.execute.return_value = []

    dummy_vector = [0.0] * 384
    get_job_matches(mock_db, dummy_vector, limit=10, skip=0)

    # Assert SET LOCAL was called
    executed_statements = [str(call.args[0]) for call in mock_db.execute.call_args_list]
    set_local_calls = [s for s in executed_statements if "SET LOCAL hnsw.ef_search" in s]
    assert len(set_local_calls) >= 1
    assert "SET LOCAL hnsw.ef_search = 400;" in set_local_calls[0]


def test_matching_service_ef_search_never_below_candidate_k(monkeypatch):
    """
    Verifies that ef_search is clamped to at least candidate_k.
    If HNSW_EF_SEARCH is 400 but candidate_k is 500, ef_search must be 500.
    """
    monkeypatch.setenv("HNSW_EF_SEARCH", "400")
    monkeypatch.setenv("HYBRID_MODE", "two_stage")

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.execute.return_value = []

    dummy_vector = [0.0] * 384
    get_job_matches(mock_db, dummy_vector, limit=10, skip=0, candidate_k=500)

    executed_statements = [str(call.args[0]) for call in mock_db.execute.call_args_list]
    set_local_calls = [s for s in executed_statements if "SET LOCAL hnsw.ef_search" in s]
    assert len(set_local_calls) >= 1
    assert "SET LOCAL hnsw.ef_search = 500;" in set_local_calls[0]


def test_real_db_set_local_ef_search():
    """
    Verifies against the live PostgreSQL database that SET LOCAL hnsw.ef_search
    actually applies to the transaction and can be read back via SHOW.
    """
    db = SessionLocal()
    try:
        db.execute(text("SET LOCAL hnsw.ef_search = 450;"))
        res = db.execute(text("SHOW hnsw.ef_search;")).scalar()
        assert res == "450"
    finally:
        db.close()
