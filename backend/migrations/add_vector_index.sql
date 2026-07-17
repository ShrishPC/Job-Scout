-- HNSW index for fast cosine similarity search on job embeddings
CREATE INDEX IF NOT EXISTS idx_jobs_embedding_hnsw ON jobs USING hnsw (embedding vector_cosine_ops);

-- Supporting indexes
CREATE INDEX IF NOT EXISTS idx_resume_is_active ON resumes (is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_jobs_workplace_type_lower ON jobs (LOWER(workplace_type));
CREATE INDEX IF NOT EXISTS idx_user_job_matches_composite ON user_job_matches (user_id, job_id);
