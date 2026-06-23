from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.job_description_service import extract_job_description_from_url

router = APIRouter(
    prefix="/extract-job-description",
    tags=["Job Description"]
)

class JobUrlRequest(BaseModel):
    job_url: str
    language: str | None = "English"

@router.post("")
def extract_description(payload: JobUrlRequest):
    result = extract_job_description_from_url(payload.job_url, payload.language or "English")
    return result
