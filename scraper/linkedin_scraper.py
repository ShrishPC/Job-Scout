import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import urllib.parse

async def get_job_links(keyword: str, location: str, limit: int = 10):
    """
    Step 1: Scrape only the job cards to get URLs and basic metadata.
    """
    safe_keyword = urllib.parse.quote(keyword)
    safe_location = urllib.parse.quote(location)
    url = f"https://www.linkedin.com/jobs/search?keywords={safe_keyword}&location={safe_location}&f_TPR=r86400"

    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Searching for {keyword} in {location}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Load more jobs
            for _ in range(1):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')
            
            links = []
            for card in job_cards[:limit]:
                try:
                    title = card.find('h3', class_='base-search-card__title').text.strip()
                    company = card.find('h4', class_='base-search-card__subtitle').text.strip()
                    location_text = card.find('span', class_='job-search-card__location').text.strip()
                    link = card.find('a', class_='base-card__full-link')['href'].split('?')[0]
                    
                    # Try to find the time status
                    time_el = card.find('time', class_='job-search-card__listdate') or \
                              card.find('time', class_='job-search-card__listdate--new')
                    date_posted = time_el.text.strip() if time_el else "Recent"
                    
                    links.append({
                        "title": title, 
                        "company": company, 
                        "location": location_text, 
                        "job_url": link,
                        "date_posted": date_posted
                    })
                except: continue
            
            await browser.close()
            return links
        except Exception as e:
            print(f"Discovery error: {e}")
            await browser.close()
            return []

async def fetch_single_description(browser_context, job_info: dict):
    """
    Helper to fetch a single description using an existing browser context.
    """
    page = await browser_context.new_page()
    url = job_info['job_url']
    try:
        print(f"  -> Fetching: {job_info['title']} @ {job_info['company']}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Public view sometimes has a "Show more" button
        try:
            show_more_button = await page.wait_for_selector('button.show-more-less-html__button--more', timeout=2000)
            if show_more_button:
                await show_more_button.click()
        except: pass

        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        desc_div = soup.find('div', class_='show-more-less-html__markup')
        job_info['description'] = desc_div.get_text(separator='\n').strip() if desc_div else ""
    except Exception as e:
        print(f"    Error on {url}: {e}")
        job_info['description'] = ""
    finally:
        await page.close()
    return job_info

async def enrich_jobs_with_descriptions(jobs_list: list):
    """
    Step 2: Fetch descriptions for a list of jobs in parallel batches.
    """
    if not jobs_list: return []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Parallel fetch with a concurrency limit
        sem = asyncio.Semaphore(3)
        
        async def sem_fetch(job):
            async with sem:
                return await fetch_single_description(context, job)
        
        enriched_jobs = await asyncio.gather(*(sem_fetch(job) for job in jobs_list))
        await browser.close()
        return enriched_jobs

if __name__ == "__main__":
    # Test run
    links = asyncio.run(get_job_links("Data Analyst", "India", limit=3))
    results = asyncio.run(enrich_jobs_with_descriptions(links))
    print(json.dumps(results, indent=2))
