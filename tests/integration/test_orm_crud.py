import pytest
from app.models.models import User, Resume, Job, UserJobMatch
from app.core.database import SessionLocal, engine

def test_int_01_orm_crud_and_pool_health(db_session):
    """
    INT-01: API <-> Postgres CRUD through the ORM; verify connection pool does not leak sessions.
    """
    initial_checkedout = engine.pool.checkedout()

    # Create test job
    job = Job(
        title="Test Integration Engineer",
        company="Integration Corp",
        description="Testing ORM CRUD and connection pooling health.",
        location="Remote",
        salary="$120k",
        job_url="https://example.com/jobs/test-orm-int",
        embedding=[0.05] * 384,
        experience_required=3,
        workplace_type="remote"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None
    job_id = job.id

    # Read
    queried = db_session.query(Job).filter(Job.id == job_id).first()
    assert queried is not None
    assert queried.title == "Test Integration Engineer"
    assert len(queried.embedding) == 384

    # Update
    queried.salary = "$135k"
    db_session.commit()
    
    updated = db_session.query(Job).filter(Job.id == job_id).first()
    assert updated.salary == "$135k"

    # Delete
    db_session.delete(updated)
    db_session.commit()

    deleted = db_session.query(Job).filter(Job.id == job_id).first()
    assert deleted is None

    # Verify session pool checkout remains stable
    assert engine.pool.checkedout() <= initial_checkedout + 1
