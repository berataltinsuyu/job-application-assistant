import json
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory
from services.file_parser_service import extract_text_from_cv
from services.job_search_service import search_jobs as service_search_jobs
from services.llm_service import extract_cv_profile, rank_jobs_for_cv

router = APIRouter(
    prefix="/job-recommendations",
    tags=["Job Recommendations"]
)


@router.post("/cv-profile")
async def get_cv_profile(
    cv_file: UploadFile = File(...),
    language: str = Form("English"),
    db: Session = Depends(get_db)
):
    cv_text = await extract_text_from_cv(cv_file)
    profile = extract_cv_profile(cv_text, language)

    # Save to history
    history = ApplicationHistory(
        request_type="cv_profile",
        cv_filename=cv_file.filename,
        job_text=None,
        result=json.dumps(profile, ensure_ascii=False)
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
        "cv_filename": cv_file.filename,
        "result": profile
    }


@router.post("/job-search")
def search_jobs(
    query: str = Form(...),
    location: str = Form(""),
    remote: bool = Form(False),
    language: str = Form("English"),
    provider: str = Form("auto")
):
    result = service_search_jobs(
        query=query,
        location=location,
        remote=remote,
        language=language,
        provider=provider
    )

    return {
        "query": query,
        "location": location,
        "remote": remote,
        "provider": provider,
        "job_count": len(result.get("jobs", [])),
        "jobs": result.get("jobs", []),
        "tried_providers": result.get("tried_providers", [])
    }


@router.post("/rank-jobs")
async def rank_jobs(
    cv_file: UploadFile = File(...),
    jobs_json: str = Form(...),
    language: str = Form("English"),
    db: Session = Depends(get_db)
):
    cv_text = await extract_text_from_cv(cv_file)
    try:
        jobs = json.loads(jobs_json)
        if not isinstance(jobs, list):
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="jobs_json must be a valid JSON list of job dictionaries."
        )

    # Limit to 10 jobs before sending to Gemini as per instructions
    jobs = jobs[:10]

    result = rank_jobs_for_cv(cv_text, jobs, language)

    # Save to history
    history = ApplicationHistory(
        request_type="ranked_jobs",
        cv_filename=cv_file.filename,
        job_text=jobs_json,
        result=json.dumps(result, ensure_ascii=False)
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
        "cv_filename": cv_file.filename,
        "result": result
    }


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    seen_urls = set()
    seen_keys = set()
    deduped = []
    
    # Sort jobs so that those with a URL are processed first
    jobs_sorted = sorted(jobs, key=lambda x: 1 if x.get("url") else 0, reverse=True)
    
    for job in jobs_sorted:
        url = job.get("url", "").strip()
        title = job.get("title", "").strip().lower()
        company = job.get("company", "").strip().lower()
        loc = job.get("location", "").strip().lower()
        key = f"{title}|{company}|{loc}"
        
        if url:
            if url not in seen_urls and key not in seen_keys:
                seen_urls.add(url)
                seen_keys.add(key)
                deduped.append(job)
        else:
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(job)
                
    return deduped


@router.post("/recommended-jobs")
async def recommended_jobs(
    cv_file: UploadFile = File(...),
    location: str = Form(""),
    remote: bool = Form(False),
    language: str = Form("English"),
    provider: str = Form("auto"),
    db: Session = Depends(get_db)
):
    # 1. Extract CV text
    cv_text = await extract_text_from_cv(cv_file)
    
    # 2. Extract CV profile
    profile = extract_cv_profile(cv_text, language)
    
    is_tr = language.lower() == "turkish"
    broad_fallbacks = [
        "yazılım geliştirici",
        "junior yazılım geliştirici",
        "backend developer",
        "yazılım stajyeri",
        "python developer",
        ".NET developer",
        "uzaktan yazılım geliştirici"
    ] if is_tr else [
        "software engineer",
        "junior software developer",
        "backend developer",
        "software engineer intern",
        "backend developer intern",
        "python developer",
        ".NET developer",
        "remote software developer"
    ]
    
    # 3. Take first 2-3 suggested search queries
    queries = profile.get("suggested_search_queries", [])[:3]
    if not queries:
        roles = profile.get("target_roles", [])[:1]
        queries = [roles[0]] if roles else ["Software Developer"]

    all_raw_jobs = []
    tried_queries = []
    all_tried_providers = []
    seen_searches = set()

    # Define the search runner helper
    def do_search(q: str, loc: str):
        search_key = (q.strip().lower(), loc.strip().lower(), remote)
        if search_key in seen_searches:
            return 0
        seen_searches.add(search_key)
        
        # Safe log (without exposing SERPAPI_API_KEY)
        print(f"Searching jobs: query='{q}', location='{loc}', remote={remote}, provider='{provider}'")
        
        try:
            search_res = service_search_jobs(
                query=q,
                location=loc,
                remote=remote,
                language=language,
                provider=provider
            )
            jobs = search_res.get("jobs", [])
            count = len(jobs)
            print(f"Found jobs: {count}")
            
            # Accumulate tried providers
            for tp in search_res.get("tried_providers", []):
                all_tried_providers.append(tp)
            
            # Record in tried queries
            tried_queries.append({
                "query": q,
                "location": loc,
                "remote": remote,
                "result_count": count
            })
            
            if count > 0:
                all_raw_jobs.extend(jobs)
            return count
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Search failed for query='{q}', location='{loc}': {str(e)}")
            tried_queries.append({
                "query": q,
                "location": loc,
                "remote": remote,
                "result_count": 0
            })
            return 0

    # Decide Alt Location Attempts
    loc_attempts = []
    if remote:
        if location != "":
            loc_attempts.append("")
        if location.lower() != "remote":
            loc_attempts.append("Remote")
    
    country_fallback = "Turkey" if is_tr else "United States"
    if location.lower() != country_fallback.lower():
        loc_attempts.append(country_fallback)

    # Helper to check if we should stop once 10 raw jobs are collected
    def has_enough_jobs():
        deduped = deduplicate_jobs(all_raw_jobs)
        return len(deduped) >= 10

    # Run suggested specific queries first
    for q in queries:
        if has_enough_jobs():
            break
        count = do_search(q, location)
        
        # If location-specific search returns 0, retry with broader locations
        if count == 0:
            for alt_loc in loc_attempts:
                if has_enough_jobs():
                    break
                do_search(q, alt_loc)

    # If total jobs found (after specific queries) is 0, try broad fallback queries
    if not deduplicate_jobs(all_raw_jobs):
        for q in broad_fallbacks:
            if has_enough_jobs():
                break
            count = do_search(q, location)
            
            # If location-specific search returns 0, retry with broader locations
            if count == 0:
                for alt_loc in loc_attempts:
                    if has_enough_jobs():
                        break
                    do_search(q, alt_loc)

    # Summarize tried providers
    summary_providers = {}
    for tp in all_tried_providers:
        p_name = tp["provider"]
        if p_name not in summary_providers:
            summary_providers[p_name] = {
                "provider": p_name,
                "result_count": 0,
                "status": tp["status"]
            }
        summary_providers[p_name]["result_count"] += tp["result_count"]
        if tp["status"] == "success":
            summary_providers[p_name]["status"] = "success"
            
    tried_providers_final = list(summary_providers.values())

    # Deduplicate and limit to 10 jobs
    final_raw_jobs = deduplicate_jobs(all_raw_jobs)[:10]

    # Check if empty results
    if not final_raw_jobs:
        empty_msg = (
            "Birden fazla arama denenmesine rağmen iş ilanı bulunamadı. 'software engineer' gibi daha genel bir pozisyon adı veya 'United States' gibi daha geniş bir lokasyon deneyin."
            if is_tr else
            "No jobs found after trying multiple search queries. Try a broader role title such as 'software engineer' or a wider location such as 'United States'."
        )
        result = {
            "candidate_profile": profile,
            "search_queries": queries,
            "tried_queries": tried_queries,
            "tried_providers": tried_providers_final,
            "raw_job_count": 0,
            "recommended_jobs": [],
            "summary": empty_msg
        }
    else:
        # Rank jobs with Gemini
        ranked_result = rank_jobs_for_cv(cv_text, final_raw_jobs, language)
        
        result = {
            "candidate_profile": profile,
            "search_queries": queries,
            "tried_queries": tried_queries,
            "tried_providers": tried_providers_final,
            "raw_job_count": len(final_raw_jobs),
            "recommended_jobs": ranked_result.get("ranked_jobs", []),
            "summary": ranked_result.get("summary", "")
        }

    # Store result in history
    history = ApplicationHistory(
        request_type="recommended_jobs",
        cv_filename=cv_file.filename,
        job_text=f"Location: {location}, Remote: {remote}, Provider: {provider}",
        result=json.dumps(result, ensure_ascii=False)
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    result["id"] = history.id
    return result
