import pytest
import os
import sys
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Ensure backend directory is in path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.core.database import SessionLocal, engine
from app.models.models import Base, User, Resume, Job, UserJobMatch, AIGenerationCache

@pytest.fixture(scope="session")
def client():
    """Returns a FastAPI TestClient configured for offline testing."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="function")
def db_session():
    """Provides a clean database session for test execution."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch):
    """Guarantees tests never make external network calls."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
