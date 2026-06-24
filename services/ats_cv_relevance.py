import re
from copy import deepcopy


JOB_FAMILY_KEYWORDS = {
    "software_backend": [
        "backend", "api", "rest", "graphql", "microservices", "database", "sql", "nosql",
        "python", "java", "c#", ".net", "node", "go", "spring", "django", "fastapi",
        "testing", "debugging", "integration", "server", "architecture",
    ],
    "frontend": [
        "frontend", "front end", "react", "vue", "angular", "javascript", "typescript",
        "html", "css", "ui", "ux", "responsive", "accessibility", "web", "component",
    ],
    "fullstack": [
        "fullstack", "full stack", "frontend", "backend", "api", "database", "react",
        "node", "typescript", "javascript", "web application", "integration",
    ],
    "ai_ml_llm": [
        "ai", "machine learning", "ml", "llm", "rag", "nlp", "vector", "embedding",
        "prompt", "model", "evaluation", "data science", "pytorch", "tensorflow",
        "scikit", "openai", "langchain", "retrieval", "classification",
    ],
    "data_analytics": [
        "data", "analytics", "analysis", "reporting", "dashboard", "sql", "excel",
        "power bi", "tableau", "python", "pandas", "etl", "warehouse", "metrics",
        "visualization", "business intelligence", "statistics",
    ],
    "business_analyst": [
        "business analyst", "requirements", "requirement analysis", "documentation",
        "process", "stakeholder", "workflow", "user story", "acceptance criteria",
        "testing", "uat", "analysis", "functional specification",
    ],
    "product_project": [
        "product", "project", "roadmap", "backlog", "agile", "scrum", "stakeholder",
        "planning", "delivery", "prioritization", "requirements", "coordination",
        "launch", "metrics",
    ],
    "fintech_payment": [
        "fintech", "payment", "payments", "transaction", "banking", "card", "merchant",
        "settlement", "reconciliation", "chargeback", "wallet", "payment gateway",
        "financial operations",
    ],
    "risk_fraud_compliance": [
        "risk", "fraud", "compliance", "aml", "kyc", "audit", "control", "monitoring",
        "investigation", "regulatory", "policy", "governance", "chargeback",
        "financial crime",
    ],
    "cybersecurity": [
        "security", "cybersecurity", "authentication", "authorization", "access control",
        "jwt", "oauth", "vulnerability", "network", "monitoring", "incident",
        "secure coding", "compliance", "encryption", "iam",
    ],
    "devops_cloud": [
        "devops", "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd",
        "pipeline", "linux", "terraform", "monitoring", "deployment", "infrastructure",
        "automation", "sre",
    ],
    "corporate_applications": [
        "erp", "crm", "corporate application", "enterprise application", "sap",
        "oracle", "workflow", "business application", "support", "configuration",
        "integration", "user support",
    ],
    "sales_operations": [
        "sales", "operations", "customer", "crm", "pipeline", "account", "revenue",
        "retail", "process", "reporting", "forecast", "support", "coordination",
    ],
    "general": [],
}

JOB_FAMILY_PRECEDENCE = [
    "ai_ml_llm",
    "cybersecurity",
    "devops_cloud",
    "risk_fraud_compliance",
    "fintech_payment",
    "data_analytics",
    "business_analyst",
    "product_project",
    "corporate_applications",
    "fullstack",
    "frontend",
    "software_backend",
    "sales_operations",
]

ROLE_TITLE_BY_FAMILY = {
    "software_backend": ("Junior Backend Developer", "Junior Backend Geliştirici"),
    "frontend": ("Junior Frontend Developer", "Junior Frontend Geliştirici"),
    "fullstack": ("Junior Full Stack Developer", "Junior Full Stack Geliştirici"),
    "ai_ml_llm": ("Junior AI/ML Engineer", "Junior AI/ML Mühendisi"),
    "data_analytics": ("Junior Data Analyst", "Junior Veri Analisti"),
    "business_analyst": ("Junior Business Analyst", "Junior İş Analisti"),
    "product_project": ("Junior Product/Project Specialist", "Junior Ürün/Proje Uzmanı"),
    "fintech_payment": ("Junior Fintech/Payment Operations Specialist", "Junior Fintech/Ödeme Operasyonları Uzmanı"),
    "risk_fraud_compliance": ("Junior Risk/Fraud Operations Analyst", "Junior Risk/Fraud Operasyon Analisti"),
    "cybersecurity": ("Junior Cybersecurity Analyst", "Junior Siber Güvenlik Analisti"),
    "devops_cloud": ("Junior DevOps/Cloud Engineer", "Junior DevOps/Bulut Mühendisi"),
    "corporate_applications": ("Junior Corporate Applications Specialist", "Junior Kurumsal Uygulamalar Uzmanı"),
    "sales_operations": ("Junior Sales Operations Specialist", "Junior Satış Operasyonları Uzmanı"),
}

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ#+./-]{2,}")
STOPWORDS = {
    "and", "or", "the", "for", "with", "from", "this", "that", "your", "you", "our",
    "are", "will", "have", "has", "any", "all", "can", "bir", "ve", "ile", "için",
    "icin", "olan", "olarak", "bu", "şu", "bir", "her", "çok", "cok",
}


def detect_job_family(job_description: str = "", target_role: str = "") -> str:
    text = f"{target_role or ''}\n{job_description or ''}".casefold()
    if not text.strip():
        return "general"

    family_scores = {}
    for family, terms in JOB_FAMILY_KEYWORDS.items():
        if family == "general":
            continue
        score = 0
        for term in terms:
            normalized_term = term.casefold()
            if normalized_term in text:
                score += 3 if " " in normalized_term or "/" in normalized_term else 1
        family_scores[family] = score

    best_score = max(family_scores.values() or [0])
    if best_score <= 0:
        return "general"

    for family in JOB_FAMILY_PRECEDENCE:
        if family_scores.get(family) == best_score:
            return family
    return "general"


def target_title_for_job_family(target_role: str, job_family: str, language: str) -> str:
    role = _clean_text(target_role)
    if role and not _looks_like_overbroad_title(role):
        return role

    titles = ROLE_TITLE_BY_FAMILY.get(job_family)
    if not titles:
        return role
    return titles[1] if str(language).lower() == "turkish" else titles[0]


def rank_ats_cv_for_job(ats_cv: dict, job_description: str) -> dict:
    result = deepcopy(ats_cv)
    if not isinstance(result, dict):
        return result

    metadata = result.setdefault("ats_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        result["ats_metadata"] = metadata

    job_family = detect_job_family(job_description, metadata.get("target_role", ""))
    metadata["job_family"] = job_family

    result["skills"] = rank_skills_for_job(result.get("skills", {}), job_description, metadata)
    result["experience"] = rank_experience_for_job(result.get("experience", []), job_description, metadata)
    result["projects"] = rank_projects_for_job(result.get("projects", []), job_description, metadata)
    result["education"] = rank_education_for_job(result.get("education", []), job_description, metadata)
    result["certifications"] = rank_certifications_for_job(result.get("certifications", []), job_description, metadata)
    result["languages"] = rank_languages_for_job(result.get("languages", []), job_description, metadata)
    return result


def rank_skills_for_job(skills: dict, job_description: str, ats_metadata: dict) -> dict:
    if not isinstance(skills, dict):
        return skills
    keywords = relevance_keywords(job_description, ats_metadata)
    ranked = deepcopy(skills)
    for group, values in ranked.items():
        if isinstance(values, list):
            ranked[group] = _rank_strings(values, keywords)
    return ranked


def rank_experience_for_job(experience: list[dict], job_description: str, ats_metadata: dict) -> list[dict]:
    if not isinstance(experience, list):
        return experience
    keywords = relevance_keywords(job_description, ats_metadata)
    ranked_records = []
    for index, record in enumerate(experience):
        if not isinstance(record, dict):
            ranked_records.append((0, index, record))
            continue
        ranked_record = deepcopy(record)
        ranked_record["bullets"] = _rank_strings(ranked_record.get("bullets", []), keywords)
        ranked_records.append((_record_score(ranked_record, keywords), index, ranked_record))
    return [record for _, _, record in sorted(ranked_records, key=lambda item: (-item[0], item[1]))]


def rank_projects_for_job(projects: list[dict], job_description: str, ats_metadata: dict) -> list[dict]:
    if not isinstance(projects, list):
        return projects
    keywords = relevance_keywords(job_description, ats_metadata)
    ranked_records = []
    for index, record in enumerate(projects):
        if not isinstance(record, dict):
            ranked_records.append((0, index, record))
            continue
        ranked_record = deepcopy(record)
        ranked_record["bullets"] = _rank_strings(ranked_record.get("bullets", []), keywords)
        ranked_record["technologies"] = _rank_strings(ranked_record.get("technologies", []), keywords)
        ranked_records.append((_record_score(ranked_record, keywords), index, ranked_record))
    return [record for _, _, record in sorted(ranked_records, key=lambda item: (-item[0], item[1]))]


def rank_education_for_job(education: list[dict], job_description: str, ats_metadata: dict) -> list[dict]:
    if not isinstance(education, list):
        return education
    keywords = relevance_keywords(job_description, ats_metadata)
    ranked_records = []
    for index, record in enumerate(education):
        if not isinstance(record, dict):
            ranked_records.append((0, 0, 0, index, record))
            continue
        ranked_record = deepcopy(record)
        ranked_record["details"] = _rank_strings(ranked_record.get("details", []), keywords)
        ranked_records.append((*_education_recency_key(ranked_record), index, ranked_record))
    return [item[4] for item in sorted(ranked_records, key=lambda item: (-item[0], -item[1], -item[2], item[3]))]


def rank_certifications_for_job(certifications: list[dict], job_description: str, ats_metadata: dict) -> list[dict]:
    if not isinstance(certifications, list):
        return certifications
    keywords = relevance_keywords(job_description, ats_metadata)
    ranked_records = []
    for index, record in enumerate(certifications):
        ranked_records.append((_record_score(record, keywords), index, deepcopy(record)))
    return [record for _, _, record in sorted(ranked_records, key=lambda item: (-item[0], item[1]))]


def rank_languages_for_job(languages: list[dict], job_description: str, ats_metadata: dict) -> list[dict]:
    if not isinstance(languages, list):
        return languages
    keywords = relevance_keywords(job_description, ats_metadata)
    ranked_records = []
    for index, record in enumerate(languages):
        ranked_records.append((_record_score(record, keywords), index, deepcopy(record)))
    return [record for _, _, record in sorted(ranked_records, key=lambda item: (-item[0], item[1]))]


def relevance_keywords(job_description: str, ats_metadata: dict | None = None) -> list[str]:
    metadata = ats_metadata if isinstance(ats_metadata, dict) else {}
    values = []
    values.extend(_metadata_list(metadata.get("job_keywords_used")))
    values.extend(_metadata_list(metadata.get("transferable_keywords_used")))
    values.extend(_metadata_list(metadata.get("target_role")))

    family = metadata.get("job_family") or detect_job_family(job_description, metadata.get("target_role", ""))
    values.extend(JOB_FAMILY_KEYWORDS.get(family, []))

    values.extend(_extract_keyword_candidates(job_description))
    return _dedupe(values)


def score_text_for_job(text: str, job_description: str, ats_metadata: dict | None = None) -> int:
    return _score_text(text, relevance_keywords(job_description, ats_metadata))


def _rank_strings(values, keywords: list[str]) -> list[str]:
    if not isinstance(values, list):
        return []
    indexed_values = [(index, _clean_text(value)) for index, value in enumerate(values) if _clean_text(value)]
    scored = [(_score_text(value, keywords), index, value) for index, value in indexed_values]
    return [value for _, _, value in sorted(scored, key=lambda item: (-item[0], item[1]))]


def _record_score(record, keywords: list[str]) -> int:
    return _score_text(_record_text(record), keywords)


def _education_recency_key(record: dict) -> tuple[int, int, int]:
    start_value = _date_sort_value(record.get("start_date"))
    end_value = _date_sort_value(record.get("end_date"))
    ongoing = _looks_current(record.get("end_date"))

    if not _clean_text(record.get("end_date")) and start_value > 0:
        ongoing = True
        end_value = start_value

    return (1 if ongoing else 0, end_value, start_value)


def _date_sort_value(value) -> int:
    text = _clean_text(value)
    if not text:
        return 0
    if _looks_current(text):
        return 999912

    normalized = text.casefold()
    years = [int(year) for year in re.findall(r"\b(19\d{2}|20\d{2})\b", normalized)]
    if not years:
        return 0

    month = _month_sort_value(normalized)
    return max(years) * 100 + month


def _month_sort_value(text: str) -> int:
    month_patterns = {
        1: ["jan", "january", "ocak"],
        2: ["feb", "february", "şubat", "subat"],
        3: ["mar", "march", "mart"],
        4: ["apr", "april", "nisan"],
        5: ["may", "mayıs", "mayis"],
        6: ["jun", "june", "haziran"],
        7: ["jul", "july", "temmuz"],
        8: ["aug", "august", "ağustos", "agustos"],
        9: ["sep", "sept", "september", "eylül", "eylul"],
        10: ["oct", "october", "ekim"],
        11: ["nov", "november", "kasım", "kasim"],
        12: ["dec", "december", "aralık", "aralik"],
    }
    for month, names in month_patterns.items():
        if any(re.search(rf"\b{re.escape(name)}\b", text) for name in names):
            return month

    numeric_months = [int(month) for month in re.findall(r"(?:^|[^\d])([01]?\d)(?:[./-])(?:19\d{2}|20\d{2})\b", text)]
    valid_months = [month for month in numeric_months if 1 <= month <= 12]
    return max(valid_months) if valid_months else 12


def _looks_current(value) -> bool:
    normalized = _normalize(value)
    if not normalized:
        return False
    current_terms = [
        "present", "current", "ongoing", "now", "to present", "currently",
        "devam", "devam ediyor", "halen", "guncel", "güncel", "şu an", "su an",
    ]
    return any(re.search(rf"(^|\W){re.escape(term)}($|\W)", normalized) for term in current_terms)


def _score_text(text: str, keywords: list[str]) -> int:
    normalized_text = _normalize(text)
    if not normalized_text:
        return 0

    text_tokens = set(_tokens(normalized_text))
    score = 0
    for keyword in keywords:
        normalized_keyword = _normalize(keyword)
        if not normalized_keyword:
            continue
        if normalized_keyword in normalized_text:
            score += 8 if " " in normalized_keyword else 5
        keyword_tokens = set(_tokens(normalized_keyword))
        if keyword_tokens:
            score += len(text_tokens & keyword_tokens)
    return score


def _record_text(record) -> str:
    if isinstance(record, dict):
        parts = []
        for value in record.values():
            if isinstance(value, list):
                parts.extend(_clean_text(item) for item in value)
            else:
                parts.append(_clean_text(value))
        return " ".join(parts)
    return _clean_text(record)


def _metadata_list(value) -> list[str]:
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if _clean_text(value):
        return [_clean_text(value)]
    return []


def _extract_keyword_candidates(text: str) -> list[str]:
    candidates = []
    cleaned = _clean_text(text)
    tokens = [token for token in _tokens(cleaned) if token not in STOPWORDS]
    candidates.extend(tokens)

    words = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü][A-Za-zÇĞİÖŞÜçğıöşü0-9#+./-]*", cleaned)
    for size in (2, 3):
        for index in range(0, max(0, len(words) - size + 1)):
            phrase = " ".join(words[index:index + size])
            if not any(word.casefold() in STOPWORDS for word in phrase.split()):
                candidates.append(phrase)
    return candidates


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN_PATTERN.findall(text or "") if token.casefold() not in STOPWORDS]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _clean_text(text).casefold()).strip()


def _clean_text(value) -> str:
    return str(value or "").strip()


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = _clean_text(value)
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _looks_like_overbroad_title(value: str) -> bool:
    normalized = _normalize(value)
    return normalized in {"", "developer", "engineer", "analyst", "specialist", "intern", "student"}
