from sqlalchemy.orm import Session
from app.models.models import Job
from sqlalchemy import text

import re

def get_job_matches(db: Session, user_embedding: list, limit: int = 10, skip: int = 0, workplace_types: list[str] | None = None, search_keyword: str | None = None):
    """
    Uses Hybrid RAG (pgvector cosine similarity + Postgres keyword matching)
    to find the most similar jobs based on the user's resume embedding and skills.
    """
    # 1. Fetch User Skills from User(id=1)
    from app.models.models import User
    user = db.query(User).filter(User.id == 1).first()
    
    skills = []
    if user and user.parsed_data and isinstance(user.parsed_data.get("skills"), list):
        skills = [s.strip().lower() for s in user.parsed_data.get("skills") if s.strip()]

    # 2. Build Keyword Match expressions
    case_whens = []
    params = {}
    for i, skill in enumerate(skills):
        param_name = f"skill_{i}"
        # Alphanumeric skills (e.g. "React", "Machine Learning") use precise word boundary regex
        if re.match(r'^[a-zA-Z0-9\s\-]+$', skill):
            regex_pattern = r'\y' + re.escape(skill).replace(r'\ ', r'\s+') + r'\y'
            params[param_name] = regex_pattern
            case_whens.append(f"""
                (CASE WHEN j.title ~* :{param_name} THEN 2.0 
                      WHEN j.description ~* :{param_name} THEN 1.0 
                      ELSE 0.0 END)
            """)
        else:
            # Special character skills (e.g. "C++", "C#", ".Net") use substring search
            params[param_name] = f"%{skill}%"
            case_whens.append(f"""
                (CASE WHEN LOWER(j.title) LIKE :{param_name} THEN 2.0 
                      WHEN LOWER(j.description) LIKE :{param_name} THEN 1.0 
                      ELSE 0.0 END)
            """)

    if case_whens:
        # Normalize: division by max possible points (2.0 points per skill)
        keyword_score_expr = f"({' + '.join(case_whens)}) / {float(2.0 * len(skills))}"
        score_calculation = f"(0.7 * (1 - (j.embedding <=> :embedding)) + 0.3 * ({keyword_score_expr})) * 100"
        order_score_expr = f"0.7 * (1 - (j.embedding <=> :embedding)) + 0.3 * ({keyword_score_expr})"
    else:
        keyword_score_expr = "0.0"
        score_calculation = "(1 - (j.embedding <=> :embedding)) * 100"
        order_score_expr = "1 - (j.embedding <=> :embedding)"

    select_clause = f"""
        SELECT j.id, j.title, j.company, j.description, j.location, j.salary, j.job_url, j.date_posted, j.experience_required, j.workplace_type,
               m.status, 
               (1 - (j.embedding <=> :embedding)) * 100 as vector_score,
               ({keyword_score_expr}) * 100 as keyword_score,
               ({score_calculation}) as match_score
        FROM jobs j
        LEFT JOIN user_job_matches m ON j.id = m.job_id
        WHERE (m.job_id IS NULL OR m.status = 'rejected')
    """
    
    params.update({"embedding": str(user_embedding), "limit": limit, "skip": skip})
    
    if search_keyword and search_keyword.strip():
        select_clause += " AND (j.title ILIKE :kw OR j.company ILIKE :kw OR j.description ILIKE :kw)"
        params["kw"] = f"%{search_keyword.strip()}%"
    
    if workplace_types and len(workplace_types) > 0:
        cleaned_types = [wt.lower().strip() for wt in workplace_types if wt]
        if cleaned_types:
            select_clause += " AND LOWER(j.workplace_type) IN :workplace_types"
            params["workplace_types"] = tuple(cleaned_types)
            
    order_and_limit = f"""
        ORDER BY ({order_score_expr}) DESC
        LIMIT :limit OFFSET :skip
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


