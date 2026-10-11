import pytest
import json
import os
from app.services.llm_service import extract_experience_heuristics
from app.services.llm_fallback import extract_structured_data_fallback

# Load the 50 synthetic resumes dataset
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_resumes_50.json"))
with open(DATA_PATH, "r", encoding="utf-8") as f:
    SYNTHETIC_RESUMES = json.load(f)

@pytest.mark.parametrize("input_text,expected_years", [
    ("5+ yrs req for this position", 5),
    ("Requires 3 years of practical experience", 3),
    ("Minimum 10 yrs experience in database administration", 10),
    ("7 years of experience in distributed systems", 7),
    ("Candidate must possess at least 4 years experience", 4),
    ("2+ years experience building web apps", 2),
    ("8-10 years experience preferred", 8),
])
def test_utc_04_experience_regex_variations(input_text, expected_years):
    """
    UTC-04: Test regex/heuristic parser extracts years of experience from varied phrases.
    """
    assert extract_experience_heuristics(input_text) == expected_years

@pytest.mark.parametrize("item", SYNTHETIC_RESUMES, ids=[f"resume_{r['id']}" for r in SYNTHETIC_RESUMES])
def test_utc_04_synthetic_dataset_parsing(item):
    """
    UTC-04: Parameterized test verifying deterministic heuristic parser across 50 diverse resume strings.
    """
    text = item["text"]
    expected_exp = item["expected_experience"]
    expected_skills = item["expected_skills"]

    # 1. Experience extraction
    extracted_exp = extract_experience_heuristics(text)
    assert extracted_exp == expected_exp, f"Failed on resume {item['id']}: expected {expected_exp}, got {extracted_exp}"

    # 2. Skill extraction without LLM
    fallback_data = extract_structured_data_fallback(text)
    extracted_skills = fallback_data["skills"]

    for expected_skill in expected_skills:
        assert expected_skill in extracted_skills, \
            f"Resume {item['id']}: Expected skill '{expected_skill}' not found in {extracted_skills}"
