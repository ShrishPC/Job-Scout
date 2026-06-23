import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import urllib.parse

async def fetch_indeed_description(browser, job_info: dict):
    """
    Helper to fetch a single description using a fresh browser context.
    """
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }
    )
    page = await context.new_page()
    url = job_info['job_url']
    try:
        print(f"  -> Fetching Indeed description: {job_info['title']} @ {job_info['company']}")
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        
        # Wait for the selector to ensure content has parsed
        try:
            await page.wait_for_selector('#jobDescriptionText', timeout=8000)
        except: pass

        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        desc_div = None
        selectors = [
            '#jobDescriptionText',
            '.jobsearch-JobComponent-description',
            '.jobsearch-jobDescriptionText',
            '#jobDetailsSection'
        ]
        for sel in selectors:
            desc_div = soup.select_one(sel)
            if desc_div:
                break
                
        job_info['description'] = desc_div.get_text(separator='\n').strip() if desc_div else ""
    except Exception as e:
        print(f"    Error on Indeed description {url}: {e}")
        job_info['description'] = ""
    finally:
        await page.close()
        await context.close()
    return job_info

async def scrape_indeed_jobs(keyword: str, location: str, limit: int = 10):
    """
    Scrapes job postings from Indeed using Playwright.
    Indeed has stronger anti-bot measures, so this uses stealth parameters.
    """
    jobs = []
    safe_keyword = urllib.parse.quote(keyword)
    safe_location = urllib.parse.quote(location)
    url = f"https://www.indeed.com/jobs?q={safe_keyword}&l={safe_location}&fromage=1"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            }
        )
        page = await context.new_page()
        
        print(f"Navigating to Indeed: {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # Wait for job beacons to render
            try:
                await page.wait_for_selector('.job_seen_beacon', timeout=8000)
            except: pass

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            job_cards = soup.select('.job_seen_beacon')
            
            for card in job_cards[:limit]:
                try:
                    title_el = card.select_one('.jobTitle a span') or card.select_one('.jobTitle span') or card.select_one('.jobTitle a')
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
            
            # Close the search context before starting detailed queries
            await page.close()
            await context.close()

            # Enrich jobs with descriptions using fresh browser contexts in parallel batches with sem
            if jobs:
                print(f"Enriching {len(jobs)} Indeed jobs with descriptions...")
                import random
                sem = asyncio.Semaphore(2)
                
                async def sem_fetch(job, index):
                    async with sem:
                        if index > 0:
                            await asyncio.sleep(random.uniform(1.5, 3.5))
                        return await fetch_indeed_description(browser, job)
                        
                jobs = list(await asyncio.gather(*(sem_fetch(job, idx) for idx, job in enumerate(jobs))))
                
        except Exception as e:
            print(f"Indeed access failed: {e}")

        await browser.close()
    
    return jobs

if __name__ == "__main__":
    results = asyncio.run(scrape_indeed_jobs("Python Developer", "Remote", limit=5))
    print(json.dumps(results, indent=2))

