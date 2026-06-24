import re
from collections import Counter
from typing import Any


ACTION_VERBS = {
    "achieved", "adapted", "analyzed", "built", "collaborated", "configured", "created",
    "delivered", "designed", "developed", "documented", "implemented", "improved",
    "integrated", "managed", "optimized", "prepared", "reviewed", "supported", "tested",
    "validated", "wrote", "led", "coordinated", "maintained", "assisted", "contributed",
}

SUSPICIOUS_CLAIMS = [
    "led enterprise-wide",
    "owned production mlops",
    "10+ years",
    "senior architect",
    "managed end-to-end enterprise",
    "production ml pipeline ownership",
    "direct compliance ownership",
]

JOB_TITLE_TERMS = {
    "developer", "engineer", "analyst", "intern", "specialist", "manager", "architect",
    "consultant", "designer", "administrator", "coordinator", "lead", "director",
}

ORG_TERMS = {
    "ltd", "inc", "a.ş", "a.s", "bank", "university", "holding", "technologies",
    "technology", "software studio", "software", "group", "corp", "corporation",
    "company", "college", "school", "institute", "labs", "lab",
}

DEGREE_TERMS = {
    "bachelor", "master", "phd", "b.s", "bs", "m.s", "msc", "degree", "engineering",
    "computer science", "business administration", "associate", "license", "lisans",
    "yüksek lisans",
}

DATE_PATTERN = re.compile(
    r"\b(19|20)\d{2}\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|present|current|now)\b",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
URL_PATTERN = re.compile(r"https?://[^\s,)>\]]+", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
CHAR_SPACED_PATTERN = re.compile(r"\b(?:[A-ZÇĞİÖŞÜ]\s+){4,}[A-ZÇĞİÖŞÜ]\b")


def analyze_cv_output_quality(
    cv_text: str,
    structured_cv: dict | None = None,
    one_page_requested: bool | None = None,
) -> dict:
    text = str(cv_text or "")
    structured = structured_cv if isinstance(structured_cv, dict) else {}
    issues: list[dict] = []

    _check_contact_quality(text, structured, issues)
    _check_content_quality(text, structured, issues)
    _check_formatting_quality(text, structured, issues, one_page_requested)
    _check_truthfulness_quality(text, structured, issues)

    critical_count = sum(1 for issue in issues if issue["severity"] == "critical")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    info_count = sum(1 for issue in issues if issue["severity"] == "info")
    score = max(0, 100 - critical_count * 25 - warning_count * 8 - info_count * 3)

    if critical_count:
        summary = "Needs review before sending due to critical contact or structure issues."
    elif warning_count:
        summary = "Usable draft with warnings; review before sending."
    elif info_count:
        summary = "Looks mostly clean with minor review notes."
    else:
        summary = "Looks clean. Still review before sending."

    return {
        "quality_score": score,
        "issues": issues,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "summary": summary,
    }


def validate_cv_structure(structured_cv: dict) -> dict:
    structured = structured_cv if isinstance(structured_cv, dict) else {}
    issues: list[dict] = []

    contact = _dict(structured.get("contact"))
    linkedin = _clean(contact.get("linkedin"))
    github = _clean(contact.get("github"))
    if linkedin and "github.com" in linkedin.lower():
        _add_issue(issues, "critical", "contact", "LinkedIn field appears to contain a GitHub URL.", "Move the URL to the GitHub field.")
    if github and "linkedin.com" in github.lower():
        _add_issue(issues, "critical", "contact", "GitHub field appears to contain a LinkedIn URL.", "Move the URL to the LinkedIn field.")
    if linkedin and github and _normalize_url(linkedin) == _normalize_url(github):
        _add_issue(issues, "critical", "contact", "The same URL appears in both LinkedIn and GitHub fields.", "Keep each social URL in the correct platform field.")

    for section_name in ("experience", "internship_experience"):
        for item in _list(structured.get(section_name)):
            title = _clean(item.get("title") or item.get("role") or item.get("position"))
            company = _clean(item.get("company") or item.get("organization") or item.get("employer"))
            _check_title_company_mix(title, company, issues, section_name)

    for item in _list(structured.get("education")):
        school = _clean(item.get("school") or item.get("institution") or item.get("university"))
        degree = _clean(item.get("degree") or item.get("program"))
        if school and _looks_like_degree(school):
            _add_issue(issues, "warning", "structure", "Education school field looks like a degree.", "Put degree/program text in the degree field.")
        if degree and _looks_like_org(degree) and not _looks_like_degree(degree):
            _add_issue(issues, "warning", "structure", "Education degree field looks like a school name.", "Put school/institution text in the school field.")

    for item in _list(structured.get("projects")):
        name = _clean(item.get("name") or item.get("title"))
        description = _clean(item.get("description") or " ".join(_list(item.get("bullets"))))
        if not name and _likely_project_title_in_description(description):
            _add_issue(issues, "info", "structure", "Project name is empty but description may contain a title.", "Move the likely title into the project name field.")

    for item in _list(structured.get("certifications")):
        name = _clean(item.get("name") or item.get("certification"))
        issuer = _clean(item.get("issuer") or item.get("organization"))
        if name and _looks_like_org(name) and issuer and not _looks_like_org(issuer):
            _add_issue(issues, "warning", "structure", "Certification name and issuer may be swapped.", "Use the certificate title as name and the issuing organization as issuer.")

    duplicate_skills = _duplicate_skills_across_categories(structured.get("skills") or structured.get("technical_skills") or structured.get("core_skills"))
    if duplicate_skills:
        _add_issue(issues, "info", "structure", f"Duplicate skills appear across categories: {', '.join(duplicate_skills[:8])}.", "Deduplicate skills or keep them in the most relevant category.")

    critical_count = sum(1 for issue in issues if issue["severity"] == "critical")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    info_count = sum(1 for issue in issues if issue["severity"] == "info")
    score = max(0, 100 - critical_count * 30 - warning_count * 10 - info_count * 4)
    return {
        "is_valid": critical_count == 0,
        "structure_score": score,
        "issues": issues,
        "summary": "Structure needs review." if issues else "Structure looks clean. Still review before sending.",
    }


def _check_contact_quality(text: str, structured: dict, issues: list[dict]) -> None:
    contact = _dict(structured.get("contact"))
    full_name = _clean(contact.get("full_name"))
    email = _clean(contact.get("email"))
    phone = _clean(contact.get("phone"))
    location = _clean(contact.get("location"))
    linkedin = _clean(contact.get("linkedin"))
    github = _clean(contact.get("github"))

    if CHAR_SPACED_PATTERN.search(text) or (full_name and CHAR_SPACED_PATTERN.search(full_name)):
        _add_issue(issues, "critical", "contact", "Full name appears character-spaced.", "Restore the name as normal words, not separated letters.")

    urls = [_normalize_url(url) for url in URL_PATTERN.findall(text)]
    url_counts = Counter(url for url in urls if url)
    duplicated_socials = [url for url, count in url_counts.items() if count > 1 and ("linkedin.com" in url or "github.com" in url)]
    if duplicated_socials:
        _add_issue(issues, "warning", "contact", "LinkedIn or GitHub URL appears duplicated.", "Keep each social link once in the contact section.")

    if linkedin and "github.com" in linkedin.lower():
        _add_issue(issues, "critical", "contact", "LinkedIn field contains a GitHub URL.", "Move the URL to GitHub.")
    if github and "linkedin.com" in github.lower():
        _add_issue(issues, "critical", "contact", "GitHub field contains a LinkedIn URL.", "Move the URL to LinkedIn.")
    if linkedin and github and _normalize_url(linkedin) == _normalize_url(github):
        _add_issue(issues, "critical", "contact", "LinkedIn and GitHub fields contain the same URL.", "Use distinct URLs for each platform.")

    for label, value, expected in (("LinkedIn", linkedin, "linkedin.com"), ("GitHub", github, "github.com")):
        if value and value.lower().startswith("http") and expected not in value.lower():
            _add_issue(issues, "warning", "contact", f"{label} URL does not look like a {label} URL.", "Verify the social URL.")

    if re.search(r"\b(?:\d\s+){7,}\d\b", text):
        _add_issue(issues, "warning", "contact", "Phone number appears split into separated digits.", "Format the phone number as a normal phone string.")
    if not email and not EMAIL_PATTERN.search(text):
        _add_issue(issues, "critical", "contact", "Email is missing.", "Add the candidate email from the source CV.")
    if not phone and not PHONE_PATTERN.search(text):
        _add_issue(issues, "critical", "contact", "Phone number is missing.", "Add the candidate phone number from the source CV.")
    if not location:
        _add_issue(issues, "warning", "contact", "Location is missing.", "Add city/country if present in the source CV.")


def _check_content_quality(text: str, structured: dict, issues: list[dict]) -> None:
    summary = _clean(structured.get("professional_summary") or structured.get("summary") or structured.get("career_objective"))
    if not summary:
        _add_issue(issues, "warning", "content", "Professional summary is empty.", "Add a short, truthful summary aligned with the target role.")
    elif len(summary.split()) > 95:
        _add_issue(issues, "warning", "content", "Professional summary is too long.", "Keep the summary concise, usually 3-5 lines.")

    skills = _flatten_skills(structured.get("skills") or structured.get("technical_skills") or structured.get("core_skills"))
    if not skills:
        _add_issue(issues, "warning", "content", "Skills section is missing.", "Add relevant skills supported by the CV.")
    elif len(skills) > 45:
        _add_issue(issues, "info", "content", "Skills section may contain too many items.", "Prioritize the most relevant supported skills.")

    if not _list(structured.get("experience")) and not _list(structured.get("internship_experience")):
        _add_issue(issues, "warning", "content", "Experience section is missing.", "Include supported work, internship, or practical experience if available.")
    if not _list(structured.get("education")):
        _add_issue(issues, "warning", "content", "Education section is missing.", "Include education if present in the source CV.")
    projects = _list(structured.get("projects"))
    if "projects" in structured and not projects:
        _add_issue(issues, "info", "content", "Projects section is enabled but empty.", "Add supported projects or disable the section for export.")

    _check_duplicate_names(projects, "project", issues)
    _check_duplicate_names(_list(structured.get("certifications")), "certification", issues)

    section_titles = re.findall(r"(?im)^\s*(experience|education|projects|skills|certifications|languages|summary)\s*$", text)
    repeated = [title for title, count in Counter(title.lower() for title in section_titles).items() if count > 1]
    if repeated:
        _add_issue(issues, "warning", "content", f"Repeated section titles detected: {', '.join(repeated)}.", "Keep each section heading once.")


def _check_formatting_quality(text: str, structured: dict, issues: list[dict], one_page_requested: bool | None) -> None:
    bullets = _extract_bullets(text, structured)
    long_bullets = [bullet for bullet in bullets if len(bullet.split()) > 38]
    if long_bullets:
        _add_issue(issues, "warning", "formatting", "Some bullet points are very long.", "Shorten bullets to improve readability and one-page fit.")

    weak_bullets = []
    for bullet in bullets:
        first = re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşü]", "", bullet.strip().split(" ", 1)[0]).lower()
        if first and first not in ACTION_VERBS and len(bullet.split()) > 5:
            weak_bullets.append(bullet)
    if weak_bullets:
        _add_issue(issues, "info", "formatting", "Some bullets may not start with action verbs.", "Start bullets with concrete action verbs when truthful.")

    skills_lines = [line for line in text.splitlines() if "skills" in line.lower() or "," in line]
    if any(line.count(",") >= 14 for line in skills_lines):
        _add_issue(issues, "info", "formatting", "Skills line may be overly dense.", "Group skills by category or reduce the line length.")

    if one_page_requested and len(text.split()) > 850:
        _add_issue(issues, "warning", "formatting", "One-page export was requested but content may be too long.", "Reduce bullets or use compact export options.")


def _check_truthfulness_quality(text: str, structured: dict, issues: list[dict]) -> None:
    haystack = text.lower()
    for claim in SUSPICIOUS_CLAIMS:
        if claim in haystack:
            _add_issue(issues, "warning", "truthfulness", f"Potentially unsupported senior claim detected: '{claim}'.", "Verify this claim is directly supported by the source CV.")


def _check_title_company_mix(title: str, company: str, issues: list[dict], section_name: str) -> None:
    if title and _looks_like_org(title) and not _looks_like_job_title(title):
        _add_issue(issues, "warning", "structure", f"{section_name} title looks like a company or organization.", "Move organization text to the company field.")
    if company and _looks_like_job_title(company) and not _looks_like_org(company):
        _add_issue(issues, "warning", "structure", f"{section_name} company looks like a job title.", "Move role text to the title field.")
    for field_name, value in (("title", title), ("company", company)):
        if value and DATE_PATTERN.search(value):
            _add_issue(issues, "warning", "structure", f"Date-like value appears inside {section_name} {field_name}.", "Move dates into a dedicated date field.")
        if value and _contains_location_hint(value):
            _add_issue(issues, "info", "structure", f"Location-like value appears inside {section_name} {field_name}.", "Move location into a dedicated location field.")


def _add_issue(issues: list[dict], severity: str, category: str, message: str, suggested_fix: str) -> None:
    issue = {
        "severity": severity,
        "category": category,
        "message": message,
        "suggested_fix": suggested_fix,
    }
    if issue not in issues:
        issues.append(issue)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _normalize_url(value: str) -> str:
    text = _clean(value).lower().rstrip("/.,")
    text = re.sub(r"^https?://(www\.)?", "", text)
    return text


def _flatten_skills(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    if isinstance(value, dict):
        flattened = []
        for item in value.values():
            flattened.extend(_flatten_skills(item))
        return flattened
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,;\n]", value) if part.strip()]
    return []


def _extract_bullets(text: str, structured: dict) -> list[str]:
    bullets = [line.strip(" -•\t") for line in text.splitlines() if line.strip().startswith(("-", "•", "*"))]
    for section_name in ("experience", "projects", "education", "certifications", "internship_experience"):
        for item in _list(structured.get(section_name)):
            bullets.extend(_clean(bullet) for bullet in _list(item.get("bullets")) if _clean(bullet))
            if _clean(item.get("description")):
                bullets.append(_clean(item.get("description")))
    return [bullet for bullet in bullets if bullet]


def _check_duplicate_names(items: list, label: str, issues: list[dict]) -> None:
    names = [_clean(item.get("name") or item.get("title") or item.get("certification")).casefold() for item in items if isinstance(item, dict)]
    duplicates = [name for name, count in Counter(name for name in names if name).items() if count > 1]
    if duplicates:
        _add_issue(issues, "warning", "content", f"Duplicated {label} names detected.", f"Remove duplicate {label} entries.")


def _looks_like_job_title(value: str) -> bool:
    words = set(re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü.]+", value.lower()))
    return bool(words & JOB_TITLE_TERMS)


def _looks_like_org(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in ORG_TERMS)


def _looks_like_degree(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in DEGREE_TERMS)


def _contains_location_hint(value: str) -> bool:
    lowered = value.lower()
    return bool(re.search(r"\b(remote|hybrid|on-site|istanbul|ankara|turkey|usa|united states|europe)\b", lowered))


def _likely_project_title_in_description(value: str) -> bool:
    text = _clean(value)
    if not text:
        return False
    first_clause = re.split(r"[:\-.]\s+", text, maxsplit=1)[0]
    return 2 <= len(first_clause.split()) <= 7 and any(char.isupper() for char in first_clause)


def _duplicate_skills_across_categories(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    seen = Counter()
    for category_values in value.values():
        for skill in _flatten_skills(category_values):
            seen[skill.casefold()] += 1
    return [skill for skill, count in seen.items() if count > 1]

