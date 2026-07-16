import sys
import os
import time
import requests

API_URL = "http://127.0.0.1:8001"

def test_hybrid_search():
    print("1. Uploading Resume...")
    resume_content = b"John Doe\njohn@example.com\n\nEXPERIENCE\nSoftware Engineer | Tech Corp\n\nSKILLS\nReact, TypeScript, Python, C++, Docker, Machine Learning\n\nEDUCATION\nB.S. Computer Science\n"
    
    files = {"file": ("resume.md", resume_content, "text/markdown")}
    resp = requests.post(f"{API_URL}/resume/parse", files=files)
    print(f"Resume Upload Status: {resp.status_code}")
    print(resp.json())
    
    # Wait for processing
    time.sleep(1)
    
    print("\n2. Getting Active Profile...")
    profile_resp = requests.get(f"{API_URL}/resume/active")
    print(f"Profile Status: {profile_resp.status_code}")
    profile_data = profile_resp.json()
    print("Parsed Data:", profile_data.get("parsed_json"))
    
    embedding = profile_data.get("embedding", [])
    print(f"Extracted Embedding Length: {len(embedding)}")
    
    if len(embedding) != 384:
        print("ERROR: Expected 384 dimensions.")
        return
        
    print("\n3. Inserting Mock Jobs...")
    # Insert mock jobs using SQLAlchemy directly
    sys.path.append(os.path.abspath("backend"))
    from app.core.database import SessionLocal
    from app.models.models import Job
    from app.services.llm_service import generate_embedding
    
    db = SessionLocal()
    
    # Clear existing jobs if any
    db.query(Job).delete()
    db.commit()
    
    mock_jobs = [
        {"title": "React Frontend Developer", "description": "Looking for a React developer with TypeScript experience. Knowing Docker is a plus.", "company": "Frontend Co"},
        {"title": "Backend Python Engineer", "description": "Need a strong Backend Python engineer. C++ knowledge is preferred.", "company": "Backend Inc"},
        {"title": "Data Scientist", "description": "Machine Learning and Python are required. Pandas and numpy.", "company": "AI startup"},
        {"title": "Construction Manager", "description": "Looking for a construction manager to build stuff.", "company": "Builder Ltd"}
    ]
    
    for mj in mock_jobs:
        emb = generate_embedding(mj['title'] + " " + mj['description'])
        job = Job(
            title=mj['title'],
            description=mj['description'],
            company=mj['company'],
            job_url=f"mock://{mj['title'].replace(' ', '')}",
            embedding=emb
        )
        db.add(job)
    db.commit()
    print("Inserted Mock Jobs.")
    
    print("\n4. Requesting Matches...")
    matches_resp = requests.post(f"{API_URL}/jobs/matches", json={
        "embedding": embedding,
        "limit": 10
    })
    
    if matches_resp.status_code == 200:
        matches = matches_resp.json()
        print(f"\nGot {len(matches)} matches:")
        for idx, match in enumerate(matches):
            print(f"#{idx+1} {match['title']} @ {match['company']}")
            print(f"    Vector Score: {match.get('vector_score', 0.0):.2f}")
            print(f"    Keyword Score: {match.get('keyword_score', 0.0):.2f}")
            print(f"    Hybrid Score: {match.get('match_score', 0.0):.2f}")
    else:
        print(f"Error fetching matches: {matches_resp.status_code}")
        print(matches_resp.text)

if __name__ == "__main__":
    test_hybrid_search()
