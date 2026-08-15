import requests
import feedparser
from bs4 import BeautifulSoup
import json
import urllib.parse

def scrape_remoteok_jobs(keyword: str, limit: int = 10):
    """
    Fetches jobs from Remote OK using their public JSON endpoint with timeout resilience.
    """
    safe_keyword = urllib.parse.quote(keyword)
    url = f"https://remoteok.com/api?tag={safe_keyword}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    print(f"Fetching Remote OK jobs for keyword '{keyword}'...")
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            print(f"Remote OK API failed with status {response.status_code}")
            return []
            
        data = response.json()
        # First element is legal disclaimer/header
        job_listings = data[1:] if isinstance(data, list) and len(data) > 1 else []
        
        jobs = []
        for item in job_listings:
            if len(jobs) >= limit:
                break
            if not isinstance(item, dict):
                continue
                
            title = item.get("position") or item.get("title")
            if not title:
                continue

            raw_desc = item.get("description", "")
            # Clean HTML tags if present in description
            if "<" in raw_desc and ">" in raw_desc:
                soup = BeautifulSoup(raw_desc, 'html.parser')
                desc_text = soup.get_text(separator=' ').strip()
            else:
                desc_text = raw_desc.strip()

            jobs.append({
                "title": title,
                "company": item.get("company", "Remote Employer"),
                "location": item.get("location") or "Remote",
                "job_url": item.get("url") or f"https://remoteok.com/l/{item.get('id', '')}",
                "description": desc_text,
                "date_posted": item.get("date", "Recent")
            })
        return jobs
    except Exception as e:
        print(f"Remote OK error: {e}")
        return []

def scrape_wwr_jobs(keyword: str, limit: int = 10):
    """
    Fetches jobs from We Work Remotely using their official RSS feed with HTML tag stripping.
    """
    url = "https://weworkremotely.com/remote-jobs.rss"
    print(f"Fetching We Work Remotely RSS for '{keyword}'...")
    
    try:
        feed = feedparser.parse(url)
        jobs = []
        keyword_lower = keyword.lower().strip()
        
        for entry in feed.entries:
            if len(jobs) >= limit:
                break
                
            entry_title = entry.get('title', '')
            entry_summary = entry.get('summary', '')

            # Basic keyword filtering in title or summary
            if not keyword_lower or keyword_lower in entry_title.lower() or keyword_lower in entry_summary.lower():
                soup = BeautifulSoup(entry_summary, 'html.parser')
                description = soup.get_text(separator='\n').strip()
                
                title = entry_title
                company = "Remote Company"
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
                    "job_url": entry.get('link', ''),
                    "description": description,
                    "date_posted": entry.get('published', 'Recent')
                })
        return jobs
    except Exception as e:
        print(f"WWR error: {e}")
        return []

if __name__ == "__main__":
    rok = scrape_remoteok_jobs("python", limit=2)
    print("Remote OK:", json.dumps(rok, indent=2))
    wwr = scrape_wwr_jobs("python", limit=2)
    print("WWR:", json.dumps(wwr, indent=2))
