from core.services.ocr_service import extract_text_from_file
from core.services.cleaning_service import clean_text
from core.services.regex_service import (
    extract_primary_email,
    extract_phone_numbers,
)
from core.services.genai_service import extract_info
from core.services.embedding_service import embed
from core.services.similarity_service import cosine_similarity
from core.services.scoring_service import calculate_final_score
from core.services.explanation_service import generate_explanation


def analyze_and_rank_resumes(file_paths, job_description):
    """
    Analyze multiple resumes and rank them based on suitability
    for the given job description.

    Fully offline, ATS-style NLP pipeline.
    All scores are normalized to 0–10.
    """

    results = []

    # 1. Prepare Job Description
    job_description_cleaned = clean_text(job_description)
    if not job_description_cleaned:
        return results

    job_vector = embed(job_description_cleaned)

    job_info = extract_info(job_description_cleaned)
    job_skills = {
        s.lower() for s in job_info.get("skills", [])
    }

    # 2. Process Each Resume
    for file_path in file_paths:
        try:
            # OCR
            raw_text = extract_text_from_file(file_path)
            if not raw_text:
                continue

            # Cleaning
            cleaned_text = clean_text(raw_text)
            if not cleaned_text:
                continue

            # Contact Info
            email = extract_primary_email(cleaned_text)
            phones = extract_phone_numbers(cleaned_text)

            # Resume NLP Extraction
            resume_info = extract_info(cleaned_text)

            name = resume_info.get("name", "Unknown")
            skills = resume_info.get("skills", [])
            education = resume_info.get("education", "Unknown")
            experience_years = resume_info.get("experience_years", 0.0)
            experience_level = resume_info.get("experience_level", "Unknown")
            domain = resume_info.get("domain", "Unknown")
            certifications = resume_info.get("certifications", [])
            project_count = resume_info.get("project_count", 0)

            resume_skills = {s.lower() for s in skills}

            # Semantic Similarity (0–10)
            resume_vector = embed(cleaned_text)
            semantic_score = cosine_similarity(resume_vector, job_vector)

            # Hard reject completely irrelevant resumes
            if semantic_score < 1.0:
                continue

            # Skill Overlap (0–1)
            if job_skills:
                skill_overlap_ratio = len(
                    job_skills & resume_skills
                ) / len(job_skills)
            else:
                skill_overlap_ratio = 0.0

            # Final ATS Score (0–10)
            match_score = calculate_final_score(
                semantic_similarity=semantic_score / 10,
                experience_years=experience_years,
                skill_overlap=skill_overlap_ratio
            )

            # Explanation
            explanation = generate_explanation(
                job_description=job_description_cleaned,
                skills=skills,
                experience_years=experience_years,
                match_score=match_score,
                semantic_similarity=semantic_score,
                skill_overlap=skill_overlap_ratio
            )

            # Collect Result
            results.append({
                "name": name,
                "email": email,
                "phone_numbers": phones,
                "skills": skills,
                "education": education,
                "experience_years": round(experience_years, 2),
                "experience_level": experience_level,
                "domain": domain,
                "certifications": certifications,
                "project_count": project_count,
                "semantic_similarity": round(semantic_score, 2),
                "skill_overlap": round(skill_overlap_ratio, 2),
                "match_score": round(match_score, 2),
                "explanation": explanation
            })

        except Exception as e:
            # One resume should never crash pipeline
            print(f"[Resume skipped] {file_path} → {e}")
            continue

    # 3. Sort by Match Score (Descending)
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results
