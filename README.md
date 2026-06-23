# 🚀 Job Scout: Neural Job Discovery & Tracking

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=nextdotjs)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Celery](https://img.shields.io/badge/Celery-Distributed-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Llama](https://img.shields.io/badge/Llama-3.2--3B-blueviolet?style=for-the-badge&logo=meta&logoColor=white)](https://huggingface.co/unsloth/Llama-3.2-3B-Instruct)

Job Scout is a modern, **100% local**, privacy-focused, full-stack job discovery and application tracking system. It uses a dual-track **Retrieval-Augmented Generation (RAG)** pipeline powered by `Llama-3.2-3B-Instruct` and `SentenceTransformers` to semantically match your resume with real-time web-scraped job postings — and generate tailored resumes and cover letters entirely on your own hardware. No cloud APIs. No data leaks.

---

## 👤 About

Job Scout was built to solve a real problem: the modern job hunt is noisy, repetitive, and privacy-invasive. Most AI job tools send your resume to third-party APIs (OpenAI, Anthropic) and lock insights behind paywalls.

This project takes a different approach:

- **Everything runs locally.** Your resume, your embeddings, your generated cover letters — all processed on your own CPU or GPU. Nothing leaves your machine.
- **AI that actually knows you.** The RAG pipeline reads your active resume semantically, finds the most relevant parts of your experience for each job, and injects them into the LLM prompt — so the output sounds like *you*, not a generic template.
- **Built for real job hunters.** From a Kanban board to track applications, to a Market Radar that maps your skills against live postings, to a one-command boot script that sets everything up — Job Scout is designed to be used daily, not just demoed.
- **Open and extensible.** The model, embedding dimensions, scraper targets, and hardware device (CPU/GPU) are all configurable via environment variables and the in-app Config panel.

> Built with Next.js 15, FastAPI, PostgreSQL + pgvector, Celery, Playwright, and Llama-3.2-3B-Instruct.

---

## 🎨 Visual Showcase

| 🌟 Warm Cream Light Theme | 📋 Kanban Board Tracker |
|:---:|:---:|
| ![Light Theme](assets/light_mode.png) | ![Pipeline Tracker](assets/pipeline.png) |

| 📂 Resume Vault | 👤 Neural Candidate Profile |
|:---:|:---:|
| ![Resume Vault](assets/vault.png) | ![Profile Details](assets/profile.png) |

### 🎥 Theme Sync Demo (Light / Dark Mode Transition)
<video src="assets/theme_c.mp4" width="100%" controls muted autoplay loop></video>

---

## ✨ Key Features

*   **🧠 Neural Matching (Semantic Search)**: Generates high-dimensional vector embeddings of your resume using `all-MiniLM-L6-v2`. Uses PostgreSQL's `pgvector` extension to rank and match jobs by semantic relevance instead of rigid keyword matching.
*   **🤖 AI Copilot — Resume Tailoring & Cover Letters**: A full-screen AI Copilot panel powered by `Llama-3.2-3B-Instruct`. Select any scraped job listing (or paste a custom description), choose a generation mode, and receive a tailored resume or personalised cover letter generated entirely on-device.
*   **🔍 Dual-Track RAG Pipeline**: Before generating, the system semantically retrieves the top 6 most relevant bullets from your active resume *and* the top 3 similar market job listings from the database — injecting this context into the LLM prompt to ground outputs in your real experience and current market language.
*   **⚡ AI Generation Cache**: SHA-256 hashed cache layer backed by PostgreSQL. Identical requests return instantly from cache (marked `"cached": true`). Cache can be cleared from the Config panel.
*   **🖥️ Dynamic Hardware Selector**: Switch AI inference between CPU and CUDA (GPU) at runtime via the Config panel — no restart required.
*   **📂 Resume Vault**: Store, activate, and manage multiple resume profiles. Switching active resumes instantly updates all matching scores across the platform.
*   **🕷️ Automated Scraping Pipeline**: Celery background tasks trigger Playwright scrapers in parallel to pull fresh postings from LinkedIn, Indeed, Naukri, RemoteOK, and We Work Remotely.
*   **📋 Kanban Board**: Move jobs through a visual application pipeline (Interested ➔ Applied ➔ Interviewing ➔ Offer).
*   **📊 Market Radar & Insights**: Highlights target roles, preferred locations, and matches your skill set against real-time market demands using interactive radar charts.
*   **🎨 Neo-Brutalist Responsive Theme System**: Stark, vibrant design toggling between warm-cream Light mode and deep Midnight-Indigo Cyberpunk Dark mode with a glowing violet grid paper effect. Thick black outlines and shadow offsets preserved globally.
*   **⚙️ System Config & Diagnostics Panel**: Toggle Light/Dark/System theme, switch AI device, clear AI cache, check backend connectivity and pgvector status in real-time.
*   **🔌 System Control**: Shut down or restart the entire Job Scout stack from the UI Exit modal — no terminal required.
*   **🔒 Privacy First**: 100% offline — resume parsing, vector embeddings, and LLM generation all run locally. Nothing is sent to external APIs.

---

## 🏗️ System Architecture

![System Architecture](assets/system_architecture.jpg)

*   **Embeddings Model**: `all-MiniLM-L6-v2` (384-dimensional vector padded to 768d for schema compatibility, running locally via `sentence-transformers`).
*   **Text Generator Model**: `unsloth/Llama-3.2-3B-Instruct` (Local inference on CPU or CUDA. Falls back to `TinyLlama-1.1B` if resources are insufficient).
*   **Vector Store**: PostgreSQL with the `pgvector` extension and HNSW index for O(log n) approximate nearest-neighbour search.
*   **Generation Strategy**: Deterministic greedy decoding (`do_sample=False`) with `repetition_penalty=1.2` to prevent hallucinations and ensure reproducible outputs.

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
