import json
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from models import ApplicationHistory
from services.file_parser_service import extract_text_from_cv
from services.llm_service import rewrite_cv_section

router = APIRouter(
    prefix="/rewrite-cv-section",
    tags=["CV Rewrite"]
)

@router.post("")
async def rewrite_section(
    cv_file: UploadFile = File(...),
    job_text: str = Form(...),
    section_type: str = Form("summary"),
    language: str = Form("Turkish"),
    tone: str = Form("professional"),
    db: Session = Depends(get_db)
):
    cv_text = await extract_text_from_cv(cv_file)

    result = rewrite_cv_section(
        cv_text=cv_text,
        job_text=job_text,
        section_type=section_type,
        language=language,
        tone=tone
    )

    history = ApplicationHistory(
        request_type="cv_rewrite",
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
        "section_type": section_type,
        "tone": tone,
        "result": result
    }
