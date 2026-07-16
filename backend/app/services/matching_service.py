from sqlalchemy.orm import Session
from app.models.models import Job
from sqlalchemy import text
import numpy as np
import re

def get_job_matches(db: Session, user_embedding: list, limit: int = 10, workplace_types: list[str] | None = None):
    """
    Uses Hybrid RAG (pgvector cosine similarity + Postgres keyword matching)
    to find the most similar jobs based on the user's resume embedding and skills.
    """
    # 1. Fetch User Skills from User(id=1)
    from app.models.models import User
    user = db.query(User).filter(User.id == 1).first()
    
    skills = []
    if user and user.parsed_data and isinstance(user.parsed_data.get("skills"), list):
    try:
        # Get active resume to extract skills for hybrid scoring
        active_resume = db.query(Resume).filter(Resume.is_active == True).first()
        skills = []
        if active_resume and active_resume.parsed_data:
            skills = active_resume.parsed_data.get('skills', [])
            
        vector_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Build strict regex matching for keyword scoring
        if skills:
            escaped_skills = []
            for s in skills:
                # Handle special chars like C++ or .NET via simple ILIKE fallback, others via \y word boundary
                if any(c in s for c in ['+', '.', '#']):
                    escaped_skills.append(f"(description ILIKE '%{s}%' OR title ILIKE '%{s}%')")
                else:
                    escaped_skills.append(f"(description ~* '\\y{s}\\y' OR title ~* '\\y{s}\\y')")
                    
            keyword_score_sql = f"""
                (
                    SELECT COUNT(*) * 1.0 / {len(skills)}
                    FROM (VALUES (1)) as dummy
                    WHERE {' OR '.join(escaped_skills)}
                )
            """
        else:
            keyword_score_sql = "0.0"

        # Using pgvector cosine distance: embedding <=> :embedding
        # Cosine distance ranges from 0 (perfect match) to 2 (perfectly opposite).
        # Cosine similarity = 1 - Cosine distance.
        query_sql = f"""
            SELECT j.id, j.title, j.company, j.description, j.location, j.salary, j.job_url, j.date_posted, j.experience_required, j.workplace_type,
                   (1 - (j.embedding <=> :embedding)) * 100 as vector_score,
                   ({keyword_score_sql}) * 100 as keyword_score,
                   
                   -- HYBRID SCORE FORMULA (70% Vector, 30% Keyword)
                   ( (1 - (j.embedding <=> :embedding)) * 100 * 0.70 ) + 
                   ( ({keyword_score_sql}) * 100 * 0.30 ) as match_score,
                   
                   ujm.status
            FROM jobs j
            LEFT JOIN user_job_matches ujm ON j.id = ujm.job_id AND ujm.user_id = 1
            WHERE (ujm.status IS NULL OR ujm.status != 'rejected')
        """
        
        if workplace_types and len(workplace_types) > 0:
            formatted_types = "', '".join(workplace_types)
            query_sql += f" AND (j.workplace_type IN ('{formatted_types}'))"
            
        query_sql += f" ORDER BY match_score DESC LIMIT :limit OFFSET :skip"
        
        results = db.execute(
            text(query_sql),
            {"embedding": vector_str, "limit": limit, "skip": skip}
        ).fetchall()
        
        matches = []
        for row in results:
            try:
                matches.append({
                    "id": row.id,
                    "title": row.title,
                    "company": row.company,
                    "description": row.description if row.description else "",
                    "location": row.location,
                    "salary": row.salary,
                    "job_url": row.job_url,
                    "date_posted": row.date_posted or "Recent",
                    "experience_required": row.experience_required,
                    "workplace_type": row.workplace_type if row.workplace_type else "unspecified",
                    "vector_score": float(row.vector_score) if row.vector_score is not None else 0.0,
                    "keyword_score": float(row.keyword_score) if row.keyword_score is not None else 0.0,
                    "match_score": float(row.match_score) if row.match_score is not None else 0.0,
                    "is_rejected": row.status == 'rejected'
                })
            except Exception as e:
                print(f"Error processing row in hybrid search: {e}")
                continue
                
        return matches
    except Exception as e:
        print(f"Error in hybrid search: {e}")
        return []
