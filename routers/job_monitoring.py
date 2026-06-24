from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from services import job_monitoring_service


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
