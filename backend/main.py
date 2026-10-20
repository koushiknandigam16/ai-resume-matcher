from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import io
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Canonical map: maps variations/synonyms to a single clean standard skill name
SKILL_SYNONYMS = {
    'html': 'HTML/HTML5',
    'html5': 'HTML/HTML5',
    'css': 'CSS/CSS3',
    'css3': 'CSS/CSS3',
    'js': 'JavaScript',
    'javascript': 'JavaScript',
    'rest api': 'REST API',
    'rest apis': 'REST API',
    'restful api': 'REST API',
    'debug': 'Debugging',
    'debugging': 'Debugging',
    'designer': 'Design',
    'designing': 'Design',
    'design': 'Design',
    'responsive design': 'Responsive Web Design',
    'responsive web design': 'Responsive Web Design',
    'web dev': 'Web Development',
    'web development': 'Web Development',
    'frontend': 'Frontend Development',
    'frontend development': 'Frontend Development',
    'backend': 'Backend Development',
    'backend development': 'Backend Development',
    'git': 'Git/GitHub',
    'github': 'Git/GitHub',
    'problem solving': 'Problem Solving',
    'system design': 'System Design',
    'python': 'Python',
    'java': 'Java',
    'c': 'C Language',
    'c++': 'C++',
    'fastapi': 'FastAPI',
    'mysql': 'MySQL',
    'aws': 'AWS Cloud',
}

STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 
    'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with', 
    'or', 'this', 'but', 'they', 'have', 'had', 'what', 'when', 'where', 'who', 'which', 
    'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 
    'can', 'just', 'should', 'now', 'using', 'following', 'across', 'role', 'jobs', 
    'bachelor', 'degree', 'preferred', 'required', 'qualification', 'equivalent', 
    'modules', 'practices', 'version', 'test', 'integration', 'collaboration'
}

def extract_text_from_pdf(pdf_bytes):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def normalize_text(text):
    """Converts text to lowercase and strips special punctuation."""
    return text.lower()

def extract_skills_and_terms(text):
    """Extracts standardized skills and clean domain terms from text."""
    normalized = normalize_text(text)
    detected_canonical_skills = set()
    
    # 1. Match known multi-word & single-word technical synonyms
    for term, canonical_name in SKILL_SYNONYMS.items():
        # Match term as a whole word/phrase
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, normalized):
            detected_canonical_skills.add(canonical_name)

    # 2. Extract remaining clean individual words
    words = set(re.findall(r'\b[a-zA-Z]{3,}\b', normalized))
    filtered_words = set()
    
    for word in words:
        if word not in STOP_WORDS:
            # Check if word is already represented in a canonical skill
            is_represented = False
            for c_skill in detected_canonical_skills:
                if word in c_skill.lower():
                    is_represented = True
                    break
            if not is_represented:
                filtered_words.add(word.capitalize())

    return detected_canonical_skills, filtered_words

def calculate_ats_score(resume_text, job_description):
    jd_skills, jd_words = extract_skills_and_terms(job_description)
    resume_skills, resume_words = extract_skills_and_terms(resume_text)

    # Calculate skill matches
    matched_skills = list(jd_skills.intersection(resume_skills))
    missing_skills = list(jd_skills - resume_skills)

    # Calculate remaining word matches
    matched_words = list(jd_words.intersection(resume_words))
    missing_words = list(jd_words - resume_words)

    # Combine canonical skills first, followed by clean keywords
    all_matched = matched_skills + matched_words
    all_missing = missing_skills + missing_words

    total_terms = len(all_matched) + len(all_missing)
    score = round((len(all_matched) / total_terms) * 100) if total_terms > 0 else 0

    return {
        "score": score,
        "matched_skills": all_matched[:12],
        "missing_skills": all_missing[:12]
    }

@app.post("/analyze")
async def analyze_resume(
    job_description: str = Form(...),
    resume_file: UploadFile = File(None),
    resume_text: str = Form(None)
):
    extracted_text = ""
    
    if resume_file:
        contents = await resume_file.read()
        extracted_text = extract_text_from_pdf(contents)
    elif resume_text:
        extracted_text = resume_text
    else:
        return {"error": "Please provide either a PDF file or paste resume text."}

    return calculate_ats_score(extracted_text, job_description)