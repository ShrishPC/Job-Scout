import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import re

async def fetch_naukri_description(browser_context, job_info: dict):
    """
    Helper to fetch a single full description using an existing browser context.
    """
    page = await browser_context.new_page()
    url = job_info['job_url']
    try:
        print(f"  -> Fetching Naukri description: {job_info['title']} @ {job_info['company']}")
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        
        # Wait briefly for standard description elements
        try:
            await page.wait_for_selector('[class*="job-desc-container"]', timeout=5000)
        except: pass
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        desc_div = None
        selectors = [
            '[class*="job-desc-container"]',
            '[class*="dang-inner-html"]',
            '[class*="JDC__dang"]',
            '[class*="jdc__content"]',
            'section.job-desc',
            '.job-desc-description',
            'div.dang-art',
            '.clearBoth',
            '.jobDesc'
        ]
        for sel in selectors:
            desc_div = soup.select_one(sel)
            if desc_div:
                break
                
        if desc_div:
            # Clean up the text
            job_info['description'] = desc_div.get_text(separator='\n').strip()
    except Exception as e:
        print(f"    Error on Naukri description {url}: {e}")
    finally:
        await page.close()
    return job_info

async def scrape_naukri_jobs(keyword: str, location: str, limit: int = 10):
    """
    Scrapes jobs from Naukri.com using Playwright.
    Naukri uses a heavy SPA structure with JSON data embedded in the page.
    """
    clean_keyword = re.sub(r'[^a-zA-Z0-9\s-]', '', keyword)
    search_slug = re.sub(r'\s+', '-', clean_keyword.lower().strip())
    
    clean_location = re.sub(r'[^a-zA-Z0-9\s-]', '', location)
    location_slug = re.sub(r'\s+', '-', clean_location.lower().strip())
    
    url = f"https://www.naukri.com/{search_slug}-jobs-in-{location_slug}"

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
                "Referer": "https://www.google.com/",
                "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            }
        )
        page = await context.new_page()
        
        print(f"Navigating to Naukri: {url}...")
        jobs = []
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
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
                    
                    company_el = card.select_one("a.comp-name") or card.select_one(".comp-name")
                    company = company_el.text.strip() if company_el else "N/A"
                    
                    location_el = card.select_one(".loc-wrap") or card.select_one(".locWraper") or card.select_one(".location")
                    loc_text = location_el.text.strip() if location_el else location
                    
                    desc_el = card.select_one(".job-desc")
                    short_desc = desc_el.text.strip() if desc_el else ""
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": loc_text,
                        "job_url": link,
                        "description": short_desc,  # Fallback snippet
                        "date_posted": "Recent"
                    })
                except Exception as e:
                    print(f"Error parsing Naukri card: {e}")
            
            # Enrich jobs with full descriptions using the same browser context in parallel
            if jobs:
                print(f"Enriching {len(jobs)} Naukri jobs with full descriptions...")
                sem = asyncio.Semaphore(3)
                
                async def sem_fetch(job):
                    async with sem:
                        return await fetch_naukri_description(context, job)
                        
                jobs = list(await asyncio.gather(*(sem_fetch(job) for job in jobs)))
                
        except Exception as e:
            print(f"Naukri access failed: {e}")
        
        await browser.close()
        return jobs

if __name__ == "__main__":
    results = asyncio.run(scrape_naukri_jobs("Software Engineer", "Bangalore", limit=3))
    print(json.dumps(results, indent=2))

