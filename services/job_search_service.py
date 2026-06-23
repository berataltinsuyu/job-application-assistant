import os
import requests
from fastapi import HTTPException

def search_jobs_with_serpapi(
    query: str,
    location: str | None,
    remote: bool,
    language: str
) -> list[dict]:
    api_key = os.getenv("SERPAPI_API_KEY")
    is_tr = language.lower() == "turkish"
    
    if not api_key:
        err_msg = (
            "Gerçek iş ilanı araması için SERPAPI_API_KEY .env dosyasına eklenmelidir."
            if is_tr else
            "SERPAPI_API_KEY is missing. Please add it to your .env file to use real job search."
        )
        raise HTTPException(status_code=400, detail=err_msg)

    if remote:
        query = f"{query} remote"

    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location or "",
        "hl": "tr" if is_tr else "en",
        "api_key": api_key
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
    except Exception:
        err_msg = (
            "Arama motoruna bağlanırken bir hata oluştu."
            if is_tr else
            "An error occurred while connecting to the search engine."
        )
        raise HTTPException(status_code=500, detail=err_msg)

    if response.status_code == 401 or "Invalid API key" in response.text:
        err_msg = (
            "SerpAPI anahtarı geçersiz olabilir veya kullanım limiti dolmuş olabilir."
            if is_tr else
            "SerpAPI key may be invalid, expired, or the usage limit may be exceeded."
        )
        raise HTTPException(status_code=401, detail=err_msg)
    
    if response.status_code != 200:
        res_json = {}
        try:
            res_json = response.json()
        except Exception:
            pass
        
        error_text = res_json.get("error", "")
        if any(x in error_text.lower() for x in ["quota", "limit", "expired", "credit", "plan"]):
            err_msg = (
                "SerpAPI anahtarı geçersiz olabilir veya kullanım limiti dolmuş olabilir."
                if is_tr else
                "SerpAPI key may be invalid, expired, or the usage limit may be exceeded."
            )
            raise HTTPException(status_code=400, detail=err_msg)
        
        err_msg = (
            f"SerpAPI araması başarısız oldu: {error_text}"
            if is_tr else
            f"SerpAPI search failed: {error_text}"
        )
        if api_key in err_msg:
            err_msg = err_msg.replace(api_key, "***")
        raise HTTPException(status_code=response.status_code, detail=err_msg)

    results = response.json()
    jobs_results = results.get("jobs_results", [])
    
    normalized_jobs = []
    for job in jobs_results:
        # Extract Apply URL:
        # 1. first apply option link if exists
        # 2. related link if exists
        # 3. serpapi/google_jobs listing link if available
        # 4. empty string
        url = ""
        apply_options = job.get("apply_options", [])
        if apply_options and isinstance(apply_options, list):
            url = apply_options[0].get("link") or ""
        
        if not url:
            related_links = job.get("related_links", [])
            if related_links and isinstance(related_links, list):
                url = related_links[0].get("link") or ""
                
        if not url:
            url = job.get("link") or job.get("share_link") or ""
            
        if not url:
            url = ""

        # Format posted_date
        posted_date = job.get("detected_extensions", {}).get("posted_at") or job.get("posted_at") or ""
        
        via = job.get("via", "")
        schedule_type = job.get("detected_extensions", {}).get("schedule_type") or ""
        wfh = job.get("detected_extensions", {}).get("work_from_home", False)
        job_id = str(job.get("job_id") or "")

        normalized_jobs.append({
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("location", ""),
            "source": "SerpAPI Google Jobs",
            "via": via,
            "url": url,
            "description": job.get("description", ""),
            "posted_date": posted_date,
            "schedule_type": schedule_type,
            "work_from_home": wfh,
            "job_id": job_id
        })

    return normalized_jobs


def search_jobs_with_jooble(
    query: str,
    location: str | None,
    remote: bool,
    language: str
) -> list[dict]:
    api_key = os.getenv("JOOBLE_API_KEY")
    is_tr = language.lower() == "turkish"
    
    if not api_key:
        err_msg = (
            "Gerçek iş ilanı araması için JOOBLE_API_KEY .env dosyasına eklenmelidir."
            if is_tr else
            "JOOBLE_API_KEY is missing. Please add it to your .env file to use real job search."
        )
        raise HTTPException(status_code=400, detail=err_msg)

    kw = query
    if remote:
        kw_suffix = "uzaktan" if is_tr else "remote"
        kw = f"{kw} {kw_suffix}"

    url = f"https://jooble.org/api/v1/db/{api_key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "keywords": kw,
        "location": location or ""
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
    except Exception:
        err_msg = (
            "Arama motoruna bağlanırken bir hata oluştu."
            if is_tr else
            "An error occurred while connecting to the search engine."
        )
        raise HTTPException(status_code=500, detail=err_msg)

    if response.status_code == 401 or "invalid key" in response.text.lower():
        err_msg = (
            "Jooble API anahtarı geçersiz olabilir veya kullanım limiti dolmuş olabilir."
            if is_tr else
            "Jooble API key may be invalid, expired, or the usage limit may be exceeded."
        )
        raise HTTPException(status_code=401, detail=err_msg)

    if response.status_code != 200:
        err_msg = (
            f"Jooble araması başarısız oldu: {response.text}"
            if is_tr else
            f"Jooble search failed: {response.text}"
        )
        if api_key in err_msg:
            err_msg = err_msg.replace(api_key, "***")
        raise HTTPException(status_code=response.status_code, detail=err_msg)

    data = response.json()
    jobs_list = data.get("jobs", [])
    
    normalized_jobs = []
    for job in jobs_list:
        normalized_jobs.append({
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "source": "Jooble",
            "via": job.get("source", ""),
            "url": job.get("link", ""),
            "description": job.get("snippet", ""),
            "posted_date": job.get("updated", ""),
            "schedule_type": job.get("type", ""),
            "work_from_home": remote or "remote" in job.get("title", "").lower() or "uzaktan" in job.get("title", "").lower(),
            "job_id": str(job.get("id", ""))
        })
        
    return normalized_jobs


def search_jobs_with_adzuna(
    query: str,
    location: str | None,
    remote: bool,
    language: str
) -> list[dict]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    is_tr = language.lower() == "turkish"
    
    if not app_id or not app_key:
        err_msg = (
            "Gerçek iş ilanı araması için ADZUNA_APP_ID ve ADZUNA_APP_KEY .env dosyasına eklenmelidir."
            if is_tr else
            "ADZUNA_APP_ID and ADZUNA_APP_KEY are missing. Please add them to your .env file to use real job search."
        )
        raise HTTPException(status_code=400, detail=err_msg)

    is_turkey = False
    if location:
        loc_lower = location.lower()
        if any(w in loc_lower for w in ["turkey", "türkiye", "istanbul", "ankara", "izmir"]):
            is_turkey = True
            
    if is_turkey:
        return []

    country = "us"
    if location:
        loc_lower = location.lower()
        if "united kingdom" in loc_lower or "uk" in loc_lower or "london" in loc_lower or "gb" in loc_lower:
            country = "gb"
            
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    
    kw = query
    if remote:
        kw = f"{kw} remote"
        
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": kw,
        "results_per_page": 15,
        "content-type": "application/json"
    }
    
    if location and location.lower() not in ["united states", "united kingdom", "us", "gb", "uk"]:
        params["where"] = location

    try:
        response = requests.get(url, params=params, timeout=15)
    except Exception:
        err_msg = (
            "Arama motoruna bağlanırken bir hata oluştu."
            if is_tr else
            "An error occurred while connecting to the search engine."
        )
        raise HTTPException(status_code=500, detail=err_msg)

    if response.status_code == 401 or response.status_code == 403 or "unauthorized" in response.text.lower():
        err_msg = (
            "Adzuna API anahtarı geçersiz olabilir veya kullanım limiti dolmuş olabilir."
            if is_tr else
            "Adzuna API key may be invalid, expired, or the usage limit may be exceeded."
        )
        raise HTTPException(status_code=401, detail=err_msg)

    if response.status_code != 200:
        err_msg = (
            f"Adzuna araması başarısız oldu: {response.text}"
            if is_tr else
            f"Adzuna search failed: {response.text}"
        )
        if app_id in err_msg:
            err_msg = err_msg.replace(app_id, "***")
        if app_key in err_msg:
            err_msg = err_msg.replace(app_key, "***")
        raise HTTPException(status_code=response.status_code, detail=err_msg)

    data = response.json()
    results = data.get("results", [])
    
    normalized_jobs = []
    for job in results:
        company_name = job.get("company", {}).get("display_name", "")
        location_name = job.get("location", {}).get("display_name", "")
        posted_date = job.get("created", "")
        contract_type = job.get("contract_type", "") or ""
        
        normalized_jobs.append({
            "title": job.get("title", ""),
            "company": company_name,
            "location": location_name,
            "source": "Adzuna",
            "via": "",
            "url": job.get("redirect_url", ""),
            "description": job.get("description", ""),
            "posted_date": posted_date,
            "schedule_type": contract_type,
            "work_from_home": remote or "remote" in job.get("title", "").lower(),
            "job_id": str(job.get("id", ""))
        })
        
    return normalized_jobs


def search_jobs(
    query: str,
    location: str | None,
    remote: bool,
    language: str,
    provider: str = "auto"
) -> dict:
    is_tr = language.lower() == "turkish"
    provider = provider.lower()
    
    has_serpapi = bool(os.getenv("SERPAPI_API_KEY"))
    has_jooble = bool(os.getenv("JOOBLE_API_KEY"))
    has_adzuna = bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"))
    
    if not (has_serpapi or has_jooble or has_adzuna):
        err_msg = (
            "Gerçek iş ilanı araması için en az bir API anahtarı (SerpAPI, Jooble veya Adzuna) .env dosyasına eklenmelidir."
            if is_tr else
            "At least one API key (SerpAPI, Jooble, or Adzuna) must be added to your .env file to use real job search."
        )
        raise HTTPException(status_code=400, detail=err_msg)
        
    tried_providers = []
    jobs = []
    
    if provider == "auto":
        is_turkey_search = False
        if location:
            loc_lower = location.lower()
            if any(w in loc_lower for w in ["turkey", "türkiye", "istanbul", "ankara", "izmir"]):
                is_turkey_search = True
        if is_tr:
            is_turkey_search = True
            
        execution_order = []
        if is_turkey_search:
            if has_jooble:
                execution_order.append("jooble")
            if has_serpapi:
                execution_order.append("serpapi")
            if has_adzuna:
                execution_order.append("adzuna")
        else:
            if has_serpapi:
                execution_order.append("serpapi")
            if has_jooble:
                execution_order.append("jooble")
            if has_adzuna:
                execution_order.append("adzuna")
                
        for p, has_key in [("serpapi", has_serpapi), ("jooble", has_jooble), ("adzuna", has_adzuna)]:
            if has_key and p not in execution_order:
                execution_order.append(p)
    else:
        if provider == "serpapi" and not has_serpapi:
            err_msg = (
                "SERPAPI_API_KEY eksik." if is_tr else "SERPAPI_API_KEY is missing."
            )
            raise HTTPException(status_code=400, detail=err_msg)
        elif provider == "jooble" and not has_jooble:
            err_msg = (
                "JOOBLE_API_KEY eksik." if is_tr else "JOOBLE_API_KEY is missing."
            )
            raise HTTPException(status_code=400, detail=err_msg)
        elif provider == "adzuna" and not has_adzuna:
            err_msg = (
                "ADZUNA_APP_ID veya APP_KEY eksik." if is_tr else "ADZUNA_APP_ID or APP_KEY is missing."
            )
            raise HTTPException(status_code=400, detail=err_msg)
            
        execution_order = [provider]

    for p in execution_order:
        try:
            if p == "serpapi":
                provider_jobs = search_jobs_with_serpapi(query, location, remote, language)
            elif p == "jooble":
                provider_jobs = search_jobs_with_jooble(query, location, remote, language)
            elif p == "adzuna":
                provider_jobs = search_jobs_with_adzuna(query, location, remote, language)
            else:
                provider_jobs = []
                
            tried_providers.append({
                "provider": p,
                "result_count": len(provider_jobs),
                "status": "success"
            })
            
            if provider_jobs:
                jobs = provider_jobs
                break
        except HTTPException as e:
            tried_providers.append({
                "provider": p,
                "result_count": 0,
                "status": f"error: {e.detail}"
            })
            if provider != "auto":
                raise e
        except Exception as e:
            tried_providers.append({
                "provider": p,
                "result_count": 0,
                "status": f"error: {str(e)}"
            })
            if provider != "auto":
                raise HTTPException(status_code=500, detail=str(e))
                
    return {
        "jobs": jobs,
        "tried_providers": tried_providers
    }
