from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from app.services.resume_service import parse_resume_to_markdown
from app.services.llm_service import (
    parse_markdown_with_llm, 
    generate_embedding, 
    generate_tailored_resume_service, 
    generate_cover_letter_service,
    generate_tailored_resume_stream,
    generate_cover_letter_stream,
    refine_stream,
    research_company_stream
)

from app.services.matching_service import get_job_matches
from app.core.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from pydantic import BaseModel, field_validator
from celery import Celery
import psutil
import os
import uuid
from app.models.models import Job, UserJobMatch, Resume, AIGenerationCache
from app.core.config import settings
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

app = FastAPI(title="Job Scout API")

@app.on_event("startup")
async def startup():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    # For local testing, ensure it gracefully fails if redis is absent
    redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

# Add CORS middleware to allow frontend communication securely
origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


class MatchRequest(BaseModel):
    embedding: list[float]
    limit: int = 10
    skip: int = 0
    workplace_types: list[str] | None = None
    search_keyword: str | None = None

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v):
        if not v:
            raise ValueError("Embedding list cannot be empty")
        if len(v) != 384:
            raise ValueError(f"Embedding must be exactly 384 dimensions (got {len(v)})")
        return v

    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError("limit must be between 1 and 100")
        return v

    @field_validator('skip')
    @classmethod
    def validate_skip(cls, v):
        if v < 0:
            raise ValueError("skip must be non-negative")
        return v


class StatusUpdate(BaseModel):
    job_id: int
    status: str

# Connect to Celery (Broker and Result Backend)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("job_scout_scraper", broker=REDIS_URL, backend=REDIS_URL)

@app.get("/")
async def root():
    return {"message": "Welcome to Job Scout API"}

@app.post("/jobs/interest")
def mark_interest(request: StatusUpdate, db: Session = Depends(get_db)):
    """
    Marks a job as 'Interested' and moves it to the Kanban board.
    """
    try:
        # Check if already exists
        match = db.query(UserJobMatch).filter(UserJobMatch.job_id == request.job_id).first()
        if match:
            match.status = request.status
        else:
            match = UserJobMatch(user_id=1, job_id=request.job_id, status=request.status)
            db.add(match)
        db.commit()
        return {"status": "success", "job_id": request.job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.get("/jobs/board")
def get_board(db: Session = Depends(get_db)):
    """
    Returns all jobs with their current application status for the Kanban board.
    """
    try:
        results = db.query(Job, UserJobMatch.status, UserJobMatch.id.label("match_id")) \
            .join(UserJobMatch, Job.id == UserJobMatch.job_id) \
            .all()
        
        board = []
        for job, status, match_id in results:
            board.append({
                "id": job.id,
                "match_id": match_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "status": status,
                "job_url": job.job_url,
                "date_posted": job.date_posted or "Recent",
                "description": job.description or ""
            })
        return board
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.post("/jobs/matches")
@cache(expire=60)
def get_matches(request: MatchRequest, db: Session = Depends(get_db)):
    """
    Returns top job matches for a given embedding. (Cached via Redis for 60 seconds)
    """
    print(f"Match request received. Embedding size: {len(request.embedding)}")
    try:
        matches = get_job_matches(db, request.embedding, request.limit, request.skip, request.workplace_types, request.search_keyword)
        print(f"Returning {len(matches)} matches.")
        return matches
    except Exception as e:
        print(f"MATCH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.post("/jobs/scrape")
def trigger_scrape(keyword: str, location: str, limit: int = 10, source: str = "linkedin"):
    """
    Triggers background scraping tasks for one or more sources.
    Source can be: linkedin, indeed, naukri, remoteok, wwr, or all.
    """
    sources = [source]
    if source == "all":
        sources = ["linkedin", "indeed", "naukri", "remoteok", "wwr"]
    
    task_ids = []
    try:
        for s in sources:
            task = celery_app.send_task(
                "tasks.scrape_and_process_jobs", 
                args=[keyword, location, limit, s]
            )
            task_ids.append(task.id)
        
        return {
            "task_ids": task_ids, 
            "status": "Tasks triggered", 
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    """
    Checks the execution state, progress, or return result of a Celery background task.
    """
    from celery.result import AsyncResult
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else False,
        }
        
        if task_result.state == 'PENDING':
            response["status"] = "Task queued / pending execution"
        elif task_result.state == 'PROGRESS':
            response["status"] = task_result.info.get('status', 'Processing...') if isinstance(task_result.info, dict) else str(task_result.info)
            response["progress"] = task_result.info if isinstance(task_result.info, dict) else {}
        elif task_result.state == 'SUCCESS':
            response["status"] = "Completed"
            response["result"] = task_result.result
        elif task_result.state == 'FAILURE':
            response["status"] = "Failed"
            response["error"] = str(task_result.info)
        else:
            response["status"] = str(task_result.state)
            if isinstance(task_result.info, dict):
                response["meta"] = task_result.info
                
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check task: {str(e)}")

class BatchTaskStatusRequest(BaseModel):
    task_ids: list[str]

@app.post("/tasks/batch-status")
def get_batch_task_status(request: BatchTaskStatusRequest):
    """
    Returns status and progress for multiple Celery background tasks in a single query.
    """
    from celery.result import AsyncResult
    try:
        results = []
        all_completed = True
        total_new_jobs = 0

        for tid in request.task_ids:
            task_result = AsyncResult(tid, app=celery_app)
            item = {
                "task_id": tid,
                "state": task_result.state,
                "ready": task_result.ready(),
                "successful": task_result.successful() if task_result.ready() else False,
            }
            if not task_result.ready():
                all_completed = False

            if task_result.state == 'PROGRESS' and isinstance(task_result.info, dict):
                item["progress"] = task_result.info
                item["status"] = task_result.info.get('status', 'Processing...')
            elif task_result.state == 'SUCCESS':
                item["result"] = task_result.result
                item["status"] = "Completed"
                if isinstance(task_result.result, dict):
                    total_new_jobs += task_result.result.get("new_jobs", 0)
            elif task_result.state == 'FAILURE':
                item["error"] = str(task_result.info)
                item["status"] = "Failed"
            else:
                item["status"] = task_result.state

            results.append(item)

        return {
            "tasks": results,
            "all_completed": all_completed,
            "total_new_jobs": total_new_jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch task status failed: {str(e)}")

@app.post("/resume/parse")
def parse_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate file type
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".md", ".txt"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    # Save the file temporarily
    temp_file_path = f"temp_{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)
        
        # 1. Convert to Markdown
        markdown_content = parse_resume_to_markdown(temp_file_path)
        
        # 2. Parse with LLM
        parsed_data = parse_markdown_with_llm(markdown_content)
        
        # 3. Generate Embedding for the whole resume
        embedding = generate_embedding(markdown_content)
        
        # 4. Deactivate all existing resumes in the resumes table
        db.query(Resume).update({Resume.is_active: False})
        
        # 5. Create new Resume entry
        new_resume = Resume(
            filename=file.filename,
            resume_markdown=markdown_content,
            parsed_data=parsed_data,
            embedding=embedding,
            is_active=True
        )
        db.add(new_resume)
        
        # 6. Save to Database for User(id=1)
        from app.models.models import User
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(id=1, name=parsed_data.get('full_name', 'Unknown'), email=parsed_data.get('email', ''))
            db.add(user)
        
        user.resume_markdown = markdown_content
        user.parsed_data = parsed_data
        user.embedding = embedding
        db.commit()
        
        return {
            "id": new_resume.id,
            "filename": file.filename, 
            "markdown": markdown_content,
            "parsed_json": parsed_data,
            "embedding": embedding,
            "embedding_length": len(embedding) if embedding else 0
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An internal server error occurred")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/resume/active")
def get_active_resume(db: Session = Depends(get_db)):
    """
    Gets the active resume/profile details for User(id=1).
    """
    try:
        from app.models.models import User
        user = db.query(User).filter(User.id == 1).first()
        if user and user.resume_markdown:
            # Try to find the active resume record to get the actual filename
            active_resume = db.query(Resume).filter(Resume.is_active == True).first()
            filename = active_resume.filename if active_resume else "Active Resume"
            
            # Convert numpy array / vector to standard list of floats
            embedding_list = [float(x) for x in user.embedding] if user.embedding is not None else []
            
            return {
                "filename": filename,
                "markdown": user.resume_markdown,
                "parsed_json": user.parsed_data,
                "embedding": embedding_list,
                "embedding_length": len(embedding_list)
            }
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.get("/resumes")
def list_resumes(db: Session = Depends(get_db)):
    """
    Lists all resumes in the vault.
    """
    try:
        resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
        result = []
        for r in resumes:
            result.append({
                "id": r.id,
                "filename": r.filename,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "is_active": r.is_active,
                "parsed_data": {
                    "full_name": r.parsed_data.get("full_name") if r.parsed_data else None,
                    "email": r.parsed_data.get("email") if r.parsed_data else None,
                    "skills_count": len(r.parsed_data.get("skills", [])) if r.parsed_data and isinstance(r.parsed_data.get("skills"), list) else 0
                }
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.post("/resumes/{resume_id}/activate")
def activate_resume(resume_id: int, db: Session = Depends(get_db)):
    """
    Sets the specified resume as active and updates User(id=1) profile.
    """
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Deactivate all
        db.query(Resume).update({Resume.is_active: False})
        
        # Activate this one
        resume.is_active = True
        
        # Sync to User
        from app.models.models import User
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(
                id=1, 
                name=resume.parsed_data.get('full_name', 'Unknown') if resume.parsed_data else 'Unknown', 
                email=resume.parsed_data.get('email', '') if resume.parsed_data else ''
            )
            db.add(user)
        else:
            if resume.parsed_data:
                user.name = resume.parsed_data.get('full_name', user.name)
                user.email = resume.parsed_data.get('email', user.email)
        
        user.resume_markdown = resume.resume_markdown
        user.parsed_data = resume.parsed_data
        user.embedding = resume.embedding
        
        db.commit()
        
        # Convert numpy array / vector to standard list of floats
        embedding_list = [float(x) for x in resume.embedding] if resume.embedding is not None else []
        
        return {
            "status": "success", 
            "message": f"Resume '{resume.filename}' is now active.",
            "profile": {
                "filename": resume.filename,
                "markdown": resume.resume_markdown,
                "parsed_json": resume.parsed_data,
                "embedding": embedding_list,
                "embedding_length": len(embedding_list)
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """
    Deletes a resume from the vault.
    """
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        was_active = resume.is_active
        db.delete(resume)
        
        if was_active:
            # Clear User profile
            from app.models.models import User
            user = db.query(User).filter(User.id == 1).first()
            if user:
                user.resume_markdown = None
                user.parsed_data = None
                user.embedding = None
                
            # Optionally activate the next most recent resume
            next_resume = db.query(Resume).order_by(Resume.created_at.desc()).first()
            if next_resume:
                next_resume.is_active = True
                if user:
                    user.resume_markdown = next_resume.resume_markdown
                    user.parsed_data = next_resume.parsed_data
                    user.embedding = next_resume.embedding
                    if next_resume.parsed_data:
                        user.name = next_resume.parsed_data.get('full_name', user.name)
                        user.email = next_resume.parsed_data.get('email', user.email)
        
        db.commit()
        return {"status": "success", "message": "Resume deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.delete("/resume/reset")
def reset_resume(db: Session = Depends(get_db)):
    """
    Clears all stored resume data for the user.
    """
    try:
        from app.models.models import User
        user = db.query(User).filter(User.id == 1).first()
        if user:
            user.resume_markdown = None
            user.parsed_data = None
            user.embedding = None
        
        # Also deactivate all resumes in the vault
        db.query(Resume).update({Resume.is_active: False})
        db.commit()
        return {"status": "success", "message": "Profile data cleared."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An internal server error occurred")

class AIGenerateRequest(BaseModel):
    job_id: int | None = None
    custom_job_description: str | None = None
    custom_job_title: str | None = None
    custom_company: str | None = None
    resume_id: int | None = None
    mode: str  # 'tailor' or 'cover_letter'

@app.post("/ai/generate")
def generate_ai(request: AIGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates a tailored resume recommendation or a custom cover letter locally using Llama-3.2-3B with caching and streaming.
    """
    try:
        # 1. Fetch Resume
        if request.resume_id:
            resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        else:
            resume = db.query(Resume).filter(Resume.is_active == True).first()
            
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found. Please upload one first.")
            
        resume_text = resume.resume_markdown or ""
        if not resume_text:
            raise HTTPException(status_code=400, detail="Resume content is empty.")
            
        # 2. Fetch Job Details
        job_title = request.custom_job_title or "Target Role"
        company = request.custom_company or "Target Company"
        job_desc = request.custom_job_description or ""
        
        if request.job_id:
            job = db.query(Job).filter(Job.id == request.job_id).first()
            if job:
                job_title = job.title
                company = job.company
                job_desc = job.description or ""
                
        if not job_desc.strip():
            raise HTTPException(status_code=400, detail="Job description is required for generation.")
            
        # Generate Cache Key based on inputs
        import hashlib
        inputs_str = f"resume_{resume.id}_job_{request.job_id or 'custom'}_{job_title}_{company}_{job_desc}_{request.mode}"
        cache_key = hashlib.sha256(inputs_str.encode('utf-8')).hexdigest()
        
        # Check Cache
        cache_entry = db.query(AIGenerationCache).filter(AIGenerationCache.cache_key == cache_key).first()
        if cache_entry:
            print(f"Cache hit for key {cache_key}!")
            def stream_cached():
                yield cache_entry.response_text
            return StreamingResponse(stream_cached(), media_type="text/plain")
            
        # Define generator for streaming and caching
        def event_generator():
            accumulated_response = []
            
            if request.mode == "tailor":
                stream = generate_tailored_resume_stream(resume_text, job_title, job_desc, db=db)
            elif request.mode == "cover_letter":
                stream = generate_cover_letter_stream(resume_text, job_title, company, job_desc, db=db)
            else:
                raise HTTPException(status_code=400, detail="Invalid generation mode. Choose 'tailor' or 'cover_letter'.")
                
            for chunk in stream:
                accumulated_response.append(chunk)
                yield chunk
                
            full_response = "".join(accumulated_response).strip()
            
            # Store in Cache
            if full_response:
                try:
                    new_cache = AIGenerationCache(cache_key=cache_key, response_text=full_response)
                    db.add(new_cache)
                    db.commit()
                except Exception as cache_err:
                    db.rollback()
                    print(f"Failed to cache generation inside stream: {cache_err}")
                    
        return StreamingResponse(event_generator(), media_type="text/plain")
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

class AIRefineRequest(BaseModel):
    current_text: str
    instruction: str

@app.post("/ai/refine")
def refine_ai(request: AIRefineRequest, db: Session = Depends(get_db)):
    """
    Refines a generated resume or cover letter based on user instructions using the local LLM.
    """
    try:
        if not request.current_text.strip():
            raise HTTPException(status_code=400, detail="Current text is required.")
        if not request.instruction.strip():
            raise HTTPException(status_code=400, detail="Instruction is required.")
            
        def event_generator():
            stream = refine_stream(request.current_text, request.instruction)
            for chunk in stream:
                yield chunk
                
        return StreamingResponse(event_generator(), media_type="text/plain")
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

class CompanyResearchRequest(BaseModel):
    company: str

@app.post("/ai/research")
def research_company(request: CompanyResearchRequest, db: Session = Depends(get_db)):
    """
    Researches a company and streams the LLM-generated cheat sheet back to the client.
    """
    try:
        if not request.company.strip():
            raise HTTPException(status_code=400, detail="Company name is required.")
            
        def event_generator():
            stream = research_company_stream(request.company, db)
            for chunk in stream:
                yield chunk
                
        return StreamingResponse(event_generator(), media_type="text/plain")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

@app.post("/ai/cache/clear")
@app.delete("/ai/cache")
def clear_ai_cache(db: Session = Depends(get_db)):
    """
    Clears all cached AI generation responses.
    """
    try:
        db.query(AIGenerationCache).delete()
        db.commit()
        return {"status": "success", "message": "AI generation cache cleared successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An internal server error occurred")

class ExportDocumentRequest(BaseModel):
    content: str
    mode: str = "cover_letter"  # "cover_letter" | "tailor" | "resume"
    title: str | None = None
    company: str | None = None
    job_title: str | None = None
    candidate_name: str | None = None
    candidate_email: str | None = None
    candidate_phone: str | None = None
    format: str = "pdf"  # "pdf" | "docx" | "txt"

@app.post("/export/document")
@app.post("/ai/export")
def export_document(request: ExportDocumentRequest):
    """
    Exports tailored resumes or cover letters directly as professional DOCX, PDF, or TXT.
    """
    import re
    from app.services.export_service import generate_docx_export, generate_pdf_export
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content is required for export.")
            
        doc_format = request.format.lower().strip()
        doc_mode = request.mode.lower().strip()
        doc_title = request.title or ("Cover_Letter" if doc_mode == "cover_letter" else "Tailored_Resume")
        
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', doc_title).strip('_') or "Document"
        
        if doc_format == "docx":
            file_bytes = generate_docx_export(
                title=doc_title,
                content=request.content,
                mode=doc_mode,
                candidate_name=request.candidate_name,
                candidate_email=request.candidate_email,
                candidate_phone=request.candidate_phone,
                company=request.company,
                job_title=request.job_title
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{safe_title}.docx"
        elif doc_format == "pdf":
            file_bytes = generate_pdf_export(
                title=doc_title,
                content=request.content,
                mode=doc_mode,
                candidate_name=request.candidate_name,
                candidate_email=request.candidate_email,
                candidate_phone=request.candidate_phone,
                company=request.company,
                job_title=request.job_title
            )
            media_type = "application/pdf"
            filename = f"{safe_title}.pdf"
        else:
            file_bytes = request.content.encode('utf-8')
            media_type = "text/plain; charset=utf-8"
            filename = f"{safe_title}.txt"

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        return Response(content=file_bytes, media_type=media_type, headers=headers)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")

@app.get("/resumes/{resume_id}/export")
def export_vault_resume(resume_id: int, format: str = "pdf", db: Session = Depends(get_db)):
    """
    Exports a specific resume stored in the vault as DOCX or PDF.
    """
    import re
    from app.services.export_service import generate_docx_export, generate_pdf_export
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        parsed = resume.parsed_data or {}
        candidate_name = parsed.get("full_name") or "Applicant"
        candidate_email = parsed.get("email") or ""
        candidate_phone = parsed.get("phone") or ""
        
        content = resume.resume_markdown or f"# {candidate_name}\n\n## Skills\n" + ", ".join(parsed.get("skills", []))
        
        doc_format = format.lower().strip()
        doc_title = f"{candidate_name}_Resume"
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', doc_title).strip('_') or "Resume"
        
        if doc_format == "docx":
            file_bytes = generate_docx_export(
                title=doc_title,
                content=content,
                mode="resume",
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{safe_title}.docx"
        elif doc_format == "pdf":
            file_bytes = generate_pdf_export(
                title=doc_title,
                content=content,
                mode="resume",
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone
            )
            media_type = "application/pdf"
            filename = f"{safe_title}.pdf"
        else:
            file_bytes = content.encode('utf-8')
            media_type = "text/plain; charset=utf-8"
            filename = f"{safe_title}.txt"

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        return Response(content=file_bytes, media_type=media_type, headers=headers)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume export failed: {str(e)}")

class ATSAnalyzeRequest(BaseModel):
    resume_id: int | None = None
    resume_text: str | None = None
    job_id: int | None = None
    job_title: str | None = None
    job_description: str | None = None
    company: str | None = None

@app.post("/ai/ats-analyze")
def ats_analyze(request: ATSAnalyzeRequest, db: Session = Depends(get_db)):
    """
    Computes deterministic ATS match score, keyword gap matrix, and category rubrics.
    """
    try:
        resume_text = ""
        candidate_name = "Candidate"
        
        if request.resume_id:
            resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
            if resume:
                resume_text = resume.resume_markdown or ""
                parsed = resume.parsed_data or {}
                candidate_name = parsed.get("full_name") or candidate_name
        elif request.resume_text and request.resume_text.strip():
            resume_text = request.resume_text.strip()
        else:
            # Fallback to active resume
            active_resume = db.query(Resume).filter(Resume.is_active == True).first()
            if active_resume:
                resume_text = active_resume.resume_markdown or ""
                parsed = active_resume.parsed_data or {}
                candidate_name = parsed.get("full_name") or candidate_name
            else:
                user = db.query(User).filter(User.id == 1).first()
                if user:
                    resume_text = user.resume_markdown or ""
                    parsed = user.parsed_data or {}
                    candidate_name = parsed.get("full_name") or candidate_name

        if not resume_text:
            raise HTTPException(status_code=400, detail="No resume content available. Please upload a resume first.")

        job_title = request.job_title or "Target Role"
        company = request.company or "Target Company"
        job_desc = request.job_description or ""

        if request.job_id:
            job = db.query(Job).filter(Job.id == request.job_id).first()
            if job:
                job_title = job.title or job_title
                company = job.company or company
                job_desc = job.description or job_desc

        if not job_desc.strip():
            raise HTTPException(status_code=400, detail="Job description is required for ATS analysis.")

        from app.services.ats_service import analyze_resume_ats_match
        result = analyze_resume_ats_match(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_desc,
            company=company,
            db=db
        )
        result["candidate_name"] = candidate_name
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ATS analysis failed: {str(e)}")

class ExportATSReportRequest(BaseModel):
    ats_data: dict
    format: str = "pdf"  # "pdf" | "docx" | "txt"
    candidate_name: str | None = None

@app.post("/export/ats-report")
def export_ats_report(request: ExportATSReportRequest):
    """
    Exports an ATS diagnostic report as a publication-grade PDF, Word DOCX, or text file.
    """
    import re
    from app.services.export_service import generate_ats_report_docx, generate_ats_report_pdf, format_ats_report_markdown
    try:
        ats_data = request.ats_data
        if not ats_data:
            raise HTTPException(status_code=400, detail="ATS evaluation data is required.")

        candidate_name = request.candidate_name or ats_data.get("candidate_name") or "Applicant"
        job_title = ats_data.get("job_title", "Position")
        company = ats_data.get("company", "Company")
        
        doc_format = request.format.lower().strip()
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', f"ATS_Report_{company}_{job_title}").strip('_') or "ATS_Report"

        if doc_format == "docx":
            file_bytes = generate_ats_report_docx(ats_data=ats_data, candidate_name=candidate_name)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{safe_title}.docx"
        elif doc_format == "pdf":
            file_bytes = generate_ats_report_pdf(ats_data=ats_data, candidate_name=candidate_name)
            media_type = "application/pdf"
            filename = f"{safe_title}.pdf"
        else:
            text_content = format_ats_report_markdown(ats_data=ats_data, candidate_name=candidate_name)
            file_bytes = text_content.encode('utf-8')
            media_type = "text/plain; charset=utf-8"
            filename = f"{safe_title}.txt"

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        return Response(content=file_bytes, media_type=media_type, headers=headers)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")

class AIConfigRequest(BaseModel):
    device: str  # 'cpu', 'cuda', or 'demo'

@app.get("/ai/config")
def get_ai_config():
    """
    Returns the current AI hardware execution device or demo mode status.
    """
    from app.services.llm_service import AI_DEVICE
    from app.core.config import settings
    if getattr(settings, "DEMO_MODE", False):
        return {"device": "demo"}
    return {"device": AI_DEVICE}

@app.post("/ai/config")
def update_ai_config(request: AIConfigRequest):
    """
    Dynamically switches AI execution backend between CPU, GPU, and DEMO mode.
    """
    from app.services.llm_service import set_ai_device
    from app.core.config import settings
    try:
        if request.device == "demo":
            settings.DEMO_MODE = True
            return {"status": "success", "device": "demo"}
        else:
            settings.DEMO_MODE = False
            set_ai_device(request.device)
            return {"status": "success", "device": request.device}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

def verify_admin_key(x_admin_key: str | None = Header(None)):
    expected_key = os.getenv("ADMIN_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="Admin API key not configured")
    if x_admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid or missing Admin API Key")
    return True

@app.post("/system/shutdown")
def shutdown_system(authorized: bool = Depends(verify_admin_key)):
    """
    Triggers an application shutdown sequence.
    """
    import os
    import signal
    import time
    import threading
    import platform
    import subprocess

    def perform_shutdown():
        time.sleep(0.5)
        if platform.system() == "Windows":
            cmd = (
                "powershell -Command \""
                "try { Stop-Process -Id (Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue).OwningProcess -Force } catch {}; "
                "Get-Process | Where-Object { $_.CommandLine -like '*celery*' } | Stop-Process -Force; "
                "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue).OwningProcess -Force"
                "\""
            )
            subprocess.Popen(cmd, shell=True)
        else:
            # macOS and Linux
            os.kill(os.getppid(), signal.SIGINT)
        
    threading.Thread(target=perform_shutdown).start()
    return {"status": "success", "message": "System shutdown initiated."}

@app.post("/system/restart")
def restart_system(authorized: bool = Depends(verify_admin_key)):
    """
    Triggers a reboot sequence of the Job Scout stack.
    """
    import os
    import signal
    import subprocess
    import time
    import threading
    import platform
    
    # Dynamically resolve project root (3 levels up from this file)
    backend_app_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(backend_app_dir)
    project_root = os.path.dirname(backend_dir)

    def reboot():
        time.sleep(0.5)
        if platform.system() == "Windows":
            cmd = (
                "powershell -Command \""
                "try { Stop-Process -Id (Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue).OwningProcess -Force } catch {}; "
                "Get-Process | Where-Object { $_.CommandLine -like '*celery*' } | Stop-Process -Force; "
                "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File run.ps1' -WorkingDirectory '" + project_root + "'; "
                "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue).OwningProcess -Force"
                "\""
            )
            subprocess.Popen(cmd, shell=True)
        else:
            # macOS and Linux
            parent_pid = os.getppid()
            cmd = f"while kill -0 {parent_pid} 2>/dev/null; do sleep 0.1; done; cd {project_root} && nohup bash run.sh > /dev/null 2>&1 &"
            subprocess.Popen(["bash", "-c", cmd], start_new_session=True)
            os.kill(parent_pid, signal.SIGINT)

    threading.Thread(target=reboot).start()
    return {"status": "success", "message": "System restart initiated."}


@app.get("/api/admin/stats")
@cache(expire=15)
def get_admin_stats(db: Session = Depends(get_db), authorized: bool = Depends(verify_admin_key)):
    """
    Returns high-level telemetry stats for the dashboard.
    """
    try:
        total_jobs = db.query(Job).count()
        total_resumes = db.query(Resume).count()
        
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        
        try:
            i = celery_app.control.inspect(timeout=0.5)
            active = i.active() if i else None
            active_count = sum(len(tasks) for tasks in active.values()) if active else 0
        except Exception:
            active_count = 0
            
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        jobs_by_day = db.query(
            func.date(Job.created_at).label('date'),
            func.count(Job.id).label('count')
        ).filter(Job.created_at >= seven_days_ago).group_by(func.date(Job.created_at)).all()
        
        jobs_chart = [{"date": str(row.date), "count": row.count} for row in jobs_by_day]

        return {
            "total_jobs": total_jobs,
            "total_resumes": total_resumes,
            "system_cpu_usage_percent": cpu_usage,
            "system_ram_usage_percent": ram.percent,
            "celery_active_tasks": active_count,
            "jobs_chart_data": jobs_chart
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
