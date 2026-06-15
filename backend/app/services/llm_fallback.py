import re
import json

# Load small English model
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # Fallback if download failed in this turn
        nlp = None
except ImportError:
    nlp = None

def extract_structured_data_fallback(markdown_content: str):
    """
    Heuristic-based extraction of resume data when LLM is unavailable.
    """
    data = {
        "full_name": "Unknown User",
        "email": "N/A",
        "phone": "N/A",
        "skills": [],
        "experience": [],
        "education": []
    }
    
    # 1. Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', markdown_content)
    if email_match:
        data["email"] = email_match.group(0)
        
    # 2. Extract Phone
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', markdown_content)
    if phone_match:
        data["phone"] = phone_match.group(0)
        
    # 3. Heuristic Name (First line often contains name)
    lines = [l.strip() for l in markdown_content.split('\n') if l.strip()]
    if lines:
        data["full_name"] = lines[0]

    # 4. Extract Skills (Common keyword matching)
    common_skills = [
        "Python", "SQL", "R", "Java", "C++", "Pandas", "NumPy", "Matplotlib", 
        "Machine Learning", "Data Analysis", "Tableau", "Power BI", "Git", 
        "Docker", "AWS", "FastAPI", "React", "Next.js", "TypeScript"
    ]
    for skill in common_skills:
        if re.search(rf'\b{skill}\b', markdown_content, re.IGNORECASE):
            data["skills"].append(skill)
            
    # 5. Experience/Education (Simple line splitting)
    # This is very rough, but better than nothing
    current_section = None
    for line in lines:
        if "EXPERIENCE" in line.upper():
            current_section = "experience"
            continue
        if "EDUCATION" in line.upper():
            current_section = "education"
            continue
            
        if current_section == "experience" and len(line) > 10:
            if i := line.find('|'): # Often company | title
                data["experience"].append({"title": line[:i].strip(), "company": line[i+1:].strip()})
        elif current_section == "education" and len(line) > 10:
            data["education"].append({"degree": line})
            
    return data

def generate_embedding_fallback(text: str):
    """
    Generates a TF-IDF or Word2Vec based pseudo-embedding when LLM is unavailable.
    For simplicity here, we'll use Spacy's built-in vectors if available.
    """
    if not nlp:
        # Final fallback: Return dummy vector
        return [0.0] * 768
        
    doc = nlp(text[:10000]) # Limit to 10k chars
    # Spacy sm model has 96 dimensions, we'll pad to 768 to match our DB schema
    # Convert numpy floats to native python floats for JSON serialization
    vec = [float(v) for v in doc.vector]
    if len(vec) < 768:
        vec.extend([0.0] * (768 - len(vec)))
    return vec[:768]
