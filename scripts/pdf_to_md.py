#!/usr/bin/env python3
import sys
import os

# Add backend to path so we can reuse the service
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.resume_service import parse_resume_to_markdown

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python pdf_to_md.py <path_to_pdf_or_docx> [output_path]")
        print("Converts PDF, DOCX, or text documents into clean Markdown.")
        sys.exit(0)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)
    
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(file_path)[0] + ".md"
    
    print(f"Converting '{file_path}' to Markdown...")
    try:
        markdown_content = parse_resume_to_markdown(file_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"✅ Successfully converted! Saved to: {output_path}")
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
