from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import MonitoredJob, JobApplicationPipeline
from services.job_monitoring_service import serialize_monitored_job

ALLOWED_STAGES = {
    "not_started",
    "preparing",
    "applied",
    "screening",
    "interview",
    "technical_interview",
    "offer",
    "rejected",
    "withdrawn",
    "archived",
}

ALLOWED_PRIORITIES = {"low", "medium", "high"}

ALLOWED_MATERIALS_STATUSES = {
    "not_started",
    "cv_needed",
    "cover_letter_needed",
    "ready",
    "submitted",
}


def get_application_pipeline(db: Session, job_id: int) -> dict:
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    if not job:
        raise LookupError("Monitored job not found.")

    pipeline = db.query(JobApplicationPipeline).filter(JobApplicationPipeline.job_id == job_id).first()
    if not pipeline:
        now = datetime.utcnow()
        pipeline = JobApplicationPipeline(
            job_id=job_id,
            application_stage="not_started",
            application_priority="medium",
            application_materials_status="not_started",
            created_at=now,
            updated_at=now,
        )
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)

    return serialize_pipeline(pipeline)


def update_application_pipeline(db: Session, job_id: int, payload: dict) -> dict:
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    if not job:
        raise LookupError("Monitored job not found.")

    pipeline = db.query(JobApplicationPipeline).filter(JobApplicationPipeline.job_id == job_id).first()
    now = datetime.utcnow()
    if not pipeline:
        pipeline = JobApplicationPipeline(
            job_id=job_id,
            application_stage="not_started",
            application_priority="medium",
            application_materials_status="not_started",
            created_at=now,
            updated_at=now,
        )
        db.add(pipeline)

    if "application_stage" in payload:
        stage = payload["application_stage"] or "not_started"
        if stage not in ALLOWED_STAGES:
            stages_list = ", ".join(sorted(ALLOWED_STAGES))
            raise ValueError(f"Invalid application stage. Allowed values: {stages_list}.")
        pipeline.application_stage = stage

        # Sync stage to monitored_jobs.status
        if stage == "applied":
            job.status = "applied"
            # Set applied_at to today if empty
            if not pipeline.applied_at and not payload.get("applied_at"):
                pipeline.applied_at = now.strftime("%Y-%m-%d")
        elif stage == "rejected":
            job.status = "rejected"
        elif stage == "archived":
            job.status = "archived"

    if "application_priority" in payload:
        priority = payload["application_priority"] or "medium"
        if priority not in ALLOWED_PRIORITIES:
            priorities_list = ", ".join(sorted(ALLOWED_PRIORITIES))
            raise ValueError(f"Invalid application priority. Allowed values: {priorities_list}.")
        pipeline.application_priority = priority

    if "application_materials_status" in payload:
        mat_status = payload["application_materials_status"] or "not_started"
        if mat_status not in ALLOWED_MATERIALS_STATUSES:
            mat_list = ", ".join(sorted(ALLOWED_MATERIALS_STATUSES))
            raise ValueError(f"Invalid application materials status. Allowed values: {mat_list}.")
        pipeline.application_materials_status = mat_status

    if "application_deadline" in payload:
        pipeline.application_deadline = _clean_string(payload["application_deadline"])
    if "applied_at" in payload:
        pipeline.applied_at = _clean_string(payload["applied_at"])
    if "next_action" in payload:
        pipeline.next_action = _clean_string(payload["next_action"])
    if "next_action_date" in payload:
        pipeline.next_action_date = _clean_string(payload["next_action_date"])
    if "interview_date" in payload:
        pipeline.interview_date = _clean_string(payload["interview_date"])
    if "contact_person" in payload:
        pipeline.contact_person = _clean_string(payload["contact_person"])
    if "contact_email" in payload:
        pipeline.contact_email = _clean_string(payload["contact_email"])
    if "application_notes" in payload:
        pipeline.application_notes = _clean_string(payload["application_notes"])

    pipeline.updated_at = now
    job.updated_at = now
    db.commit()
    db.refresh(pipeline)
    db.refresh(job)

    return {
        "job": serialize_monitored_job(job),
        "pipeline": serialize_pipeline(pipeline)
    }


def list_pipeline_jobs(db: Session, filters: dict | None = None) -> list[dict]:
    query = db.query(MonitoredJob, JobApplicationPipeline).outerjoin(JobApplicationPipeline, MonitoredJob.id == JobApplicationPipeline.job_id)
    filters = filters or {}

    # Status & source filters
    if filters.get("status"):
        query = query.filter(MonitoredJob.status == filters["status"])
    if filters.get("source"):
        query = query.filter(MonitoredJob.source == filters["source"])
    if filters.get("min_match_score") is not None:
        query = query.filter(MonitoredJob.match_score >= int(filters["min_match_score"]))

    # Pipeline specific filters
    if filters.get("application_stage"):
        stage = filters["application_stage"]
        if stage == "not_started":
            # Handle nulls as not_started defaults
            query = query.filter(or_(JobApplicationPipeline.application_stage == stage, JobApplicationPipeline.id.is_(None)))
        else:
            query = query.filter(JobApplicationPipeline.application_stage == stage)

    if filters.get("application_priority"):
        priority = filters["application_priority"]
        if priority == "medium":
            query = query.filter(or_(JobApplicationPipeline.application_priority == priority, JobApplicationPipeline.id.is_(None)))
        else:
            query = query.filter(JobApplicationPipeline.application_priority == priority)

    if filters.get("due_before"):
        query = query.filter(JobApplicationPipeline.application_deadline <= filters["due_before"])

    if filters.get("next_action_before"):
        query = query.filter(JobApplicationPipeline.next_action_date <= filters["next_action_before"])

    query = query.order_by(MonitoredJob.discovered_at.desc(), MonitoredJob.match_score.desc())
    
    results = []
    for job, pipeline in query.all():
        results.append({
            "job": serialize_monitored_job(job),
            "pipeline": serialize_pipeline(pipeline) if pipeline else get_default_pipeline_dict(job.id)
        })
    return results


def serialize_pipeline(pipeline: JobApplicationPipeline) -> dict:
    return {
        "id": pipeline.id,
        "job_id": pipeline.job_id,
        "application_stage": pipeline.application_stage or "not_started",
        "application_priority": pipeline.application_priority or "medium",
        "application_deadline": pipeline.application_deadline or "",
        "applied_at": pipeline.applied_at or "",
        "next_action": pipeline.next_action or "",
        "next_action_date": pipeline.next_action_date or "",
        "interview_date": pipeline.interview_date or "",
        "contact_person": pipeline.contact_person or "",
        "contact_email": pipeline.contact_email or "",
        "application_notes": pipeline.application_notes or "",
        "application_materials_status": pipeline.application_materials_status or "not_started",
        "created_at": pipeline.created_at,
        "updated_at": pipeline.updated_at,
    }


def get_default_pipeline_dict(job_id: int) -> dict:
    return {
        "id": None,
        "job_id": job_id,
        "application_stage": "not_started",
        "application_priority": "medium",
        "application_deadline": "",
        "applied_at": "",
        "next_action": "",
        "next_action_date": "",
        "interview_date": "",
        "contact_person": "",
        "contact_email": "",
        "application_notes": "",
        "application_materials_status": "not_started",
        "created_at": None,
        "updated_at": None,
    }


def _clean_string(value) -> str:
    return str(value or "").strip()
