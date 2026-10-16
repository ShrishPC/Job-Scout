# Job Scout Academic & Defense Documentation Suite

This directory contains the complete academic documentation, presentation slide decks, and examination defense manuals for **Job Scout: An Air-Gapped Semantic Job Discovery & Local Generative Platform**.

---

## 1. Master Thesis & Comprehensive Reports (`PDF/`)
* **[`Job_Scout_Complete_Report.pdf`](./PDF/Job_Scout_Complete_Report.pdf)** (89 Pages):
  * The full formal university thesis report covering Problem Formulation, Literature Review, System Analysis & Design (UML, DFD, ERD), System Implementation, Automated Testing Suite (126 tests, 79% line coverage), Empirical Benchmarking (HNSW parameter sweeps, Two-Stage Hybrid Latency, Retrieval Metrics), Limitations, and Appendices.
* **[`Nit-picked-Questions.pdf`](./PDF/Nit-picked-Questions.pdf)** (51 Pages):
  * The comprehensive viva voce defense manual containing 53 hostile examiner trap questions (Q1–Q53), the Claude Security Audit remediations (CWE-89 SQL injection parameterization, CWE-22 path traversal defense, admin API key dependency injection), DDR4 memory bus latency physics, and word-for-word spoken defense scripts.

## 2. Editable Document Source Files
* **[`Nit-picked-Questions.docx`](./Nit-picked-Questions.docx)**:
  * Full editable Microsoft Word source for the 51-page defense manual with professional formatting, Arial headings, Calibri body, alert callouts, and styled tables.

## 3. Defense Presentations (`Presentation/`)
* **[`job-scout-canva.pptx`](./Presentation/job-scout-canva.pptx)**:
  * The approved 16-slide presentation deck incorporating the 15-second abstract pivot, system architecture, hybrid search precision, local RAG synthesis, and empirical benchmarks.
* **[`Job_Scout_Defense_Presentation.pptx`](./Presentation/Job_Scout_Defense_Presentation.pptx)**:
  * Standalone PowerPoint defense deck.
* **[`generate_deck.py`](./Presentation/generate_deck.py)** & **[`generate_lively_deck.py`](./Presentation/generate_lively_deck.py)**:
  * Programmatic presentation generation scripts using `python-pptx`.
