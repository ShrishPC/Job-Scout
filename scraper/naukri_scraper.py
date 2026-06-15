import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import re

async def scrape_naukri_jobs(keyword: str, location: str, limit: int = 10):
    """
    Scrapes jobs from Naukri.com using Playwright.
    Naukri uses a heavy SPA structure with JSON data embedded in the page.
    """
    # Naukri search URL format - sanitize to keep only alphanumeric characters and dashes
    clean_keyword = re.sub(r'[^a-zA-Z0-9\s-]', '', keyword)
    search_slug = re.sub(r'\s+', '-', clean_keyword.lower().strip())
    
    clean_location = re.sub(r'[^a-zA-Z0-9\s-]', '', location)
    location_slug = re.sub(r'\s+', '-', clean_location.lower().strip())
    
    url = f"https://www.naukri.com/{search_slug}-jobs-in-{location_slug}"


    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to Naukri: {url}...")
        jobs = []
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            # Wait for job cards to render
            await page.wait_for_selector(".srp-jobtuple-wrapper", timeout=10000)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            job_cards = soup.select(".srp-jobtuple-wrapper")
            
            for card in job_cards[:limit]:
                try:
                    title_el = card.select_one("a.title")
                    title = title_el.text.strip() if title_el else "N/A"
                    link = title_el['href'] if title_el else ""
                    
                    company_el = card.select_one("a.comp-name")
                    company = company_el.text.strip() if company_el else "N/A"
                    
                    location_el = card.select_one("span.loc-wrap")
                    loc_text = location_el.text.strip() if location_el else location
                    
                    desc_el = card.select_one(".job-desc")
                    description = desc_el.text.strip() if desc_el else ""
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": loc_text,
                        "job_url": link,
                        "description": description,
                        "date_posted": "Recent"
                    })
                except Exception as e:
                    print(f"Error parsing Naukri card: {e}")
        except Exception as e:
            print(f"Naukri access failed: {e}")
        
        await browser.close()
        return jobs

if __name__ == "__main__":
    # Test
    results = asyncio.run(scrape_naukri_jobs("Software Engineer", "Bangalore", limit=3))
    print(json.dumps(results, indent=2))
