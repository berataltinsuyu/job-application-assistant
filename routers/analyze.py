import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory
from services.file_parser_service import extract_text_from_cv
from services.llm_service import analyze_cv_for_job

router = APIRouter(
    prefix="/analyze",
    tags=["Analyze"]
)


@router.post("")
async def analyze_application(
    cv_file: UploadFile = File(...),
    job_text: str = Form(...),
    language: str = Form("Turkish"),
    db: Session = Depends(get_db)
):
    cv_text = await extract_text_from_cv(cv_file)

    result = analyze_cv_for_job(
        cv_text=cv_text,
        job_text=job_text,
        language=language
    )

    history = ApplicationHistory(
        request_type="analyze",
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
        "cv_text_length": len(cv_text),
        "job_text_length": len(job_text),
        "language": language,
        "result": result
    }
