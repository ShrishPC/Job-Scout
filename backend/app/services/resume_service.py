from markitdown import MarkItDown
import os

def parse_resume_to_markdown(file_path: str) -> str:
    """
    Converts a resume (PDF, Docx, Markdown, etc.) to Markdown format.
    """
    try:
        if file_path.lower().endswith('.md') or file_path.lower().endswith('.markdown'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        md = MarkItDown()
        result = md.convert(file_path)
        return result.text_content
    except Exception as e:
        raise Exception(f"Failed to parse resume: {str(e)}")
