import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory
from services.ats_cv_export_service import (
    build_plain_text_preview,
    render_ats_cv_to_docx,
    render_ats_cv_to_pdf,
)
from services.ats_cv_postprocessing import align_target_title, ensure_ats_metadata_fields
from services.ats_cv_schema import get_empty_ats_cv_schema, validate_ats_cv_schema
from services.ats_cv_templates import (
    get_ats_cv_template,
    get_ats_cv_templates,
    validate_template_id,
)
from services.file_parser_service import extract_text_from_cv
from services.llm_service import generate_ats_cv_json

router = APIRouter()


@router.get("/templates")
def list_ats_cv_templates():
    return {
        "templates": get_ats_cv_templates()
    }


@router.get("/templates/{template_id}")
def read_ats_cv_template(template_id: str):
    try:
        template = get_ats_cv_template(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "template": template
    }


@router.get("/schema")
def read_ats_cv_schema():
    return {
        "schema": get_empty_ats_cv_schema()
    }


@router.post("/validate-template")
async def validate_ats_cv_template(request: Request):
    template_id = ""
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()
        if isinstance(body, dict):
            template_id = str(body.get("template_id") or "")
    elif (
        "application/x-www-form-urlencoded" in content_type
        or "multipart/form-data" in content_type
    ):
        form = await request.form()
        template_id = str(form.get("template_id") or "")

    template_id = template_id.strip()

    return {
        "template_id": template_id,
        "is_valid": validate_template_id(template_id),
    }


@router.post("/generate")
async def generate_ats_cv(
    cv_file: UploadFile = File(...),
    job_description: str = Form(...),
    template_id: str = Form(...),
    language: str = Form("Turkish"),
    db: Session = Depends(get_db),
):
    template_id = template_id.strip()

    if not validate_template_id(template_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ATS CV template_id: {template_id}"
        )

    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="job_description is required."
        )

    cv_text = await extract_text_from_cv(cv_file)
    template = get_ats_cv_template(template_id)
    ats_cv = generate_ats_cv_json(
        cv_text=cv_text,
        job_description=job_description,
        template=template,
        language=language
    )
    ats_cv = ensure_ats_metadata_fields(ats_cv)
    ats_cv = align_target_title(ats_cv, language)

    is_valid, errors = validate_ats_cv_schema(ats_cv)

    history = ApplicationHistory(
        request_type="ats_cv_builder",
        cv_filename=cv_file.filename,
        job_text=job_description,
        result=json.dumps(
            {
                "template": template,
                "language": language,
                "ats_cv": ats_cv,
                "validation": {
                    "is_valid": is_valid,
                    "errors": errors,
                },
            },
            ensure_ascii=False
        )
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "template": template,
        "language": language,
        "ats_cv": ats_cv,
        "validation": {
            "is_valid": is_valid,
            "errors": errors,
        },
    }


@router.post("/export-docx")
async def export_ats_cv_docx(
    ats_cv_json: str = Form(""),
    template_id: str = Form(""),
    language: str = Form("Turkish"),
):
    ats_cv, template = _parse_export_payload(ats_cv_json, template_id, language)
    docx_bytes = render_ats_cv_to_docx(ats_cv, template, language)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="ats_cv_{template["id"]}.docx"'
        },
    )


@router.post("/export-pdf")
async def export_ats_cv_pdf(
    ats_cv_json: str = Form(""),
    template_id: str = Form(""),
    language: str = Form("Turkish"),
):
    ats_cv, template = _parse_export_payload(ats_cv_json, template_id, language)
    pdf_bytes = render_ats_cv_to_pdf(ats_cv, template, language)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ats_cv_{template["id"]}.pdf"'
        },
    )


@router.post("/export-txt")
async def export_ats_cv_txt(
    ats_cv_json: str = Form(""),
    template_id: str = Form(""),
    language: str = Form("Turkish"),
):
    ats_cv, template = _parse_export_payload(ats_cv_json, template_id, language)
    text = build_plain_text_preview(ats_cv, template, language)

    return Response(
        content=text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="ats_cv_{template["id"]}.txt"'
        },
    )


def _parse_export_payload(ats_cv_json: str, template_id: str, language: str) -> tuple[dict, dict]:
    template_id = (template_id or "").strip()
    if not template_id:
        raise HTTPException(status_code=400, detail="template_id is required.")

    if not ats_cv_json.strip():
        raise HTTPException(status_code=400, detail="ats_cv_json is required.")

    if not validate_template_id(template_id):
        raise HTTPException(status_code=400, detail=f"Invalid ATS CV template_id: {template_id}")

    try:
        parsed_json = json.loads(ats_cv_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="ats_cv_json must be valid JSON.") from exc

    if not isinstance(parsed_json, dict):
        raise HTTPException(status_code=400, detail="ats_cv_json must be a JSON object.")

    ats_cv = parsed_json.get("ats_cv") if isinstance(parsed_json.get("ats_cv"), dict) else parsed_json
    ats_cv = ensure_ats_metadata_fields(ats_cv)
    ats_cv = align_target_title(ats_cv, language)

    is_valid, errors = validate_ats_cv_schema(ats_cv)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "ats_cv_json does not match the required ATS CV schema.",
                "errors": errors,
            },
        )

    template = get_ats_cv_template(template_id)
    return ats_cv, template
