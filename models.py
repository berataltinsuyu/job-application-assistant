from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from database import Base


class ApplicationHistory(Base):
    __tablename__ = "application_history"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String(50), nullable=False)
    cv_filename = Column(String(255), nullable=True)
    job_text = Column(Text, nullable=True)
    result = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobAlertProfile(Base):
    __tablename__ = "job_alert_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    keywords = Column(Text, nullable=False, default="[]")
    location = Column(String(255), nullable=True)
    seniority = Column(String(100), nullable=True)
    job_type = Column(String(100), nullable=True)
    work_model = Column(String(100), nullable=True)
    sources = Column(Text, nullable=False, default='["manual_mock"]')
    excluded_keywords = Column(Text, nullable=False, default="[]")
    min_match_score = Column(Integer, nullable=False, default=40)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobSearchRun(Base):
    __tablename__ = "job_search_runs"

    id = Column(Integer, primary_key=True, index=True)
    alert_profile_id = Column(Integer, ForeignKey("job_alert_profiles.id"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="running")
    source_count = Column(Integer, nullable=False, default=0)
    jobs_found = Column(Integer, nullable=False, default=0)
    new_jobs_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)


class MonitoredJob(Base):
    __tablename__ = "monitored_jobs"
    __table_args__ = (
        UniqueConstraint("alert_profile_id", "source", "source_job_id", name="uq_monitored_job_source"),
    )

    id = Column(Integer, primary_key=True, index=True)
    alert_profile_id = Column(Integer, ForeignKey("job_alert_profiles.id"), nullable=True, index=True)
    run_id = Column(Integer, ForeignKey("job_search_runs.id"), nullable=True, index=True)
    source = Column(String(100), nullable=False)
    source_job_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    work_model = Column(String(100), nullable=True)
    seniority = Column(String(100), nullable=True)
    job_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    posted_at = Column(String(100), nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    match_score = Column(Integer, nullable=False, default=0)
    match_summary = Column(Text, nullable=True)
    matched_keywords = Column(Text, nullable=False, default="[]")
    missing_keywords = Column(Text, nullable=False, default="[]")
    status = Column(String(50), nullable=False, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobIntelligenceReport(Base):
    __tablename__ = "job_intelligence_reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("monitored_jobs.id"), nullable=False, index=True, unique=True)
    job_family = Column(String(100), nullable=False)
    seniority_assessment = Column(String(100), nullable=False)
    report_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobApplicationPipeline(Base):
    __tablename__ = "job_application_pipeline"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("monitored_jobs.id"), nullable=False, index=True, unique=True)
    application_stage = Column(String(50), nullable=False, default="not_started")
    application_priority = Column(String(50), nullable=False, default="medium")
    application_deadline = Column(String(100), nullable=True)
    applied_at = Column(String(100), nullable=True)
    next_action = Column(Text, nullable=True)
    next_action_date = Column(String(100), nullable=True)
    interview_date = Column(String(100), nullable=True)
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    application_notes = Column(Text, nullable=True)
    application_materials_status = Column(String(50), nullable=False, default="not_started")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobApplicationAsset(Base):
    __tablename__ = "job_application_assets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("monitored_jobs.id"), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)  # tailored_cv, cover_letter, application_email
    title = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=True)
    structured_json = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    export_format = Column(String(50), nullable=True)  # text, json, pdf, docx, txt
    template_id = Column(String(100), nullable=True)
    language = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



