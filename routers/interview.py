from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory
from services.llm_service import generate_interview_questions

router = APIRouter(
    prefix="/interview-prep",
    tags=["Interview Prep"]
)


@router.post("")
def create_interview_prep(
    job_text: str = Form(...),
    db: Session = Depends(get_db)
):
    result = generate_interview_questions(job_text=job_text)

    history = ApplicationHistory(
        request_type="interview",
        cv_filename=None,
        job_text=job_text,
        result=result
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
        "job_text_length": len(job_text),
        "result": result
    }