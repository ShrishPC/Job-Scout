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
    Heuristic-based extraction of resume data when LLM is unavailable or in DEMO mode.
    Dynamically extracts information from ANY uploaded resume without hardcoded assumptions.
    """
    data = {
        "full_name": "Candidate",
        "email": "N/A",
        "phone": "N/A",
        "target_role": "Software Engineer",
        "target_location": "Remote",
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
        
    # 3. Dynamic Candidate Name (First clean line in header)
    lines = [l.strip() for l in markdown_content.split('\n') if l.strip()]
    for line in lines[:6]:
        clean = re.sub(r'^[#\s\*\-\•\|]+', '', line).strip()
        if (clean and len(clean.split()) in (2, 3, 4) 
                and '@' not in clean 
                and not any(kw in clean.lower() for kw in ['resume', 'curriculum', 'vitae', 'contact', 'email', 'phone', 'summary', 'profile', 'linkedin', 'github', 'portfolio'])):
            data["full_name"] = clean
            break
    if data["full_name"] == "Candidate" and lines:
        data["full_name"] = re.sub(r'^[#\s\*\-\•\|]+', '', lines[0]).strip()

    # 4. Dynamic Target Role
    role_candidates = [
        "Data Analyst", "Data Scientist", "Machine Learning Engineer", "AI Engineer",
        "Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Engineer",
        "Fullstack Developer", "DevOps Engineer", "Cloud Architect", "Systems Engineer",
        "Mobile Developer", "Android Developer", "iOS Developer", "QA Engineer",
        "Security Engineer", "Database Administrator", "Business Analyst", "Product Manager"
    ]
    for role in role_candidates:
        if re.search(rf'\b{re.escape(role)}\b', markdown_content, re.IGNORECASE):
            data["target_role"] = role
            break

    # 5. Dynamic Target Location
    loc_match = re.search(r'\b([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)\b', markdown_content[:600])
    if loc_match and not any(kw in loc_match.group(1).lower() for kw in ['curriculum', 'university', 'college', 'school']):
        data["target_location"] = loc_match.group(1).strip()
    elif "remote" in markdown_content[:1000].lower():
        data["target_location"] = "Remote"

    # 6. Extract Skills (Comprehensive multi-domain tech keywords)
    common_skills = [
        "Python", "SQL", "R", "Java", "C++", "C#", ".NET", "Golang", "Rust", "Swift", "Kotlin",
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Scikit-Learn", "PyTorch", "TensorFlow",
        "Machine Learning", "Data Analysis", "Data Cleaning", "Tableau", "Power BI", "Git", "GitHub",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD",
        "FastAPI", "Django", "Flask", "React", "Next.js", "TypeScript", "JavaScript", "HTML", "CSS",
        "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch", "Kafka", "Celery",
        "Linux", "REST API", "GraphQL", "Microservices"
    ]
    for skill in common_skills:
        if re.match(r'^[a-zA-Z0-9\s\-]+$', skill):
            pattern = rf'\b{re.escape(skill)}\b'
        else:
            pattern = rf'(?:^|[\s,;:(]){re.escape(skill)}(?:$|[\s,;:).])'
        if re.search(pattern, markdown_content, re.IGNORECASE):
            data["skills"].append(skill)
            
    # 7. Experience / Education line extraction
    current_section = None
    for line in lines:
        upper_line = line.upper()
        if "EXPERIENCE" in upper_line or "WORK HISTORY" in upper_line:
            current_section = "experience"
            continue
        if "EDUCATION" in upper_line or "ACADEMIC" in upper_line:
            current_section = "education"
            continue
        if "PROJECTS" in upper_line or "SKILLS" in upper_line:
            current_section = None
            continue
            
        if current_section == "experience" and len(line) > 10:
            if '|' in line:
                i = line.find('|')
                data["experience"].append({"title": line[:i].strip(), "company": line[i+1:].strip()})
            elif len(data["experience"]) < 5:
                data["experience"].append({"title": line[:60].strip(), "company": "Experience"})
        elif current_section == "education" and len(line) > 10:
            if len(data["education"]) < 4:
                data["education"].append({"degree": line.strip()})
            
    return data

def generate_embedding_fallback(text: str):
    """
    Generates a TF-IDF or Word2Vec based pseudo-embedding when LLM is unavailable.
    For simplicity here, we'll use Spacy's built-in vectors if available.
    """
    if not nlp:
        # Final fallback: Return dummy vector
        return [0.0] * 384
        
    doc = nlp(text[:10000]) # Limit to 10k chars
    # Spacy sm model has 96 dimensions, we'll pad to 384 to match our DB schema
    # Convert numpy floats to native python floats for JSON serialization
    vec = [float(v) for v in doc.vector]
    if len(vec) < 384:
        vec.extend([0.0] * (384 - len(vec)))
    return vec[:384]

