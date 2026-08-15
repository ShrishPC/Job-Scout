import os
import fitz # PyMuPDF
import docx
from markitdown import MarkItDown

def parse_resume_to_markdown(file_path: str) -> str:
    """
    Converts a resume (PDF, DOCX, Markdown, TXT, etc.) into clean Markdown text.
    Includes robust fallback extractors if MarkItDown encounters unusual binary formatting.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # Fast path for plain text and markdown
    if ext in ('.md', '.markdown', '.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Direct text read failed: {e}")

    # Primary conversion via MarkItDown
    try:
        md = MarkItDown()
        result = md.convert(file_path)
        if result and result.text_content and len(result.text_content.strip()) > 0:
            return result.text_content.strip()
    except Exception as e:
        print(f"MarkItDown conversion warning on {file_path}: {e}. Trying fallback extractors...")

    # Secondary fallback for PDF using PyMuPDF (fitz)
    if ext == '.pdf':
        try:
            doc = fitz.open(file_path)
            extracted_text = []
            for page in doc:
                text = page.get_text("text")
                if text:
                    extracted_text.append(text.strip())
            doc.close()
            combined = "\n\n".join(extracted_text).strip()
            if combined:
                return combined
        except Exception as pdf_err:
            print(f"PyMuPDF fallback failed: {pdf_err}")

    # Secondary fallback for DOCX using python-docx
    if ext in ('.docx', '.doc'):
        try:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            combined = "\n\n".join(paragraphs).strip()
            if combined:
                return combined
        except Exception as docx_err:
            print(f"python-docx fallback failed: {docx_err}")

    # Final fallback: raw binary decode with ignore
    try:
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()
            return raw_bytes.decode('utf-8', errors='ignore').strip()
    except Exception as raw_err:
        raise Exception(f"Failed to extract text from resume '{file_path}': {str(raw_err)}")
