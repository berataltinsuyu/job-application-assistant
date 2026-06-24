def extract_job_description_from_url(job_url: str, language: str = "English") -> dict:
    is_tr = language.lower() == "turkish"
    message = (
        "URL'den iş ilanı çekme devre dışı. Lütfen iş ilanı metnini Genel Dosyalar ve Ayarlar bölümüne manuel olarak yapıştırın."
        if is_tr else
        "Job URL fetching is disabled. Please paste the job description manually in Global Uploads & Settings."
    )
    return {
        "success": False,
        "source_url": (job_url or "").strip(),
        "extracted_text": "",
        "message": message,
    }
