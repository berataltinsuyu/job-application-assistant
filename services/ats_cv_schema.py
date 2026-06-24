from copy import deepcopy


ATS_CV_SCHEMA = {
    "contact": {
        "full_name": "",
        "target_title": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": "",
    },
    "professional_summary": "",
    "career_objective": "",
    "technical_summary": "",
    "skills": {
        "technical_skills": [],
        "core_skills": [],
        "tools": [],
        "databases": [],
        "cloud": [],
        "soft_skills": [],
    },
    "experience": [
        {
            "company": "",
            "role": "",
            "location": "",
            "start_date": "",
            "end_date": "",
            "bullets": [],
        }
    ],
    "projects": [
        {
            "name": "",
            "description": "",
            "technologies": [],
            "bullets": [],
            "link": "",
        }
    ],
    "education": [
        {
            "school": "",
            "degree": "",
            "department": "",
            "start_date": "",
            "end_date": "",
            "details": [],
        }
    ],
    "certifications": [
        {
            "name": "",
            "issuer": "",
            "date": "",
            "link": "",
        }
    ],
    "languages": [
        {
            "language": "",
            "level": "",
        }
    ],
    "ats_metadata": {
        "target_role": "",
        "target_company": "",
        "job_family": "",
        "job_keywords_used": [],
        "transferable_keywords_used": [],
        "missing_keywords": [],
        "risky_keywords_not_added": [],
        "ats_score_before": 0,
        "ats_score_after": 0,
        "optimization_summary": "",
        "alignment_confidence": "",
        "adaptation_notes": [],
        "ats_score_explanation": {
            "before_reason": "",
            "after_reason": "",
            "improvement_reasons": [],
            "remaining_gaps": [],
        },
    },
}

REQUIRED_TOP_LEVEL_KEYS = set(ATS_CV_SCHEMA.keys())


def get_empty_ats_cv_schema() -> dict:
    """Return an empty structured ATS CV schema."""
    return deepcopy(ATS_CV_SCHEMA)


def validate_ats_cv_schema(data: dict) -> tuple[bool, list[str]]:
    """Perform lightweight validation for the structured ATS CV schema."""
    errors = []

    if not isinstance(data, dict):
        return False, ["Schema data must be a dictionary."]

    missing_keys = sorted(REQUIRED_TOP_LEVEL_KEYS - set(data.keys()))
    for key in missing_keys:
        errors.append(f"Missing required top-level key: {key}")

    if "contact" in data and not isinstance(data["contact"], dict):
        errors.append("contact must be a dictionary.")

    if "skills" in data and not isinstance(data["skills"], dict):
        errors.append("skills must be a dictionary.")

    for list_key in ["experience", "projects", "education", "certifications", "languages"]:
        if list_key in data and not isinstance(data[list_key], list):
            errors.append(f"{list_key} must be a list.")

    if "ats_metadata" in data and not isinstance(data["ats_metadata"], dict):
        errors.append("ats_metadata must be a dictionary.")
    elif "ats_metadata" in data:
        alignment_confidence = data["ats_metadata"].get("alignment_confidence")
        if alignment_confidence and alignment_confidence not in {"high", "medium", "low"}:
            errors.append("ats_metadata.alignment_confidence must be high, medium, or low.")

        adaptation_notes = data["ats_metadata"].get("adaptation_notes")
        if adaptation_notes is not None and not isinstance(adaptation_notes, list):
            errors.append("ats_metadata.adaptation_notes must be a list.")

        ats_score_explanation = data["ats_metadata"].get("ats_score_explanation")
        if ats_score_explanation is not None and not isinstance(ats_score_explanation, dict):
            errors.append("ats_metadata.ats_score_explanation must be a dictionary.")
        elif isinstance(ats_score_explanation, dict):
            for list_key in ["improvement_reasons", "remaining_gaps"]:
                value = ats_score_explanation.get(list_key)
                if value is not None and not isinstance(value, list):
                    errors.append(f"ats_metadata.ats_score_explanation.{list_key} must be a list.")

        for list_key in [
            "job_keywords_used",
            "transferable_keywords_used",
            "missing_keywords",
            "risky_keywords_not_added",
        ]:
            value = data["ats_metadata"].get(list_key)
            if value is not None and not isinstance(value, list):
                errors.append(f"ats_metadata.{list_key} must be a list.")

    return len(errors) == 0, errors
