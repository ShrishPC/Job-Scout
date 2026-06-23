from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.services.resume_service import parse_resume_to_markdown
from app.services.llm_service import parse_markdown_with_llm, generate_embedding, generate_tailored_resume_service, generate_cover_letter_service
from app.services.matching_service import get_job_matches
from app.core.database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from celery import Celery
import os
from app.models.models import Job, UserJobMatch, Resume, AIGenerationCache
from app.core.config import settings

app = FastAPI(title="Job Scout API")

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
    workplace_types: list[str] | None = None

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v):
        if not v:
            raise ValueError("Embedding list cannot be empty")
        if len(v) != 768:
            raise ValueError(f"Embedding must be exactly 768 dimensions (got {len(v)})")
        return v

class StatusUpdate(BaseModel):
    job_id: int
    status: str

# Connect to Celery
celery_app = Celery("job_scout_scraper", broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"))

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
        raise HTTPException(status_code=500, detail=str(e))

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
                "date_posted": job.date_posted or "Recent"
            })
        return board
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobs/matches")
def get_matches(request: MatchRequest, db: Session = Depends(get_db)):
    """
    Returns top job matches for a given embedding.
    """
    print(f"Match request received. Embedding size: {len(request.embedding)}")
    try:
        matches = get_job_matches(db, request.embedding, request.limit, request.workplace_types)
        print(f"Returning {len(matches)} matches.")
        return matches
    except Exception as e:
        print(f"MATCH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/resume/parse")
def parse_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save the file temporarily
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            content = file.file.read()
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
        raise HTTPException(status_code=500, detail=str(e))
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
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

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
    Generates a tailored resume recommendation or a custom cover letter locally using Llama-3.2-3B with caching.
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
            return {
                "mode": request.mode,
                "job_title": job_title,
                "company": company,
                "result": cache_entry.response_text,
                "cached": True
            }
            
        # 3. Generate if not cached
        if request.mode == "tailor":
            result = generate_tailored_resume_service(resume_text, job_title, job_desc, db=db)
        elif request.mode == "cover_letter":
            result = generate_cover_letter_service(resume_text, job_title, company, job_desc, db=db)
        else:
            raise HTTPException(status_code=400, detail="Invalid generation mode. Choose 'tailor' or 'cover_letter'.")
            
        # Store in Cache
        try:
            new_cache = AIGenerationCache(cache_key=cache_key, response_text=result)
            db.add(new_cache)
            db.commit()
        except Exception as cache_err:
            db.rollback()
            print(f"Failed to cache generation: {cache_err}")
            
        return {
            "mode": request.mode,
            "job_title": job_title,
            "company": company,
            "result": result,
            "cached": False
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))

class AIConfigRequest(BaseModel):
    device: str  # 'cpu' or 'cuda'

@app.get("/ai/config")
def get_ai_config():
    """
    Returns the current AI hardware execution device.
    """
    from app.services.llm_service import AI_DEVICE
    return {"device": AI_DEVICE}

@app.post("/ai/config")
def update_ai_config(request: AIConfigRequest):
    """
    Dynamically switches AI execution backend between CPU and CUDA (GPU).
    """
    from app.services.llm_service import set_ai_device
    try:
        set_ai_device(request.device)
        return {"status": "success", "device": request.device}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/shutdown")
def shutdown_system():
    """
    Triggers an application shutdown sequence.
    """
    import os
    import signal
    import time
    import threading

    def kill_parent():
        time.sleep(0.5)
        os.kill(os.getppid(), signal.SIGINT)
        
    threading.Thread(target=kill_parent).start()
    return {"status": "success", "message": "System shutdown initiated."}

@app.post("/system/restart")
def restart_system():
    """
    Triggers a reboot sequence of the Job Scout stack.
    """
    import os
    import signal
    import subprocess
    import time
    import threading
    
    def reboot():
        time.sleep(0.5)
        parent_pid = os.getppid()
        project_root = "/home/rishav/job-scout"
        cmd = f"while kill -0 {parent_pid} 2>/dev/null; do sleep 0.1; done; cd {project_root} && nohup bash run.sh > /dev/null 2>&1 &"
        subprocess.Popen(["bash", "-c", cmd], start_new_session=True)
        os.kill(parent_pid, signal.SIGINT)

    threading.Thread(target=reboot).start()
    return {"status": "success", "message": "System restart initiated."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
