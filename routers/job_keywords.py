import json
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from database import get_db
from models import ApplicationHistory
from services.llm_service import extract_job_keywords

router = APIRouter(
    prefix="/job-keywords",
    tags=["Keywords"]
)

@router.post("")
def get_job_keywords(
    job_text: str = Form(...),
    language: str = Form("Turkish"),
    db: Session = Depends(get_db)
):
    result = extract_job_keywords(
        job_text=job_text,
        language=language
    )

    history = ApplicationHistory(
        request_type="job_keywords",
        cv_filename=None,
        job_text=job_text,
        result=json.dumps(result, ensure_ascii=False)
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
        "language": language,
        "result": result
    }
