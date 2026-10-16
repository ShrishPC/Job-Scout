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
    """Guarantees tests never make external network calls and execute swiftly."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setenv("DEMO_MODE", "True")
    from app.core.config import settings
    settings.DEMO_MODE = True

@pytest.fixture(scope="session", autouse=True)
def preserve_active_profile():
    """Restores the user's active resume and cleans test artifacts after test session ends."""
    session = SessionLocal()
    active = session.query(Resume).filter(Resume.is_active == True).first()
    active_id = active.id if active else None
    session.close()
    yield
    session = SessionLocal()
    try:
        session.query(Resume).filter(
            (Resume.filename.like("activate_test_%")) | 
            (Resume.filename.like("test_resume%")) |
            (Resume.filename.like("devon_resume%"))
        ).delete(synchronize_session=False)
        if active_id:
            session.query(Resume).update({Resume.is_active: False})
            restored = session.query(Resume).filter(Resume.id == active_id).first()
            if restored:
                restored.is_active = True
                user = session.query(User).filter(User.id == 1).first()
                if user:
                    user.resume_markdown = restored.resume_markdown
                    user.parsed_data = restored.parsed_data
                    user.embedding = restored.embedding
                    if restored.parsed_data:
                        user.name = restored.parsed_data.get('full_name', user.name)
                        user.email = restored.parsed_data.get('email', user.email)
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()



