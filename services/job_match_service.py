import re


def score_job_against_profile(job: dict, alert_profile: dict) -> dict:
    keywords = _list_value(alert_profile.get("keywords"))
    excluded_keywords = _list_value(alert_profile.get("excluded_keywords"))

    title = _clean_text(job.get("title"))
    description = _clean_text(job.get("description"))
    haystack = f"{title} {description}"

    matched_keywords = [keyword for keyword in keywords if _keyword_matches(keyword, haystack)]
    missing_keywords = [keyword for keyword in keywords if keyword not in matched_keywords]

    score = 0
    if keywords:
        score += round((len(matched_keywords) / len(keywords)) * 60)
    else:
        score += 30

    field_matches = []
    for field_name, weight in [
        ("location", 10),
        ("seniority", 10),
        ("job_type", 10),
        ("work_model", 10),
    ]:
        expected = _clean_text(alert_profile.get(field_name))
        actual = _clean_text(job.get(field_name))
        if not expected:
            score += weight // 2
            continue
        if actual and _field_matches(expected, actual):
            score += weight
            field_matches.append(field_name)
        else:
            missing_keywords.append(f"{field_name}: {expected}")

    excluded_hits = [keyword for keyword in excluded_keywords if _keyword_matches(keyword, haystack)]
    if excluded_hits:
        score -= min(40, 20 + (len(excluded_hits) * 10))

    score = max(0, min(100, int(score)))
    matched_output = matched_keywords + field_matches
    missing_output = [item for item in missing_keywords if item not in matched_output]

    summary = _build_summary(score, matched_keywords, field_matches, excluded_hits)
    return {
        "match_score": score,
        "match_summary": summary,
        "matched_keywords": matched_output,
        "missing_keywords": missing_output,
    }


def _build_summary(score: int, matched_keywords: list[str], field_matches: list[str], excluded_hits: list[str]) -> str:
    parts = [f"Deterministic match score: {score}/100."]
    if matched_keywords:
        parts.append(f"Matched keywords: {', '.join(matched_keywords[:6])}.")
    else:
        parts.append("No profile keywords matched the title or description.")
    if field_matches:
        parts.append(f"Matched filters: {', '.join(field_matches)}.")
    if excluded_hits:
        parts.append(f"Excluded keyword penalty applied: {', '.join(excluded_hits[:4])}.")
    return " ".join(parts)


def _list_value(value) -> list[str]:
    if isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = re.split(r"[,;\n]", value)
    else:
        values = []
    return [_clean_text(item) for item in values if _clean_text(item)]


def _keyword_matches(keyword: str, haystack: str) -> bool:
    normalized_keyword = _normalize(keyword)
    normalized_haystack = _normalize(haystack)
    if not normalized_keyword:
        return False
    pattern = r"(?<!\w)" + re.escape(normalized_keyword) + r"(?!\w)"
    return bool(re.search(pattern, normalized_haystack))


def _field_matches(expected: str, actual: str) -> bool:
    normalized_expected = _normalize(expected)
    normalized_actual = _normalize(actual)
    return normalized_expected in normalized_actual or normalized_actual in normalized_expected


def _normalize(value: str) -> str:
    cleaned = _clean_text(value)
    turkish_mapped = cleaned.replace("İ", "i").replace("I", "ı")
    return re.sub(r"\s+", " ", turkish_mapped.lower()).strip()


def _clean_text(value) -> str:
    return str(value or "").strip()
