import pytest
from sqlalchemy import text
from app.core.database import engine

def test_utc_01_db_indexes_exist():
    """
    UTC-01: Verify that HNSW index and supporting indexes created by
    backend/migrations/add_vector_index.sql and init_db.py exist in PostgreSQL.
    """
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE schemaname = 'public';
        """)).fetchall()

        index_names = {row[0] for row in result}
        index_defs = {row[0]: row[1] for row in result}

        # Check HNSW index exists on jobs
        assert "idx_jobs_embedding_hnsw" in index_names or "jobs_embedding_hnsw_idx" in index_names, \
            "HNSW vector index missing on jobs table"
        
        # Check partial index on resumes(is_active)
        assert "idx_resume_is_active" in index_names, \
            "Partial index idx_resume_is_active missing on resumes table"
        
        # Check functional index on LOWER(workplace_type)
        assert "idx_jobs_workplace_type_lower" in index_names, \
            "Functional index idx_jobs_workplace_type_lower missing on jobs table"
        
        # Check composite index on user_job_matches(user_id, job_id)
        assert "idx_user_job_matches_composite" in index_names, \
            "Composite index idx_user_job_matches_composite missing on user_job_matches table"

        # Verify HNSW index uses cosine distance operator
        hnsw_name = "idx_jobs_embedding_hnsw" if "idx_jobs_embedding_hnsw" in index_names else "jobs_embedding_hnsw_idx"
        assert "vector_cosine_ops" in index_defs[hnsw_name], \
            "HNSW index must use vector_cosine_ops"
