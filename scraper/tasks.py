from celery_app import app
import asyncio
from sqlalchemy.orm import Session
import os
import sys

# Add backend to path to reuse models and database
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models.models import Job
from app.services.llm_service import generate_embedding, extract_experience_from_job
from linkedin_scraper import get_job_links, enrich_jobs_with_descriptions
from indeed_scraper import scrape_indeed_jobs
from naukri_scraper import scrape_naukri_jobs
from remote_scrapers import scrape_remoteok_jobs, scrape_wwr_jobs

def safe_update_state(task_instance, state: str, meta: dict):
    """
    Safely updates task progress state only if running inside an active Celery worker context with a task_id.
    """
    try:
        if task_instance and getattr(task_instance, "request", None) and getattr(task_instance.request, "id", None):
            task_instance.update_state(state=state, meta=meta)
    except Exception as e:
        print(f"Warning: safe_update_state skipped ({e})")

def determine_workplace_type(title: str, location: str, description: str, source: str) -> str:
    """
    Infers whether a job is remote, hybrid, or onsite based on title, location, and description.
    """
    if source in ("remoteok", "wwr"):
        return "remote"
        
    combined_text = f"{title} {location} {description}".lower()
    
    if "hybrid" in combined_text or "flexible remote" in combined_text:
        return "hybrid"
        
    if "remote" in combined_text or "work from home" in combined_text or "wfh" in combined_text or "anywhere" in combined_text:
        return "remote"
        
    if not location or location.strip() == "":
        return "unspecified"
        
    return "onsite"

@app.task(bind=True)
def scheduled_scrape(self):
    """
    Automated task triggered by Celery Beat every 10 minutes.
    Dispatches background scrape across default search terms.
    """
    return scrape_and_process_jobs.apply_async(args=["Software Engineer", "Remote", 15, "linkedin"])

@app.task(bind=True)
def scrape_and_process_jobs(self, keyword: str, location: str, limit: int = 10, source: str = "linkedin"):
    """
    Optimized asynchronous Celery task with real-time state reporting and batch database persistence.
    """
    print(f"Starting optimized {source} scrape for '{keyword}' in '{location}'...")
    
    safe_update_state(
        self,
        state='PROGRESS', 
        meta={
            'status': f'Initiating {source} discovery...', 
            'source': source, 
            'keyword': keyword,
            'location': location,
            'current': 0, 
            'total': limit
        }
    )
    
    db: Session = SessionLocal()
    try:
        jobs_data = []

        if source == "linkedin":
            safe_update_state(self, state='PROGRESS', meta={'status': 'Discovering LinkedIn job postings...', 'source': source, 'current': 0, 'total': limit})
            discovered_links = asyncio.run(get_job_links(keyword, location, limit))

            # Batch-filter existing jobs
            existing_urls = set(
                row[0] for row in db.query(Job.job_url)
                .filter(Job.job_url.in_([j['job_url'] for j in discovered_links if j.get('job_url')]))
                .all()
            )
            new_jobs_to_process = [j for j in discovered_links if j.get('job_url') and j['job_url'] not in existing_urls]
            print(f"Found {len(discovered_links)} jobs, {len(new_jobs_to_process)} are new.")
            
            safe_update_state(self, state='PROGRESS', meta={'status': f'Enriching {len(new_jobs_to_process)} new job descriptions...', 'source': source, 'current': 0, 'total': len(new_jobs_to_process)})
            jobs_data = asyncio.run(enrich_jobs_with_descriptions(new_jobs_to_process))
            
        elif source == "indeed":
            safe_update_state(self, state='PROGRESS', meta={'status': 'Scraping Indeed listings...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = asyncio.run(scrape_indeed_jobs(keyword, location, limit))
        elif source == "naukri":
            safe_update_state(self, state='PROGRESS', meta={'status': 'Scraping Naukri listings...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = asyncio.run(scrape_naukri_jobs(keyword, location, limit))
        elif source == "remoteok":
            safe_update_state(self, state='PROGRESS', meta={'status': 'Fetching Remote OK jobs...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = scrape_remoteok_jobs(keyword, limit)
        elif source == "wwr":
            safe_update_state(self, state='PROGRESS', meta={'status': 'Fetching We Work Remotely feed...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = scrape_wwr_jobs(keyword, limit)
        else:
            return {"status": "error", "message": f"Unknown source: {source}", "new_jobs": 0}

        # Filter duplicates across all sources
        all_urls = [j.get('job_url') for j in jobs_data if j.get('job_url')]
        existing_urls = set(
            row[0] for row in db.query(Job.job_url).filter(Job.job_url.in_(all_urls)).all()
        ) if all_urls else set()
        
        new_jobs = [j for j in jobs_data if j.get('job_url') and j['job_url'] not in existing_urls]
        total_to_process = len(new_jobs)
        processed_count = 0

        for idx, job_info in enumerate(new_jobs):
            try:
                safe_update_state(
                    self,
                    state='PROGRESS', 
                    meta={
                        'status': f"Generating embedding for {job_info.get('title', 'job')} ({idx + 1}/{total_to_process})...",
                        'source': source,
                        'current': idx + 1,
                        'total': total_to_process
                    }
                )

                content_to_embed = job_info.get('description') or f"{job_info['title']} at {job_info['company']}"
                embedding = generate_embedding(content_to_embed)
                
                experience_req = 0
                if job_info.get('description'):
                    experience_req = extract_experience_from_job(job_info['description'])
                
                workplace_type = determine_workplace_type(
                    job_info.get('title', ''),
                    job_info.get('location', ''),
                    job_info.get('description', ''),
                    source
                )
                
                new_job = Job(
                    title=job_info.get('title', 'Untitled Position'),
                    company=job_info.get('company', 'Confidential'),
                    description=job_info.get('description', ''),
                    location=job_info.get('location', 'Remote'),
                    job_url=job_info['job_url'],
                    embedding=embedding,
                    experience_required=experience_req,
                    workplace_type=workplace_type,
                    date_posted=job_info.get('date_posted', 'Recent'),
                    parsed_data={}
                )
                db.add(new_job)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing job {job_info.get('job_url', 'unknown')}: {e}")
                db.rollback()

        db.commit()
        print(f"Finished processing {processed_count} new jobs from {source}.")
        return {
            "status": "success", 
            "new_jobs": processed_count, 
            "total_found": len(jobs_data),
            "source": source,
            "keyword": keyword,
            "location": location
        }

    except Exception as e:
        print(f"Scraping task error: {e}")
        return {"status": "error", "message": str(e), "source": source}
    finally:
        db.close()
