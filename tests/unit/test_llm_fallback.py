import pytest
from unittest.mock import patch, MagicMock
import app.services.llm_service as llm_service
from app.services.llm_service import get_local_llm, parse_markdown_with_llm

def test_utc_05_primary_oom_falls_back_to_tinyllama(monkeypatch):
    """
    UTC-05: Simulate OOM on primary model (Llama-3.2-3B), assert TinyLlama is loaded.
    """
    # Reset global state
    llm_service.local_llm = None
    llm_service.LLM_DEVICE = None
    llm_service.ACTIVE_LLM_MODEL_NAME = None

    calls = []

    def mock_pipeline(task, model=None, **kwargs):
        calls.append(model)
        if "Llama-3.2" in model:
            raise RuntimeError("CUDA out of memory / simulated CPU OOM")
        # TinyLlama loads successfully
        mock_instance = MagicMock()
        mock_instance.return_value = [{"generated_text": '{"full_name": "Fallback Candidate"}'}]
        return mock_instance

    monkeypatch.setattr(llm_service, "pipeline", mock_pipeline)
    
    loaded_llm = get_local_llm()
    assert loaded_llm is not None
    assert "TinyLlama/TinyLlama-1.1B-Chat-v1.0" in calls
    assert llm_service.ACTIVE_LLM_MODEL_NAME == "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

def test_utc_05_both_models_fail_uses_heuristic_fallback(monkeypatch):
    """
    UTC-05: Simulate both primary and TinyLlama failing, assert heuristic path, no crash.
    """
    from app.core.config import settings
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    llm_service.local_llm = None

    def mock_pipeline_always_fail(task, model=None, **kwargs):
        raise RuntimeError(f"Simulated fatal error loading {model}")

    monkeypatch.setattr(llm_service, "pipeline", mock_pipeline_always_fail)

    sample_resume = "Sarah Connor\nsarah@example.com\n555-9090\nSkilled in Python, SQL, and Docker with 5 years experience."
    
    result = parse_markdown_with_llm(sample_resume)
    
    assert result is not None
    assert result["email"] == "sarah@example.com"
    assert "Python" in result["skills"]
    assert "SQL" in result["skills"]
    assert "Docker" in result["skills"]
