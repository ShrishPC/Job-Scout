# 🚀 Job Scout: Neural Job Discovery & Tracking

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=nextdotjs)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Celery](https://img.shields.io/badge/Celery-Distributed-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

Job Scout is a modern, privacy-focused, full-stack job discovery and application tracking system. By leveraging local AI models (**SentenceTransformers** and **TinyLlama**), Job Scout matches your resume with real-time web-scraped job postings using vector similarity, providing a "Tinder-like" swipe-and-track dashboard for your career hunt.

---

## ✨ Key Features

*   **🧠 Neural Matching (Semantic Search)**: Generates high-dimensional vector embeddings of your resume. Uses PostgreSQL's `pgvector` extension to rank and match jobs based on semantic relevance instead of rigid keyword matching.
*   **📂 Resume Vault**: Store, activate, and manage multiple resume profiles. Switching active resumes instantly updates your job matching scores across the platform.
*   **🤖 Local AI Parser**: Automatically extracts candidate names, contact details, skills, education, and work history from resumes locally on your CPU.
*   **🕷️ Automated Scraping Pipeline**: Celery background tasks trigger Playwright scrapers in parallel to pull fresh postings from LinkedIn, Indeed, Naukri, RemoteOK, and We Work Remotely.
*   **📋 Kanban Board**: Move jobs through a visual application pipeline (Interested ➔ Applied ➔ Interviewing ➔ Offer).
*   **📊 Market Radar & Insights**: Highlights target roles, preferred locations, and matches your skill set against real-time market demands using interactive radar charts.
*   **🎨 Neo-Brutalist Responsive Theme System**: Stark, vibrant Neo-Brutalist design that dynamically toggles between a colorful warm-cream Light mode and a deep Midnight-Indigo Cyberpunk Dark mode (`#090a0f`) with a glowing violet grid paper effect (`rgba(99, 102, 241, 0.08)`). Thick black outlines and offsets are preserved globally.
*   **⚙️ System Config & Diagnostics Panel**: Access settings directly from the navigation bar. Toggle visual interface mode (Light, Dark, or System-preferred sync) and check server diagnostics (Backend API connection status, pgvector engine activation, environment parameters) in real-time.
*   **🔒 Privacy First**: 100% offline resume parsing and embedding generation—no data leaves your machine or goes to external paid APIs (like OpenAI or Anthropic).

---

## 🏗️ System Architecture

![System Architecture](assets/system_architecture.jpg)

*   **Embeddings Model**: `all-MiniLM-L6-v2` (384-dimensional vector padded to 768d for schema compatibility, running locally).
*   **Text Generator Model**: `TinyLlama-1.1B-Chat-v1.0` (Local resume extraction on CPU).

---

## 🚦 Getting Started

### Prerequisites

Ensure you have the following installed:
*   [Docker & Docker Compose](https://docs.docker.com/get-docker/)
*   [Node.js (v18+) & npm](https://nodejs.org/)
*   [Python (v3.10+)](https://www.python.org/)

---

### ⚡ Quick Start: One-Command Boot (Recommended)

Job Scout comes with a self-bootstrapping launcher. Run the script from the project root:

**For Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

**For Windows (PowerShell):**
```powershell
.\run.ps1
```

> **⚠️ Warning**: If you encounter an `ExecutionPolicy` error, you can temporarily bypass it by running:
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\run.ps1
> ```

**What this script does automatically:**
1.  Checks that Docker is active.
2.  Creates local configuration files (`.env` and `backend/.env`) from templates.
3.  Initializes isolated Python virtual environments (`venv`) for the backend and scraper.
4.  Installs all required dependencies (`pip install`, `npm install`).
5.  Pre-downloads local AI models to avoid request timeouts.
6.  Installs Playwright browser dependencies.
7.  Launches PostgreSQL, Redis, FastAPI, Celery Workers, and the Next.js Dev Server.

To shut down all services cleanly, press `Ctrl+C` in your terminal.

---

### 🐳 Setup via Docker Compose (100% Containerized)

You can run the entire stack containerized using Docker Compose:

```bash
# 1. Download local models to prevent startup timeouts
python3 -m venv setup_venv && source setup_venv/bin/activate
pip install sentence-transformers transformers torch
python scripts/download_models.py
deactivate && rm -rf setup_venv

# 2. Start all services containerized
docker compose up --build
```

---

### 🛠️ Manual Step-by-Step Installation

If you prefer to run services manually, open four terminal windows and execute the following:

#### 1. Database & Message Broker (Docker)
```bash
docker compose up -d db redis
```

#### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python init_db.py         # Run DB migrations
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 3. Scraper Setup
```bash
cd scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
celery -A celery_app worker --loglevel=info
```
*(In a separate terminal, launch the scheduler: `celery -A celery_app beat --loglevel=info`)*

#### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```text
├── backend/                  # FastAPI Backend API
│   ├── app/
│   │   ├── core/             # DB setup & Configuration
│   │   ├── models/           # SQLAlchemy models with pgvector columns
│   │   ├── services/         # Embedding generation & LLM parsing logic
│   │   └── main.py           # API endpoints and routers
│   ├── requirements.txt      # Backend Python dependencies
│   └── Dockerfile            # Backend Docker build instructions
├── frontend/                 # Next.js Frontend App
│   ├── src/
│   │   ├── components/ui/    # UI elements (JobCard, FileUpload, Kanban)
│   │   └── app/              # App router (globals, page layouts)
│   └── package.json          # Frontend Node dependencies
├── scraper/                  # Scrapers & Task Engine
│   ├── celery_app.py         # Celery task configuration
│   ├── tasks.py              # Background scraping workflows
│   ├── linkedin_scraper.py   # Playwright scraper module
│   ├── requirements.txt      # Scraper Python dependencies
│   └── Dockerfile            # Scraper Docker build instructions
├── scripts/                  # Helper Utilities
│   ├── download_models.py    # Downloads and caches LLMs locally
│   └── pdf_to_md.py          # Standalone PDF converter
└── docker-compose.yml        # Orchestration file for all services
```

---

## 📝 Environment Variables

The default setup is designed to run locally out-of-the-box. If you deploy this to production, update the `.env` settings:

```env
# Database configuration url (pgvector driver compatibility)
DATABASE_URL=postgresql://postgres:password@localhost:5432/job_scout

# Redis broker URL
REDIS_URL=redis://localhost:6379/0

# CORS Allowed Origins (Comma-separated allowed client-side addresses)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🔒 Security & Privacy Notice

*   **Data Protection**: Job Scout was built to preserve candidate data privacy. Your resume text, contact parameters, and application notes never exit your machine, protecting high-value PII.
*   **SQL Injection Prevention**: All raw database commands utilize bound parameters to prevent input attacks.
*   **XSS Protection**: Frontend components render text properties safely inside native React containers rather than using raw HTML injection.
*   **Secrets Safety**: Do not check active database passwords or credentials into GitHub. The local `.env` configuration is untracked by Git.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

*Disclaimer: Job Scout scrapers are intended for educational and personal use only. Please respect the Terms of Service and scraping guidelines of the platforms being targeted.*
