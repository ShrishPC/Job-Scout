import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import urllib.parse

async def scrape_indeed_jobs(keyword: str, location: str, limit: int = 10):
    """
    Scrapes job postings from Indeed using Playwright.
    Indeed has stronger anti-bot measures, so this is a simplified version.
    """
    jobs = []
    # Indeed search URL
    safe_keyword = urllib.parse.quote(keyword)
    safe_location = urllib.parse.quote(location)
    url = f"https://www.indeed.com/jobs?q={safe_keyword}&l={safe_location}&fromage=1"


    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to Indeed: {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Indeed often shows a CAPTCHA or "I am human" check.
            # In a real scenario, we'd need a solver or proxy.
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Indeed job card containers (selectors often change)
            job_cards = soup.select('.job_seen_beacon')
            
            for card in job_cards[:limit]:
                try:
                    title_el = card.select_one('h2.jobTitle span')
                    title = title_el.text.strip() if title_el else "N/A"
                    
                    company_el = card.select_one('[data-testid="company-name"]')
                    company = company_el.text.strip() if company_el else "N/A"
                    
                    location_el = card.select_one('[data-testid="text-location"]')
                    location_text = location_el.text.strip() if location_el else "N/A"
                    
                    jk = card.select_one('a[data-jk]')['data-jk']
                    link = f"https://www.indeed.com/viewjob?jk={jk}"
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location_text,
                        "job_url": link
                    })
                except Exception as e:
                    print(f"Error parsing Indeed card: {e}")
        except Exception as e:
            print(f"Indeed access failed: {e}")

        await browser.close()
    
    return jobs

if __name__ == "__main__":
    results = asyncio.run(scrape_indeed_jobs("Python Developer", "Remote", limit=5))
    print(json.dumps(results, indent=2))
