import json
from datetime import datetime

from sqlalchemy.orm import Session

from models import JobAlertProfile, JobSearchRun, MonitoredJob
from services.job_match_service import _normalize as _normalize_for_dedupe
from services.job_match_service import score_job_against_profile
from services.job_sources import get_phase_2a_adapters


ALLOWED_JOB_STATUSES = {"new", "saved", "rejected", "applied", "archived"}
DEFAULT_SOURCE = "manual_mock"


def create_alert_profile(db: Session, payload: dict) -> dict:
    now = _utc_now()
    profile = JobAlertProfile(
        name=_required_text(payload.get("name"), "name"),
        keywords=_json_list(payload.get("keywords")),
        location=_optional_text(payload.get("location")),
        seniority=_optional_text(payload.get("seniority")),
        job_type=_optional_text(payload.get("job_type")),
        work_model=_optional_text(payload.get("work_model")),
        sources=_json_list(_valid_sources(payload.get("sources"))),
        excluded_keywords=_json_list(payload.get("excluded_keywords")),
        min_match_score=_score_value(payload.get("min_match_score", 40)),
        is_active=bool(payload.get("is_active", True)),
        created_at=now,
        updated_at=now,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return serialize_alert_profile(profile)


def list_alert_profiles(db: Session, include_inactive: bool = True) -> list[dict]:
    query = db.query(JobAlertProfile)
    if not include_inactive:
        query = query.filter(JobAlertProfile.is_active.is_(True))
    profiles = query.order_by(JobAlertProfile.created_at.desc()).all()
    return [serialize_alert_profile(profile) for profile in profiles]


def get_alert_profile(db: Session, alert_id: int) -> dict | None:
    profile = _get_alert_model(db, alert_id)
    return serialize_alert_profile(profile) if profile else None


def update_alert_profile(db: Session, alert_id: int, payload: dict) -> dict | None:
    profile = _get_alert_model(db, alert_id)
    if not profile:
        return None

    if "name" in payload:
        profile.name = _required_text(payload.get("name"), "name")
    if "keywords" in payload:
        profile.keywords = _json_list(payload.get("keywords"))
    if "location" in payload:
        profile.location = _optional_text(payload.get("location"))
    if "seniority" in payload:
        profile.seniority = _optional_text(payload.get("seniority"))
    if "job_type" in payload:
        profile.job_type = _optional_text(payload.get("job_type"))
    if "work_model" in payload:
        profile.work_model = _optional_text(payload.get("work_model"))
    if "sources" in payload:
        profile.sources = _json_list(_valid_sources(payload.get("sources")))
    if "excluded_keywords" in payload:
        profile.excluded_keywords = _json_list(payload.get("excluded_keywords"))
    if "min_match_score" in payload:
        profile.min_match_score = _score_value(payload.get("min_match_score"))
    if "is_active" in payload:
        profile.is_active = bool(payload.get("is_active"))

    profile.updated_at = _utc_now()
    db.commit()
    db.refresh(profile)
    return serialize_alert_profile(profile)


def deactivate_alert_profile(db: Session, alert_id: int) -> dict | None:
    return update_alert_profile(db, alert_id, {"is_active": False})


def run_alert_profile(db: Session, alert_id: int) -> dict:
    profile = _get_alert_model(db, alert_id)
    if not profile:
        raise LookupError("Alert profile not found.")
    if not profile.is_active:
        raise ValueError("Alert profile is inactive.")

    alert_profile = serialize_alert_profile(profile)
    adapters = _adapters_for_profile(alert_profile)
    now = _utc_now()
    run = JobSearchRun(
        alert_profile_id=profile.id,
        started_at=now,
        status="running",
        source_count=len(adapters),
        jobs_found=0,
        new_jobs_count=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    jobs_found = 0
    new_jobs_count = 0
    try:
        for adapter in adapters:
            source_jobs = adapter.search_jobs(alert_profile)
            jobs_found += len(source_jobs)
            for source_job in source_jobs:
                normalized_job = _normalize_job(source_job, adapter.source_name)
                score = score_job_against_profile(normalized_job, alert_profile)
                if score["match_score"] < alert_profile["min_match_score"]:
                    continue

                existing = _find_existing_job(db, profile.id, normalized_job["source"], normalized_job["source_job_id"])
                if existing:
                    _update_existing_job(existing, normalized_job, score, run.id)
                else:
                    monitored_job = _build_monitored_job(profile.id, run.id, normalized_job, score)
                    db.add(monitored_job)
                    new_jobs_count += 1

        run.status = "success"
        run.jobs_found = jobs_found
        run.new_jobs_count = new_jobs_count
        run.finished_at = _utc_now()
        db.commit()
        db.refresh(run)
        return {
            "run": serialize_search_run(run),
            "jobs": list_monitored_jobs(db, alert_profile_id=profile.id),
        }
    except Exception as exc:
        db.rollback()
        run = db.query(JobSearchRun).filter(JobSearchRun.id == run.id).first()
        if run:
            run.status = "failed"
            run.jobs_found = jobs_found
            run.new_jobs_count = new_jobs_count
            run.finished_at = _utc_now()
            run.error_message = str(exc)
            db.commit()
            db.refresh(run)
        raise


def list_monitored_jobs(
    db: Session,
    alert_profile_id: int | None = None,
    status: str | None = None,
    source: str | None = None,
) -> list[dict]:
    query = db.query(MonitoredJob)
    if alert_profile_id is not None:
        query = query.filter(MonitoredJob.alert_profile_id == alert_profile_id)
    if status:
        _validate_status(status)
        query = query.filter(MonitoredJob.status == status)
    if source:
        query = query.filter(MonitoredJob.source == source)
    jobs = query.order_by(MonitoredJob.discovered_at.desc(), MonitoredJob.match_score.desc()).all()
    return [serialize_monitored_job(job) for job in jobs]


def get_monitored_job(db: Session, job_id: int) -> dict | None:
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    return serialize_monitored_job(job) if job else None


def update_job_status(db: Session, job_id: int, status: str) -> dict | None:
    _validate_status(status)
    job = db.query(MonitoredJob).filter(MonitoredJob.id == job_id).first()
    if not job:
        return None
    job.status = status
    job.updated_at = _utc_now()
    db.commit()
    db.refresh(job)
    return serialize_monitored_job(job)


def list_search_runs(db: Session, alert_profile_id: int | None = None) -> list[dict]:
    query = db.query(JobSearchRun)
    if alert_profile_id is not None:
        query = query.filter(JobSearchRun.alert_profile_id == alert_profile_id)
    runs = query.order_by(JobSearchRun.started_at.desc()).all()
    return [serialize_search_run(run) for run in runs]


def serialize_alert_profile(profile: JobAlertProfile) -> dict:
    return {
        "id": profile.id,
        "name": profile.name,
        "keywords": _json_loads(profile.keywords),
        "location": profile.location or "",
        "seniority": profile.seniority or "",
        "job_type": profile.job_type or "",
        "work_model": profile.work_model or "",
        "sources": _json_loads(profile.sources) or [DEFAULT_SOURCE],
        "excluded_keywords": _json_loads(profile.excluded_keywords),
        "min_match_score": profile.min_match_score,
        "is_active": profile.is_active,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def serialize_search_run(run: JobSearchRun) -> dict:
    return {
        "id": run.id,
        "alert_profile_id": run.alert_profile_id,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "status": run.status,
        "source_count": run.source_count,
        "jobs_found": run.jobs_found,
        "new_jobs_count": run.new_jobs_count,
        "error_message": run.error_message or "",
    }


def serialize_monitored_job(job: MonitoredJob) -> dict:
    return {
        "id": job.id,
        "alert_profile_id": job.alert_profile_id,
        "run_id": job.run_id,
        "source": job.source,
        "source_job_id": job.source_job_id,
        "title": job.title,
        "company": job.company or "",
        "location": job.location or "",
        "work_model": job.work_model or "",
        "seniority": job.seniority or "",
        "job_type": job.job_type or "",
        "description": job.description or "",
        "url": job.url or "",
        "posted_at": job.posted_at or "",
        "discovered_at": job.discovered_at,
        "match_score": job.match_score,
        "match_summary": job.match_summary or "",
        "matched_keywords": _json_loads(job.matched_keywords),
        "missing_keywords": _json_loads(job.missing_keywords),
        "status": job.status,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def _get_alert_model(db: Session, alert_id: int) -> JobAlertProfile | None:
    return db.query(JobAlertProfile).filter(JobAlertProfile.id == alert_id).first()


def _adapters_for_profile(alert_profile: dict):
    available = get_phase_2a_adapters()
    requested_sources = alert_profile.get("sources") or [DEFAULT_SOURCE]
    return [available[source] for source in requested_sources if source in available]


def _find_existing_job(db: Session, alert_profile_id: int, source: str, source_job_id: str) -> MonitoredJob | None:
    return (
        db.query(MonitoredJob)
        .filter(
            MonitoredJob.alert_profile_id == alert_profile_id,
            MonitoredJob.source == source,
            MonitoredJob.source_job_id == source_job_id,
        )
        .first()
    )


def _build_monitored_job(alert_profile_id: int, run_id: int, job: dict, score: dict) -> MonitoredJob:
    now = _utc_now()
    return MonitoredJob(
        alert_profile_id=alert_profile_id,
        run_id=run_id,
        source=job["source"],
        source_job_id=job["source_job_id"],
        title=job["title"],
        company=job.get("company"),
        location=job.get("location"),
        work_model=job.get("work_model"),
        seniority=job.get("seniority"),
        job_type=job.get("job_type"),
        description=job.get("description"),
        url=job.get("url"),
        posted_at=job.get("posted_at"),
        discovered_at=now,
        match_score=score["match_score"],
        match_summary=score["match_summary"],
        matched_keywords=_json_list(score["matched_keywords"]),
        missing_keywords=_json_list(score["missing_keywords"]),
        status="new",
        created_at=now,
        updated_at=now,
    )


def _update_existing_job(existing: MonitoredJob, job: dict, score: dict, run_id: int) -> None:
    existing.run_id = run_id
    existing.title = job["title"]
    existing.company = job.get("company")
    existing.location = job.get("location")
    existing.work_model = job.get("work_model")
    existing.seniority = job.get("seniority")
    existing.job_type = job.get("job_type")
    existing.description = job.get("description")
    existing.url = job.get("url")
    existing.posted_at = job.get("posted_at")
    existing.match_score = score["match_score"]
    existing.match_summary = score["match_summary"]
    existing.matched_keywords = _json_list(score["matched_keywords"])
    existing.missing_keywords = _json_list(score["missing_keywords"])
    existing.updated_at = _utc_now()


def _normalize_job(job: dict, source_name: str) -> dict:
    source = _optional_text(job.get("source")) or source_name
    source_job_id = _required_text(job.get("source_job_id"), "source_job_id")
    title = _required_text(job.get("title"), "title")
    return {
        "source": source,
        "source_job_id": source_job_id,
        "title": title,
        "company": _optional_text(job.get("company")),
        "location": _optional_text(job.get("location")),
        "work_model": _optional_text(job.get("work_model")),
        "seniority": _optional_text(job.get("seniority")),
        "job_type": _optional_text(job.get("job_type")),
        "description": _optional_text(job.get("description")),
        "url": _optional_text(job.get("url")),
        "posted_at": _optional_text(job.get("posted_at")),
    }


def _valid_sources(value) -> list[str]:
    sources = _list_value(value) or [DEFAULT_SOURCE]
    invalid_sources = [source for source in sources if source != DEFAULT_SOURCE]
    if invalid_sources:
        raise ValueError("Phase 2A supports only the manual_mock source.")
    return [DEFAULT_SOURCE]


def _validate_status(status: str) -> None:
    if status not in ALLOWED_JOB_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_JOB_STATUSES))
        raise ValueError(f"Invalid job status. Allowed values: {allowed}.")


def _required_text(value, field_name: str) -> str:
    text = _optional_text(value)
    if not text:
        raise ValueError(f"{field_name} is required.")
    return text


def _optional_text(value) -> str:
    return str(value or "").strip()


def _score_value(value) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        raise ValueError("min_match_score must be an integer between 0 and 100.")


def _json_list(value) -> str:
    return json.dumps(_list_value(value), ensure_ascii=False)


def _json_loads(value) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _list_value(value) -> list[str]:
    if isinstance(value, list):
        raw_values = value
    elif isinstance(value, str):
        raw_values = value.replace("\n", ",").split(",")
    else:
        raw_values = []
    result = []
    seen = set()
    for item in raw_values:
        text = _optional_text(item)
        key = _normalize_for_dedupe(text)
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _utc_now() -> datetime:
    return datetime.utcnow()
