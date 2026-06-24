import json
import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from models import MonitoredJob, JobIntelligenceReport, JobApplicationPipeline, JobApplicationAsset
from services.file_parser_service import extract_text_from_cv
from services.llm_service import generate_ats_cv_json, generate_cover_letter, generate_application_email
from services.ats_cv_templates import get_ats_cv_template
from services.ats_cv_postprocessing import (
    ensure_ats_metadata_fields,
    align_target_title,
    ensure_ats_score_explanation,
    extract_contact_fields_from_text,
    extract_contact_fields_from_cv_text,
    extract_proper_nouns_from_cv_text,
    restore_contact_fields_from_source,
    restore_preserved_entity_fields_from_source,
    unspace_cv_text,
    _clean_character_spacing,
    clean_structured_cv_before_export,
)
from services.ats_cv_relevance import rank_ats_cv_for_job
from services.ats_cv_export_service import (
    build_plain_text_preview,
    render_ats_cv_to_pdf,
    render_ats_cv_to_docx,
)
from services.cv_quality_service import analyze_cv_output_quality, validate_cv_structure


from difflib import SequenceMatcher
import re

LOCKED_CONTACT_FIELDS = {
    "locked_full_name": "full_name",
    "locked_email": "email",
    "locked_phone": "phone",
    "locked_location": "location",
    "locked_linkedin": "linkedin",
    "locked_github": "github",
    "locked_portfolio": "portfolio",
}

def _locked_text(value) -> str:
    return str(value or "").strip()

def _apply_locked_contact_fields(ats_cv: dict, locked_values: dict) -> dict:
    if not isinstance(ats_cv, dict):
        return ats_cv

    contact = ats_cv.setdefault("contact", {})
    if not isinstance(contact, dict):
        contact = {}
        ats_cv["contact"] = contact

    for form_field, contact_field in LOCKED_CONTACT_FIELDS.items():
        val = locked_values.get(form_field, "")
        clean_val = _clean_character_spacing(val)
        if clean_val:
            contact[contact_field] = clean_val
        else:
            if contact_field != "full_name" and contact_field in contact:
                contact[contact_field] = ""

    if "full_name" in contact:
        contact["full_name"] = _clean_character_spacing(contact["full_name"])

    return ats_cv

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


ASSETS_DIR = "generated_assets"


def serialize_asset(asset: JobApplicationAsset) -> dict:
    try:
        struct_json = json.loads(asset.structured_json) if asset.structured_json else None
    except Exception:
        struct_json = None

    return {
        "id": asset.id,
        "job_id": asset.job_id,
        "asset_type": asset.asset_type,
        "title": asset.title,
        "content_text": asset.content_text,
        "structured_json": struct_json,
        "file_path": asset.file_path,
        "export_format": asset.export_format,
        "template_id": asset.template_id,
        "language": asset.language,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
    }


def serialize_job(job: MonitoredJob) -> dict:
    return {
        "id": job.id,
        "alert_profile_id": job.alert_profile_id,
        "run_id": job.run_id,
        "source": job.source,
        "source_job_id": job.source_job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "work_model": job.work_model,
        "seniority": job.seniority,
        "job_type": job.job_type,
        "description": job.description,
        "url": job.url,
        "posted_at": job.posted_at,
        "match_score": job.match_score,
        "status": job.status,
    }


def _sync_pipeline_status(db: Session, job_id: int):
    assets = db.query(JobApplicationAsset).filter(JobApplicationAsset.job_id == job_id).all()
    asset_types = {a.asset_type for a in assets}

    pipeline = db.query(JobApplicationPipeline).filter(JobApplicationPipeline.job_id == job_id).first()
    if not pipeline:
        pipeline = JobApplicationPipeline(job_id=job_id)
        db.add(pipeline)

    if "tailored_cv" in asset_types and ("cover_letter" in asset_types or "application_email" in asset_types):
        pipeline.application_materials_status = "ready"
    elif "tailored_cv" in asset_types:
        pipeline.application_materials_status = "cover_letter_needed"
    elif "cover_letter" in asset_types or "application_email" in asset_types:
        pipeline.application_materials_status = "cv_needed"
    
    db.commit()
    db.refresh(pipeline)


def _get_job_description_with_intelligence(db: Session, job: MonitoredJob) -> str:
    job_description = job.description or ""
    intelligence = db.query(JobIntelligenceReport).filter(JobIntelligenceReport.job_id == job.id).first()
    
    if intelligence:
        try:
            intel_data = json.loads(intelligence.report_json) if isinstance(intelligence.report_json, str) else intelligence.report_json
        except Exception:
            intel_data = {}

        risk_notes = intel_data.get("risk_notes", [])
        requirements = intel_data.get("required_qualifications", [])

        intel_context = (
            f"\nDetected Job Family: {intelligence.job_family}\n"
            f"Seniority Assessment: {intelligence.seniority_assessment}\n"
        )
        if risk_notes:
            intel_context += f"Risk Notes (Do not invent experience or make false claims relating to these risk notes): {', '.join(risk_notes)}\n"
        if requirements:
            intel_context += f"Required Qualifications: {', '.join(requirements)}\n"

        job_description += f"\n\nAdditional Job Detail Intelligence Context:\n{intel_context}"
    
    return job_description


async def generate_job_tailored_cv(
    db: Session,
    job_id: int,
    cv_file: UploadFile,
    template_id: str,
    language: str,
    output_format: str,
    one_page: bool,
    enabled_sections: list[str] | None,
    adaptation_level: str = "balanced",
    docx_render_mode: str = "programmatic",
    docx_template_id: str = "",
) -> dict:
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv_text = await extract_text_from_cv(cv_file)
    cv_text = unspace_cv_text(cv_text)
    job_description = _get_job_description_with_intelligence(db, job)

    try:
        template = get_ats_cv_template(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    source_contact = extract_contact_fields_from_cv_text(cv_text)
    locked_nouns = extract_proper_nouns_from_cv_text(cv_text)

    locked_contact_values = {
        "locked_full_name": source_contact.get("full_name", ""),
        "locked_email": source_contact.get("email", ""),
        "locked_phone": source_contact.get("phone", ""),
        "locked_location": source_contact.get("location", ""),
        "locked_linkedin": source_contact.get("linkedin", ""),
        "locked_github": source_contact.get("github", ""),
        "locked_portfolio": source_contact.get("portfolio", "")
    }

    ats_cv = generate_ats_cv_json(
        cv_text=cv_text,
        job_description=job_description,
        template=template,
        language=language,
        adaptation_level=adaptation_level,
    )
    ats_cv = ensure_ats_metadata_fields(ats_cv)
    ats_cv = align_target_title(ats_cv, language)
    ats_cv = ensure_ats_score_explanation(ats_cv, language)
    ats_cv = restore_contact_fields_from_source(ats_cv, source_contact)
    ats_cv = restore_preserved_entity_fields_from_source(ats_cv, cv_text)
    ats_cv = _apply_locked_contact_fields(ats_cv, locked_contact_values)
    ats_cv = _restore_locked_proper_nouns(ats_cv, locked_nouns)

    ats_cv = rank_ats_cv_for_job(ats_cv, job.description or "")

    ats_cv = clean_structured_cv_before_export(ats_cv)

    ats_cv = _apply_locked_contact_fields(ats_cv, locked_contact_values)
    ats_cv = _restore_locked_proper_nouns(ats_cv, locked_nouns)

    # Reapply overrides again just before final export rendering
    ats_cv = _apply_locked_contact_fields(ats_cv, locked_contact_values)
    ats_cv = _restore_locked_proper_nouns(ats_cv, locked_nouns)

    sections_set = set(enabled_sections) if enabled_sections else None
    text_preview = build_plain_text_preview(
        ats_cv=ats_cv,
        template=template,
        language=language,
        one_page=one_page,
        enabled_sections=sections_set,
        export_style="standard"
    )
    structure_report = validate_cv_structure(ats_cv)
    quality_report = analyze_cv_output_quality(
        cv_text=text_preview,
        structured_cv=ats_cv,
        one_page_requested=one_page,
    )
    structured_payload = dict(ats_cv)
    structured_payload.update({
        "quality_report": quality_report,
        "structure_report": structure_report,
        "adaptation_level": _normalize_adaptation_level(adaptation_level),
    })

    if docx_render_mode == "template":
        structured_payload["docx_render_mode"] = "template"
        structured_payload["docx_template_id"] = docx_template_id
    else:
        structured_payload["docx_render_mode"] = "programmatic"

    fmt = output_format.lower()
    if fmt == "pdf":
        file_bytes = render_ats_cv_to_pdf(
            ats_cv=ats_cv,
            template=template,
            language=language,
            one_page=one_page,
            enabled_sections=sections_set,
            export_style="standard"
        )
    elif fmt == "docx":
        if docx_render_mode == "template":
            from services.docx_template_service import render_cv_with_docx_template
            import uuid
            temp_path = f"scratch/temp_tailored_{uuid.uuid4().hex}.docx"
            try:
                render_res = render_cv_with_docx_template(
                    structured_cv=ats_cv,
                    template_id=docx_template_id,
                    output_path=temp_path,
                    metadata={"docx_render_mode": "template", "docx_template_id": docx_template_id}
                )
                if render_res.get("success"):
                    with open(temp_path, "rb") as f:
                        file_bytes = f.read()
                else:
                    warnings_str = ", ".join(render_res.get("warnings", []))
                    err_detail = warnings_str or render_res.get("message") or "Unknown template rendering error"
                    raise HTTPException(
                        status_code=400,
                        detail=f"Template rendering failed: {err_detail}. Please use Programmatic DOCX fallback."
                    )
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Template rendering failed. Please use Programmatic DOCX fallback."
                )
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        else:
            file_bytes = render_ats_cv_to_docx(
                ats_cv=ats_cv,
                template=template,
                language=language,
                one_page=one_page,
                enabled_sections=sections_set,
                export_style="standard"
            )
    elif fmt == "txt":
        file_bytes = text_preview.encode("utf-8")
    elif fmt == "json":
        file_bytes = json.dumps(ats_cv, ensure_ascii=False, indent=2).encode("utf-8")
    else:
        file_bytes = render_ats_cv_to_pdf(
            ats_cv=ats_cv,
            template=template,
            language=language,
            one_page=one_page,
            enabled_sections=sections_set,
            export_style="standard"
        )
        fmt = "pdf"

    resolved_template_id = docx_template_id if (fmt == "docx" and docx_render_mode == "template") else template_id
    os.makedirs(ASSETS_DIR, exist_ok=True)
    filename = _cv_asset_filename("tailored_cv", resolved_template_id, fmt)
    file_path = os.path.join(ASSETS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    asset = JobApplicationAsset(
        job_id=job_id,
        asset_type="tailored_cv",
        title=f"Tailored CV - {resolved_template_id} ({language})",
        content_text=text_preview,
        structured_json=json.dumps(structured_payload, ensure_ascii=False),
        file_path=file_path,
        export_format=fmt,
        template_id=template_id,
        language=language
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    _sync_pipeline_status(db, job_id)

    return {
        "job": serialize_job(job),
        "asset": serialize_asset(asset),
        "download_url_or_path": f"/job-monitoring/assets/{asset.id}/download"
    }


def _normalize_adaptation_level(value: str) -> str:
    normalized = str(value or "balanced").strip().lower()
    if normalized in {"conservative", "balanced", "strong"}:
        return normalized
    return "balanced"


def _cv_asset_filename(asset_type: str, template_id: str, extension: str) -> str:
    safe_asset_type = re.sub(r"[^a-z0-9_]+", "_", str(asset_type or "tailored_cv").lower()).strip("_")
    safe_template_id = re.sub(r"[^a-z0-9_]+", "_", str(template_id or "classic_ats").lower()).strip("_")
    safe_extension = re.sub(r"[^a-z0-9]+", "", str(extension or "pdf").lower()) or "pdf"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{safe_asset_type}_{safe_template_id}_{timestamp}.{safe_extension}"


async def generate_job_cover_letter(
    db: Session,
    job_id: int,
    cv_file: UploadFile,
    language: str,
    tone: str | None
) -> dict:
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv_text = await extract_text_from_cv(cv_file)
    job_description = _get_job_description_with_intelligence(db, job)

    content = generate_cover_letter(
        cv_text=cv_text,
        job_text=job_description,
        tone=tone or "professional",
        language=language
    )

    os.makedirs(ASSETS_DIR, exist_ok=True)
    filename = f"cover_{job_id}_{uuid.uuid4().hex[:8]}.txt"
    file_path = os.path.join(ASSETS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(content.encode("utf-8"))

    asset = JobApplicationAsset(
        job_id=job_id,
        asset_type="cover_letter",
        title=f"Cover Letter - {tone or 'professional'} ({language})",
        content_text=content,
        structured_json=None,
        file_path=file_path,
        export_format="txt",
        template_id=None,
        language=language
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    _sync_pipeline_status(db, job_id)

    return {
        "job": serialize_job(job),
        "asset": serialize_asset(asset),
        "download_url_or_path": f"/job-monitoring/assets/{asset.id}/download"
    }


async def generate_job_application_email(
    db: Session,
    job_id: int,
    cv_file: UploadFile,
    language: str,
    tone: str | None
) -> dict:
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv_text = await extract_text_from_cv(cv_file)
    job_description = _get_job_description_with_intelligence(db, job)

    result = generate_application_email(
        cv_text=cv_text,
        job_text=job_description,
        language=language,
        tone=tone or "professional",
        company_name=job.company,
        position_title=job.title
    )

    content_text = (
        f"Subject: {result.get('subject')}\n\n"
        f"Email Body:\n{result.get('email_body')}\n\n"
        f"Short LinkedIn Message:\n{result.get('short_linkedin_message')}\n\n"
        f"Follow-up Message:\n{result.get('follow_up_message')}"
    )

    os.makedirs(ASSETS_DIR, exist_ok=True)
    filename = f"email_{job_id}_{uuid.uuid4().hex[:8]}.json"
    file_path = os.path.join(ASSETS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))

    asset = JobApplicationAsset(
        job_id=job_id,
        asset_type="application_email",
        title=f"Application Email - {tone or 'professional'} ({language})",
        content_text=content_text,
        structured_json=json.dumps(result, ensure_ascii=False),
        file_path=file_path,
        export_format="json",
        template_id=None,
        language=language
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    _sync_pipeline_status(db, job_id)

    return {
        "job": serialize_job(job),
        "asset": serialize_asset(asset),
        "download_url_or_path": f"/job-monitoring/assets/{asset.id}/download"
    }


def list_job_assets(db: Session, job_id: int) -> list[dict]:
    assets = db.query(JobApplicationAsset).filter(JobApplicationAsset.job_id == job_id).all()
    return [serialize_asset(a) for a in assets]


def get_job_asset(db: Session, asset_id: int) -> dict:
    asset = db.query(JobApplicationAsset).filter(JobApplicationAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return serialize_asset(asset)
