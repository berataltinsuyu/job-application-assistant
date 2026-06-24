import re
from difflib import SequenceMatcher
from copy import deepcopy

from services.ats_cv_relevance import detect_job_family, target_title_for_job_family


METADATA_DEFAULTS = {
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

CONTACT_FIELDS_TO_RESTORE = ("email", "phone", "linkedin", "github", "portfolio")
PRESERVED_ENTITY_FIELDS = {
    "contact": ["full_name"],
    "experience": ["company"],
    "projects": ["name"],
    "education": ["school"],
    "certifications": ["name", "issuer"],
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

    explanation = metadata.get("ats_score_explanation")
    if not isinstance(explanation, dict):
        metadata["ats_score_explanation"] = deepcopy(METADATA_DEFAULTS["ats_score_explanation"])
    else:
        for key, default_value in METADATA_DEFAULTS["ats_score_explanation"].items():
            if key not in explanation:
                explanation[key] = deepcopy(default_value)

    return result


def ensure_ats_score_explanation(ats_cv: dict, language: str) -> dict:
    result = ensure_ats_metadata_fields(ats_cv)
    metadata = result["ats_metadata"]
    explanation = metadata["ats_score_explanation"]

    has_required_content = (
        explanation.get("before_reason")
        and explanation.get("after_reason")
        and isinstance(explanation.get("improvement_reasons"), list)
        and isinstance(explanation.get("remaining_gaps"), list)
    )
    if has_required_content:
        return result

    is_turkish = language.lower() == "turkish"
    before_score = metadata.get("ats_score_before", 0)
    after_score = metadata.get("ats_score_after", 0)
    direct_keywords = metadata.get("job_keywords_used", [])
    transferable_keywords = metadata.get("transferable_keywords_used", [])
    missing_keywords = metadata.get("missing_keywords", [])
    risky_keywords = metadata.get("risky_keywords_not_added", [])

    if is_turkish:
        explanation["before_reason"] = (
            f"Orijinal CV için tahmini skor {before_score}; çünkü bazı hedef anahtar kelimeler ve iş ilanına özel vurgu eksikti."
        )
        explanation["after_reason"] = (
            f"Optimize edilmiş CV için tahmini skor {after_score}; çünkü desteklenen anahtar kelimeler ve aktarılabilir deneyimler daha görünür hale getirildi."
        )
        explanation["improvement_reasons"] = _non_empty_or_default([
            _keyword_sentence("Doğrudan desteklenen anahtar kelimeler eklendi veya öne çıkarıldı", direct_keywords),
            _keyword_sentence("Aktarılabilir yetkinlikler iş ilanına uygun şekilde ifade edildi", transferable_keywords),
            metadata.get("optimization_summary", ""),
        ], "CV dili, iş ilanındaki beklentilere daha uygun hale getirildi.")
        explanation["remaining_gaps"] = _non_empty_or_default([
            _keyword_sentence("Eksik doğrudan deneyimler", missing_keywords),
            _keyword_sentence("Dürüst olmadığı için doğrudan eklenmeyen riskli iddialar", risky_keywords),
        ], "Belirgin bir ek boşluk tespit edilmedi; yine de bu skor tahminidir.")
    else:
        explanation["before_reason"] = (
            f"The original CV received an estimated score of {before_score} because some target keywords and job-specific positioning were not prominent."
        )
        explanation["after_reason"] = (
            f"The optimized CV received an estimated score of {after_score} because supported keywords and transferable experience were made clearer."
        )
        explanation["improvement_reasons"] = _non_empty_or_default([
            _keyword_sentence("Directly supported keywords were added or emphasized", direct_keywords),
            _keyword_sentence("Transferable skills were reframed toward the job", transferable_keywords),
            metadata.get("optimization_summary", ""),
        ], "The CV wording was aligned more closely with the job description.")
        explanation["remaining_gaps"] = _non_empty_or_default([
            _keyword_sentence("Missing direct experience", missing_keywords),
            _keyword_sentence("Risky claims not added because they were not directly supported", risky_keywords),
        ], "No major remaining gaps were identified, but this is still an estimate.")

    return result


def extract_contact_fields_from_cv_text(cv_text: str) -> dict:
    """Extract conservative contact values from the source CV text."""
    text = unspace_cv_text(cv_text)
    contact = {
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": "",
    }

    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if email_match:
        contact["email"] = _clean_contact_value(email_match.group(0))

    phone_match = _find_phone_match(text)
    if phone_match:
        contact["phone"] = _clean_phone_value(phone_match)

    linkedin_match = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s,;|)>\]]+",
        text,
        flags=re.IGNORECASE,
    )
    if linkedin_match:
        contact["linkedin"] = _clean_contact_value(linkedin_match.group(0))

    github_match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/[^\s,;|)>\]]+",
        text,
        flags=re.IGNORECASE,
    )
    if github_match:
        contact["github"] = _clean_contact_value(github_match.group(0))

    portfolio = _find_portfolio_url(text)
    if portfolio:
        contact["portfolio"] = portfolio

    contact["full_name"] = _infer_full_name_from_top_lines(text)
    contact["location"] = _infer_location_from_text(text, contact)

    return contact


def extract_contact_fields_from_text(cv_text: str) -> dict:
    """Backward-compatible wrapper for CV contact extraction."""
    return extract_contact_fields_from_cv_text(cv_text)


def extract_proper_nouns_from_cv_text(cv_text: str) -> dict:
    """Infer protected proper nouns conservatively from CV section text."""
    text = unspace_cv_text(cv_text)
    sections = _split_cv_text_into_sections(text)
    return {
        "schools": _extract_schools(sections, text),
        "companies": _extract_companies(sections),
        "projects": _extract_project_names(sections),
        "certifications": _extract_certification_names(sections),
    }


def restore_contact_fields_from_source(ats_cv: dict, source_contact: dict) -> dict:
    """Restore exact source contact values without changing generated title/content."""
    result = deepcopy(ats_cv)
    source_contact = source_contact or {}
    contact = result.setdefault("contact", {})
    if not isinstance(contact, dict):
        result["contact"] = {}
        contact = result["contact"]

    for field in CONTACT_FIELDS_TO_RESTORE:
        value = _clean_contact_value(source_contact.get(field))
        if value:
            contact[field] = value

    return result


def restore_preserved_entity_fields_from_source(ats_cv: dict, cv_text: str) -> dict:
    """Restore proper nouns that Gemini may have misspelled, without normalizing text."""
    result = deepcopy(ats_cv)
    source_text = cv_text or ""
    candidates = _extract_preserved_entity_candidates(source_text)
    if not candidates:
        return result

    contact = result.get("contact")
    if isinstance(contact, dict):
        for field in PRESERVED_ENTITY_FIELDS["contact"]:
            contact[field] = _restore_entity_value(contact.get(field), source_text, candidates)

    for section_key in ["experience", "projects", "education", "certifications"]:
        records = result.get(section_key)
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            for field in PRESERVED_ENTITY_FIELDS[section_key]:
                record[field] = _restore_entity_value(record.get(field), source_text, candidates)

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


def _infer_full_name_from_top_lines(text: str) -> str:
    for line in _top_cv_lines(text, limit=10):
        if _line_has_contact_signal(line):
            continue
        if _looks_like_section_heading(line):
            continue
        if _looks_like_person_name(line):
            return line
    return ""


def _infer_location_from_text(text: str, contact: dict) -> str:
    label_patterns = [
        r"(?:location|address|city|konum|adres|şehir|sehir)\s*[:\-]\s*([^\n|•]+)",
    ]
    for pattern in label_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            location = _clean_location_value(match.group(1))
            if location:
                return location

    for line in _top_cv_lines(text, limit=8):
        remaining = line
        for value in contact.values():
            if value:
                remaining = remaining.replace(str(value), " ")
        remaining = re.sub(r"(?:https?://|www\.)\S+", " ", remaining, flags=re.IGNORECASE)
        remaining = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", " ", remaining)
        remaining = re.sub(r"(?:\+?\s?\d[\d\s().-]{7,}\d)", " ", remaining)
        for part in re.split(r"[|•]", remaining):
            location = _clean_location_value(part)
            if _looks_like_location(location):
                return location

    return ""


def _top_cv_lines(text: str, limit: int) -> list[str]:
    lines = []
    for raw_line in (text or "").splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip().strip("-•|")
        if line:
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def _line_has_contact_signal(line: str) -> bool:
    normalized = line.lower()
    return (
        "@" in line
        or "linkedin.com/" in normalized
        or "github.com/" in normalized
        or bool(re.search(r"(?:https?://|www\.)", line, flags=re.IGNORECASE))
        or bool(re.search(r"\d", line))
    )


def _looks_like_section_heading(line: str) -> bool:
    normalized = re.sub(r"[^a-zA-ZçğıöşüÇĞİÖŞÜ\s]+", " ", line).casefold()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    headings = {
        "profile",
        "summary",
        "professional summary",
        "career objective",
        "objective",
        "experience",
        "work experience",
        "professional experience",
        "education",
        "skills",
        "technical skills",
        "projects",
        "certifications",
        "languages",
        "profil",
        "özet",
        "ozet",
        "deneyim",
        "iş deneyimi",
        "is deneyimi",
        "eğitim",
        "egitim",
        "yetenekler",
        "projeler",
        "sertifikalar",
        "diller",
    }
    return normalized in headings


def _looks_like_person_name(line: str) -> bool:
    if not 4 <= len(line) <= 70:
        return False
    if re.search(r"[:/@|•]", line):
        return False
    words = [word for word in re.split(r"\s+", line) if word]
    if not 2 <= len(words) <= 5:
        return False
    if all(len(word) == 1 for word in words):
        return False
    role_terms = {
        "developer",
        "engineer",
        "analyst",
        "specialist",
        "manager",
        "intern",
        "student",
        "consultant",
        "assistant",
        "resume",
        "curriculum",
        "vitae",
        "cv",
    }
    if any(word.lower().strip(".,") in role_terms for word in words):
        return False
    return all(re.fullmatch(r"[A-Za-zÇĞİÖŞÜçğıöşü'’.-]+", word) for word in words)


def _clean_location_value(value: str) -> str:
    location = re.sub(r"\s+", " ", str(value or "")).strip().strip(".,;:()[]{}")
    if len(location) > 80:
        return ""
    return location


def _looks_like_location(value: str) -> bool:
    if not value or len(value) < 3:
        return False
    if _line_has_contact_signal(value):
        return False
    if re.search(r"\b(university|college|developer|engineer|analyst|specialist|manager)\b", value, re.IGNORECASE):
        return False
    words = [word for word in re.split(r"[\s,]+", value) if word]
    if not 1 <= len(words) <= 5:
        return False
    has_location_shape = "," in value or any(word[:1].isupper() for word in words)
    return has_location_shape and all(re.fullmatch(r"[A-Za-zÇĞİÖŞÜçğıöşü'’.-]+", word) for word in words)


def _split_cv_text_into_sections(text: str) -> dict[str, list[str]]:
    sections = {
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
    }
    current_section = ""
    section_aliases = {
        "education": {"education", "eğitim", "egitim", "academic background"},
        "experience": {"experience", "work experience", "professional experience", "deneyim", "iş deneyimi", "is deneyimi", "employment"},
        "projects": {"projects", "projeler", "project experience"},
        "certifications": {"certifications", "certificates", "sertifikalar", "licenses", "courses"},
    }

    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip().strip("-•|")
        if not line:
            continue

        heading_key = _section_heading_key(line, section_aliases)
        if heading_key:
            current_section = heading_key
            continue

        if current_section:
            sections[current_section].append(line)

    return sections


def _section_heading_key(line: str, section_aliases: dict[str, set[str]]) -> str:
    normalized = re.sub(r"[^a-zA-ZçğıöşüÇĞİÖŞÜ\s]+", " ", line).casefold()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if len(normalized.split()) > 4:
        return ""
    for key, aliases in section_aliases.items():
        if normalized in {alias.casefold() for alias in aliases}:
            return key
    return ""


def _extract_schools(sections: dict[str, list[str]], full_text: str) -> list[str]:
    values = []
    school_pattern = (
        r"[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+"
        r"(?:\s+[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+){0,6}"
        r"\s+(?:University|Üniversitesi|Universitesi|College|Institute|School|Academy)"
    )
    search_text = "\n".join(sections.get("education", [])) or full_text
    values.extend(match.group(0).strip() for match in re.finditer(school_pattern, search_text))
    return _dedupe_preserve_order(values)


def _extract_companies(sections: dict[str, list[str]]) -> list[str]:
    values = []
    company_suffix_pattern = re.compile(
        r"[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+"
        r"(?:\s+[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+){0,5}"
        r"\s+(?:A\.Ş\.|AS|Ltd\.?|LLC|Inc\.?|Corp\.?|Company|Technologies|Technology|Bank|Bankası|Banka|Group|Holding)",
    )
    for line in sections.get("experience", []):
        matches = [match.group(0).strip() for match in company_suffix_pattern.finditer(line)]
        values.extend(matches)
        if not matches and _looks_like_entity_title(line):
            values.append(_strip_date_range(line))
    return _dedupe_preserve_order(values)


def _extract_project_names(sections: dict[str, list[str]]) -> list[str]:
    values = []
    for line in sections.get("projects", []):
        cleaned = _strip_date_range(line)
        if _looks_like_entity_title(cleaned):
            values.append(cleaned)
    return _dedupe_preserve_order(values)


def _extract_certification_names(sections: dict[str, list[str]]) -> list[str]:
    values = []
    for line in sections.get("certifications", []):
        cleaned = _strip_date_range(line)
        if cleaned and len(cleaned) <= 120 and not _line_has_contact_signal(cleaned):
            values.append(cleaned)
    return _dedupe_preserve_order(values)


def _looks_like_entity_title(line: str) -> bool:
    cleaned = _clean_location_value(line)
    if not cleaned or len(cleaned) > 90:
        return False
    if _line_has_contact_signal(cleaned):
        return False
    if re.search(r"\b(responsible|worked|developed|created|supported|managed|experience|education)\b", cleaned, re.IGNORECASE):
        return False
    words = [word for word in re.split(r"\s+", cleaned) if word]
    if not 1 <= len(words) <= 8:
        return False
    return any(word[:1].isupper() for word in words) and not cleaned.endswith(".")


def _strip_date_range(line: str) -> str:
    cleaned = re.sub(r"\b(?:19|20)\d{2}\b\s*(?:[-–—]\s*(?:present|current|ongoing|(?:19|20)\d{2}))?", "", line, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*[-–—|]\s*$", "", cleaned)
    return _clean_location_value(cleaned)


def _find_phone_match(text: str) -> str:
    for match in re.finditer(r"(?:\+?\s?\d[\d\s().-]{7,}\d)", text):
        value = _clean_contact_value(match.group(0))
        digit_count = sum(character.isdigit() for character in value)
        if 9 <= digit_count <= 16:
            return value
    return ""


def _find_portfolio_url(text: str) -> str:
    for match in re.finditer(r"(?:https?://|www\.)[^\s,;|)>\]]+", text, flags=re.IGNORECASE):
        value = _clean_contact_value(match.group(0))
        normalized = value.lower()
        if "linkedin.com/" in normalized or "github.com/" in normalized:
            continue
        if "@" in normalized:
            continue
        return value
    return ""


def _clean_contact_value(value) -> str:
    return str(value or "").strip().rstrip(".,;:)]}>")


def _clean_phone_value(value) -> str:
    phone = _clean_contact_value(value)
    if not phone:
        return ""

    comparable_phone = phone.replace("+", "").strip()
    groups = [group for group in re.split(r"\s+", comparable_phone) if group]
    digit_groups = [group for group in groups if re.fullmatch(r"\d", group)]
    digits = "".join(character for character in phone if character.isdigit())

    if len(digit_groups) >= 8 and len(digit_groups) == len(groups) and 10 <= len(digits) <= 13:
        if digits.startswith("90") and len(digits) == 12:
            return f"+90 {digits[2:5]} {digits[5:8]} {digits[8:10]} {digits[10:12]}"
        if digits.startswith("0") and len(digits) == 11:
            return f"{digits[0:4]} {digits[4:7]} {digits[7:9]} {digits[9:11]}"
        if len(digits) == 10:
            return f"{digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"

    return phone


def _extract_preserved_entity_candidates(cv_text: str) -> list[str]:
    candidates = []

    for raw_line in cv_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip().strip("-•|")
        if 2 <= len(line) <= 90 and not re.search(r"@", line):
            candidates.append(line)

    phrase_patterns = [
        r"[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+(?:\s+[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+){0,5}\s+(?:University|Üniversitesi|Universitesi)",
        r"[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+(?:\s+[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ.'’&-]+){0,5}\s+(?:Bank|Bankası|Banka|A\.Ş\.|Ltd\.|Inc\.|LLC|Company|Technologies)",
    ]
    for pattern in phrase_patterns:
        candidates.extend(match.group(0).strip() for match in re.finditer(pattern, cv_text))

    return _dedupe_preserve_order(candidates)


def _restore_entity_value(value, source_text: str, candidates: list[str]) -> str:
    current = str(value or "").strip()
    if not current:
        return current
    if current in source_text:
        return current

    normalized_current = _normalize_for_similarity(current)
    if len(normalized_current) < 4:
        return current

    best_candidate = ""
    best_score = 0.0
    for candidate in candidates:
        normalized_candidate = _normalize_for_similarity(candidate)
        if not normalized_candidate:
            continue
        length_ratio = len(normalized_current) / max(1, len(normalized_candidate))
        if length_ratio < 0.55 or length_ratio > 1.8:
            continue
        score = SequenceMatcher(None, normalized_current, normalized_candidate).ratio()
        if score > best_score:
            best_candidate = candidate
            best_score = score

    if best_score >= 0.86:
        return best_candidate
    return current


def _normalize_for_similarity(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+", "", value).casefold()


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def detect_role_family(title: str) -> str:
    family = detect_job_family(target_role=title)
    return "" if family == "general" else family


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


def _keyword_sentence(prefix: str, values: list) -> str:
    if not values:
        return ""
    return f"{prefix}: {', '.join(str(value) for value in values if value)}"


def _non_empty_or_default(values: list[str], default: str) -> list[str]:
    cleaned = [value for value in values if value]
    return cleaned or [default]


def build_aligned_target_title(target_role: str, target_family: str, language: str) -> str:
    return target_title_for_job_family(target_role, target_family or "general", language) or target_role


def _clean_character_spacing(val: str) -> str:
    if not val:
        return ""
    val_str = str(val).strip()
    
    # Split by two or more spaces to detect words
    parts = re.split(r"\s{2,}", val_str)
    cleaned_parts = []
    for part in parts:
        part_tokens = part.split()
        if not part_tokens:
            continue
        # If the part looks character-spaced: e.g. single letters separated by space
        # We consider it character-spaced if there is more than 1 token and
        # at least 70% of tokens are single characters.
        if len(part_tokens) > 1 and (sum(1 for t in part_tokens if len(t) == 1) / len(part_tokens)) >= 0.70:
            cleaned_parts.append("".join(part_tokens))
        else:
            cleaned_parts.append(part)
            
    if len(parts) == 1:
        tokens = val_str.split()
        if len(tokens) > 1 and (sum(1 for t in tokens if len(t) == 1) / len(tokens)) >= 0.70:
            return "".join(tokens)
            
    return " ".join(cleaned_parts)


def unspace_cv_text(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        cleaned_lines.append(_clean_character_spacing(line))
    return "\n".join(cleaned_lines)

