from urllib.parse import urlparse

import requests

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - optional dependency guard
    BeautifulSoup = None


FAILURE_MESSAGE_EN = "Could not extract this page automatically. Please paste the job description manually."
FAILURE_MESSAGE_TR = "Bu sayfa otomatik çıkarılamadı. Lütfen ilan açıklamasını manuel yapıştırın."


def extract_job_description_from_url(job_url: str, language: str = "English") -> dict:
    """Single user-triggered URL extraction helper.

    This is not a source adapter and must not be used by monitoring runs. It performs one
    normal HTTP GET for one explicit user-provided URL, then returns readable text or a
    clean manual-paste fallback message.
    """
    is_tr = language.lower() == "turkish"
    failure_message = FAILURE_MESSAGE_TR if is_tr else FAILURE_MESSAGE_EN
    job_url = (job_url or "").strip()

    if not _is_valid_http_url(job_url):
        return _failure(job_url, failure_message)

    try:
        response = requests.get(
            job_url,
            headers={
                "User-Agent": "JobApplicationAssistant/Phase3A manual-url-extractor",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=10,
            allow_redirects=True,
        )
    except requests.RequestException:
        return _failure(job_url, failure_message)

    content_type = (response.headers.get("content-type") or "").lower()
    if response.status_code in {401, 403, 407, 408, 409, 423, 429}:
        return _failure(job_url, failure_message)
    if response.status_code < 200 or response.status_code >= 300:
        return _failure(job_url, failure_message)
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return _failure(job_url, failure_message)

    html = response.text or ""
    title, text = _extract_readable_html(html)
    if not _is_clean_extracted_text(text):
        return _failure(job_url, failure_message)

    return {
        "success": True,
        "url": job_url,
        "source_url": job_url,
        "title": title,
        "text": text,
        "extracted_text": text,
        "message": "Content extracted successfully.",
    }


def _is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _failure(url: str, message: str) -> dict:
    return {
        "success": False,
        "url": url,
        "source_url": url,
        "title": "",
        "text": "",
        "extracted_text": "",
        "message": message,
    }


def _extract_readable_html(html: str) -> tuple[str, str]:
    if BeautifulSoup is None:
        return "", _clean_text(html)

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form"]):
        element.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = _clean_text(soup.title.string)

    meta_description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_description = _clean_text(meta.get("content"))

    containers = []
    for selector in ["main", "article", "[role='main']", ".job-description", ".description"]:
        containers.extend(soup.select(selector))
    if not containers and soup.body:
        containers = [soup.body]
    if not containers:
        containers = [soup]

    text_parts = []
    if title:
        text_parts.append(title)
    if meta_description:
        text_parts.append(meta_description)
    for container in containers[:3]:
        container_text = _clean_text(container.get_text(separator="\n"))
        if container_text and container_text not in text_parts:
            text_parts.append(container_text)

    return title, _clean_text("\n\n".join(text_parts))


def _clean_text(value: str) -> str:
    lines = [line.strip() for line in str(value or "").splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def _is_clean_extracted_text(text: str) -> bool:
    if len(text or "") < 80:
        return False
    lowered = text.lower()
    blocked_markers = [
        "cloudflare",
        "checking your browser",
        "enable javascript and cookies",
        "access denied",
        "captcha",
        "verify you are human",
    ]
    return not any(marker in lowered for marker in blocked_markers)
