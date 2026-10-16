import sys
import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import subprocess

prs = Presentation()
prs.slide_width = Inches(13.333)  # 16:9 widescreen
prs.slide_height = Inches(7.5)

# Color Palette: Dark AI / Tech Aesthetic
BG_NAVY = RGBColor(10, 17, 40)          # #0A1128 Deep Tech Navy
CARD_BG = RGBColor(16, 28, 60)          # #101C3C Tech Card Navy
CARD_BORDER = RGBColor(24, 45, 90)      # #182D5A Subtle Grid Line
CYAN_ACCENT = RGBColor(0, 240, 255)     # #00F0FF Glowing Electric Cyan
TEXT_WHITE = RGBColor(240, 246, 255)    # #F0F6FF Crisp White
TEXT_MUTED = RGBColor(148, 163, 184)    # #94A3B8 Slate Gray
GREEN_ACCENT = RGBColor(34, 197, 94)    # #22C55E Metric Success Green
ALERT_ACCENT = RGBColor(244, 63, 94)    # #F43F5E Metric Alert Coral

def apply_background(slide):
    # Add deep navy background shape
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_NAVY
    bg.line.color.rgb = BG_NAVY
    # Top subtle tech border glow line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = CYAN_ACCENT
    line.line.color.rgb = CYAN_ACCENT
    return bg

def add_header(slide, title_text, category_text="JOB SCOUT // DEFENSE PRESENTATION"):
    # Category tag
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf_cat = cat_box.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = "Arial"
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = CYAN_ACCENT
    
    # Title
    t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.8))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.name = "Arial"
    p_t.font.size = Pt(24)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_WHITE

def create_card(slide, left, top, width, height, title=None, border_color=CARD_BORDER):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = border_color
    card.line.width = Pt(1.2)
    
    if title:
        tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.4))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = title.upper()
        p.font.name = "Arial"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = CYAN_ACCENT
    return card

blank_slide_layout = prs.slide_layouts[6]

# -------------------------------------------------------------
# SLIDE 1: TITLE SLIDE
# -------------------------------------------------------------
s1 = prs.slides.add_slide(blank_slide_layout)
apply_background(s1)

# Center Title Box
title_card = create_card(s1, Inches(1.5), Inches(1.8), Inches(10.333), Inches(4.2), border_color=CYAN_ACCENT)

# Badge
badge = s1.shapes.add_textbox(Inches(2.0), Inches(2.2), Inches(9.333), Inches(0.4))
p_b = badge.text_frame.paragraphs[0]
p_b.text = "MASTER OF SCIENCE IN APPLIED DATA SCIENCE  |  FINAL PROJECT DEFENSE"
p_b.font.name = "Arial"
p_b.font.size = Pt(11)
p_b.font.bold = True
p_b.font.color.rgb = CYAN_ACCENT

# Main Title
m_title = s1.shapes.add_textbox(Inches(2.0), Inches(2.7), Inches(9.333), Inches(1.5))
p_m = m_title.text_frame.paragraphs[0]
p_m.text = "JOB SCOUT"
p_m.font.name = "Arial"
p_m.font.size = Pt(44)
p_m.font.bold = True
p_m.font.color.rgb = TEXT_WHITE

p_sub = m_title.text_frame.add_paragraph()
p_sub.text = "AI-Powered Job Discovery & ATS Optimization Platform"
p_sub.font.name = "Arial"
p_sub.font.size = Pt(20)
p_sub.font.color.rgb = CYAN_ACCENT

# Metadata Box
meta = s1.shapes.add_textbox(Inches(2.0), Inches(4.5), Inches(9.333), Inches(1.2))
tf_meta = meta.text_frame
p1 = tf_meta.paragraphs[0]
p1.text = "Candidate: Shrish Prasad Chakraborty (Reg. No: RA2532014010136)  |  Guide: Dr. R. Thilagavathy"
p1.font.name = "Arial"
p1.font.size = Pt(12)
p1.font.bold = True
p1.font.color.rgb = TEXT_WHITE

p2 = tf_meta.add_paragraph()
p2.text = "SRM Institute of Science & Technology  |  Department of Computer Applications"
p2.font.name = "Calibri"
p2.font.size = Pt(11)
p2.font.color.rgb = TEXT_MUTED

p3 = tf_meta.add_paragraph()
p3.text = "Repository: https://github.com/ShrishPC/Job-Scout.git  |  Local Target: /home/rishav/job-scout/"
p3.font.name = "Calibri"
p3.font.size = Pt(10)
p3.font.color.rgb = CYAN_ACCENT

# -------------------------------------------------------------
# SLIDE 2: PROBLEM STATEMENT & OBJECTIVES
# -------------------------------------------------------------
s2 = prs.slides.add_slide(blank_slide_layout)
apply_background(s2)
add_header(s2, "The Real-World Crisis & System Objectives")

# Left Card: The ATS Crisis
create_card(s2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="THE RECRUITMENT ASYMMETRY CRISIS", border_color=ALERT_ACCENT)
tb_left = s2.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.2), Inches(4.4))
tf_l = tb_left.text_frame
tf_l.word_wrap = True

bullets_l = [
    ("75% Black-Box ATS Rejection:", " Opaque keyword filters discard qualified candidates over lexical discrepancies without semantic parsing."),
    ("Severe Privacy & PII Exposure:", " Cloud resume tools leak full employment histories, contact info, and proprietary code to third-party LLM APIs."),
    ("SaaS Paywalls & Inefficiency:", " Subscription models charge recurring fees while candidates juggle manual searches across 5+ fragmented job portals.")
]
for i, (b_title, b_desc) in enumerate(bullets_l):
    p = tf_l.paragraphs[0] if i == 0 else tf_l.add_paragraph()
    p.space_after = Pt(14)
    r1 = p.add_run()
    r1.text = "• " + b_title
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = ALERT_ACCENT
    r2 = p.add_run()
    r2.text = b_desc
    r2.font.size = Pt(11)
    r2.font.color.rgb = TEXT_WHITE

# Right Card: Project Objectives
create_card(s2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="CORE SYSTEM OBJECTIVES", border_color=CYAN_ACCENT)
tb_right = s2.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.4))
tf_r = tb_right.text_frame
tf_r.word_wrap = True

bullets_r = [
    ("Autonomous Job Harvesting:", " Build a multi-source headless scraper for 5 portals (LinkedIn, Indeed, Naukri, RemoteOK, WWR) with Redis/Celery."),
    ("Two-Stage Hybrid Matchmaking:", " Merge 70% semantic vector search (pgvector HNSW) + 30% keyword frequency for sub-10ms matching."),
    ("Deterministic ATS Scoring:", " Engineer an explainable 100-point diagnostic rubric identifying hard/soft skill gaps with zero AI hallucination."),
    ("Air-Gapped Local LLM Tailoring:", " Execute on-device RAG synthesis via Llama-3.2-3B, delivering 100% data sovereignty with zero cloud API costs.")
]
for i, (b_title, b_desc) in enumerate(bullets_r):
    p = tf_r.paragraphs[0] if i == 0 else tf_r.add_paragraph()
    p.space_after = Pt(14)
    r1 = p.add_run()
    r1.text = "• " + b_title
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = CYAN_ACCENT
    r2 = p.add_run()
    r2.text = b_desc
    r2.font.size = Pt(11)
    r2.font.color.rgb = TEXT_WHITE

# -------------------------------------------------------------
# SLIDE 3: EXISTING SYSTEM VS PROPOSED SYSTEM
# -------------------------------------------------------------
s3 = prs.slides.add_slide(blank_slide_layout)
apply_background(s3)
add_header(s3, "Architectural Comparison: Existing Systems vs. Job Scout")

headers = ["Operational Dimension", "Traditional / Commercial ATS Tools", "Job Scout Platform (Proposed)"]
data = [
    ["Search & Matching", "Exact lexical keywords (misses conceptual synonyms)", "Two-stage hybrid: 70% semantic (HNSW) + 30% keyword"],
    ["Candidate Data Privacy", "Third-party cloud transmission; PII retention risk", "100% Air-gapped on-device processing; zero egress"],
    ["Cost & Accessibility", "Recurring SaaS paywalls ($20-$50/month per user)", "Zero API cost; self-hosted open-source architecture"],
    ["ATS Diagnostics", "Opaque percentage score; non-actionable suggestions", "Deterministic 100-point rubric; exact keyword gap analysis"],
    ["Content Generation", "Cloud LLMs (OpenAI/Claude API) or rigid templates", "Local RAG via Llama-3.2-3B with SSE token streaming"],
    ["Data Harvesting", "Manual browsing or vendor-locked proprietary feeds", "Autonomous Celery task queue scraping 5 live portals"]
]

table_shape = s3.shapes.add_table(len(data) + 1, 3, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.8))
table = table_shape.table
table.columns[0].width = Inches(2.3)
table.columns[1].width = Inches(4.7)
table.columns[2].width = Inches(4.7)

for col_idx, h in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = CARD_BORDER
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.name = "Arial"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT if col_idx == 2 else TEXT_WHITE

for row_idx, r in enumerate(data):
    for col_idx, val in enumerate(r):
        cell = table.cell(row_idx + 1, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_BG if row_idx % 2 == 0 else RGBColor(12, 22, 50)
        p = cell.text_frame.paragraphs[0]
        p.text = val
        p.font.name = "Calibri"
        p.font.size = Pt(10)
        p.font.color.rgb = CYAN_ACCENT if col_idx == 2 else (ALERT_ACCENT if col_idx == 1 and row_idx < 3 else TEXT_WHITE)

# -------------------------------------------------------------
# SLIDE 4: SYSTEM ARCHITECTURE
# -------------------------------------------------------------
s4 = prs.slides.add_slide(blank_slide_layout)
apply_background(s4)
add_header(s4, "System Architecture: Decoupled 4-Tier Microservice Topology")

# 4 Tier Cards
tiers = [
    ("TIER 1: PRESENTATION", "Next.js 14 / React 18 SPA\n• Dark glassmorphic interface\n• Server-Sent Events (SSE) listener\n• Interactive Kanban board\n• Real-time ATS visualizer", Inches(0.8)),
    ("TIER 2: APPLICATION API", "FastAPI / Uvicorn Service\n• Pydantic schema validation\n• SentenceTransformer engine\n• Two-stage hybrid SQL generator\n• 100-point ATS rubric calculator", Inches(3.8)),
    ("TIER 3: DATA & VECTORS", "PostgreSQL 16 + pgvector\n• HNSW index (m=16, ef=128)\n• Session ef_search=400 clamp\n• Composite indexing on workplace\n• Full-text TSVECTOR integration", Inches(6.8)),
    ("TIER 4: ASYNC WORKERS", "Redis 7.2 + Celery 5.3\n• Distributed scraper task broker\n• Playwright 1.44 headless daemon\n• SHA-256 LLM response cache\n• Deduplication fingerprinting", Inches(9.8))
]

for title, body, left in tiers:
    create_card(s4, left, Inches(1.6), Inches(2.7), Inches(5.0), title=title, border_color=CYAN_ACCENT)
    tb = s4.shapes.add_textbox(left + Inches(0.15), Inches(2.2), Inches(2.4), Inches(4.2))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(body.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.name = "Calibri"
        p.font.size = Pt(11) if i == 0 else Pt(10)
        p.font.bold = (i == 0)
        p.font.color.rgb = CYAN_ACCENT if i == 0 else TEXT_WHITE
        p.space_after = Pt(4)

# -------------------------------------------------------------
# SLIDE 5: TECHNOLOGIES USED
# -------------------------------------------------------------
s5 = prs.slides.add_slide(blank_slide_layout)
apply_background(s5)
add_header(s5, "Technology Stack: On-Device High-Performance Infrastructure")

stack_groups = [
    ("CORE BACKEND & API", [
        ("FastAPI (Python 3.11):", "Asynchronous high-throughput ASGI framework with native Pydantic validation."),
        ("SQLAlchemy 2.0 ORM:", "Session pooling (pool_size=10, max_overflow=20) with pre-ping validation."),
        ("PostgreSQL 16 + pgvector:", "Relational persistence with vector similarity indexing in a single engine.")
    ], Inches(0.8), Inches(1.6)),
    ("EMBEDDINGS & LOCAL LLM", [
        ("all-MiniLM-L6-v2:", "384-dimensional sentence transformer generating embeddings in ~5ms on CPU."),
        ("Llama-3.2-3B-Instruct:", "SOTA small language model running 100% locally via PyTorch & Transformers."),
        ("TinyLlama-1.1B:", "Ultra-lightweight secondary fallback model for low-resource environments.")
    ], Inches(6.8), Inches(1.6)),
    ("ASYNCHRONOUS ENGINE", [
        ("Redis 7.2 Cache & Broker:", "In-memory broker for Celery queues and SHA-256 response caching."),
        ("Celery 5.3 Distributed Queue:", "Non-blocking background job scheduling across multiple scraper workers."),
        ("Playwright 1.44 Headless:", "Robust browser automation handling dynamic Single-Page Applications.")
    ], Inches(0.8), Inches(4.3)),
    ("FRONTEND & DEVOPS", [
        ("Next.js 14 & React 18:", "Component-driven frontend optimized for real-time SSE streaming."),
        ("Docker & Docker Compose:", "Multi-container orchestration providing one-command reproducible setups."),
        ("pytest Testing Suite:", "126 automated test cases verifying 79% backend line coverage.")
    ], Inches(6.8), Inches(4.3))
]

for title, items, left, top in stack_groups:
    create_card(s5, left, top, Inches(5.7), Inches(2.6), title=title, border_color=CYAN_ACCENT)
    tb = s5.shapes.add_textbox(left + Inches(0.2), top + Inches(0.55), Inches(5.3), Inches(1.9))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, (b_title, b_desc) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(4)
        r1 = p.add_run()
        r1.text = "• " + b_title + " "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = CYAN_ACCENT
        r2 = p.add_run()
        r2.text = b_desc
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = TEXT_WHITE

# -------------------------------------------------------------
# SLIDE 6: IMPLEMENTATION & KEY FEATURES
# -------------------------------------------------------------
s6 = prs.slides.add_slide(blank_slide_layout)
apply_background(s6)
add_header(s6, "Implementation Highlights: 4 Engineering Milestones")

features = [
    ("MILESTONE 1: RESUME PARSING", [
        "Multi-engine pipeline supporting PDF, DOCX, and TXT formats.",
        "Regex heuristics strip tables, headers, and binary formatting noise.",
        "Generates clean, standardized Markdown for vectorization and prompt injection."
    ], Inches(0.8), Inches(1.6)),
    ("MILESTONE 2: TWO-STAGE HYBRID SQL", [
        "Stage 1 filters top 200 candidate IDs via pgvector HNSW in 2.88 ms.",
        "Stage 2 evaluates keyword ILIKE frequency only on candidates in 1.45 ms.",
        "Achieves 9.08 ms end-to-end API latency (98.1x faster than single-stage legacy)."
    ], Inches(6.8), Inches(1.6)),
    ("MILESTONE 3: DETERMINISTIC ATS RUBRIC", [
        "100-point explainable score: Hard Skills (40), Soft (20), Exp (25), Edu (10), Format (5).",
        "Deterministic frequency-weighted keyword gap analysis isolates missing skills.",
        "Zero LLM hallucination in ATS scoring; 100% reproducible diagnostic math."
    ], Inches(0.8), Inches(4.3)),
    ("MILESTONE 4: LOCAL RAG & SSE STREAMING", [
        "Llama-3.2-3B synthesizes tailored executive summary + 3 STAR bullet points.",
        "FastAPI Server-Sent Events (SSE) stream tokens with first-token latency of 1.2s.",
        "SHA-256 Redis cache returns identical queries in 2.00 ms (30,637x acceleration)."
    ], Inches(6.8), Inches(4.3))
]

for title, bullets, left, top in features:
    create_card(s6, left, top, Inches(5.7), Inches(2.6), title=title, border_color=CYAN_ACCENT)
    tb = s6.shapes.add_textbox(left + Inches(0.2), top + Inches(0.55), Inches(5.3), Inches(1.9))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(4)
        r = p.add_run()
        r.text = "• " + b
        r.font.size = Pt(10)
        r.font.color.rgb = TEXT_WHITE

# -------------------------------------------------------------
# SLIDE 7: RESULTS & PERFORMANCE EVALUATION
# -------------------------------------------------------------
s7 = prs.slides.add_slide(blank_slide_layout)
apply_background(s7)
add_header(s7, "Empirical Validation: Benchmarks & Measured Outcomes")

# 4 Metric Highlight Cards
metrics = [
    ("9.08 ms", "API Latency (100k Rows)", "POST /jobs/matches (98.1x speedup)", Inches(0.8)),
    ("0.9565", "HNSW Recall@10", "Tuned at ef_search=400 (2.88 ms)", Inches(3.8)),
    ("0.985", "Retrieval NDCG@10", "Hybrid Ranking (P@5 = 0.986, MRR = 1.0)", Inches(6.8)),
    ("30,637x", "Redis Cache Speedup", "61.33 s Cold CPU down to 2.00 ms", Inches(9.8))
]

for val, title, desc, left in metrics:
    create_card(s7, left, Inches(1.6), Inches(2.7), Inches(1.6), border_color=CYAN_ACCENT)
    tb = s7.shapes.add_textbox(left, Inches(1.7), Inches(2.7), Inches(1.4))
    tf = tb.text_frame
    p1 = tf.paragraphs[0]
    p1.alignment = PP_ALIGN.CENTER
    p1.text = val
    p1.font.name = "Arial"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = CYAN_ACCENT
    
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = title
    p2.font.name = "Arial"
    p2.font.size = Pt(10)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE
    
    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.text = desc
    p3.font.name = "Calibri"
    p3.font.size = Pt(9)
    p3.font.color.rgb = TEXT_MUTED

# Bottom Left: Automated Test Suite Card
create_card(s7, Inches(0.8), Inches(3.4), Inches(5.7), Inches(3.5), title="TEST SUITE & SECURITY AUDIT", border_color=CARD_BORDER)
tb_ts = s7.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(5.3), Inches(2.8))
tf_ts = tb_ts.text_frame
tf_ts.word_wrap = True
ts_lines = [
    ("126 Automated Tests Passing:", " 100% pass rate in 14.60 seconds via pytest CI."),
    ("79% Backend Code Coverage:", " 100% on models & config; 88% on ATS rubric; 84% on parser."),
    ("Air-Gapped Offline Operation:", " Ingestion & matching runs in 145.55 ms with zero internet connectivity."),
    ("Security Vulnerability Hardening:", " Parameterized SQL injection defense; admin token authorization; 10MB upload clamp.")
]
for i, (b_title, b_desc) in enumerate(ts_lines):
    p = tf_ts.paragraphs[0] if i == 0 else tf_ts.add_paragraph()
    p.space_after = Pt(6)
    r1 = p.add_run()
    r1.text = "• " + b_title
    r1.font.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = CYAN_ACCENT
    r2 = p.add_run()
    r2.text = b_desc
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = TEXT_WHITE

# Bottom Right: LLM Grounding & Factuality Card
create_card(s7, Inches(6.8), Inches(3.4), Inches(5.7), Inches(3.5), title="MODEL FACTUALITY & HUMAN REVIEW", border_color=CARD_BORDER)
tb_llm = s7.shapes.add_textbox(Inches(7.0), Inches(3.9), Inches(5.3), Inches(2.8))
tf_llm = tb_llm.text_frame
tf_llm.word_wrap = True
llm_lines = [
    ("9.5% Unsupported Claims (Llama-3.2):", " Only 8/84 bullet claims unsupported vs 29.8% (25/84) for TinyLlama."),
    ("4.20 / 5.00 Blind Human Review:", " Evaluated across 20 samples for relevance, tone, and ATS alignment (vs 2.75)."),
    ("CPU Throughput Limit Proof:", " 1.82 tokens/sec on CPU proven bound by 6.42 GB bfloat16 RAM bus bandwidth."),
    ("Zero Cloud Dependency:", " Full local inference eliminates API quota depletion, downtime, and billing costs.")
]
for i, (b_title, b_desc) in enumerate(llm_lines):
    p = tf_llm.paragraphs[0] if i == 0 else tf_llm.add_paragraph()
    p.space_after = Pt(6)
    r1 = p.add_run()
    r1.text = "• " + b_title
    r1.font.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = CYAN_ACCENT
    r2 = p.add_run()
    r2.text = b_desc
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = TEXT_WHITE

# -------------------------------------------------------------
# SLIDE 8: LIVE DEMO TRANSITION SLIDE
# -------------------------------------------------------------
s8 = prs.slides.add_slide(blank_slide_layout)
apply_background(s8)
add_header(s8, "System Demonstration: End-to-End Live Workflow")

create_card(s8, Inches(1.5), Inches(1.6), Inches(10.333), Inches(5.2), title="LOCAL VERIFICATION CHECKLIST (HOST: /home/rishav/job-scout/)", border_color=CYAN_ACCENT)

tb_demo = s8.shapes.add_textbox(Inches(1.8), Inches(2.2), Inches(9.7), Inches(4.4))
tf_demo = tb_demo.text_frame
tf_demo.word_wrap = True

demo_steps = [
    ("Step 1: Container Orchestration Check", "Verify healthy containers: FastAPI (8001), Next.js (3000), PostgreSQL (5435), Redis (6379), and Celery worker."),
    ("Step 2: Resume Ingestion & Parsing", "Upload a sample PDF resume into the Vault module; demonstrate instant Markdown extraction and 384-d vector generation."),
    ("Step 3: Two-Stage Hybrid Matchmaking", "Execute live job match query; observe sub-10ms response time as pgvector HNSW retrieves and reranks 100k job rows."),
    ("Step 4: Deterministic ATS Diagnostic", "Inspect 100-point ATS scorecard; highlight exact skill gap breakdown (matched vs missing high-priority target keywords)."),
    ("Step 5: Local RAG Synthesis Streaming", "Trigger on-device tailoring via Llama-3.2-3B; witness live Server-Sent Events (SSE) token generation with zero cloud APIs."),
    ("Step 6: Instant 2.00 ms Cache Hit", "Re-request identical job tailoring; verify immediate Redis SHA-256 cache response delivering a 30,637x acceleration."),
    ("Step 7: Kanban Application Lifecycle", "Drag tailored job card into 'Applied' column on the Pipeline Kanban board; verify persistent PostgreSQL transaction commit.")
]

for i, (s_title, s_desc) in enumerate(demo_steps):
    p = tf_demo.paragraphs[0] if i == 0 else tf_demo.add_paragraph()
    p.space_after = Pt(7)
    r1 = p.add_run()
    r1.text = f"{s_title}: "
    r1.font.bold = True
    r1.font.size = Pt(11)
    r1.font.color.rgb = CYAN_ACCENT
    r2 = p.add_run()
    r2.text = s_desc
    r2.font.size = Pt(10)
    r2.font.color.rgb = TEXT_WHITE

# -------------------------------------------------------------
# SLIDE 9: CONCLUSION & FUTURE ENHANCEMENTS
# -------------------------------------------------------------
s9 = prs.slides.add_slide(blank_slide_layout)
apply_background(s9)
add_header(s9, "Conclusion & Future Research Horizons")

# Left Card: Project Impact
create_card(s9, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), title="PROJECT ACHIEVEMENTS & CONTRIBUTIONS", border_color=CYAN_ACCENT)
tb_concl = s9.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(5.2), Inches(4.4))
tf_c = tb_concl.text_frame
tf_c.word_wrap = True

bullets_c = [
    ("Applicant-Side ATS Parity:", " Democratized commercial-grade ATS intelligence, enabling candidates to navigate corporate hiring filters equitably."),
    ("High-Performance Hybrid Retrieval:", " Engineered a two-stage SQL architecture achieving 9.08 ms query latency across 100k rows (98.1x speedup)."),
    ("Uncompromising Data Sovereignty:", " Delivered 100% on-device local AI synthesis with zero external data egress, satisfying strict privacy mandates."),
    ("Empirically Validated Software:", " Validated via 126 automated tests (79% coverage), 95.65% HNSW recall, and 4.20/5.00 blind human review.")
]
for i, (b_title, b_desc) in enumerate(bullets_c):
    p = tf_c.paragraphs[0] if i == 0 else tf_c.add_paragraph()
    p.space_after = Pt(14)
    r1 = p.add_run()
    r1.text = "• " + b_title
    r1.font.bold = True
    r1.font.size = Pt(11)
    r1.font.color.rgb = CYAN_ACCENT
    r2 = p.add_run()
    r2.text = b_desc
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = TEXT_WHITE

# Right Card: Future Horizons
create_card(s9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), title="FUTURE RESEARCH & SCALING HORIZONS", border_color=CARD_BORDER)
tb_fut = s9.shapes.add_textbox(Inches(7.0), Inches(2.2), Inches(5.3), Inches(4.4))
tf_f = tb_fut.text_frame
tf_f.word_wrap = True

bullets_f = [
    ("4-Bit GGUF Quantization (llama.cpp):", " Compress model footprint to 2.2 GB RAM, doubling CPU token throughput from 1.8 to 4.5+ tokens/sec."),
    ("Multi-Profile Portfolio Management:", " Enable job seekers to maintain targeted resume variants (e.g., DevOps vs Data Science) with differential ranking."),
    ("Automated LaTeX Typographic Engine:", " Programmatically recompile tailored resumes into ATS-compliant PDFs via headless LaTeX/Typst compilers."),
    ("LoRA Domain Adaptation:", " Fine-tune low-rank adapters on specific industry job postings to further reduce unsupported claims below 5%.")
]
for i, (b_title, b_desc) in enumerate(bullets_f):
    p = tf_f.paragraphs[0] if i == 0 else tf_f.add_paragraph()
    p.space_after = Pt(14)
    r1 = p.add_run()
    r1.text = "• " + b_title
    r1.font.bold = True
    r1.font.size = Pt(11)
    r1.font.color.rgb = CYAN_ACCENT
    r2 = p.add_run()
    r2.text = b_desc
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = TEXT_WHITE

# Save Deck
OUT_PPTX = "/home/rishav/job-scout/Document/Presentation/Job_Scout_Defense_Presentation.pptx"
prs.save(OUT_PPTX)
print(f"Presentation saved successfully to {OUT_PPTX}")

# Convert to PDF
cmd = f"libreoffice --headless --convert-to pdf {OUT_PPTX} --outdir /home/rishav/job-scout/Document/Presentation/"
res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
if res.returncode == 0:
    print("PDF version successfully generated!")
else:
    print("PDF export note:", res.stderr)
