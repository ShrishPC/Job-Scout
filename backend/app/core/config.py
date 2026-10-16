from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job Scout"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/job_scout")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000,http://0.0.0.0:3000")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "False").lower() == "true"
    HNSW_EF_SEARCH: int = int(os.getenv("HNSW_EF_SEARCH", "400"))
    HYBRID_MODE: str = os.getenv("HYBRID_MODE", "two_stage").lower()

    class Config:
        env_file = ".env"

settings = Settings()

