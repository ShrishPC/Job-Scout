# Job Scout Project - Conversation Context (Updated June 10, 2026)

## 1. Project Overview
**Job Scout** is a local-first, AI-powered job discovery and tracking pipeline. It uses local LLMs and Vector Embeddings to match user resumes against real-time scraped job listings from multiple global and regional sources.

## 2. Technical Stack
*   **Backend:** FastAPI (Python 3.14+)
*   **Frontend:** Next.js 15 (App Router, TypeScript, Tailwind CSS)
*   **Database:** PostgreSQL with `pgvector` for semantic search.
*   **Cache/Broker:** Redis
*   **Async Processing:** Celery + Celery Beat
*   **AI/NLP (Local-Only):**
    *   **Parsing:** TinyLlama-1.1B (via HuggingFace Transformers)
    *   **Embeddings:** all-MiniLM-L6-v2 (via SentenceTransformers)
    *   **Portability:** All models are cached in a project-relative `models/` directory.
*   **Scraping:** Playwright (Chromium), BeautifulSoup4, Requests, Feedparser.
*   **Document Parsing:** `markitdown` (PDF/DOCX support).

## 3. Key Achievements & Updates

### Infrastructure & Setup
*   **Dockerized Services:** DB (pgvector) and Redis are managed via Docker Compose.
*   **Environment:** Initialized `.env` files and verified all virtual environments and node modules.
*   **Schema:** Initialized the database schema with `init_db.py`.

### AI Architecture Refactor
*   **Removed Fast Mode (API):** Completely stripped out Google Gemini API dependencies (`google-genai`) and UI toggles. The system is now 100% local-first and free.
*   **Model Optimization:** Implemented persistent caching in the `models/` directory to ensure models are not re-downloaded when moving the project between machines.

### Expanded Job Discovery
*   **Multi-Source Scraper:** The system now fetches from 5 distinct sources:
    1.  **LinkedIn**: Optimized Discovery + Parallel Enrichment.
    2.  **Indeed**: Beacon-based scraping.
    3.  **Naukri.com**: Custom Playwright scraper for the Indian market.
    4.  **Remote OK**: Official JSON API integration for global remote roles.
    5.  **We Work Remotely**: RSS-based discovery for high-quality remote jobs.
*   **Batch Scraping:** The `/jobs/scrape` endpoint now supports `source="all"` to trigger parallel hunts across all platforms.

### UI & Core Features
*   **Vault**: Placeholder for managing multiple resume versions and career assets.
*   **Profile**: Manages the "Neural Identity" (structured skills and embeddings) parsed from the active resume.
*   **Bug Fixes:** Resolved syntax errors in the scraper's task logic and the frontend's main landing page.

## 4. Current Service Status
*   **Backend:** [http://localhost:8000](http://localhost:8000)
*   **Frontend:** [http://localhost:3000](http://localhost:3000)
*   **Scraper/Beat:** Running in background, logging to `scraper/scraper.log` and `scraper/beat.log`.

## 5. Next Steps / Left Off At
*   The system is fully initialized and discovery-ready.
*   Future work can focus on implementing the "Vault" file management or enhancing the "Market Intelligence Radar" visualization.
