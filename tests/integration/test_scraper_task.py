import pytest
import sys
import os
from unittest.mock import MagicMock

# Add scraper directory to path
possible_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scraper")),
    "/app/scraper",
    "/scraper"
]
for p in possible_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from app.models.models import Job
from tasks import scrape_and_process_jobs

def test_int_02_scraper_dedup_and_embedding_dimension(db_session, monkeypatch):
    """
    INT-02: Celery task with a stub scraper: dedup skips existing job_url values;
    new embeddings stored with dimension 384.
    """
    # 1. Insert an existing job
    existing_url = "https://example.com/jobs/already-indexed-123"
    db_session.query(Job).filter(Job.job_url == existing_url).delete()
    
    existing_job = Job(
        title="Existing Data Engineer",
        company="Legacy Corp",
        description="Already saved description",
        job_url=existing_url,
        embedding=[0.01] * 384
    )
    db_session.add(existing_job)
    db_session.commit()

    # 2. Stub the remote scraper returning 1 duplicate and 1 brand new job
    new_url = "https://example.com/jobs/brand-new-456"
    db_session.query(Job).filter(Job.job_url == new_url).delete()
    db_session.commit()

    stub_discovered = [
        {
            "title": "Existing Data Engineer",
            "company": "Legacy Corp",
            "description": "Duplicate job that should be filtered out",
            "location": "Remote",
            "job_url": existing_url,
            "date_posted": "Yesterday",
            "salary": "$100k"
        },
        {
            "title": "Fresh AI Engineer",
            "company": "NextGen AI",
            "description": "5+ yrs req experience with Python and pgvector.",
            "location": "San Francisco, CA",
            "job_url": new_url,
            "date_posted": "Today",
            "salary": "$160k"
        }
    ]

    import tasks
    monkeypatch.setattr(tasks, "scrape_remoteok_jobs", lambda kw, lim: stub_discovered)

    # Execute Celery task synchronously via .apply()
    async_res = scrape_and_process_jobs.apply(kwargs={
        "keyword": "AI", 
        "location": "Remote", 
        "limit": 2, 
        "source": "remoteok"
    })
    result = async_res.result

    assert result["status"] == "success"
    # Only the fresh job should have been added
    assert result["new_jobs"] == 1

    # Verify newly saved job in database has 384 dimensions
    fresh_job = db_session.query(Job).filter(Job.job_url == new_url).first()
    assert fresh_job is not None
    assert fresh_job.title == "Fresh AI Engineer"
    assert len(fresh_job.embedding) == 384
    assert fresh_job.experience_required == 5

    # Cleanup
    db_session.delete(fresh_job)
    db_session.delete(existing_job)
    db_session.commit()
