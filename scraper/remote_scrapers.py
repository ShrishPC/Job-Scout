import requests
import feedparser
from bs4 import BeautifulSoup
import json
import asyncio
import urllib.parse

def scrape_remoteok_jobs(keyword: str, limit: int = 10):
    """
    Fetches jobs from Remote OK using their JSON API.
    """
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://remoteok.com/api?tag={safe_keyword}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    print(f"Fetching Remote OK jobs for {keyword}...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Remote OK API failed with status {response.status_code}")
            return []
            
        data = response.json()
        # First item is a legal notice/header
        job_listings = data[1:]
        
        jobs = []
        for item in job_listings[:limit]:
            jobs.append({
                "title": item.get("position"),
                "company": item.get("company"),
                "location": item.get("location") or "Remote",
                "job_url": item.get("url"),
                "description": item.get("description", ""),
                "date_posted": item.get("date", "Recent")
            })
        return jobs
    except Exception as e:
        print(f"Remote OK error: {e}")
        return []

def scrape_wwr_jobs(keyword: str, limit: int = 10):
    """
    Fetches jobs from We Work Remotely using their RSS feed.
    """
    url = "https://weworkremotely.com/remote-jobs.rss"
    print(f"Fetching We Work Remotely RSS...")
    
    try:
        feed = feedparser.parse(url)
        jobs = []
        
        keyword_lower = keyword.lower()
        
        for entry in feed.entries:
            if len(jobs) >= limit:
                break
                
            # Basic keyword filtering in title or summary
            if keyword_lower in entry.title.lower() or keyword_lower in entry.summary.lower():
                # Summary often contains HTML, clean it up for description
                soup = BeautifulSoup(entry.summary, 'html.parser')
                description = soup.get_text(separator='\n').strip()
                
                # Title format is usually "Company: Title" or "Title at Company"
                title = entry.title
                company = "N/A"
                if ":" in title:
                    parts = title.split(":", 1)
                    company = parts[0].strip()
                    title = parts[1].strip()
                elif " at " in title:
                    parts = title.split(" at ", 1)
                    title = parts[0].strip()
                    company = parts[1].strip()

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": "Remote",
                    "job_url": entry.link,
                    "description": description,
                    "date_posted": entry.published if hasattr(entry, 'published') else "Recent"
                })
        return jobs
    except Exception as e:
        print(f"WWR error: {e}")
        return []

if __name__ == "__main__":
    # Test
    rok = scrape_remoteok_jobs("python", limit=2)
    print("Remote OK:", json.dumps(rok, indent=2))
    
    wwr = scrape_wwr_jobs("python", limit=2)
    print("WWR:", json.dumps(wwr, indent=2))
