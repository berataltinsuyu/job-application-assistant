import re
from copy import deepcopy
from typing import Any

from services.ats_cv_relevance import (
    detect_job_family,
    rank_experience_for_job,
    rank_projects_for_job,
    rank_skills_for_job,
    relevance_keywords,
    score_text_for_job,
)


FRAUD_RISK_PAYMENT_TERMS = [
    "fraud",
    "risk",
    "payment",
    "payments",
    "transaction",
    "transactions",
    "suspicious",
    "chargeback",
    "dispute",
    "operation",
    "operations",
    "monitoring",
    "investigation",
    "documentation",
    "data analysis",
    "validation",
    "sql",
    "excel",
    "ms office",
    "api",
    "e-commerce",
    "merchant",
]

SUPPORTED_CONCEPTS = {
    "payment_systems": {
        "patterns": ["payment", "payments", "transaction", "bank", "banking", "merchant", "pos", "ödeme", "banka"],
        "skill": "Payment Systems",
        "summary": "payment systems",
        "tr_summary": "ödeme sistemleri",
    },
    "api_testing": {
        "patterns": ["api", "postman", "endpoint", "integration", "testing", "test", "doğrulama", "entegrasyon"],
        "skill": "API Testing",
        "summary": "API testing",
        "tr_summary": "API testleri",
    },
    "data_validation": {
        "patterns": ["validation", "validated", "verify", "verified", "data", "integrity", "sql", "query", "doğrulama", "veri"],
        "skill": "Data Validation",
        "summary": "data validation",
        "tr_summary": "veri doğrulama",
    },
    "sql_querying": {
        "patterns": ["sql", "postgresql", "mysql", "database", "query", "sorgu", "veritabanı", "veritabani"],
        "skill": "SQL Querying",
        "summary": "SQL/database operations",
        "tr_summary": "SQL/veritabanı işlemleri",
    },
    "process_documentation": {
        "patterns": ["documentation", "documented", "requirement", "process", "workflow", "analysis", "dokümantasyon", "süreç"],
        "skill": "Process Documentation",
        "summary": "process documentation",
        "tr_summary": "süreç dokümantasyonu",
    },
    "operations": {
        "patterns": ["operations", "operation", "support", "customer", "retail", "workflow", "süreç", "operasyon", "destek"],
        "skill": "Operational Workflows",
        "summary": "operational workflows",
        "tr_summary": "operasyonel iş akışları",
    },
    "collaboration": {
        "patterns": ["collaborated", "communication", "cross-functional", "team", "coordinated", "iletişim", "ekip"],
        "skill": "Cross-functional Collaboration",
        "summary": "cross-functional collaboration",
        "tr_summary": "ekipler arası iş birliği",
    },
}


def standardize_cv_adaptation_quality(
    structured_cv: dict,
    job_description: str,
    adaptation_level: str,
    source_cv_text: str | None = None,
    language: str = "English",
) -> dict:
    """Apply deterministic post-generation adaptation quality standards.

    This does not call an LLM. It preserves structured records and only reorders or
    adds conservative, source-supported emphasis where the selected mode allows it.
    """
    if not isinstance(structured_cv, dict):
        return structured_cv

    level = _normalize_adaptation_level(adaptation_level)
    result = deepcopy(structured_cv)
    metadata = result.setdefault("ats_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        result["ats_metadata"] = metadata

    detected_domain = detect_adaptation_domain(job_description, metadata.get("target_role", ""))
    metadata["detected_adaptation_domain"] = detected_domain

    source_corpus = _structured_text(result)
    if source_cv_text:
        source_corpus = f"{source_cv_text}\n{source_corpus}"
    supported = _supported_concepts(source_corpus)

    metadata["job_family"] = _job_family_for_domain(detected_domain, job_description, metadata.get("target_role", ""))
    metadata["job_keywords_used"] = _merge_list(
        metadata.get("job_keywords_used"),
        _supported_keyword_terms(supported, detected_domain),
    )
    metadata["transferable_keywords_used"] = _merge_list(
        metadata.get("transferable_keywords_used"),
        _transferable_keyword_terms(supported, detected_domain, level),
    )

    if level in {"balanced", "strong"}:
        result["skills"] = rank_skills_for_job(result.get("skills", {}), job_description, metadata)
        result["experience"] = rank_experience_for_job(result.get("experience", []), job_description, metadata)
        result["projects"] = rank_projects_for_job(result.get("projects", []), job_description, metadata)

    if level == "strong":
        _apply_strong_standard(result, job_description, detected_domain, supported, language)
    elif level == "balanced":
        _apply_balanced_standard(result, job_description, detected_domain, supported, language)

    metadata["adaptation_quality_report"] = build_adaptation_quality_report(
        result,
        job_description=job_description,
        adaptation_level=level,
        detected_domain=detected_domain,
    )
    return result


def build_adaptation_quality_report(
    structured_cv: dict,
    job_description: str,
    adaptation_level: str,
    detected_domain: str | None = None,
) -> dict:
    level = _normalize_adaptation_level(adaptation_level)
    domain = detected_domain or detect_adaptation_domain(job_description, _metadata(structured_cv).get("target_role", ""))
    metadata = _metadata(structured_cv)
    keywords = relevance_keywords(job_description, metadata)
    target_terms = _domain_terms(domain)

    contact = structured_cv.get("contact", {}) if isinstance(structured_cv, dict) else {}
    title = _clean(contact.get("target_title") if isinstance(contact, dict) else "")
    summary = _clean(
        structured_cv.get("professional_summary")
        or structured_cv.get("summary")
        or structured_cv.get("career_objective")
    )
    skills_text = _skills_text(structured_cv.get("skills"))
    experience_text = _records_text(structured_cv.get("experience"))
    projects_text = _records_text(structured_cv.get("projects"))

    report = {
        "adaptation_level": level,
        "detected_domain": domain,
        "target_keyword_coverage": _coverage(_structured_text(structured_cv), target_terms),
        "summary_alignment": _alignment_score(summary, job_description, metadata),
        "skills_alignment": _alignment_score(skills_text, job_description, metadata),
        "experience_alignment": _alignment_score(experience_text, job_description, metadata),
        "project_alignment": _alignment_score(projects_text, job_description, metadata),
        "warnings": [],
    }

    if level == "strong":
        if _coverage(f"{title} {summary}", target_terms) < 2:
            report["warnings"].append("Strong adaptation title/summary may be too generic for the target job.")
        if _coverage(skills_text, target_terms + keywords[:8]) < 2:
            report["warnings"].append("Strong adaptation skills may not prioritize enough target-relevant terms.")
        if _alignment_score(experience_text, job_description, metadata) <= 0:
            report["warnings"].append("Strong adaptation experience bullets may not preserve target-relevant evidence.")
    return report


def detect_adaptation_domain(job_description: str = "", target_role: str = "") -> str:
    text = _normalize(f"{target_role or ''}\n{job_description or ''}")
    if not text:
        return "general_it"

    fraud_risk = _count_hits(text, ["fraud", "risk", "suspicious", "chargeback", "dispute", "investigation", "monitoring"])
    payments = _count_hits(text, ["payment", "payments", "transaction", "merchant", "banking", "e-commerce", "ecommerce"])
    operations = _count_hits(text, ["operation", "operations", "documentation", "validation", "sql", "excel", "api", "data analysis"])
    if (fraud_risk and payments) or (fraud_risk and operations and "payment" in text):
        return "fraud_risk_payments"

    family = detect_job_family(job_description, target_role)
    return {
        "risk_fraud_compliance": "fraud_risk_payments",
        "fintech_payment": "fraud_risk_payments" if fraud_risk else "fintech_payments",
        "software_backend": "backend_software",
        "data_analytics": "data_analytics",
        "business_analyst": "business_analyst",
        "product_project": "product_analyst",
    }.get(family, "general_it")


def _apply_strong_standard(
    structured_cv: dict,
    job_description: str,
    domain: str,
    supported: set[str],
    language: str,
) -> None:
    if domain == "fraud_risk_payments":
        _ensure_fraud_payment_title(structured_cv, language)
        _ensure_fraud_payment_summary(structured_cv, supported, language)
        _prioritize_supported_skills(structured_cv, supported, include_transferable_domain=True)
        _prioritize_record_bullets(structured_cv, job_description)
        _add_supported_bullet_emphasis(structured_cv, supported, language)
    else:
        _prioritize_supported_skills(structured_cv, supported, include_transferable_domain=False)
        _prioritize_record_bullets(structured_cv, job_description)


def _apply_balanced_standard(
    structured_cv: dict,
    job_description: str,
    domain: str,
    supported: set[str],
    language: str,
) -> None:
    if domain == "fraud_risk_payments":
        _prioritize_supported_skills(structured_cv, supported, include_transferable_domain=False)
    _prioritize_record_bullets(structured_cv, job_description)


def _ensure_fraud_payment_title(structured_cv: dict, language: str) -> None:
    contact = structured_cv.setdefault("contact", {})
    if not isinstance(contact, dict):
        contact = {}
        structured_cv["contact"] = contact

    current = _clean(contact.get("target_title"))
    if _coverage(current, ["fraud", "risk", "payment", "ödeme", "risk"]) >= 1:
        return

    if _is_turkish(language):
        contact["target_title"] = "Ödeme Sistemleri ve Risk Operasyonları Destek Uzmanı"
    else:
        contact["target_title"] = "Payment Systems & Fraud Prevention Support"


def _ensure_fraud_payment_summary(structured_cv: dict, supported: set[str], language: str) -> None:
    current = _clean(
        structured_cv.get("professional_summary")
        or structured_cv.get("summary")
        or structured_cv.get("career_objective")
    )
    if _coverage(current, ["fraud", "risk", "payment", "payments", "validation", "api", "sql", "ödeme", "veri"]) >= 3:
        return

    concept_order = [
        "payment_systems",
        "data_validation",
        "api_testing",
        "sql_querying",
        "process_documentation",
        "operations",
        "collaboration",
    ]
    selected = [concept for concept in concept_order if concept in supported][:5]
    if not selected:
        return

    if _is_turkish(language):
        terms = [SUPPORTED_CONCEPTS[concept]["tr_summary"] for concept in selected]
        summary = (
            f"{', '.join(terms)} alanlarında desteklenen deneyime sahip; "
            "fraud, risk ve ödeme operasyonları desteğine veri doğrulama, dokümantasyon ve analitik düşünme odağıyla uyumlanan aday."
        )
    else:
        terms = [SUPPORTED_CONCEPTS[concept]["summary"] for concept in selected]
        summary = (
            f"Candidate with supported experience in {', '.join(terms)}, aligned with fraud, risk, "
            "and payment operations support through data validation, documentation, and analytical workflows."
        )

    structured_cv["professional_summary"] = summary
    if not _clean(structured_cv.get("career_objective")):
        structured_cv["career_objective"] = summary


def _prioritize_supported_skills(structured_cv: dict, supported: set[str], include_transferable_domain: bool) -> None:
    skills = structured_cv.setdefault("skills", {})
    if not isinstance(skills, dict):
        return

    additions = []
    for concept in [
        "data_validation",
        "api_testing",
        "sql_querying",
        "process_documentation",
        "payment_systems",
        "operations",
        "collaboration",
    ]:
        if concept in supported:
            additions.append(SUPPORTED_CONCEPTS[concept]["skill"])

    if include_transferable_domain:
        technical_values = _list(skills.get("technical_skills"))
        skills["technical_skills"] = _dedupe(additions + technical_values)
        core_values = _list(skills.get("core_skills"))
        core_additions = []
        if {"payment_systems", "data_validation"} & supported:
            core_additions.append("Risk/Fraud Operations Awareness")
        skills["core_skills"] = _dedupe(core_additions + core_values)
    else:
        target_group = "core_skills"
        values = _list(skills.get(target_group))
        skills[target_group] = _dedupe(additions + values)

    for group, values in list(skills.items()):
        if isinstance(values, list):
            skills[group] = _dedupe(values)


def _prioritize_record_bullets(structured_cv: dict, job_description: str) -> None:
    metadata = _metadata(structured_cv)
    keywords = relevance_keywords(job_description, metadata)
    for section_key in ["experience", "projects"]:
        for record in _list(structured_cv.get(section_key)):
            if isinstance(record, dict):
                record["bullets"] = _rank_list(record.get("bullets"), keywords)
                if section_key == "projects":
                    record["technologies"] = _rank_list(record.get("technologies"), keywords)


def _add_supported_bullet_emphasis(structured_cv: dict, supported: set[str], language: str) -> None:
    if "payment_systems" not in supported and "data_validation" not in supported:
        return

    phrase = (
        "Vurguyu ödeme süreçleri, veri doğrulama ve operasyonel dokümantasyonla ilişkilendirdi."
        if _is_turkish(language)
        else "Emphasized payment workflows, data validation, and operational documentation for transferable risk/fraud support."
    )

    for record in _list(structured_cv.get("experience")):
        if not isinstance(record, dict):
            continue
        record_text = _normalize(_record_text(record))
        if not any(term in record_text for term in ["payment", "transaction", "bank", "merchant", "ödeme", "banka"]):
            continue
        bullets = _list(record.get("bullets"))
        if bullets and _coverage(" ".join(bullets[:2]), ["payment", "validation", "api", "sql", "documentation", "ödeme", "veri"]) >= 2:
            return
        record["bullets"] = _dedupe([phrase] + bullets)
        return


def _supported_concepts(source_text: str) -> set[str]:
    normalized = _normalize(source_text)
    supported = set()
    for concept, config in SUPPORTED_CONCEPTS.items():
        if any(_normalize(pattern) in normalized for pattern in config["patterns"]):
            supported.add(concept)
    return supported


def _supported_keyword_terms(supported: set[str], domain: str) -> list[str]:
    terms = [SUPPORTED_CONCEPTS[concept]["skill"] for concept in supported if concept in SUPPORTED_CONCEPTS]
    if domain == "fraud_risk_payments":
        if "payment_systems" in supported:
            terms.append("payment operations")
        if "data_validation" in supported:
            terms.append("data validation")
        if "api_testing" in supported:
            terms.append("API validation")
        if "sql_querying" in supported:
            terms.append("SQL")
    return terms


def _transferable_keyword_terms(supported: set[str], domain: str, level: str) -> list[str]:
    if domain != "fraud_risk_payments" or level != "strong":
        return []
    if {"payment_systems", "data_validation", "api_testing", "sql_querying"} & supported:
        return ["fraud prevention support", "risk operations support", "payment operations support"]
    return []


def _job_family_for_domain(domain: str, job_description: str, target_role: str) -> str:
    if domain == "fraud_risk_payments":
        return "risk_fraud_compliance"
    if domain == "fintech_payments":
        return "fintech_payment"
    if domain == "backend_software":
        return "software_backend"
    return detect_job_family(job_description, target_role)


def _domain_terms(domain: str) -> list[str]:
    if domain == "fraud_risk_payments":
        return FRAUD_RISK_PAYMENT_TERMS
    if domain == "backend_software":
        return ["backend", "api", "database", "sql", "software", "testing"]
    if domain == "data_analytics":
        return ["data", "analysis", "analytics", "sql", "excel", "reporting"]
    if domain == "business_analyst":
        return ["requirements", "process", "documentation", "analysis", "workflow"]
    return []


def _metadata(structured_cv: dict) -> dict:
    if not isinstance(structured_cv, dict):
        return {}
    metadata = structured_cv.get("ats_metadata")
    return metadata if isinstance(metadata, dict) else {}


def _rank_list(values: Any, keywords: list[str]) -> list[str]:
    cleaned = [(index, _clean(value)) for index, value in enumerate(_list(values)) if _clean(value)]
    scored = [(score_text_for_job(value, "", {"job_keywords_used": keywords}), index, value) for index, value in cleaned]
    return [value for _, _, value in sorted(scored, key=lambda item: (-item[0], item[1]))]


def _alignment_score(text: str, job_description: str, metadata: dict) -> int:
    return score_text_for_job(text, job_description, metadata)


def _coverage(text: str, terms: list[str]) -> int:
    normalized = _normalize(text)
    return sum(1 for term in terms if _normalize(term) and _normalize(term) in normalized)


def _count_hits(text: str, terms: list[str]) -> int:
    return sum(1 for term in terms if _normalize(term) in text)


def _structured_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_structured_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_structured_text(item) for item in value)
    return _clean(value)


def _records_text(records: Any) -> str:
    return " ".join(_record_text(record) for record in _list(records))


def _record_text(record: Any) -> str:
    return _structured_text(record)


def _skills_text(skills: Any) -> str:
    return _structured_text(skills)


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _merge_list(existing: Any, additions: list[str]) -> list[str]:
    return _dedupe(_list(existing) + additions)


def _dedupe(values: list[Any]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = _clean(value)
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _normalize_adaptation_level(value: str) -> str:
    normalized = str(value or "balanced").strip().lower()
    if normalized in {"conservative", "balanced", "strong"}:
        return normalized
    return "balanced"


def _is_turkish(language: str) -> bool:
    return str(language or "").strip().lower() == "turkish"


def _normalize(value: Any) -> str:
    return _clean(value).casefold()


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
