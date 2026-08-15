from celery_app import app
import asyncio
from linkedin_scraper import get_job_links, enrich_jobs_with_descriptions
from indeed_scraper import scrape_indeed_jobs
from naukri_scraper import scrape_naukri_jobs
from remote_scrapers import scrape_remoteok_jobs, scrape_wwr_jobs
from sqlalchemy.orm import Session
import sys
import os

# Add backend to path to reuse models and core logic
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models.models import Job
from app.services.llm_service import generate_embedding, extract_experience_from_job

def determine_workplace_type(title: str, location: str, description: str, source: str) -> str:
    """
    Heuristically identifies if a job is remote, hybrid, onsite, or negotiable
    based on title, location, description, and source engine.
    """
    source_lower = source.lower() if source else ""
    if "remoteok" in source_lower or "wwr" in source_lower:
        return "remote"
        
    title_lower = title.lower() if title else ""
    loc_lower = location.lower() if location else ""
    desc_lower = description.lower() if description else ""
    
    # Check remote keywords
    if "remote" in loc_lower or "telecommute" in loc_lower or "work from home" in loc_lower or "wfh" in loc_lower:
        return "remote"
    if "remote" in title_lower or "wfh" in title_lower:
        return "remote"
        
    # Check hybrid keywords
    if "hybrid" in loc_lower or "hybrid" in title_lower:
        return "hybrid"
    if "hybrid" in desc_lower or "work from office and home" in desc_lower:
        if "hybrid work" in desc_lower or "hybrid model" in desc_lower or "hybrid setup" in desc_lower or "hybrid role" in desc_lower:
            return "hybrid"
            
    # Check negotiable keywords
    if "negotiable" in desc_lower or "location negotiable" in desc_lower or "remote negotiable" in desc_lower or "flexible location" in desc_lower:
        return "negotiable"
        
    # Standard check for remote in description
    if "100% remote" in desc_lower or "fully remote" in desc_lower or "work from anywhere" in desc_lower:
        return "remote"
        
    if not location or location.strip() == "":
        return "unspecified"
        
    return "onsite"

@app.task(bind=True)
def scheduled_scrape(self):
    """
    Automated task triggered by Celery Beat every 10 minutes.
    Uses default search terms to keep the database fresh.
    """
    return scrape_and_process_jobs("Software Engineer", "Remote", limit=15, source="linkedin")

@app.task(bind=True)
def scrape_and_process_jobs(self, keyword: str, location: str, limit: int = 10, source: str = "linkedin"):
    """
    Optimized asynchronous Celery task with real-time state reporting.
    1. Discovers links.
    2. Batch filters duplicates.
    3. Enriches descriptions in parallel.
    4. Computes vector embeddings and stores in PostgreSQL pgvector.
    """
    print(f"Starting optimized {source} scrape for '{keyword}' in '{location}'...")
    
    self.update_state(
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
        new_jobs_to_process = []
        jobs_data = []

        if source == "linkedin":
            self.update_state(state='PROGRESS', meta={'status': 'Discovering LinkedIn job postings...', 'source': source, 'current': 0, 'total': limit})
            discovered_links = asyncio.run(get_job_links(keyword, location, limit))

            # Batch-filter existing jobs
            existing_urls = set(
                row[0] for row in db.query(Job.job_url)
                .filter(Job.job_url.in_([j['job_url'] for j in discovered_links]))
                .all()
            )
            new_jobs_to_process = [j for j in discovered_links if j['job_url'] not in existing_urls]
            print(f"Found {len(discovered_links)} jobs, {len(new_jobs_to_process)} are new.")
            
            self.update_state(state='PROGRESS', meta={'status': f'Enriching {len(new_jobs_to_process)} new job descriptions...', 'source': source, 'current': 0, 'total': len(new_jobs_to_process)})
            jobs_data = asyncio.run(enrich_jobs_with_descriptions(new_jobs_to_process))
            
        elif source == "indeed":
            self.update_state(state='PROGRESS', meta={'status': 'Scraping Indeed listings...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = asyncio.run(scrape_indeed_jobs(keyword, location, limit))
        elif source == "naukri":
            self.update_state(state='PROGRESS', meta={'status': 'Scraping Naukri listings...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = asyncio.run(scrape_naukri_jobs(keyword, location, limit))
        elif source == "remoteok":
            self.update_state(state='PROGRESS', meta={'status': 'Fetching Remote OK jobs...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = scrape_remoteok_jobs(keyword, limit)
        elif source == "wwr":
            self.update_state(state='PROGRESS', meta={'status': 'Fetching We Work Remotely feed...', 'source': source, 'current': 0, 'total': limit})
            jobs_data = scrape_wwr_jobs(keyword, limit)
        else:
            return {"status": "error", "message": f"Unknown source: {source}", "new_jobs": 0}

        total_to_process = len(jobs_data)
        processed_count = 0

        for idx, job_info in enumerate(jobs_data):
            try:
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'status': f"Generating embedding for {job_info.get('title', 'job')} ({idx + 1}/{total_to_process})...",
                        'source': source,
                        'current': idx + 1,
                        'total': total_to_process
                    }
                )

                # Check existence to avoid duplicate entries
                existing_job = db.query(Job).filter(Job.job_url == job_info['job_url']).first()
                if existing_job:
                    continue
                
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
