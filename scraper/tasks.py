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

@app.task
def scheduled_scrape():
    """
    Automated task triggered by Celery Beat every 10 minutes.
    Uses default search terms to keep the database fresh.
    """
    return scrape_and_process_jobs("Software Engineer", "Remote", limit=15, source="linkedin")

@app.task
def scrape_and_process_jobs(keyword: str, location: str, limit: int = 10, source: str = "linkedin"):
    """
    Optimized Celery task:
    1. Discover links first.
    2. Filter out jobs already in DB.
    3. Enrich only NEW jobs in parallel.
    """
    print(f"Starting optimized {source} scrape for {keyword} in {location}...")
    
    db: Session = SessionLocal()
    new_jobs_to_process = []
    
    try:
        if source == "linkedin":
            # Phase 1: Quick Discovery
            discovered_links = asyncio.run(get_job_links(keyword, location, limit))
            
            # Phase 2: Filter existing
            for job_info in discovered_links:
                existing = db.query(Job.id).filter(Job.job_url == job_info['job_url']).first()
                if not existing:
                    new_jobs_to_process.append(job_info)
            
            print(f"Found {len(discovered_links)} jobs, {len(new_jobs_to_process)} are new.")
            
            # Phase 3: Parallel Enrichment
            jobs_data = asyncio.run(enrich_jobs_with_descriptions(new_jobs_to_process))
            
        elif source == "indeed":
            jobs_data = asyncio.run(scrape_indeed_jobs(keyword, location, limit))
        elif source == "naukri":
            jobs_data = asyncio.run(scrape_naukri_jobs(keyword, location, limit))
        elif source == "remoteok":
            jobs_data = scrape_remoteok_jobs(keyword, limit)
        elif source == "wwr":
            jobs_data = scrape_wwr_jobs(keyword, limit)
        else:
            return {"status": "error", "message": f"Unknown source: {source}"}
            
    except Exception as e:
        print(f"Scraping failed: {e}")
        return {"status": "error", "message": str(e)}

    processed_count = 0
    for job_info in jobs_data:
        try:
            # Check again just in case (race conditions)
            existing_job = db.query(Job).filter(Job.job_url == job_info['job_url']).first()
            if existing_job:
                continue
            
            content_to_embed = job_info.get('description') or f"{job_info['title']} at {job_info['company']}"
            
            print(f"Generating embedding for {job_info['title']}...")
            embedding = generate_embedding(content_to_embed)
            
            experience_req = 0
            if job_info.get('description'):
                experience_req = extract_experience_from_job(job_info['description'])
            
            workplace_type = determine_workplace_type(
                job_info['title'],
                job_info['location'],
                job_info.get('description', ''),
                source
            )
            
            new_job = Job(
                title=job_info['title'],
                company=job_info['company'],
                description=job_info.get('description', ''),
                location=job_info['location'],
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
            print(f"Error processing job {job_info['job_url']}: {e}")
            db.rollback()
    
    db.commit()
    db.close()
    
    print(f"Finished processing {processed_count} new jobs from {source}.")
    return {"status": "success", "new_jobs": processed_count, "source": source}

