import json
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import Base, SessionLocal, engine, ensure_job_monitoring_schema
from models import JobAlertProfile, JobApplicationPipeline, JobIntelligenceReport, MonitoredJob
from services.job_monitoring_service import create_manual_job, serialize_alert_profile
from services.job_sources import seed_default_source_settings


DEMO_PROFILE_NAME = "Demo Search Profile"
DEMO_JOBS = [
    {
        "source_job_id": "demo-junior-backend-api-developer",
        "title": "Junior Backend API Developer",
        "company": "Demo Software Studio",
        "location": "Remote",
        "work_model": "Remote",
        "seniority": "Junior",
        "job_type": "Full-time",
        "posted_at": "2026-06-15",
        "url": "https://example.com/demo-jobs/junior-backend-api-developer",
        "description": (
            "Build and maintain REST API endpoints, write SQL queries, document service behavior, "
            "review logs, and collaborate with product teammates on backend features. Experience "
            "with Python, FastAPI, Git, testing, and clear communication is useful."
        ),
    },
    {
        "source_job_id": "demo-ai-applications-intern",
        "title": "AI Applications Intern",
        "company": "Demo AI Lab",
        "location": "Istanbul, Turkey",
        "work_model": "Hybrid",
        "seniority": "Intern",
        "job_type": "Internship",
        "posted_at": "2026-06-18",
        "url": "https://example.com/demo-jobs/ai-applications-intern",
        "description": (
            "Support prototype AI application workflows, prepare prompt tests, connect simple APIs, "
            "organize evaluation notes, and document findings for the engineering team. Python, "
            "LLM basics, REST APIs, and curiosity about applied AI are relevant."
        ),
    },
]


def _json_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def ensure_demo_profile(db) -> JobAlertProfile:
    now = _utc_now()
    profile = db.query(JobAlertProfile).filter(JobAlertProfile.name == DEMO_PROFILE_NAME).first()
    if not profile:
        profile = JobAlertProfile(
            name=DEMO_PROFILE_NAME,
            created_at=now,
            updated_at=now,
        )
        db.add(profile)

    profile.keywords = _json_list(["Python", "API", "FastAPI", "SQL", "AI", "LLM", "Git"])
    profile.location = "Remote, Istanbul, Hybrid"
    profile.seniority = "Intern, Junior"
    profile.job_type = "Full-time, Internship"
    profile.work_model = "Remote, Hybrid"
    profile.sources = _json_list(["manual_mock"])
    profile.excluded_keywords = _json_list(["senior", "lead", "manager"])
    profile.min_match_score = 35
    profile.is_active = True
    profile.updated_at = now
    db.commit()
    db.refresh(profile)
    return profile


def ensure_demo_jobs(db, profile: JobAlertProfile) -> list[MonitoredJob]:
    created_or_updated = []
    for job in DEMO_JOBS:
        result = create_manual_job(
            db,
            {
                "alert_profile_id": profile.id,
                "source": "manual_import",
                **job,
            },
        )
        model = db.query(MonitoredJob).filter(MonitoredJob.id == result["id"]).first()
        if model:
            created_or_updated.append(model)
    return created_or_updated


def ensure_pipeline(db, job: MonitoredJob) -> None:
    now = _utc_now()
    pipeline = db.query(JobApplicationPipeline).filter(JobApplicationPipeline.job_id == job.id).first()
    if not pipeline:
        pipeline = JobApplicationPipeline(job_id=job.id, created_at=now)
        db.add(pipeline)

    pipeline.application_stage = "preparing"
    pipeline.application_priority = "high"
    pipeline.application_deadline = "2026-07-05"
    pipeline.next_action = "Review tailored CV and prepare cover letter."
    pipeline.next_action_date = "2026-06-28"
    pipeline.application_notes = "Demo pipeline record seeded locally. No external calls were made."
    pipeline.application_materials_status = "cv_needed"
    pipeline.updated_at = now
    db.commit()


def ensure_intelligence_report(db, job: MonitoredJob) -> None:
    now = _utc_now()
    report = db.query(JobIntelligenceReport).filter(JobIntelligenceReport.job_id == job.id).first()
    if not report:
        report = JobIntelligenceReport(job_id=job.id, created_at=now)
        db.add(report)

    report.job_family = "software_backend"
    report.seniority_assessment = "junior"
    report.report_json = json.dumps(
        {
            "job_family": "software_backend",
            "seniority_assessment": "junior",
            "application_recommendation": "apply_with_tailored_cv",
            "role_summary": "Fictional junior backend API role for demo review.",
            "candidate_strengths": ["Python", "API development", "SQL", "documentation"],
            "candidate_gaps": ["Production monitoring depth", "larger service ownership"],
            "suggested_cv_focus": ["API projects", "testing", "database work"],
            "interview_focus": ["REST API design", "SQL basics", "debugging workflow"],
            "risk_notes": ["Demo report only; it was not generated by Gemini."],
        },
        ensure_ascii=False,
    )
    report.updated_at = now
    db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_job_monitoring_schema()

    db = SessionLocal()
    try:
        seed_default_source_settings(db)
        profile = ensure_demo_profile(db)
        jobs = ensure_demo_jobs(db, profile)
        if jobs:
            ensure_pipeline(db, jobs[0])
            ensure_intelligence_report(db, jobs[0])

        profile_data = serialize_alert_profile(profile)
        print("Demo data ready.")
        print(f"Search profile: #{profile.id} {profile_data['name']}")
        print(f"Demo jobs: {len(jobs)}")
        print("Idempotent: re-running updates the same demo rows.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
