from sqlalchemy import Column, Integer, String, JSON, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    resume_markdown = Column(Text)
    parsed_data = Column(JSON)  # Stores skills, experience, etc.
    embedding = Column(Vector(384))  # 384 dimensions for local MiniLM embeddings
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    resume_markdown = Column(Text)
    parsed_data = Column(JSON)  # Stores skills, experience, etc.
    embedding = Column(Vector(384))  # 384 dimensions for local MiniLM embeddings
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    description = Column(Text)
    location = Column(String)
    salary = Column(String)
    job_url = Column(String, unique=True)
    parsed_data = Column(JSON)
    embedding = Column(Vector(384))  # 384 dimensions for local MiniLM embeddings
    experience_required = Column(Integer, default=0)
    workplace_type = Column(String, default="unspecified") # remote, hybrid, onsite, negotiable, unspecified
    date_posted = Column(String) # Captured from scraper
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserJobMatch(Base):
    __tablename__ = "user_job_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    status = Column(String, default="interested") # interested, applied, interviewing, offered, rejected
    notes = Column(Text)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AIGenerationCache(Base):
    __tablename__ = "ai_generation_caches"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True)
    response_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
