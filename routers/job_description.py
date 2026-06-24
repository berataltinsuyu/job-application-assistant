from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.job_description_service import extract_job_description_from_url

router = APIRouter(
    prefix="/extract-job-description",
    tags=["Job Description"]
)

class JobUrlRequest(BaseModel):
    url: str | None = None
    job_url: str | None = None
    language: str | None = "English"

@router.post("")
def extract_description(payload: JobUrlRequest):
    url = payload.url or payload.job_url
    result = extract_job_description_from_url(url, payload.language or "English")
    if not url or not result.get("url"):
        raise HTTPException(status_code=400, detail="Invalid URL. Please provide an http or https URL.")
    if not result.get("success") and not str(url).strip().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL. Please provide an http or https URL.")
    return result
