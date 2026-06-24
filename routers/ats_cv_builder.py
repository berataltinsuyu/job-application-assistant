import json
import re
import traceback
import uuid
from datetime import datetime
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory
from services.ats_cv_export_service import (
    build_plain_text_preview,
    render_ats_cv_to_docx,
    render_ats_cv_to_pdf,
)
from services.ats_cv_postprocessing import (
    align_target_title,
    ensure_ats_metadata_fields,
    ensure_ats_score_explanation,
    extract_contact_fields_from_text,
    restore_contact_fields_from_source,
    restore_preserved_entity_fields_from_source,
)
from services.ats_cv_relevance import rank_ats_cv_for_job
from services.ats_cv_schema import get_empty_ats_cv_schema, validate_ats_cv_schema
from services.ats_cv_templates import (
    get_ats_cv_template,
    get_ats_cv_templates,
    validate_template_id,
)
from services.cv_quality_service import analyze_cv_output_quality, validate_cv_structure
from services.file_parser_service import extract_text_from_cv
from services.llm_service import GEMINI_MODEL, generate_ats_cv_json

router = APIRouter()

LOCKED_CONTACT_FIELDS = {
    "locked_full_name": "full_name",
    "locked_email": "email",
    "locked_phone": "phone",
    "locked_location": "location",
    "locked_linkedin": "linkedin",
    "locked_github": "github",
    "locked_portfolio": "portfolio",
}


def _generate_request_id() -> str:
    return uuid.uuid4().hex[:8]


def _log_generate_checkpoint(request_id: str, checkpoint: str, **metadata) -> None:
    safe_metadata = " ".join(f"{key}={value}" for key, value in metadata.items())
    suffix = f" {safe_metadata}" if safe_metadata else ""
    print(f"[ats-cv/generate:{request_id}] {checkpoint}{suffix}", flush=True)


def _log_generate_exception(request_id: str) -> None:
    print(f"[ats-cv/generate:{request_id}] exception traceback follows", flush=True)
    print(traceback.format_exc(), flush=True)


def _provided_locked_fields(locked_values: dict) -> list[str]:
    return [
        LOCKED_CONTACT_FIELDS[key]
        for key, value in locked_values.items()
        if key in LOCKED_CONTACT_FIELDS and _locked_text(value)
    ]


def _locked_proper_noun_counts(locked_nouns: dict) -> dict:
    return {
        str(key): len(value)
        for key, value in locked_nouns.items()
        if isinstance(value, list)
    }


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
    locked_full_name: str = Form(""),
    locked_email: str = Form(""),
    locked_phone: str = Form(""),
    locked_location: str = Form(""),
    locked_linkedin: str = Form(""),
    locked_github: str = Form(""),
    locked_portfolio: str = Form(""),
    locked_proper_nouns_json: str = Form(""),
    adaptation_level: str = Form("balanced"),
    db: Session = Depends(get_db),
):
    request_id = _generate_request_id()
    _log_generate_checkpoint(request_id, "received request", template_id=template_id, language=language)

    try:
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

        locked_contact_values = {
            "locked_full_name": locked_full_name,
            "locked_email": locked_email,
            "locked_phone": locked_phone,
            "locked_location": locked_location,
            "locked_linkedin": locked_linkedin,
            "locked_github": locked_github,
            "locked_portfolio": locked_portfolio,
        }
        _log_generate_checkpoint(
            request_id,
            "locked contact parsed",
            provided_fields=_provided_locked_fields(locked_contact_values),
        )

        locked_proper_nouns = _parse_locked_proper_nouns(locked_proper_nouns_json)
        _log_generate_checkpoint(
            request_id,
            "locked proper nouns parsed",
            proper_noun_counts=_locked_proper_noun_counts(locked_proper_nouns),
        )

        cv_text = await extract_text_from_cv(cv_file)
        _log_generate_checkpoint(request_id, "cv text extracted", cv_text_chars=len(cv_text))

        source_contact = extract_contact_fields_from_text(cv_text)
        template = get_ats_cv_template(template_id)
        _log_generate_checkpoint(request_id, "template loaded", resolved_template_id=template.get("id"))

        _log_generate_checkpoint(request_id, "before Gemini call", model=GEMINI_MODEL)
        ats_cv = generate_ats_cv_json(
            cv_text=cv_text,
            job_description=job_description,
            template=template,
            language=language,
            adaptation_level=adaptation_level,
        )
        _log_generate_checkpoint(
            request_id,
            "after Gemini call",
            top_level_keys=sorted(ats_cv.keys()) if isinstance(ats_cv, dict) else type(ats_cv).__name__,
        )

        ats_cv = ensure_ats_metadata_fields(ats_cv)
        ats_cv = align_target_title(ats_cv, language)
        ats_cv = ensure_ats_score_explanation(ats_cv, language)
        ats_cv = restore_contact_fields_from_source(ats_cv, source_contact)
        ats_cv = restore_preserved_entity_fields_from_source(ats_cv, cv_text)
        ats_cv = _apply_locked_contact_fields(ats_cv, locked_contact_values)
        ats_cv = _restore_locked_proper_nouns(ats_cv, locked_proper_nouns)
        ats_cv = rank_ats_cv_for_job(ats_cv, job_description)
        ats_cv = _apply_locked_contact_fields(ats_cv, locked_contact_values)
        ats_cv = _restore_locked_proper_nouns(ats_cv, locked_proper_nouns)
        _log_generate_checkpoint(request_id, "after postprocessing")

        _log_generate_checkpoint(request_id, "before validation")
        is_valid, errors = validate_ats_cv_schema(ats_cv)
        text_preview = build_plain_text_preview(
            ats_cv=ats_cv,
            template=template,
            language=language,
            one_page=False,
            enabled_sections=None,
            export_style="standard",
        )
        structure_report = validate_cv_structure(ats_cv)
        quality_report = analyze_cv_output_quality(
            cv_text=text_preview,
            structured_cv=ats_cv,
            one_page_requested=False,
        )

        _log_generate_checkpoint(request_id, "before history save", validation_ok=is_valid)
        history = ApplicationHistory(
            request_type="ats_cv_builder",
            cv_filename=cv_file.filename,
            job_text=job_description,
            result=json.dumps(
                {
                    "template": template,
                    "language": language,
                    "adaptation_level": _normalize_adaptation_level(adaptation_level),
                    "ats_cv": ats_cv,
                    "validation": {
                        "is_valid": is_valid,
                        "errors": errors,
                    },
                    "quality_report": quality_report,
                    "structure_report": structure_report,
                },
                ensure_ascii=False
            )
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        _log_generate_checkpoint(request_id, "before response")
        return {
            "template": template,
            "language": language,
            "adaptation_level": _normalize_adaptation_level(adaptation_level),
            "ats_cv": ats_cv,
            "validation": {
                "is_valid": is_valid,
                "errors": errors,
            },
            "quality_report": quality_report,
            "structure_report": structure_report,
        }
    except HTTPException as exc:
        _log_generate_exception(request_id)
        if exc.status_code >= 500:
            raise HTTPException(
                status_code=exc.status_code,
                detail="ATS CV generation failed. Check backend logs for the exact failing line."
            ) from exc
        raise
    except Exception as exc:
        _log_generate_exception(request_id)
        raise HTTPException(
            status_code=500,
            detail="ATS CV generation failed. Check backend logs for the exact failing line."
        ) from exc


@router.post("/export-docx")
async def export_ats_cv_docx(
    ats_cv_json: str = Form(""),
    template_id: str = Form(""),
    language: str = Form("Turkish"),
    one_page: str = Form("false"),
    enabled_sections: str = Form(""),
    export_style: str = Form("standard"),
):
    ats_cv, template, parsed_one_page, parsed_sections, parsed_export_style = _parse_export_payload(
        ats_cv_json, template_id, language, one_page, enabled_sections, export_style
    )
    docx_bytes = render_ats_cv_to_docx(
        ats_cv, template, language, parsed_one_page, parsed_sections, parsed_export_style
    )

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{_cv_export_filename("ats_cv", template["id"], "docx")}"'
        },
    )


@router.post("/export-pdf")
async def export_ats_cv_pdf(
    ats_cv_json: str = Form(""),
    template_id: str = Form(""),
    language: str = Form("Turkish"),
    one_page: str = Form("false"),
    enabled_sections: str = Form(""),
    export_style: str = Form("standard"),
):
    ats_cv, template, parsed_one_page, parsed_sections, parsed_export_style = _parse_export_payload(
        ats_cv_json, template_id, language, one_page, enabled_sections, export_style
    )
    pdf_bytes = render_ats_cv_to_pdf(
        ats_cv, template, language, parsed_one_page, parsed_sections, parsed_export_style
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{_cv_export_filename("ats_cv", template["id"], "pdf")}"'
        },
    )


@router.post("/export-txt")
async def export_ats_cv_txt(
    ats_cv_json: str = Form(""),
    template_id: str = Form(""),
    language: str = Form("Turkish"),
    one_page: str = Form("false"),
    enabled_sections: str = Form(""),
    export_style: str = Form("standard"),
):
    ats_cv, template, parsed_one_page, parsed_sections, parsed_export_style = _parse_export_payload(
        ats_cv_json, template_id, language, one_page, enabled_sections, export_style
    )
    text = build_plain_text_preview(ats_cv, template, language, parsed_one_page, parsed_sections, parsed_export_style)

    return Response(
        content=text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{_cv_export_filename("ats_cv", template["id"], "txt")}"'
        },
    )


def _parse_export_payload(
    ats_cv_json: str,
    template_id: str,
    language: str,
    one_page: str,
    enabled_sections: str,
    export_style: str,
) -> tuple[dict, dict, bool, set[str], str]:
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
    ats_cv = ensure_ats_score_explanation(ats_cv, language)

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
    parsed_one_page = _parse_bool(one_page)
    parsed_sections = _parse_enabled_sections(enabled_sections)
    parsed_export_style = _parse_export_style(export_style, parsed_one_page)

    return ats_cv, template, parsed_one_page, parsed_sections, parsed_export_style


def _parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off", ""}:
        return False
    raise HTTPException(status_code=400, detail="one_page must be true or false.")


def _parse_export_style(value: str, one_page: bool) -> str:
    normalized = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in {"", "standard", "normal"}:
        return "balanced_one_page" if one_page else "standard"
    if normalized in {"balanced", "one_page", "balanced_one_page"}:
        return "balanced_one_page"
    if normalized == "compact":
        return "compact"
    raise HTTPException(status_code=400, detail="export_style must be standard, compact, or balanced_one_page.")


def _normalize_adaptation_level(value: str) -> str:
    normalized = str(value or "balanced").strip().lower()
    if normalized in {"conservative", "balanced", "strong"}:
        return normalized
    return "balanced"


def _cv_export_filename(asset_type: str, template_id: str, extension: str) -> str:
    safe_asset_type = re.sub(r"[^a-z0-9_]+", "_", str(asset_type or "ats_cv").lower()).strip("_")
    safe_template_id = re.sub(r"[^a-z0-9_]+", "_", str(template_id or "classic_ats").lower()).strip("_")
    safe_extension = re.sub(r"[^a-z0-9]+", "", str(extension or "pdf").lower()) or "pdf"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{safe_asset_type}_{safe_template_id}_{timestamp}.{safe_extension}"


def _parse_enabled_sections(value: str) -> set[str]:
    default_sections = {
        "contact",
        "summary",
        "skills",
        "experience",
        "projects",
        "education",
        "certifications",
        "languages",
    }

    if not value.strip():
        return default_sections

    try:
        parsed_value = json.loads(value)
        if not isinstance(parsed_value, list):
            raise ValueError
        sections = {str(section).strip() for section in parsed_value if str(section).strip()}
    except json.JSONDecodeError as exc:
        if value.strip().startswith(("[", "{")):
            raise HTTPException(
                status_code=400,
                detail="enabled_sections must be valid JSON list or comma-separated string."
            ) from exc
        sections = {section.strip() for section in value.split(",") if section.strip()}
    except ValueError:
        if value.strip().startswith(("[", "{")):
            raise HTTPException(
                status_code=400,
                detail="enabled_sections JSON value must be a list."
            )
        sections = {section.strip() for section in value.split(",") if section.strip()}

    valid_sections = default_sections
    invalid_sections = sorted(sections - valid_sections)
    if invalid_sections:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid enabled_sections value(s): {', '.join(invalid_sections)}"
        )
    if not sections:
        raise HTTPException(status_code=400, detail="enabled_sections cannot be empty.")

    return sections


def _apply_locked_contact_fields(ats_cv: dict, locked_values: dict) -> dict:
    if not isinstance(ats_cv, dict):
        return ats_cv

    contact = ats_cv.setdefault("contact", {})
    if not isinstance(contact, dict):
        contact = {}
        ats_cv["contact"] = contact

    for form_field, contact_field in LOCKED_CONTACT_FIELDS.items():
        locked_value = _locked_text(locked_values.get(form_field))
        if locked_value:
            contact[contact_field] = locked_value

    return ats_cv


def _restore_locked_proper_nouns(ats_cv: dict, locked_nouns: dict) -> dict:
    if not isinstance(ats_cv, dict) or not locked_nouns:
        return ats_cv

    _restore_locked_record_field(ats_cv.get("education"), "school", locked_nouns.get("schools", []))
    _restore_locked_record_field(ats_cv.get("experience"), "company", locked_nouns.get("companies", []))
    _restore_locked_record_field(ats_cv.get("projects"), "name", locked_nouns.get("projects", []))
    _restore_locked_record_field(ats_cv.get("certifications"), "name", locked_nouns.get("certifications", []))
    issuer_values = (
        locked_nouns.get("issuers", [])
        + locked_nouns.get("certification_issuers", [])
        + locked_nouns.get("companies", [])
    )
    _restore_locked_record_field(ats_cv.get("certifications"), "issuer", issuer_values)

    return ats_cv


def _restore_locked_record_field(records, field: str, locked_values: list[str]) -> None:
    locked_values = [_locked_text(value) for value in locked_values if _locked_text(value)]
    if not isinstance(records, list) or not locked_values:
        return

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        current_value = _locked_text(record.get(field))
        locked_match = _best_locked_proper_noun_match(current_value, locked_values)
        if locked_match:
            record[field] = locked_match
        elif not current_value and index < len(locked_values):
            record[field] = locked_values[index]


def _best_locked_proper_noun_match(current_value: str, locked_values: list[str]) -> str:
    if not current_value:
        return locked_values[0] if len(locked_values) == 1 else ""

    current_key = _proper_noun_match_key(current_value)
    if not current_key:
        return ""

    best_value = ""
    best_score = 0.0
    for locked_value in locked_values:
        locked_key = _proper_noun_match_key(locked_value)
        if not locked_key:
            continue
        if current_key == locked_key:
            return locked_value
        if len(current_key) >= 4 and (current_key in locked_key or locked_key in current_key):
            return locked_value
        score = SequenceMatcher(None, current_key, locked_key).ratio()
        if score > best_score:
            best_value = locked_value
            best_score = score

    return best_value if best_score >= 0.74 else ""


def _parse_locked_proper_nouns(raw_value: str) -> dict:
    if not _locked_text(raw_value):
        return {}

    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="locked_proper_nouns_json must be valid JSON.") from exc

    if not isinstance(parsed_value, dict):
        raise HTTPException(status_code=400, detail="locked_proper_nouns_json must be a JSON object.")

    locked_nouns = {}
    for key, value in parsed_value.items():
        if isinstance(value, list):
            locked_nouns[str(key)] = [_locked_text(item) for item in value if _locked_text(item)]
    return locked_nouns


def _proper_noun_match_key(value: str) -> str:
    text = _locked_text(value).casefold()
    translation_table = str.maketrans({
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "Ş": "s",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    })
    return re.sub(r"[^a-z0-9]+", "", text.translate(translation_table))


def _locked_text(value) -> str:
    return str(value or "").strip()
