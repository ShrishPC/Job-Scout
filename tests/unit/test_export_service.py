import pytest
import io
import fitz
import docx
from app.services.export_service import (
    parse_markdown_runs,
    generate_docx_export,
    generate_pdf_export
)

def test_parse_markdown_runs():
    text = "Hello **world** this is **bold** text and normal."
    runs = parse_markdown_runs(text)
    assert len(runs) == 5
    assert runs[0] == ("Hello ", False)
    assert runs[1] == ("world", True)
    assert runs[2] == (" this is ", False)
    assert runs[3] == ("bold", True)
    assert runs[4] == (" text and normal.", False)

def test_parse_markdown_runs_empty_and_plain():
    runs_empty = parse_markdown_runs("")
    assert runs_empty == []

    runs_plain = parse_markdown_runs("Simple plain text")
    assert runs_plain == [("Simple plain text", False)]

def test_generate_docx_export():
    markdown_content = (
        "# Professional Summary\n"
        "Senior Engineer with 8+ years experience in **distributed systems**.\n\n"
        "## Key Achievements\n"
        "- **Optimized latency** by 45% using Redis caching.\n"
        "- Spearheaded cloud migration on AWS."
    )
    docx_bytes = generate_docx_export(
        title="Tailored Resume",
        content=markdown_content,
        mode="tailor",
        candidate_name="Alex Mercer",
        candidate_email="alex@example.com",
        candidate_phone="+1-555-0199",
        company="TechCorp",
        job_title="Lead Architect"
    )
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 0
    # DOCX files are zip archives starting with PK\x03\x04
    assert docx_bytes.startswith(b"PK\x03\x04")

    # Read back with python-docx to verify content
    doc = docx.Document(io.BytesIO(docx_bytes))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "ALEX MERCER" in full_text
    assert "alex@example.com" in full_text
    assert "PROFESSIONAL SUMMARY" in full_text

def test_generate_pdf_export():
    markdown_content = (
        "# Professional Summary\n"
        "Experienced Backend Developer with deep knowledge of **Python** and **FastAPI**.\n\n"
        "## Core Competencies\n"
        "- Scaled API to 10M daily requests.\n"
        "- Automated testing coverage to 85%.\n\n"
        "### Certifications\n"
        "AWS Certified Solutions Architect"
    )
    pdf_bytes = generate_pdf_export(
        title="Cover Letter",
        content=markdown_content,
        mode="cover_letter",
        candidate_name="Samira Khan",
        candidate_email="samira@example.com",
        candidate_phone="+1-555-0144",
        company="GlobalTech",
        job_title="Principal Engineer"
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF starts with %PDF
    assert pdf_bytes.startswith(b"%PDF")

    # Read back with PyMuPDF (fitz) to verify pages and text
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert len(doc) >= 1
    page1_text = doc[0].get_text("text")
    assert "SAMIRA KHAN" in page1_text
    assert "samira@example.com" in page1_text
    doc.close()
