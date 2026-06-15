from sqlalchemy.orm import Session
from app.models.models import Job
from sqlalchemy import text
import numpy as np

def get_job_matches(db: Session, user_embedding: list, limit: int = 10, workplace_types: list[str] | None = None):
    """
    Uses pgvector to find the most similar jobs based on the user's resume embedding.
    Includes jobs not in UserJobMatch OR jobs marked as 'rejected'.
    Supports filtering by remote, hybrid, onsite, or negotiable workplace types.
    """
    select_clause = """
        SELECT j.id, j.title, j.company, j.description, j.location, j.salary, j.job_url, j.date_posted, j.experience_required, j.workplace_type,
               m.status, (1 - (j.embedding <=> :embedding)) * 100 as match_score
        FROM jobs j
        LEFT JOIN user_job_matches m ON j.id = m.job_id
        WHERE (m.job_id IS NULL OR m.status = 'rejected')
    """
    
    params = {"embedding": str(user_embedding), "limit": limit}
    
    # If workplace filters are provided, clean them and add IN clause safely
    if workplace_types and len(workplace_types) > 0:
        cleaned_types = [wt.lower().strip() for wt in workplace_types if wt]
        if cleaned_types:
            select_clause += " AND LOWER(j.workplace_type) IN :workplace_types"
            params["workplace_types"] = tuple(cleaned_types)
            
    order_and_limit = """
        ORDER BY j.embedding <=> :embedding
        LIMIT :limit
    """
    
    query = text(select_clause + order_and_limit)
    results = db.execute(query, params)
    
    matches = []
    for row in results:
        try:
            matches.append({
                "id": row.id,
                "title": row.title,
                "company": row.company,
                "description": row.description if row.description else "", # Return full description for modal
                "location": row.location,
                "salary": row.salary,
                "job_url": row.job_url,
                "date_posted": row.date_posted or "Recent",
                "experience_required": row.experience_required,
                "workplace_type": row.workplace_type if row.workplace_type else "unspecified",
                "match_score": float(row.match_score) if row.match_score is not None else 0.0,
                "is_rejected": row.status == 'rejected'
            })
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
    
    return matches

