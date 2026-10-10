# 🚀 Job Scout: AI-Powered Job Discovery & ATS Optimization

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)
![pgvector](https://img.shields.io/badge/pgvector-Supported-success.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)

**Job Scout** is a privacy-first, Retrieval-Augmented Generation (RAG) platform designed to bridge the semantic gap between applicants and Applicant Tracking Systems (ATS). By utilizing local AI models and vector similarity search, it matches candidates to ideal roles and generates highly tailored application materials—all without transmitting sensitive personal data to external cloud APIs.

## ✨ Key Features

- **Semantic Vector Matching:** Uses `all-MiniLM-L6-v2` and PostgreSQL (`pgvector`) with an HNSW index to match resumes to job descriptions based on contextual meaning, not just exact keywords.
- **100% Offline AI Generation:** Integrates `Llama-3.2-3B-Instruct` locally via PyTorch to generate ATS-optimized cover letters and resume bullets, guaranteeing zero data leakage.
- **Automated Job Scraping:** Asynchronous Celery workers periodically extract and index job listings from target career portals.
- **Microservices Architecture:** Fully containerized environment comprising FastAPI, Next.js, Redis, and PostgreSQL.
- **Sub-10ms Query Latency:** Optimized vector indexing guarantees rapid candidate-to-job matching, verified by included benchmarking scripts.

---

## 🏗️ Architecture

Job Scout is built on a containerized microservices architecture:

1. **Frontend (Next.js):** React-based UI with Server-Sent Events (SSE) for streaming LLM outputs.
2. **Backend API (FastAPI):** Python REST API handling orchestration, RAG logic, and model inference.
3. **Database (PostgreSQL + pgvector):** Relational and vector storage for resumes and job embeddings.
4. **Message Broker (Redis):** Task queuing for background jobs.
5. **Worker (Celery):** Handles asynchronous web scraping and bulk embedding tasks.
6. **Scheduler (Celery-Beat):** Triggers periodic pipeline updates.

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed on your host machine:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- At least 8GB of free RAM (for running the local LLM in `bfloat16` precision)

---

## 🚀 Quick Start

**1. Clone the repository**
```bash
git clone https://github.com/ShrishPC/Job-Scout.git
cd job-scout
```

**2. Start the Docker containers**
```bash
docker compose up --build -d
```
*Note: On the first boot, the backend will download the `all-MiniLM-L6-v2` and `Llama-3.2` models. This may take a few minutes depending on your internet connection.*

**3. Access the Application**
- **Frontend UI:** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger):** [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 📊 Performance Benchmarking

To prove the efficiency of the HNSW vector indexing, a benchmark script is included. It generates 10,000 mock 384-dimensional job embeddings and measures the latency of sequential scans vs. indexed graph traversal.

Run the benchmark inside the backend container:
```bash
docker compose exec backend python scripts/benchmark_pgvector.py
```
*Expected Output: Sequential scans (~140ms) vs. HNSW Index (~9ms).*

---

## 🔒 Security & Privacy

- **Offline Inference:** All AI/ML processing occurs on the host CPU/GPU. No resume data is sent to OpenAI, Anthropic, or any external vendor.
- **Vulnerability Mitigation:** Employs parameterized SQL queries to prevent injection attacks and UUID-based file handling to block Path Traversal.

---

## 👨‍💻 Author

**Shrish Prasad Chakraborty**  
Department of Computer Applications  
SRM Institute of Science and Technology  

---
*Developed as a Minor Project (2026-2027).*
