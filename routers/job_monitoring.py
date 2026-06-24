from typing import Any
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from services import job_monitoring_service, job_application_pipeline_service, job_application_asset_service
from services.job_sources import (
    get_available_sources,
    get_source_setting,
    update_source_setting,
    validate_source_can_run,
)



router = APIRouter(
    prefix="/job-monitoring",
    tags=["Job Monitoring"]
)


class AlertProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    keywords: list[str] = Field(default_factory=list)
    location: str = ""
    seniority: str = ""
    job_type: str = ""
    work_model: str = ""
    sources: list[str] = Field(default_factory=lambda: ["manual_mock"])
    excluded_keywords: list[str] = Field(default_factory=list)
    min_match_score: int = Field(default=40, ge=0, le=100)
    is_active: bool = True


class AlertProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    keywords: list[str] | None = None
    location: str | None = None
    seniority: str | None = None
    job_type: str | None = None
    work_model: str | None = None
    sources: list[str] | None = None
    excluded_keywords: list[str] | None = None
    min_match_score: int | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class JobStatusUpdate(BaseModel):
    status: str


class SourceSettingUpdate(BaseModel):
    enabled: bool | None = None
    cooldown_minutes: int | None = Field(default=None, ge=0)
    config_json: dict[str, Any] | None = None


class ManualJobCreate(BaseModel):
    alert_profile_id: int | None = None
    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    location: str = ""
    work_model: str = ""
    seniority: str = ""
    job_type: str = ""
    description: str = Field(..., min_length=1)
    url: str = ""
    source: str = "manual_import"
    posted_at: str = ""


class JobRescoreRequest(BaseModel):
    alert_profile_id: int


@router.get("/alerts")
def list_alerts(
    include_inactive: bool = Query(True),
    db: Session = Depends(get_db),
):
    return job_monitoring_service.list_alert_profiles(db, include_inactive=include_inactive)


@router.post("/alerts")
def create_alert(payload: AlertProfileCreate, db: Session = Depends(get_db)):
    try:
        return job_monitoring_service.create_alert_profile(db, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = job_monitoring_service.get_alert_profile(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert profile not found.")
    return alert


@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: int, payload: AlertProfileUpdate, db: Session = Depends(get_db)):
    try:
        update_data: dict[str, Any] = payload.model_dump(exclude_unset=True)
        alert = job_monitoring_service.update_alert_profile(db, alert_id, update_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not alert:
        raise HTTPException(status_code=404, detail="Alert profile not found.")
    return alert


@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = job_monitoring_service.deactivate_alert_profile(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert profile not found.")
    return {"message": "Alert profile deactivated.", "alert": alert}


@router.post("/alerts/{alert_id}/run")
def run_alert(alert_id: int, db: Session = Depends(get_db)):
    try:
        return job_monitoring_service.run_alert_profile(db, alert_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Job monitoring run failed.") from exc


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    try:
        return {"sources": get_available_sources(db)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to list source settings.") from exc


@router.get("/sources/{source_name}")
def get_source(source_name: str, db: Session = Depends(get_db)):
    source = get_source_setting(db, source_name)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    return {"source": source}


@router.patch("/sources/{source_name}")
def patch_source(source_name: str, payload: SourceSettingUpdate, db: Session = Depends(get_db)):
    try:
        update_data = payload.model_dump(exclude_unset=True)
        source = update_source_setting(source_name, update_data, db)
        return {"source": source}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to update source setting.") from exc


@router.post("/sources/{source_name}/test")
def test_source(source_name: str, db: Session = Depends(get_db)):
    source = get_source_setting(db, source_name)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    can_run = validate_source_can_run(source_name, db)
    if source_name == "manual_mock" and can_run:
        return {"source_name": source_name, "success": True, "message": "manual_mock is available and runnable."}
    if source_name == "manual_import":
        return {"source_name": source_name, "success": False, "message": "manual_import is a manual-only source and cannot be run."}
    return {
        "source_name": source_name,
        "success": False,
        "message": source.get("message") or "Source is not runnable in Phase 3A.",
    }


@router.get("/jobs")
def list_jobs(
    alert_profile_id: int | None = Query(None),
    status: str | None = Query(None),
    source: str | None = Query(None),
    min_match_score: int | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    try:
        return job_monitoring_service.list_monitored_jobs(
            db,
            alert_profile_id=alert_profile_id,
            status=status,
            source=source,
            min_match_score=min_match_score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/jobs/manual")
def create_manual_job(payload: ManualJobCreate, db: Session = Depends(get_db)):
    try:
        return job_monitoring_service.create_manual_job(db, payload.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Manual job import failed.") from exc


@router.post("/jobs/{job_id}/rescore")
def rescore_job(job_id: int, payload: JobRescoreRequest, db: Session = Depends(get_db)):
    try:
        job = job_monitoring_service.rescore_job(db, job_id, payload.alert_profile_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Job rescore failed.") from exc
    if not job:
        raise HTTPException(status_code=404, detail="Monitored job not found.")
    return job


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = job_monitoring_service.get_monitored_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Monitored job not found.")
    return job


@router.patch("/jobs/{job_id}/status")
def update_job_status(job_id: int, payload: JobStatusUpdate, db: Session = Depends(get_db)):
    try:
        job = job_monitoring_service.update_job_status(db, job_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not job:
        raise HTTPException(status_code=404, detail="Monitored job not found.")
    return job


@router.get("/runs")
def list_runs(
    alert_profile_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return job_monitoring_service.list_search_runs(db, alert_profile_id=alert_profile_id)


class JobAnalyzeRequest(BaseModel):
    alert_profile_id: int | None = None


@router.post("/jobs/{job_id}/analyze")
def analyze_job(job_id: int, payload: JobAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        return job_monitoring_service.analyze_job(db, job_id, payload.alert_profile_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Job intelligence analysis failed.") from exc


@router.get("/jobs/{job_id}/intelligence")
def get_job_intelligence(job_id: int, db: Session = Depends(get_db)):
    try:
        res = job_monitoring_service.get_job_intelligence(db, job_id)
        if res is None:
            raise HTTPException(status_code=404, detail="Intelligence report not found.")
        return res
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to retrieve job intelligence.") from exc


class JobPipelineUpdate(BaseModel):
    application_stage: str | None = None
    application_priority: str | None = None
    application_deadline: str | None = None
    applied_at: str | None = None
    next_action: str | None = None
    next_action_date: str | None = None
    interview_date: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    application_notes: str | None = None
    application_materials_status: str | None = None


@router.get("/jobs/{job_id}/pipeline")
def get_job_pipeline(job_id: int, db: Session = Depends(get_db)):
    try:
        pipeline = job_application_pipeline_service.get_application_pipeline(db, job_id)
        return {"job_id": job_id, "pipeline": pipeline}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to retrieve job application pipeline.") from exc


@router.patch("/jobs/{job_id}/pipeline")
def update_job_pipeline(job_id: int, payload: JobPipelineUpdate, db: Session = Depends(get_db)):
    try:
        update_data = payload.model_dump(exclude_unset=True)
        return job_application_pipeline_service.update_application_pipeline(db, job_id, update_data)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to update job application pipeline.") from exc


@router.get("/pipeline")
def list_pipeline_jobs(
    application_stage: str | None = Query(None),
    application_priority: str | None = Query(None),
    status: str | None = Query(None),
    source: str | None = Query(None),
    min_match_score: int | None = Query(None, ge=0, le=100),
    due_before: str | None = Query(None),
    next_action_before: str | None = Query(None),
    db: Session = Depends(get_db),
):
    try:
        filters = {
            "application_stage": application_stage,
            "application_priority": application_priority,
            "status": status,
            "source": source,
            "min_match_score": min_match_score,
            "due_before": due_before,
            "next_action_before": next_action_before,
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        return job_application_pipeline_service.list_pipeline_jobs(db, filters)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to list pipeline jobs.") from exc


# Phase 2E - Job-to-Application Asset Generator Endpoints

from services.ats_cv_templates import validate_template_id

@router.post("/jobs/{job_id}/assets/tailored-cv")
async def create_job_tailored_cv(
    job_id: int,
    cv_file: UploadFile = File(...),
    template_id: str = Form("classic_ats"),
    language: str = Form("English"),
    output_format: str = Form("pdf"),
    one_page: bool = Form(False),
    enabled_sections: str | None = Form(None),
    adaptation_level: str = Form("balanced"),
    db: Session = Depends(get_db),
):
    if not validate_template_id(template_id):
        raise HTTPException(status_code=400, detail=f"Invalid template_id: {template_id}")

    if not cv_file or not cv_file.filename:
        raise HTTPException(status_code=400, detail="cv_file is required")

    sections_list = None
    if enabled_sections:
        try:
            sections_list = json.loads(enabled_sections)
            if not isinstance(sections_list, list):
                sections_list = [s.strip() for s in enabled_sections.split(",") if s.strip()]
        except Exception:
            sections_list = [s.strip() for s in enabled_sections.split(",") if s.strip()]

    try:
        res = await job_application_asset_service.generate_job_tailored_cv(
            db=db,
            job_id=job_id,
            cv_file=cv_file,
            template_id=template_id,
            language=language,
            output_format=output_format,
            one_page=one_page,
            enabled_sections=sections_list,
            adaptation_level=adaptation_level,
        )
        return res
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate tailored CV.") from exc


@router.post("/jobs/{job_id}/assets/cover-letter")
async def create_job_cover_letter(
    job_id: int,
    cv_file: UploadFile = File(...),
    language: str = Form("English"),
    tone: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not cv_file or not cv_file.filename:
        raise HTTPException(status_code=400, detail="cv_file is required")

    try:
        res = await job_application_asset_service.generate_job_cover_letter(
            db=db,
            job_id=job_id,
            cv_file=cv_file,
            language=language,
            tone=tone
        )
        return res
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate cover letter.") from exc


@router.post("/jobs/{job_id}/assets/application-email")
async def create_job_application_email(
    job_id: int,
    cv_file: UploadFile = File(...),
    language: str = Form("English"),
    tone: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not cv_file or not cv_file.filename:
        raise HTTPException(status_code=400, detail="cv_file is required")

    try:
        res = await job_application_asset_service.generate_job_application_email(
            db=db,
            job_id=job_id,
            cv_file=cv_file,
            language=language,
            tone=tone
        )
        return res
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate application email.") from exc


@router.get("/jobs/{job_id}/assets")
def get_job_assets(job_id: int, db: Session = Depends(get_db)):
    # Verify job exists
    from models import MonitoredJob
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        assets = job_application_asset_service.list_job_assets(db, job_id)
        return {"job_id": job_id, "assets": assets}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to list assets.") from exc


@router.get("/assets")
def get_all_assets(db: Session = Depends(get_db)):
    try:
        from models import JobApplicationAsset
        assets = db.query(JobApplicationAsset).order_by(JobApplicationAsset.created_at.desc()).all()
        return {"assets": [job_application_asset_service.serialize_asset(a) for a in assets]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to list all assets.") from exc


@router.get("/assets/{asset_id}")
def get_single_asset(asset_id: int, db: Session = Depends(get_db)):
    try:
        asset = job_application_asset_service.get_job_asset(db, asset_id)
        return {"asset": asset}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to get asset.") from exc


@router.get("/assets/{asset_id}/download")
def download_asset(asset_id: int, db: Session = Depends(get_db)):
    try:
        asset = job_application_asset_service.get_job_asset(db, asset_id)
        file_path = asset.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Physical file path not specified in database")

        # Resolve paths to prevent traversal
        safe_dir = os.path.abspath("generated_assets")
        resolved_path = os.path.abspath(file_path)
        if not resolved_path.startswith(safe_dir + os.sep) and resolved_path != safe_dir:
            raise HTTPException(status_code=403, detail="Access denied: file path is outside the allowed directory.")

        if not os.path.exists(resolved_path):
            raise HTTPException(status_code=404, detail="Physical file not found on disk")

        filename = os.path.basename(resolved_path)
        ext = asset.get("export_format")
        media_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
            "json": "application/json",
            "text": "text/plain"
        }
        media_type = media_types.get(ext, "application/octet-stream")

        return FileResponse(path=resolved_path, filename=filename, media_type=media_type)
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to download asset.") from exc
