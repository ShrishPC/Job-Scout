#!/usr/bin/env python3
"""
Index Real Jobs Matching Shrish's Resume (Posted in last 48 hours)
- Ingests /app/active_resume.pdf
- Sets active profile in PostgreSQL
- Deletes synthetic benchmark jobs (TechCorp, Distractor, Paraphrase, Disjoint)
- Fetches real jobs posted in the last 48h from WWR, RemoteOK, Jobicy
- Computes vector embeddings and saves into PostgreSQL
- Evicts stale Redis cache
"""

import os
import sys
import json
import datetime
from dateutil import parser as date_parser
import requests
import feedparser
from bs4 import BeautifulSoup
from sqlalchemy import text

# Add backend to path
sys.path.append('/app')
from app.core.database import SessionLocal
from app.models.models import Job, User, Resume
from app.services.llm_service import generate_embedding, extract_experience_from_job
from app.services.llm_fallback import extract_structured_data_fallback
import redis

def parse_and_activate_resume(db, pdf_path):
    print(f"[*] Parsing active resume from {pdf_path}...")
    import fitz
    doc = fitz.open(pdf_path)
    resume_text = "\n".join([page.get_text() for page in doc])
    
    # Extract structured data
    parsed_data = extract_structured_data_fallback(resume_text)
    parsed_data["full_name"] = "Shrish Prasad Chakraborty"
    parsed_data["target_role"] = "Data Analyst / Applied Data Science"
    parsed_data["target_location"] = "Remote / Hybrid"
    parsed_data["email"] = "shrishchakrabarty84@gmail.com"
    parsed_data["phone"] = "+91 76700 11252"
    
    # Ensure critical skills from resume are present
    key_skills = [
        "Python", "SQL", "R", "Pandas", "NumPy", "Matplotlib", "Seaborn",
        "Data Cleaning", "Exploratory Data Analysis", "Descriptive Statistics",
        "Machine Learning", "Data Analysis", "MySQL", "SQLite", "FastAPI",
        "Next.js", "Docker", "PostgreSQL", "Redis", "Git", "GitHub"
    ]
    for s in key_skills:
        if s not in parsed_data["skills"]:
            parsed_data["skills"].append(s)
            
    print(f"[*] Generating 384-dimensional dense embedding for candidate resume...")
    embedding = generate_embedding(resume_text)
    
    # Deactivate existing resumes
    db.query(Resume).update({Resume.is_active: False})
    
    # Create or update active resume entry
    active_resume = Resume(
        filename="RESUME UPDATED(FINAL).pdf",
        resume_markdown=resume_text,
        parsed_data=parsed_data,
        embedding=embedding,
        is_active=True
    )
    db.add(active_resume)
    
    # Update User(id=1)
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, name="Shrish Prasad Chakraborty", email="shrishchakrabarty84@gmail.com")
        db.add(user)
        
    user.name = "Shrish Prasad Chakraborty"
    user.email = "shrishchakrabarty84@gmail.com"
    user.resume_markdown = resume_text
    user.parsed_data = parsed_data
    user.embedding = embedding
    
    db.commit()
    print(f"[✓] Active resume saved for {user.name} (ID: {active_resume.id}).")
    return embedding, parsed_data

def clean_synthetic_benchmark_jobs(db):
    print("[*] Removing synthetic benchmark records (TechCorp, Distractor, Paraphrase, Disjoint)...")
    deleted = db.execute(text("""
        DELETE FROM jobs 
        WHERE company LIKE 'TechCorp%' 
           OR company LIKE 'Distractor%' 
           OR company LIKE 'Paraphrase%' 
           OR company LIKE 'Disjoint%'
    """))
    db.commit()
    print(f"[✓] Cleaned {deleted.rowcount} synthetic benchmark jobs from active database.")

def fetch_recent_jobs_last_48h():
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=48)
    print(f"[*] Fetching real jobs posted after {cutoff.strftime('%Y-%m-%d %H:%M UTC')}...")
    
    collected_jobs = []
    seen_urls = set()

    # 1. We Work Remotely Feeds
    wwr_feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/all-other-remote-jobs.rss",
        "https://weworkremotely.com/remote-jobs.rss"
    ]
    for feed_url in wwr_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                pub = entry.get('published')
                if not pub:
                    continue
                try:
                    dt = date_parser.parse(pub)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
                    if dt < cutoff:
                        continue
                except Exception:
                    continue
                
                link = entry.get('link')
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)
                
                raw_title = entry.get('title', '')
                company = "Remote Company"
                title = raw_title
                if ":" in raw_title:
                    parts = raw_title.split(":", 1)
                    company = parts[0].strip()
                    title = parts[1].strip()
                elif " at " in raw_title:
                    parts = raw_title.split(" at ", 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                    
                summary = entry.get('summary', '')
                soup = BeautifulSoup(summary, 'html.parser')
                desc = soup.get_text(separator='\n').strip()
                
                collected_jobs.append({
                    "title": title,
                    "company": company,
                    "location": "Remote",
                    "job_url": link,
                    "description": desc,
                    "date_posted": dt.strftime("%Y-%m-%d %H:%M"),
                    "source": "We Work Remotely"
                })
        except Exception as e:
            print(f"Warning: WWR feed {feed_url} error: {e}")

    # 2. Remote OK
    for tag in ["data", "python", "analyst", "sql", "machine-learning"]:
        try:
            url = f"https://remoteok.com/api?tag={tag}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()[1:]
                for item in data:
                    d_str = item.get('date')
                    if not d_str:
                        continue
                    try:
                        dt = date_parser.parse(d_str)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=datetime.timezone.utc)
                        if dt < cutoff:
                            continue
                    except Exception:
                        continue
                        
                    link = item.get('url') or f"https://remoteok.com/l/{item.get('id', '')}"
                    if not link or link in seen_urls:
                        continue
                    seen_urls.add(link)
                    
                    raw_desc = item.get('description', '')
                    soup = BeautifulSoup(raw_desc, 'html.parser') if '<' in raw_desc else None
                    desc = soup.get_text(separator=' ').strip() if soup else raw_desc.strip()
                    
                    collected_jobs.append({
                        "title": item.get('position', 'Data Specialist'),
                        "company": item.get('company', 'Tech Employer'),
                        "location": item.get('location') or "Remote",
                        "job_url": link,
                        "description": desc,
                        "date_posted": dt.strftime("%Y-%m-%d %H:%M"),
                        "source": "Remote OK"
                    })
        except Exception as e:
            print(f"Warning: RemoteOK tag {tag} error: {e}")

    # 3. Jobicy API
    try:
        r = requests.get("https://jobicy.com/api/v2/remote-jobs?count=50", timeout=10)
        if r.status_code == 200:
            data = r.json().get('jobs', [])
            for item in data:
                d_str = item.get('pubDate')
                if not d_str:
                    continue
                try:
                    dt = date_parser.parse(d_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
                    if dt < cutoff:
                        continue
                except Exception:
                    continue
                    
                link = item.get('url')
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)
                
                raw_desc = item.get('jobDescription', '')
                soup = BeautifulSoup(raw_desc, 'html.parser') if '<' in raw_desc else None
                desc = soup.get_text(separator=' ').strip() if soup else raw_desc.strip()
                
                collected_jobs.append({
                    "title": item.get('jobTitle', 'Engineer'),
                    "company": item.get('companyName', 'Global Enterprise'),
                    "location": item.get('jobGeo') or "Remote",
                    "job_url": link,
                    "description": desc,
                    "date_posted": dt.strftime("%Y-%m-%d %H:%M"),
                    "source": "Jobicy"
                })
    except Exception as e:
        print(f"Warning: Jobicy error: {e}")

    print(f"[✓] Total fresh jobs collected from last 48 hours: {len(collected_jobs)}")
    return collected_jobs

def index_jobs_to_db(db, jobs_data):
    if not jobs_data:
        print("[!] No new jobs to index.")
        return 0

    # Filter already existing URLs
    all_urls = [j['job_url'] for j in jobs_data if j.get('job_url')]
    existing_urls = set(
        row[0] for row in db.query(Job.job_url).filter(Job.job_url.in_(all_urls)).all()
    ) if all_urls else set()
    
    new_jobs = [j for j in jobs_data if j['job_url'] not in existing_urls]
    print(f"[*] Indexing {len(new_jobs)} completely new jobs into PostgreSQL with embeddings...")

    saved_count = 0
    for idx, j in enumerate(new_jobs, 1):
        try:
            content_to_embed = f"{j['title']} at {j['company']}. {j.get('description', '')[:1000]}"
            emb = generate_embedding(content_to_embed)
            
            exp_req = extract_experience_from_job(j.get('description', ''))
            
            title_lower = j['title'].lower()
            workplace_type = "remote"
            if "hybrid" in title_lower or "hybrid" in j.get('location', '').lower():
                workplace_type = "hybrid"
            elif "onsite" in title_lower:
                workplace_type = "onsite"

            job_row = Job(
                title=j['title'],
                company=j['company'],
                description=j['description'],
                location=j['location'],
                job_url=j['job_url'],
                embedding=emb,
                experience_required=exp_req,
                workplace_type=workplace_type,
                date_posted=j['date_posted'],
                parsed_data={"source": j.get('source', 'Web')}
            )
            db.add(job_row)
            saved_count += 1
            if idx % 10 == 0 or idx == len(new_jobs):
                db.commit()
                print(f"    Indexed {idx}/{len(new_jobs)} jobs...")
        except Exception as e:
            print(f"    Error indexing job {j.get('title')}: {e}")
            db.rollback()

    db.commit()
    print(f"[✓] Successfully indexed {saved_count} real jobs into PostgreSQL!")
    return saved_count

def flush_redis_cache():
    print("[*] Flushing Redis cache to clear stale demo matches...")
    try:
        r = redis.Redis(host="redis", port=6379, db=0)
        r.flushall()
        print("[✓] Redis cache flushed successfully.")
    except Exception as e:
        print(f"Warning: Failed to flush Redis: {e}")

def main():
    db = SessionLocal()
    try:
        # 1. Parse and set active resume
        pdf_path = "/app/active_resume.pdf"
        parse_and_activate_resume(db, pdf_path)
        
        # 2. Clean out synthetic benchmark jobs
        clean_synthetic_benchmark_jobs(db)
        
        # 3. Fetch real jobs posted in the last 48 hours
        fresh_jobs = fetch_recent_jobs_last_48h()
        
        # 4. Index them with embeddings
        index_jobs_to_db(db, fresh_jobs)
        
        # 5. Flush Redis cache
        flush_redis_cache()
        
        # 6. Report total active jobs in DB
        total_jobs = db.query(Job).count()
        print(f"\n=======================================================")
        print(f"🎉 Job Scout is now live with real candidate data!")
        print(f"   Candidate: Shrish Prasad Chakraborty")
        print(f"   Target:    Data Analyst / Applied Data Science")
        print(f"   Total Real Jobs in DB: {total_jobs}")
        print(f"=======================================================\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
