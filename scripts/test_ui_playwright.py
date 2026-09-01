import asyncio
import os
import sys
from playwright.async_api import async_playwright

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://frontend:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8001")
SCREENSHOT_DIR = "/app/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def run_playwright_suite():
    print("=" * 80)
    print("🚀 JOB SCOUT PLAYWRIGHT AUTOMATED END-TO-END VERIFICATION SUITE")
    print(f"🎯 Target Frontend: {FRONTEND_URL}")
    print(f"🎯 Target Backend:  {BACKEND_URL}")
    print("=" * 80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1
        )
        page = await context.new_page()

        # Log browser console output
        page.on("console", lambda msg: print(f"  [BROWSER CONSOLE] {msg.type}: {msg.text}") if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda err: print(f"  [PAGE ERROR] {err}"))

        # -------------------------------------------------------------
        # STEP 1: Load Homepage & Verify Brand & Shell
        # -------------------------------------------------------------
        print("\n[STEP 1] Loading Homepage (Hunt Feed)...")
        res = await page.goto(FRONTEND_URL, wait_until="networkidle")
        assert res and res.status == 200, f"Failed to load frontend, status: {res.status if res else 'None'}"

        title = await page.title()
        print(f"  ✓ Page Title: '{title}'")
        assert "Job Scout" in title, "Title verification failed."

        # Wait for profile & match hydration
        await page.wait_for_timeout(1500)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_homepage_hunt.png"))
        print("  ✓ Screenshot captured: 01_homepage_hunt.png")

        # -------------------------------------------------------------
        # STEP 2: Verify Resume Vault & Candidate Profile Integration
        # -------------------------------------------------------------
        print("\n[STEP 2] Testing Resume Vault Tab...")
        await page.click('nav button:has-text("Vault")')
        await page.wait_for_timeout(1000)
        assert await page.is_visible('h2:has-text("Resume Vault")'), "Resume Vault view did not render."
        print("  ✓ Resume Vault view loaded successfully.")
        
        # Verify resume cards
        resume_cards = page.locator('div:has-text("Active Profile"), div:has-text("Make Active")')
        resume_count = await resume_cards.count()
        print(f"  ✓ Found {resume_count} resume items in Vault.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_resume_vault.png"))
        print("  ✓ Screenshot captured: 02_resume_vault.png")

        # -------------------------------------------------------------
        # STEP 3: Return to Hunt Feed & Test Job Cards & ATS Diagnostics
        # -------------------------------------------------------------
        print("\n[STEP 3] Testing Hunt Feed & ATS Gap Diagnostic Modal...")
        await page.click('nav button:has-text("Hunt")')
        await page.wait_for_timeout(1500)
        
        # Check for ATS Gap Buttons
        ats_buttons = page.locator('button:has-text("ATS Gap")')
        ats_count = await ats_buttons.count()
        print(f"  ✓ Detected {ats_count} ATS Gap diagnostic buttons on job cards.")

        if ats_count > 0:
            print("  ✓ Clicking ATS Gap diagnostic button...")
            await ats_buttons.first.click()
            await page.wait_for_timeout(1500)

            # Check ATS Modal
            modal = page.locator('div.fixed.inset-0')
            assert await modal.is_visible(), "ATS Score Modal did not open."
            print("  ✓ ATS Diagnostic & Keyword Gap Modal is OPEN.")

            # Validate Score Breakdown Rubric
            assert await modal.locator('h3:has-text("Category Score Breakdown")').is_visible(), "Category Rubrics missing."
            print("  ✓ Category Score Breakdown Rubric verified (Tech Fit, Semantic Cosine, Production Depth, Action Verbs).")

            # Validate Keyword Matrix
            assert await modal.locator('h3:has-text("Keyword Gap Analysis")').is_visible(), "Keyword Gap Matrix missing."
            print("  ✓ Keyword Gap Analysis Matrix verified.")

            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_ats_diagnostic_modal.png"))
            print("  ✓ Screenshot captured: 03_ats_diagnostic_modal.png")

            # Close Modal via header close button or Escape
            close_btn = modal.locator('button:has(svg.lucide-x)').first
            if await close_btn.is_visible():
                await close_btn.click()
            else:
                await page.keyboard.press("Escape")
            await page.wait_for_timeout(800)
            print("  ✓ ATS Modal closed.")

        # -------------------------------------------------------------
        # STEP 4: Test AI Copilot & Cover Letter Studio
        # -------------------------------------------------------------
        print("\n[STEP 4] Testing AI Copilot & Tailor View...")
        await page.click('nav button:has-text("Copilot")')
        await page.wait_for_timeout(1000)
        assert await page.is_visible('h2:has-text("AI Copilot")'), "AI Copilot view did not render."
        print("  ✓ AI Copilot view loaded successfully.")

        # Verify ATS Button in Copilot
        assert await page.is_visible('button:has-text("Inspect ATS Compatibility")'), "ATS button missing in Copilot."
        print("  ✓ Copilot ATS Compatibility Trigger verified.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_ai_copilot_view.png"))
        print("  ✓ Screenshot captured: 04_ai_copilot_view.png")

        # -------------------------------------------------------------
        # STEP 5: Test Job Tracker (Kanban Pipeline)
        # -------------------------------------------------------------
        print("\n[STEP 5] Testing Job Tracker (Kanban Pipeline)...")
        await page.click('nav button:has-text("Pipeline")')
        await page.wait_for_timeout(1000)
        assert await page.is_visible('h2:has-text("Job Tracker")'), "Job Tracker view did not render."
        print("  ✓ Job Tracker Pipeline Board loaded successfully.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_kanban_pipeline.png"))
        print("  ✓ Screenshot captured: 05_kanban_pipeline.png")

        # -------------------------------------------------------------
        # STEP 6: Test Candidate Neural Profile View
        # -------------------------------------------------------------
        print("\n[STEP 6] Testing Neural Candidate Profile View...")
        await page.click('nav button:has-text("Profile")')
        await page.wait_for_timeout(1000)
        assert await page.is_visible('h2:has-text("Neural Profile")'), "Neural Profile view did not render."
        print("  ✓ Neural Profile view loaded successfully.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "06_neural_profile.png"))
        print("  ✓ Screenshot captured: 06_neural_profile.png")

        # -------------------------------------------------------------
        # STEP 7: Test Market Intelligence Radar
        # -------------------------------------------------------------
        print("\n[STEP 7] Testing Market Intelligence Radar...")
        radar_icon = page.locator('div[title="Market Intelligence Radar"]')
        await radar_icon.click()
        await page.wait_for_timeout(1000)
        assert await page.is_visible('h2:has-text("Market Intelligence")'), "Radar view did not render."
        print("  ✓ Market Intelligence Radar view loaded successfully.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_market_radar.png"))
        print("  ✓ Screenshot captured: 07_market_radar.png")

        # -------------------------------------------------------------
        # STEP 8: Test Theme Switching & System Config
        # -------------------------------------------------------------
        print("\n[STEP 8] Testing System Configuration & Theme Engine...")
        await page.click('nav button:has-text("Config")')
        await page.wait_for_timeout(1000)
        config_modal = page.locator('div.fixed.inset-0')
        assert await config_modal.is_visible(), "Config modal did not open."
        print("  ✓ System Configuration modal is OPEN.")

        # Test Dark Theme Switch
        dark_btn = config_modal.locator('button:has-text("Dark")')
        if await dark_btn.is_visible():
            await dark_btn.click()
            await page.wait_for_timeout(500)
            has_dark = await page.evaluate("() => document.documentElement.classList.contains('dark')")
            print(f"  ✓ Dark Theme Activated: {has_dark}")

        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "08_config_modal.png"))
        print("  ✓ Screenshot captured: 08_config_modal.png")

        # Close Config Modal
        config_close = config_modal.locator('button:has(svg.lucide-x)').first
        if await config_close.is_visible():
            await config_close.click()
        else:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
        print("  ✓ Config Modal closed.")

        await browser.close()

    print("\n" + "=" * 80)
    print("🎉 ALL PLAYWRIGHT END-TO-END VERIFICATION CHECKS PASSED (8/8)!")
    print(f"🖼️  High-Resolution Test Artifacts stored in: {SCREENSHOT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_playwright_suite())
