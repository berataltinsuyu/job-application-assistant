import json
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from models import ApplicationHistory
from services.file_parser_service import extract_text_from_cv
from services.llm_service import generate_personalized_interview

router = APIRouter(
    prefix="/personalized-interview-prep",
    tags=["Personalized Interview Prep"]
)

@router.post("")
async def get_personalized_interview_prep(
    cv_file: UploadFile = File(...),
    job_text: str = Form(...),
    language: str = Form("Turkish"),
    difficulty: str = Form("medium"),
    db: Session = Depends(get_db)
):
    cv_text = await extract_text_from_cv(cv_file)

    result = generate_personalized_interview(
        cv_text=cv_text,
        job_text=job_text,
        language=language,
        difficulty=difficulty
    )

    history = ApplicationHistory(
        request_type="personalized_interview",
        cv_filename=cv_file.filename,
        job_text=job_text,
        result=json.dumps(result, ensure_ascii=False)
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
        "cv_filename": cv_file.filename,
        "language": language,
        "difficulty": difficulty,
        "result": result
    }
