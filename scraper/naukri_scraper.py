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
    url = job_info.get('job_url', '')
    if not url:
        await page.close()
        return job_info

    try:
        print(f"  -> Fetching Naukri description: {job_info['title']} @ {job_info['company']}")
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        
        try:
            await page.wait_for_selector('[class*="job-desc-container"]', timeout=4000)
        except Exception:
            pass
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
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
                job_info['description'] = desc_div.get_text(separator='\n').strip()
                break
    except Exception as e:
        print(f"    Error on Naukri description {url}: {e}")
    finally:
        try:
            await page.close()
        except Exception:
            pass
    return job_info

async def scrape_naukri_jobs(keyword: str, location: str = "", limit: int = 10):
    """
    Scrapes jobs from Naukri.com using headless Playwright.
    """
    clean_keyword = re.sub(r'[^a-zA-Z0-9\s-]', '', keyword)
    search_slug = re.sub(r'\s+', '-', clean_keyword.lower().strip())
    
    clean_location = re.sub(r'[^a-zA-Z0-9\s-]', '', location) if location else ""
    location_slug = re.sub(r'\s+', '-', clean_location.lower().strip()) if clean_location else ""
    
    if location_slug:
        url = f"https://www.naukri.com/{search_slug}-jobs-in-{location_slug}"
    else:
        url = f"https://www.naukri.com/{search_slug}-jobs"

    jobs = []
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.google.com/"
                }
            )
            page = await context.new_page()
            
            print(f"Navigating to Naukri: {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            try:
                await page.wait_for_selector(".srp-jobtuple-wrapper", timeout=8000)
            except Exception:
                pass
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            job_cards = soup.select(".srp-jobtuple-wrapper")
            
            for card in job_cards[:limit]:
                try:
                    title_el = card.select_one("a.title")
                    title = title_el.text.strip() if title_el else "N/A"
                    link = title_el['href'] if title_el and 'href' in title_el.attrs else ""
                    
                    company_el = card.select_one("a.comp-name") or card.select_one(".comp-name")
                    company = company_el.text.strip() if company_el else "N/A"
                    
                    location_el = card.select_one(".loc-wrap") or card.select_one(".locWraper") or card.select_one(".location")
                    loc_text = location_el.text.strip() if location_el else (location or "Remote")
                    
                    desc_el = card.select_one(".job-desc")
                    short_desc = desc_el.text.strip() if desc_el else ""
                    
                    if title != "N/A":
                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": loc_text,
                            "job_url": link,
                            "description": short_desc,
                            "date_posted": "Recent"
                        })
                except Exception as card_err:
                    print(f"Error parsing Naukri card: {card_err}")
            
            if jobs:
                print(f"Enriching {len(jobs)} Naukri jobs with full descriptions...")
                sem = asyncio.Semaphore(3)
                
                async def sem_fetch(job):
                    async with sem:
                        return await fetch_naukri_description(context, job)
                        
                jobs = list(await asyncio.gather(*(sem_fetch(job) for job in jobs)))
            
            await browser.close()
        except Exception as e:
            print(f"Naukri scraping failed: {e}")
            
    return jobs

if __name__ == "__main__":
    results = asyncio.run(scrape_naukri_jobs("Software Engineer", "Bangalore", limit=3))
    print(json.dumps(results, indent=2))
