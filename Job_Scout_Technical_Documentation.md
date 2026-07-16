# Job Scout Technical Documentation Suite
#job-scout #documentation #architecture #ai

[[System Overview]] | [[Component Breakdown]] | [[AI Architecture]] | [[System Evaluation]] | [[Roadmap]]

---

## 1. System Overview & Core Mechanics

### Executive Summary
Job Scout is a production-grade, AI-powered job tracking and application generation platform. It automates the discovery of job postings across multiple platforms, applies a local, privacy-first AI to parse resumes, and utilizes Retrieval-Augmented Generation (RAG) to dynamically generate highly tailored cover letters and resume summaries.

### Core Features
- **Automated Job Scraping:** Background workers dynamically scrape and process job listings.
- **Semantic Job Matching:** Matches job descriptions to user profiles using vector embeddings.
- **Local AI Generation:** 100% local, privacy-first generation of tailored cover letters and resume summaries. No external API keys are required.
- **Kanban Tracking:** Visual board to track job applications across various states.
- **Dynamic Device Switching:** Toggles AI computation between CPU and CUDA for hardware optimization.

### Tech Stack
- **Frontend:** Next.js 16.2.7 (Turbopack), React, Tailwind CSS, Lucide Icons.
- **Backend API:** Python, FastAPI, SQLAlchemy, Pydantic.
- **Database:** PostgreSQL with `pgvector` extension for semantic search, SQLAlchemy ORM.
- **Background Workers:** Celery, Redis (Broker/Backend).
- **AI & NLP Pipeline:** 
  - **Local LLM:** `unsloth/Llama-3.2-3B-Instruct` via Hugging Face `transformers`.
  - **Embeddings:** `all-MiniLM-L6-v2` via `sentence-transformers`.
  - **Fallback:** `TinyLlama-1.1B` and heuristic methods.

---

## 2. Complete Codebase & Component Breakdown

### 2.1 API Routes & Backend Core
**File:** `backend/app/main.py`
The FastAPI application core. It orchestrates job matching, background task triggering, resume parsing, and RAG execution.

```python
# main.py - API Core Snippet
@app.post("/ai/generate")
def generate_ai(request: AIGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates a tailored resume recommendation or a custom cover letter 
    locally using Llama-3.2-3B with caching.
    """
    try:
        # Fetch Resume
        if request.resume_id:
            resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        else:
            resume = db.query(Resume).filter(Resume.is_active == True).first()
            
        # ... validation checks ...

        # Cache check to avoid redundant LLM execution
        import hashlib
        inputs_str = f"resume_{resume.id}_job_{request.job_id or 'custom'}_{job_title}_{company}_{job_desc}_{request.mode}"
        cache_key = hashlib.sha256(inputs_str.encode('utf-8')).hexdigest()
        
        cache_entry = db.query(AIGenerationCache).filter(AIGenerationCache.cache_key == cache_key).first()
        if cache_entry:
            return {"mode": request.mode, "result": cache_entry.response_text, "cached": True}
            
        # AI Generation Call
        if request.mode == "tailor":
            result = generate_tailored_resume_service(resume_text, job_title, job_desc, db=db)
        elif request.mode == "cover_letter":
            result = generate_cover_letter_service(resume_text, job_title, company, job_desc, db=db)
            
        # Store Result in DB Cache
        new_cache = AIGenerationCache(cache_key=cache_key, response_text=result)
        db.add(new_cache)
        db.commit()
            
        return {"result": result, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```
*Commentary:* Implements a cryptographic hash cache for AI generation to save immense CPU/GPU cycles on identical requests. Connects directly to the `llm_service`.

### 2.2 Artificial Intelligence & NLP Services
**File:** `backend/app/services/llm_service.py`
Handles LLM initialization, hardware thread management, caching, and prompt engineering.

```python
# llm_service.py - Context Retrieval (RAG) Snippet
RESUME_LINE_EMBEDDING_CACHE = {}

def get_cached_line_embeddings(clean_texts: list[str]) -> list[list[float]]:
    """
    Retrieves embeddings for a list of resume lines, using an in-memory cache to skip re-encoding.
    """
    global RESUME_LINE_EMBEDDING_CACHE
    uncached_texts = []
    
    for text in clean_texts:
        if text in RESUME_LINE_EMBEDDING_CACHE:
            continue
        uncached_texts.append(text)
        
    if uncached_texts:
        new_embeddings = generate_embeddings_batch(uncached_texts)
        for text, emb in zip(uncached_texts, new_embeddings):
            RESUME_LINE_EMBEDDING_CACHE[text] = emb
            
    return [RESUME_LINE_EMBEDDING_CACHE[text] for text in clean_texts]

def retrieve_rag_context(resume_text: str, job_desc: str, db: Session = None) -> str:
    """
    RAG: Retrieves relevant sections of the candidate's resume and similar jobs from database.
    """
    context_parts = []
    
    # Extract bullets from resume
    lines = [(line, re.sub(r'^[\s\-\*\•\d\.\>\+]+', '', line).strip()) for line in resume_text.split('\n') if len(line.strip()) > 15]
    
    if lines:
        job_embedding = generate_embedding(job_desc)
        clean_texts = [clean for original, clean in lines]
        
        # Batch and Cache Embeddings to save processing time
        line_embeddings = get_cached_line_embeddings(clean_texts)
        
        scored_lines = []
        for idx, (original, clean) in enumerate(lines):
            similarity = sum(a * b for a, b in zip(job_embedding[:384], line_embeddings[idx][:384]))
            scored_lines.append((similarity, original))
        
        scored_lines.sort(key=lambda x: x[0], reverse=True)
        top_bullets = [line for score, line in scored_lines[:6]]
        
        context_parts.append("MOST RELEVANT CANDIDATE EXPERIENCES/SKILLS FROM RESUME:")
        for b in top_bullets:
            context_parts.append(f"- {b}")
            
    return "\n".join(context_parts)
```
*Commentary:* Features an in-memory memory caching mechanism (`RESUME_LINE_EMBEDDING_CACHE`) specifically optimized for repetitive RAG loops during candidate generation.

### 2.3 Background Task Orchestration (Celery)
**File:** `scraper/celery_app.py`
Manages the Celery worker and beat definitions for asynchronous scraping.

```python
# celery_app.py - Configuration Snippet
import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

# Explicitly load .env so Celery processes pick up the updated ports
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

app = Celery("job_scout_scraper",
             broker=REDIS_URL,
             backend=REDIS_URL,
             include=["tasks"])

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Schedule automated background scraping tasks
    beat_schedule={
        "daily-job-scrape": {
            "task": "tasks.scrape_and_process_jobs",
            "schedule": crontab(hour=0, minute=0),
            "args": ("Software Engineer", "Remote", 50, "all")
        }
    }
)
```
*Commentary:* Uses `dotenv` explicitly to ensure background workers respect dynamically configured network ports (e.g., Redis on 6380 instead of 6379 to bypass OS daemon conflicts).

### 2.4 Frontend: AI Tailor UI Component
**File:** `frontend/src/components/ui/AITailorView.tsx`
Handles user interactions for custom cover letter and tailored resume summary generation.

```typescript
// AITailorView.tsx - Generation Handler Snippet
const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setResult('');

    const payload: any = { mode: mode };

    if (isCustomJob) {
        if (!customTitle.trim() || !customDesc.trim()) {
            setError("Please fill in the Job Title and Job Description.");
            setGenerating(false);
            return;
        }
        payload.custom_job_title = customTitle;
        payload.custom_job_description = customDesc;
    } else {
        if (!selectedJobId) {
            setError("Please select a job from the list.");
            return;
        }
        payload.job_id = parseInt(selectedJobId);
    }

    try {
        const response = await axios.post(`${apiHost}/ai/generate`, payload);
        setResult(response.data.result);
    } catch (err: any) {
        setError(err.response?.data?.detail || "Local AI Generation failed.");
    } finally {
        setGenerating(false);
    }
};
```
*Commentary:* Provides a robust, reactive UI state machine for handling slow local LLM generations. Gracefully manages loading states and filters out invalid jobs (e.g., empty descriptions) to prevent `400 Bad Request` backend errors.

---

## 3. AI Architecture & Knowledge Processing

The AI stack in Job Scout is intentionally decoupled from external APIs to guarantee privacy and reduce costs. 

### RAG Mechanics
The RAG pipeline operates on two distinct semantic vectors:
1. **Resume Embeddings:** Entire resumes are embedded during upload, allowing high-level semantic matching against incoming job scrapes.
2. **Line-Level Embeddings:** For generation (tailoring), the resume is tokenized into bullet points. Each bullet point is vectorized and matched directly against the specific job description's embedding. This ensures the top 6 most relevant candidate experiences are injected into the LLM's prompt window, preventing hallucinations and grounding the output in factual history.

### Hardware Management
The `llm_service.py` dynamically adjusts `torch.set_num_threads()` to prevent CPU core starvation on consumer hardware. Users can toggle processing contexts seamlessly via the API (`/ai/config` -> `cpu` or `cuda`).

---

## 4. System Evaluation & Benchmarks

- **Port Conflict Mitigation:** Initial system designs mapped Postgres to `5432` and Redis to `6379`. To guarantee isolation from pre-existing host daemons during local deployment, ports have been successfully remapped to `5435` and `6380` respectively in `docker-compose.yml`.
- **RAG Optimization:** Implementing `RESUME_LINE_EMBEDDING_CACHE` reduced generation time drastically. By keeping line-level vector representations in memory, the system avoids recalculating `all-MiniLM-L6-v2` encodings for the same resume lines across multiple job applications.
- **Frontend Stability:** `AITailorView` includes strict validation, discarding scraped jobs that lack descriptions (stubs), thus mitigating `AxiosError 400 Bad Request` issues during generation.

---

## 5. Roadmap & Future Work

- **[[Multi-Agent Scraping]]:** Develop specialized Selenium/Playwright scraper agents to bypass complex bot protections on specific job boards.
- **[[Cloud Offloading Strategy]]:** Introduce an optional API gateway pattern to seamlessly route generation requests to external APIs (OpenAI/Anthropic) if the user's local hardware is constrained.
- **[[Analytics Dashboard]]:** Expand the frontend to visualize conversion rates based on the Kanban board status (e.g., Application Sent -> Interviewing).
