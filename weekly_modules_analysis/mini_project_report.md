# Job Scout: An AI-Driven Resume Parsing and Job Matching Platform

<div align="center"><b>Abstract</b></div>

Modern job hunting is increasingly challenging due to the high volume of applicants and the rigid reliance on automated applicant tracking systems. This project aims to develop Job Scout, an intelligent, AI-driven platform that seamlessly matches candidates to relevant job postings by analyzing their resumes using advanced Retrieval-Augmented Generation (RAG) and hybrid vector search techniques. The system integrates a Next.js frontend with a FastAPI backend, utilizing a PostgreSQL database equipped with pgvector for high-performance cosine similarity calculations. Automated web scrapers gather real-time job listings, while a local Large Language Model (Llama-3.2-3B) parses user resumes, generates high-dimensional embeddings, and tailors application assets like cover letters. The implemented platform successfully provides highly personalized job recommendations, filters opportunities based on multi-dimensional skill matrices, and visualizes candidate capabilities through an interactive radar chart, all while running efficient background updates via Celery. By automating the tedious aspects of job discovery and application tailoring, this system significantly reduces candidate fatigue and bridges the gap between employer requirements and applicant competencies in the contemporary digital recruitment landscape.

*Keywords*: Retrieval-Augmented Generation, Resume Parsing, Artificial Intelligence, Job Matching, Vector Search.

---

## Weekly Modules Breakdown

**Module 1: System Design and Frontend Foundation**
- Gathered requirements and designed the database schema with pgvector for high-dimensional embeddings.
- Initialized the Next.js frontend with a custom Brutalist UI design system using Tailwind CSS.
- Defined core REST API endpoints and initialized the FastAPI backend structure.

**Module 2: Automated Data Aggregation and Queuing**
- Developed web scrapers using Selenium and BeautifulSoup to fetch live job postings from LinkedIn and Indeed.
- Integrated Celery and Redis to handle asynchronous background scraping tasks on a recurring schedule.
- Built heuristics for remote/hybrid workplace classification and job data normalization.

**Module 3: Resume Parsing and Knowledge Extraction**
- Built file upload pipelines supporting PDF parsing via PyMuPDF and markdown formatting.
- Integrated LLM-based skill extraction to identify candidates' key competencies, experience, and educational background.
- Established the Vault interface for users to manage multiple resume profiles.

**Module 4: Retrieval-Augmented Generation (RAG) Engine**
- Integrated a locally hosted Llama-3.2-3B model utilizing Unsloth and Hugging Face Transformers.
- Designed a hybrid RAG search matching algorithm combining cosine similarity on resume embeddings with keyword boosting.
- Implemented the Hunt dashboard featuring live search filters and skill gap analysis via dynamic radar charts.

**Module 5: Generative AI Copilot and System Polish**
- Developed the AI Copilot feature for generating tailored cover letters and resume revision suggestions.
- Implemented server-side streaming (Server-Sent Events) for real-time generative feedback.
- Finalized end-to-end testing, dockerized the architecture, and deployed the Next.js, FastAPI, PostgreSQL, and Celery containers.
