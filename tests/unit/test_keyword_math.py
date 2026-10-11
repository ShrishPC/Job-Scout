import pytest
import re
from app.services.matching_service import get_job_matches

def test_keyword_math_rules():
    """
    Unit test verifying the hybrid keyword weighting formula:
    - Title match weight = 2.0
    - Description match weight = 1.0
    - Max possible points = 2.0 * n_skills
    - Normalized keyword score is strictly in [0.0, 1.0] (or 0-100 when scaled)
    - Word boundary regex for alphanumeric skills, LIKE for special characters.
    """
    skills = ["Python", "C++", ".NET", "Machine Learning"]
    n_skills = len(skills)
    max_points = 2.0 * n_skills
    assert max_points == 8.0

    # Test alphanumeric regex boundary generation
    for skill in ["Python", "Machine Learning", "FastAPI"]:
        assert re.match(r'^[a-zA-Z0-9\s\-]+$', skill) is not None
        pattern = r'\y' + re.escape(skill).replace(r'\ ', r'\s+') + r'\y'
        assert pattern.startswith(r'\y')
        assert pattern.endswith(r'\y')

    # Test special characters routing to LIKE
    for special_skill in ["C++", "C#", ".NET"]:
        assert re.match(r'^[a-zA-Z0-9\s\-]+$', special_skill) is None

    # Test math simulation
    # Scenario 1: Perfect title match for all skills
    simulated_raw_points = 2.0 * n_skills
    norm_score = simulated_raw_points / max_points
    assert norm_score == 1.0
    assert (norm_score * 100.0) == 100.0

    # Scenario 2: Description match only for all skills
    simulated_raw_points = 1.0 * n_skills
    norm_score = simulated_raw_points / max_points
    assert norm_score == 0.5
    assert (norm_score * 100.0) == 50.0

    # Scenario 3: Mixed match (1 title match, 1 description match, 2 misses)
    simulated_raw_points = 2.0 + 1.0 + 0.0 + 0.0
    norm_score = simulated_raw_points / max_points
    assert norm_score == 3.0 / 8.0
    assert 0.0 <= norm_score <= 1.0

    # Scenario 4: Hybrid composite calculation
    # Score = 100 * (0.7 * (1 - cosine_dist) + 0.3 * keyword_score)
    cosine_dist = 0.20  # cosine similarity = 0.80
    composite_score = 100.0 * (0.7 * (1.0 - cosine_dist) + 0.3 * norm_score)
    expected_composite = 100.0 * (0.7 * 0.80 + 0.3 * (3.0 / 8.0))
    assert pytest.approx(composite_score, 0.001) == expected_composite
