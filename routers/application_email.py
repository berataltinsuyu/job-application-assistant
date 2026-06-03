import json
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from models import ApplicationHistory
from services.file_parser_service import extract_text_from_cv
from services.llm_service import generate_application_email

router = APIRouter(
    prefix="/application-email",
    tags=["Application Email"]
)

@router.post("")
async def get_application_email(
    cv_file: UploadFile = File(...),
    job_text: str = Form(...),
    language: str = Form("Turkish"),
    tone: str = Form("professional"),
    company_name: str | None = Form(None),
    position_title: str | None = Form(None),
    db: Session = Depends(get_db)
):
    cv_text = await extract_text_from_cv(cv_file)

    result = generate_application_email(
        cv_text=cv_text,
        job_text=job_text,
        language=language,
        tone=tone,
        company_name=company_name,
        position_title=position_title
    )

    history = ApplicationHistory(
        request_type="application_email",
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
        "tone": tone,
        "company_name": company_name,
        "position_title": position_title,
        "result": result
    }
