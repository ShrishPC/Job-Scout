import sys
import os
# Add backend to path so we can reuse the service
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.resume_service import parse_resume_to_markdown

def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_md.py <path_to_pdf>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    
    print(f"Converting {file_path} to Markdown...")
    try:
        markdown_content = parse_resume_to_markdown(file_path)
        
        output_path = os.path.splitext(file_path)[0] + ".md"
        with open(output_path, "w") as f:
            f.write(markdown_content)
        
        print(f"Successfully converted! Saved to: {output_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
