from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory
from services.file_parser_service import extract_text_from_cv
from services.llm_service import generate_cover_letter

router = APIRouter(
    prefix="/cover-letter",
    tags=["Cover Letter"]
)


@router.post("")
async def create_cover_letter(
    cv_file: UploadFile = File(...),
    job_text: str = Form(...),
    tone: str = Form("professional"),
    db: Session = Depends(get_db)
):
    cv_text = await extract_text_from_cv(cv_file)

    result = generate_cover_letter(
        cv_text=cv_text,
        job_text=job_text,
        tone=tone
    )

    history = ApplicationHistory(
        request_type="cover_letter",
        cv_filename=cv_file.filename,
        job_text=job_text,
        result=result
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
        "cv_filename": cv_file.filename,
        "tone": tone,
        "result": result
    }