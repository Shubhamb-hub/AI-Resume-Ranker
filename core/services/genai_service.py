import re
import spacy
from datetime import datetime

# Global config
nlp = spacy.load("en_core_web_sm")
CURRENT_YEAR = datetime.now().year
MAX_EXPERIENCE_YEARS = 40  # sanity cap

# SKILL TAXONOMY
SKILL_KEYWORDS = {
    # Programming
    "python", "java", "c", "c++", "sql", "r", "javascript",

    # Data / AI
    "data science", "machine learning", "deep learning",
    "nlp", "computer vision", "statistics", "data analytics",

    # Libraries / Tools
    "pandas", "numpy", "scikit-learn", "tensorflow",
    "pytorch", "keras", "opencv", "matplotlib", "seaborn",

    # BI
    "excel", "power bi", "tableau",

    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "git"
}

SKILL_ALIASES = {
    "ml": "machine learning",
    "dl": "deep learning",
    "natural language processing": "nlp",
    "cv": "computer vision",
    "sklearn": "scikit-learn"
}

# EDUCATION HIERARCHY (ranked)
EDUCATION_LEVELS = [
    (1, "SECONDARY (10TH)", [
        "10th", "ssc", "secondary school", "matriculation"
    ]),
    (2, "HIGHER SECONDARY (12TH)", [
        "12th", "hsc", "higher secondary", "intermediate"
    ]),
    (3, "DIPLOMA", [
        "diploma", "polytechnic"
    ]),
    (4, "BACHELOR", [
        "b.tech", "b.e", "b.sc", "bca",
        "bachelor of technology",
        "bachelor of engineering",
        "bachelor of science",
        "undergraduate"
    ]),
    (5, "MASTER", [
        "m.tech", "m.sc", "mba", "mca",
        "master of technology",
        "master of science",
        "postgraduate"
    ]),
    (6, "PHD", [
        "phd", "doctor of philosophy", "doctoral"
    ])
]

# EXPERIENCE PATTERNS
YEAR_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(years|yrs)",
    re.I
)

DATE_RANGE_PATTERN = re.compile(
    r"(19\d{2}|20\d{2})\s*(?:-|to|–)\s*(present|19\d{2}|20\d{2})",
    re.I
)

# NAME EXTRACTION
def extract_name(text):
    """
    Extract candidate name from first lines using NER + heuristics.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()][:5]

    for line in lines:
        if len(line.split()) > 4:
            continue

        doc = nlp(line)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.title()

    return "Unknown"

# EXPERIENCE EXTRACTION
def extract_experience_years(text):
    text = text.lower()
    candidates = []

    matches = YEAR_PATTERN.findall(text)
    for m in matches:
        try:
            candidates.append(float(m[0]))
        except:
            pass

    ranges = DATE_RANGE_PATTERN.findall(text)
    for start, end in ranges:
        try:
            start_year = int(start)
            end_year = CURRENT_YEAR if end.lower() == "present" else int(end)
            diff = end_year - start_year
            if 0 <= diff <= MAX_EXPERIENCE_YEARS:
                candidates.append(diff)
        except:
            continue

    if not candidates:
        return 0.0

    return min(max(candidates), MAX_EXPERIENCE_YEARS)

# EXPERIENCE LEVEL
def infer_experience_level(years):
    if years <= 1:
        return "Fresher"
    if years <= 3:
        return "Junior"
    if years <= 6:
        return "Mid-Level"
    return "Senior"

# EDUCATION EXTRACTION (HIGHEST ONLY)
def extract_education(text):
    text = text.lower()
    found = []

    for rank, label, patterns in EDUCATION_LEVELS:
        for p in patterns:
            if p in text:
                found.append((rank, label))
                break

    if not found:
        return "Unknown"

    return max(found, key=lambda x: x[0])[1]

# SKILLS EXTRACTION
def extract_skills(text):
    text = text.lower()
    found = set()

    for skill in SKILL_KEYWORDS:
        if skill in text:
            found.add(skill)

    for alias, canonical in SKILL_ALIASES.items():
        if alias in text:
            found.add(canonical)

    doc = nlp(text)
    for chunk in doc.noun_chunks:
        if chunk.text in SKILL_KEYWORDS:
            found.add(chunk.text)

    return sorted(s.title() for s in found)

# CERTIFICATIONS
def extract_certifications(text):
    cert_keywords = [
        "certified", "certification",
        "coursera", "udemy",
        "aws certified", "google certified",
        "azure certified"
    ]

    results = []
    for line in text.splitlines():
        if any(k in line.lower() for k in cert_keywords):
            results.append(line.strip())

    return results

# PROJECT COUNT
def extract_project_count(text):
    return len(re.findall(r"\bproject\b", text.lower()))

# DOMAIN INFERENCE
def infer_domain(skills):
    s = {x.lower() for x in skills}

    if {"machine learning", "deep learning", "nlp"} & s:
        return "Data Science / AI"
    if {"sql", "excel", "power bi", "tableau"} & s:
        return "Data Analytics"
    if {"aws", "docker", "kubernetes"} & s:
        return "Cloud / DevOps"
    if {"java", "c++", "javascript"} & s:
        return "Software Development"

    return "General"

# MAIN EXTRACTION FUNCTION
def extract_info(resume_text):
    """
    Fully offline, ATS-grade resume parser.
    """

    if not resume_text or not isinstance(resume_text, str):
        return {
            "name": "Unknown",
            "skills": [],
            "education": "Unknown",
            "experience_years": 0.0,
            "experience_level": "Unknown",
            "domain": "Unknown",
            "certifications": [],
            "project_count": 0
        }

    name = extract_name(resume_text)
    skills = extract_skills(resume_text)
    education = extract_education(resume_text)
    experience_years = extract_experience_years(resume_text)
    experience_level = infer_experience_level(experience_years)
    domain = infer_domain(skills)
    certifications = extract_certifications(resume_text)
    project_count = extract_project_count(resume_text)

    return {
        "name": name,
        "skills": skills,
        "education": education,
        "experience_years": round(experience_years, 2),
        "experience_level": experience_level,
        "domain": domain,
        "certifications": certifications,
        "project_count": project_count
    }
