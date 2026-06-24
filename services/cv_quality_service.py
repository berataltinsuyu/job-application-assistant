import re
from collections import Counter
from typing import Any


ACTION_VERBS = {
    "achieved", "adapted", "analyzed", "built", "collaborated", "configured", "created",
    "delivered", "designed", "developed", "documented", "implemented", "improved",
    "integrated", "managed", "optimized", "prepared", "reviewed", "supported", "tested",
    "validated", "wrote", "led", "coordinated", "maintained", "assisted", "contributed",
    "accelerated", "accomplished", "administered", "advised", "allocated", "approved",
    "architected", "assessed", "authored", "automated", "budgeted", "calculated",
    "championed", "clarified", "coached", "compiled", "composed", "conducted",
    "consolidated", "consulted", "crafted", "decreased", "defined", "delegated",
    "deployed", "detailed", "directed", "discovered", "distributed",
    "drafted", "edited", "educated", "eliminated", "enabled", "enacted", "encouraged",
    "engineered", "enhanced", "established", "evaluated", "examined", "executed",
    "expanded", "expedited", "facilitated", "forecasted", "formulated", "fostered",
    "founded", "generated", "guided", "headed", "identified", "illustrated",
    "increased", "influenced", "initiated", "inspected", "inspired",
    "installed", "instructed", "insured", "introduced", "investigated", "launched",
    "lectured", "liaised", "maximized", "mediated", "mentored", "merged", "minimized",
    "modeled", "moderated", "monitored", "motivated", "negotiated", "obtained",
    "operated", "organized", "originated", "overhauled", "oversaw", "participated",
    "partnered", "performed", "pioneered", "planned", "positioned", "predicted",
    "prevented", "processed", "produced", "programmed", "promoted", "proposed",
    "provided", "published", "purchased", "realized", "recommended", "reconciled",
    "recorded", "recruited", "redesigned", "reduced", "referred", "regulated",
    "rehabilitated", "remodeled", "rendered", "reorganized", "repaired", "reported",
    "represented", "researched", "resolved", "restructured", "retrieved", "revamped",
    "revised", "scheduled", "screened", "secured", "selected", "served", "shaped",
    "simplified", "solved", "sparked", "spearheaded", "standardized", "stimulated",
    "streamlined", "structured", "studied", "supervised", "surveyed", "targeted",
    "taught", "trained", "transferred", "transformed", "translated", "upgraded",
    "utilised", "utilized", "verified", "build", "building", "create", "creating", "develop",
    "developing", "implement", "implementing", "manage", "managing", "optimize",
    "optimizing", "design", "designing", "direct", "directing", "lead", "leading",
    "maintain", "maintaining", "support", "supporting", "test", "testing", "write",
    "writing", "coordinate", "coordinating", "collaborate", "collaborating"
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

STRONG_ORG_TERMS = {
    "ltd", "inc", "a.ş", "a.s", "holding", "corp", "corporation", "co.", "incorporated",
    "university", "college", "school", "institute", "academy"
}

ORG_TERMS = {
    "ltd", "inc", "a.ş", "a.s", "bank", "university", "holding", "technologies",
    "technology", "software studio", "software", "group", "corp", "corporation",
    "company", "college", "school", "institute", "labs", "lab", "academy", "studio",
    "solutions", "systems"
}

DEGREE_TERMS = {
    "bachelor", "master", "phd", "b.s", "bs", "m.s", "msc", "degree", "engineering",
    "computer science", "business administration", "associate", "license", "lisans",
    "yüksek lisans",
}

DATE_FRAGMENT_PATTERN = re.compile(
    r"\b(19|20)\d{2}\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|present|current|now|ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\b",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
URL_PATTERN = re.compile(r"https?://[^\s,)>\]]+", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
CHAR_SPACED_PATTERN = re.compile(r"\b(?:[a-zA-ZÇĞİÖŞÜçğıöşü]\s+){3,}[a-zA-ZÇĞİÖŞÜçğıöşü]\b")


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

    # Tuned weights: critical: -20, warning: -7, info: -2
    score = max(0, 100 - critical_count * 20 - warning_count * 7 - info_count * 2)

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

    swapped_socials = False
    if linkedin and "github.com" in linkedin.lower():
        swapped_socials = True
    if github and "linkedin.com" in github.lower():
        swapped_socials = True
    if swapped_socials:
        _add_issue(
            issues,
            "critical",
            "contact",
            "LinkedIn/GitHub fields may be swapped.",
            "Ensure LinkedIn URL is in the LinkedIn field and GitHub URL is in the GitHub field."
        )

    if linkedin and github and _normalize_url(linkedin) == _normalize_url(github) and not swapped_socials:
        _add_issue(
            issues,
            "critical",
            "contact",
            "The same URL appears in both LinkedIn and GitHub fields.",
            "Keep each social URL in the correct platform field."
        )

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

    duplicate_skills = _dedupe_skills(structured.get("skills") or structured.get("technical_skills") or structured.get("core_skills"))
    if duplicate_skills:
        _add_issue(issues, "info", "structure", f"Duplicate skills appear across categories: {', '.join(duplicate_skills[:8])}.", "Deduplicate skills or keep them in the most relevant category.")

    critical_count = sum(1 for issue in issues if issue["severity"] == "critical")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    info_count = sum(1 for issue in issues if issue["severity"] == "info")

    # Tuned weights: critical: -20, warning: -7, info: -2
    score = max(0, 100 - critical_count * 20 - warning_count * 7 - info_count * 2)
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

    swapped_socials = False
    if linkedin and "github.com" in linkedin.lower():
        swapped_socials = True
    if github and "linkedin.com" in github.lower():
        swapped_socials = True
    if swapped_socials:
        _add_issue(issues, "critical", "contact", "LinkedIn/GitHub fields may be swapped.", "Ensure LinkedIn URL is in the LinkedIn field and GitHub URL is in the GitHub field.")

    if linkedin and github and _normalize_url(linkedin) == _normalize_url(github) and not swapped_socials:
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
    if title and _looks_like_company(title) and not _looks_like_job_title(title):
        _add_issue(
            issues,
            "warning",
            "structure",
            "Title field may contain organization text.",
            "Move organization text to the company field."
        )
    if company and _looks_like_job_title(company) and not _looks_like_company(company):
        _add_issue(
            issues,
            "warning",
            "structure",
            "Company field may contain a role title.",
            "Move role text to the title field."
        )
    for field_name, value in (("title", title), ("company", company)):
        if value and _contains_date_fragment(value):
            _add_issue(
                issues,
                "warning",
                "structure",
                "Date appears inside company/title field.",
                "Move date-like values into a dedicated date field."
            )
        if value and _contains_location_fragment(value):
            _add_issue(
                issues,
                "info",
                "structure",
                "Location appears inside company/title field.",
                "Move location-like text to the location field."
            )


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


def _normalize_for_compare(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]", "", text).lower()


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
    lowered = value.lower()
    words = set(re.findall(r"[a-zçğıöşü]+", lowered))
    if words & STRONG_ORG_TERMS:
        return False
    return bool(words & JOB_TITLE_TERMS)


def _looks_like_org(value: str) -> bool:
    lowered = value.lower()
    words = set(re.findall(r"[a-zçğıöşü]+", lowered))
    if not words:
        return False
    if words & STRONG_ORG_TERMS:
        return True
    if any(term in lowered for term in ORG_TERMS):
        if not (words & JOB_TITLE_TERMS):
            return True
    return False


def _looks_like_company(value: str) -> bool:
    return _looks_like_org(value)


def _looks_like_degree(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in DEGREE_TERMS)


def _contains_location_hint(value: str) -> bool:
    return _contains_location_fragment(value)


def _contains_location_fragment(value: str) -> bool:
    lowered = value.lower()
    return bool(re.search(r"\b(remote|hybrid|on-site|istanbul|ankara|turkey|usa|united states|europe|izmir|bursa|kocaeli|location)\b", lowered))


def _contains_date_fragment(value: str) -> bool:
    return bool(DATE_FRAGMENT_PATTERN.search(value))


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


def _dedupe_skills(skills: Any) -> list[str]:
    return _duplicate_skills_across_categories(skills)
