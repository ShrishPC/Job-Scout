from sqlalchemy.orm import Session
from app.models.models import Job
from sqlalchemy import text

import re
import os

def get_job_matches(
    db: Session, 
    user_embedding: list, 
    limit: int = 10, 
    skip: int = 0, 
    workplace_types: list[str] | None = None, 
    search_keyword: str | None = None,
    candidate_k: int | None = None,
    hybrid_mode: str | None = None,
    user_skills: list[str] | None = None
):
    """
    Uses Hybrid RAG (pgvector cosine similarity + Postgres keyword matching)
    to find the most similar jobs based on the user's resume embedding and skills.
    """
    from app.core.config import settings

    # 1. Fetch User Skills (from argument or User(id=1))
    if user_skills is not None:
        skills = [s.strip().lower() for s in user_skills if s and s.strip()]
    else:
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

    ef_search = int(os.getenv("HNSW_EF_SEARCH", str(getattr(settings, "HNSW_EF_SEARCH", 400))))
    if hybrid_mode is None:
        hybrid_mode = os.getenv("HYBRID_MODE", getattr(settings, "HYBRID_MODE", "two_stage")).lower()
    else:
        hybrid_mode = hybrid_mode.lower()

    if hybrid_mode == "two_stage":
        if candidate_k is None:
            candidate_k = int(os.getenv("CANDIDATE_K", str(max(100, (limit + skip) * 5))))
        # ef_search must never be below candidate_k
        ef_search = max(ef_search, candidate_k)
        params.update({"embedding": str(user_embedding), "limit": limit, "skip": skip, "candidate_k": candidate_k})

        where_filters = []
        if search_keyword and search_keyword.strip():
            where_filters.append("(j.title ILIKE :kw OR j.company ILIKE :kw OR j.description ILIKE :kw)")
            params["kw"] = f"%{search_keyword.strip()}%"

        if workplace_types and len(workplace_types) > 0:
            cleaned_types = [wt.lower().strip() for wt in workplace_types if wt]
            if cleaned_types:
                where_filters.append("LOWER(j.workplace_type) IN :workplace_types")
                params["workplace_types"] = tuple(cleaned_types)

        filter_str = f"WHERE {' AND '.join(where_filters)}" if where_filters else ""

        cte_keyword_expr = keyword_score_expr.replace("j.", "c.")
        cte_order_expr = order_score_expr.replace("j.", "c.")
        cte_score_calc = score_calculation.replace("j.", "c.")

        query_sql = f"""
            WITH candidates AS (
                SELECT j.id, j.title, j.company, j.description, j.location, j.salary, j.job_url, 
                       j.date_posted, j.experience_required, j.workplace_type, j.embedding
                FROM jobs j
                {filter_str}
                ORDER BY j.embedding <=> :embedding
                LIMIT :candidate_k
            )
            SELECT c.id, c.title, c.company, c.description, c.location, c.salary, c.job_url, 
                   c.date_posted, c.experience_required, c.workplace_type,
                   m.status,
                   (1 - (c.embedding <=> :embedding)) * 100 as vector_score,
                   ({cte_keyword_expr}) * 100 as keyword_score,
                   ({cte_score_calc}) as match_score
            FROM candidates c
            LEFT JOIN user_job_matches m ON c.id = m.job_id
            WHERE (m.job_id IS NULL OR m.status = 'rejected')
            ORDER BY ({cte_order_expr}) DESC
            LIMIT :limit OFFSET :skip
        """
        query = text(query_sql)
    else:
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

    db.execute(text(f"SET LOCAL hnsw.ef_search = {ef_search};"))
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


