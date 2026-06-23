from copy import deepcopy


METADATA_DEFAULTS = {
    "target_role": "",
    "target_company": "",
    "job_keywords_used": [],
    "transferable_keywords_used": [],
    "missing_keywords": [],
    "risky_keywords_not_added": [],
    "ats_score_before": 0,
    "ats_score_after": 0,
    "optimization_summary": "",
    "alignment_confidence": "",
    "adaptation_notes": [],
}

SENIORITY_KEYWORDS = {
    "senior",
    "lead",
    "principal",
    "manager",
    "head",
    "director",
    "architect",
}


def ensure_ats_metadata_fields(ats_cv: dict) -> dict:
    result = deepcopy(ats_cv)
    metadata = result.setdefault("ats_metadata", {})

    if not isinstance(metadata, dict):
        result["ats_metadata"] = deepcopy(METADATA_DEFAULTS)
        return result

    for key, default_value in METADATA_DEFAULTS.items():
        if key not in metadata:
            metadata[key] = deepcopy(default_value)

    return result


def align_target_title(ats_cv: dict, language: str) -> dict:
    result = ensure_ats_metadata_fields(ats_cv)
    contact = result.setdefault("contact", {})

    if not isinstance(contact, dict):
        result["contact"] = {}
        contact = result["contact"]

    target_role = str(result.get("ats_metadata", {}).get("target_role") or "").strip()
    current_title = str(contact.get("target_title") or "").strip()

    if not target_role:
        return result

    target_family = detect_role_family(target_role)
    current_family = detect_role_family(current_title)

    should_replace = not current_title
    if target_family and current_family and target_family != current_family:
        should_replace = True
    elif target_family and not current_family:
        should_replace = True
    elif has_senior_title(current_title):
        should_replace = True
    elif target_family and title_language_mismatch(current_title, language):
        should_replace = True

    if should_replace:
        contact["target_title"] = build_aligned_target_title(target_role, target_family, language)

    return result


def detect_role_family(title: str) -> str:
    normalized = title.lower()
    if not normalized:
        return ""

    risk_keywords = [
        "fraud",
        "risk",
        "payment",
        "payments",
        "fintech",
        "aml",
        "chargeback",
        "compliance",
        "transaction",
        "banking operations",
        "ödeme",
        "dolandırıcılık",
        "uyum",
        "risk operasyon",
    ]
    operations_keywords = [
        "operations",
        "operation",
        "ops",
        "analyst",
        "specialist",
        "support",
        "process",
        "operasyon",
        "analist",
        "uzman",
        "süreç",
    ]
    software_keywords = [
        "backend",
        "software",
        "developer",
        "engineer",
        ".net",
        "dotnet",
        "java",
        "python",
        "api",
        "full-stack",
        "full stack",
        "frontend",
        "geliştirici",
        "yazılım",
        "mühendis",
    ]
    analyst_keywords = [
        "business analyst",
        "it analyst",
        "corporate application",
        "corporate applications",
        "application specialist",
        "applications specialist",
        "erp",
        "system analyst",
        "systems analyst",
        "requirements",
        "iş analisti",
        "kurumsal uygulama",
        "sistem analisti",
    ]
    data_keywords = [
        "data",
        "reporting",
        "report",
        "analytics",
        "dashboard",
        "business intelligence",
        "bi analyst",
        "veri",
        "raporlama",
        "analitik",
    ]

    has_risk_keyword = any(keyword in normalized for keyword in risk_keywords)
    has_operations_keyword = any(keyword in normalized for keyword in operations_keywords)
    if "fraud" in normalized or "aml" in normalized or "chargeback" in normalized:
        return "risk_operations"
    if has_risk_keyword and has_operations_keyword:
        return "risk_operations"
    if ("payment" in normalized or "ödeme" in normalized or "fintech" in normalized) and not any(
        keyword in normalized for keyword in software_keywords
    ):
        return "risk_operations"
    if any(keyword in normalized for keyword in data_keywords):
        return "data_reporting"
    if any(keyword in normalized for keyword in analyst_keywords):
        return "business_analyst"
    if any(keyword in normalized for keyword in software_keywords):
        return "software_backend"

    return ""


def has_senior_title(title: str) -> bool:
    normalized = title.lower()
    return any(keyword in normalized for keyword in SENIORITY_KEYWORDS)


def title_language_mismatch(title: str, language: str) -> bool:
    normalized = title.lower()
    is_turkish = language.lower() == "turkish"

    english_role_terms = {
        "developer",
        "engineer",
        "analyst",
        "specialist",
        "operations",
        "reporting",
        "business analyst",
        "software",
    }
    turkish_role_terms = {
        "geliştirici",
        "mühendis",
        "analisti",
        "uzmanı",
        "operasyon",
        "raporlama",
        "iş analisti",
        "yazılım",
    }

    if is_turkish:
        return any(term in normalized for term in english_role_terms)

    return any(term in normalized for term in turkish_role_terms)


def build_aligned_target_title(target_role: str, target_family: str, language: str) -> str:
    normalized_role = target_role.lower()
    is_turkish = language.lower() == "turkish"

    if target_family == "risk_operations":
        if is_turkish:
            if "fraud" in normalized_role or "risk" in normalized_role:
                return "Junior Fraud/Risk Operasyon Analisti"
            if "fintech" in normalized_role:
                return "Junior Fintech Operasyon Analisti"
            return "Junior Ödeme Sistemleri ve Risk Operasyonları Uzmanı"
        if "fraud" in normalized_role or "risk" in normalized_role:
            return "Junior Fraud/Risk Operations Analyst"
        if "fintech" in normalized_role:
            return "Junior Fintech Operations Analyst"
        if "payment" in normalized_role:
            return "Junior Payment Operations Analyst"
        return "Junior Payment Systems & Risk Operations Specialist"

    if target_family == "software_backend":
        if ".net" in normalized_role or "dotnet" in normalized_role:
            return "Junior .NET Developer"
        if is_turkish:
            if "backend" in normalized_role or "api" in normalized_role:
                return "Junior Backend Geliştirici"
            return "Junior Yazılım Geliştirici"
        if "backend" in normalized_role or "api" in normalized_role:
            return "Junior Backend Developer"
        return "Junior Software Developer"

    if target_family == "business_analyst":
        if is_turkish:
            if "corporate" in normalized_role or "application" in normalized_role or "uygulama" in normalized_role:
                return "Junior Kurumsal Uygulamalar Uzmanı"
            return "Junior IT İş Analisti"
        if "corporate" in normalized_role or "application" in normalized_role:
            return "Junior Corporate Applications Specialist"
        if "it" in normalized_role:
            return "Junior IT Analyst"
        return "Junior IT Business Analyst"

    if target_family == "data_reporting":
        if is_turkish:
            if "report" in normalized_role or "rapor" in normalized_role:
                return "Junior Raporlama Analisti"
            return "Junior Veri Analisti"
        if "report" in normalized_role:
            return "Junior Reporting Analyst"
        if "business" in normalized_role:
            return "Junior Business Data Analyst"
        return "Junior Data Analyst"

    return target_role
