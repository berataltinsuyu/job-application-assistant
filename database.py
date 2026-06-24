from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./job_application_assistant.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_job_monitoring_schema():
    """Keep Phase 2B manual imports compatible with Phase 2A SQLite databases."""
    with engine.begin() as connection:
        table_exists = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='monitored_jobs'"
        ).fetchone()
        if not table_exists:
            return

        columns = {
            row[1]: row
            for row in connection.exec_driver_sql("PRAGMA table_info(monitored_jobs)").fetchall()
        }
        alert_not_null = bool(columns.get("alert_profile_id") and columns["alert_profile_id"][3])
        run_not_null = bool(columns.get("run_id") and columns["run_id"][3])
        if not alert_not_null and not run_not_null:
            return

        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("ALTER TABLE monitored_jobs RENAME TO monitored_jobs_phase2a_backup")
        connection.exec_driver_sql(
            """
            CREATE TABLE monitored_jobs (
                id INTEGER NOT NULL,
                alert_profile_id INTEGER,
                run_id INTEGER,
                source VARCHAR(100) NOT NULL,
                source_job_id VARCHAR(255) NOT NULL,
                title VARCHAR(255) NOT NULL,
                company VARCHAR(255),
                location VARCHAR(255),
                work_model VARCHAR(100),
                seniority VARCHAR(100),
                job_type VARCHAR(100),
                description TEXT,
                url TEXT,
                posted_at VARCHAR(100),
                discovered_at DATETIME NOT NULL,
                match_score INTEGER NOT NULL,
                match_summary TEXT,
                matched_keywords TEXT NOT NULL,
                missing_keywords TEXT NOT NULL,
                status VARCHAR(50) NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                PRIMARY KEY (id),
                CONSTRAINT uq_monitored_job_source UNIQUE (alert_profile_id, source, source_job_id),
                FOREIGN KEY(alert_profile_id) REFERENCES job_alert_profiles (id),
                FOREIGN KEY(run_id) REFERENCES job_search_runs (id)
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO monitored_jobs (
                id, alert_profile_id, run_id, source, source_job_id, title, company, location,
                work_model, seniority, job_type, description, url, posted_at, discovered_at,
                match_score, match_summary, matched_keywords, missing_keywords, status,
                created_at, updated_at
            )
            SELECT
                id, alert_profile_id, run_id, source, source_job_id, title, company, location,
                work_model, seniority, job_type, description, url, posted_at, discovered_at,
                match_score, match_summary, matched_keywords, missing_keywords, status,
                created_at, updated_at
            FROM monitored_jobs_phase2a_backup
            """
        )
        connection.exec_driver_sql("DROP TABLE monitored_jobs_phase2a_backup")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_monitored_jobs_alert_profile_id ON monitored_jobs (alert_profile_id)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_monitored_jobs_run_id ON monitored_jobs (run_id)")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
