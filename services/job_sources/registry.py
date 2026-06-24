import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import JobSourceSetting
from services.job_sources.manual_mock import ManualMockJobSourceAdapter
from services.job_sources.source_config import DEFAULT_SOURCE_CONFIGS, get_default_source_config


RUNNABLE_ADAPTERS = {
    ManualMockJobSourceAdapter.source_name: ManualMockJobSourceAdapter,
}


def seed_default_source_settings(db: Session) -> None:
    now = datetime.utcnow()
    for source_name, config in DEFAULT_SOURCE_CONFIGS.items():
        existing = db.query(JobSourceSetting).filter(JobSourceSetting.source_name == source_name).first()
        if existing:
            changed = False
            for field in ["display_name", "runnable", "status", "safety_notes"]:
                value = config.get(field)
                if getattr(existing, field) != value:
                    setattr(existing, field, value)
                    changed = True
            if existing.cooldown_minutes is None:
                existing.cooldown_minutes = int(config.get("cooldown_minutes", 0) or 0)
                changed = True
            if not existing.config_json:
                existing.config_json = "{}"
                changed = True
            if changed:
                existing.updated_at = now
            continue

        db.add(
            JobSourceSetting(
                source_name=source_name,
                display_name=config["display_name"],
                enabled=bool(config["enabled"]),
                runnable=bool(config["runnable"]),
                status=config["status"],
                cooldown_minutes=int(config.get("cooldown_minutes", 0) or 0),
                last_run_at=config.get("last_run_at"),
                last_status=config.get("last_status"),
                last_error=config.get("last_error"),
                config_json="{}",
                safety_notes=config.get("safety_notes", ""),
                created_at=now,
                updated_at=now,
            )
        )
    db.commit()


def _get_session(db: Session | None):
    if db is not None:
        return db, False
    from database import SessionLocal
    return SessionLocal(), True


def get_available_sources(db: Session | None = None) -> list[dict]:
    db, should_close = _get_session(db)
    try:
        seed_default_source_settings(db)
        settings = db.query(JobSourceSetting).order_by(JobSourceSetting.id.asc()).all()
        return [serialize_source_setting(setting) for setting in settings]
    finally:
        if should_close:
            db.close()


def get_source_setting(db: Session | None, source_name: str) -> dict | None:
    db, should_close = _get_session(db)
    try:
        seed_default_source_settings(db)
        setting = db.query(JobSourceSetting).filter(JobSourceSetting.source_name == source_name).first()
        return serialize_source_setting(setting) if setting else None
    finally:
        if should_close:
            db.close()


def get_source_setting_by_name(source_name: str) -> dict | None:
    return get_source_setting(None, source_name)


def get_enabled_runnable_sources(db: Session | None = None) -> list[dict]:
    return [
        source for source in get_available_sources(db)
        if source["enabled"] and source["runnable"] and source["status"] == "active"
    ]


def get_source_adapter(source_name: str):
    config = get_default_source_config(source_name)
    if not config or source_name not in RUNNABLE_ADAPTERS:
        return None
    if source_name != "manual_mock":
        return None
    return RUNNABLE_ADAPTERS[source_name]()


def validate_source_can_run(source_name: str, db: Session | None = None) -> bool:
    can_run, _reason = can_run_source(source_name, db)
    return can_run


def can_run_source(source_name: str, db: Session | None = None) -> tuple[bool, str | None]:
    source = get_source_setting(db, source_name)
    if not source:
        return False, f"Unknown source: {source_name}"
    if not source["enabled"]:
        return False, f"{source_name} is disabled."
    if not source["runnable"]:
        return False, f"{source_name} is not a runnable monitoring source."
    if source["status"] == "not_implemented":
        return False, f"{source_name} is not implemented in Phase 3A."
    if source["fetches_external_url"]:
        return False, f"{source_name} is blocked because Phase 3A sources must not fetch external URLs."

    cooldown = int(source.get("cooldown_minutes") or 0)
    last_run_at = source.get("last_run_at")
    if cooldown > 0 and last_run_at:
        if isinstance(last_run_at, str):
            try:
                last_run_dt = datetime.fromisoformat(last_run_at)
            except ValueError:
                last_run_dt = None
        else:
            last_run_dt = last_run_at
        if last_run_dt and datetime.utcnow() - last_run_dt < timedelta(minutes=cooldown):
            next_run = last_run_dt + timedelta(minutes=cooldown)
            return False, f"{source_name} is cooling down until {next_run.isoformat(timespec='seconds')} UTC."

    return True, None


def update_source_setting(source_name: str, payload: dict, db: Session | None = None) -> dict:
    db, should_close = _get_session(db)
    try:
        result = _update_source_setting_with_session(db, source_name, payload)
        return result
    finally:
        if should_close:
            db.close()


def _update_source_setting_with_session(db: Session, source_name: str, payload: dict) -> dict:
    seed_default_source_settings(db)
    setting = db.query(JobSourceSetting).filter(JobSourceSetting.source_name == source_name).first()
    if not setting:
        raise LookupError("Source setting not found.")

    default_config = get_default_source_config(source_name)
    if not default_config:
        raise LookupError("Source setting not found.")

    if "cooldown_minutes" in payload:
        cooldown = int(payload.get("cooldown_minutes") or 0)
        if cooldown < 0:
            raise ValueError("cooldown_minutes cannot be negative.")
        setting.cooldown_minutes = cooldown

    if "enabled" in payload:
        enabled = bool(payload.get("enabled"))
        if enabled and default_config.get("status") == "not_implemented":
            raise ValueError("Not implemented placeholder sources cannot be enabled in Phase 3A.")
        setting.enabled = enabled

    if "config_json" in payload:
        config_json = payload.get("config_json")
        if isinstance(config_json, dict):
            setting.config_json = json.dumps(config_json, ensure_ascii=False)
        elif isinstance(config_json, str):
            try:
                parsed = json.loads(config_json or "{}")
            except json.JSONDecodeError as exc:
                raise ValueError("config_json must be valid JSON.") from exc
            if not isinstance(parsed, dict):
                raise ValueError("config_json must be a JSON object.")
            setting.config_json = json.dumps(parsed, ensure_ascii=False)
        elif config_json is None:
            setting.config_json = "{}"
        else:
            raise ValueError("config_json must be a JSON object.")

    setting.runnable = bool(default_config["runnable"])
    setting.status = default_config["status"]
    setting.display_name = default_config["display_name"]
    setting.safety_notes = default_config.get("safety_notes", "")
    setting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(setting)
    return serialize_source_setting(setting)


def record_source_run(db: Session, source_name: str, status: str, error: str | None = None) -> None:
    seed_default_source_settings(db)
    setting = db.query(JobSourceSetting).filter(JobSourceSetting.source_name == source_name).first()
    if not setting:
        return
    now = datetime.utcnow()
    setting.last_run_at = now
    setting.last_status = status
    setting.last_error = error or ""
    setting.updated_at = now
    db.commit()


def serialize_source_setting(setting: JobSourceSetting) -> dict:
    default_config = get_default_source_config(setting.source_name) or {}
    try:
        config_json = json.loads(setting.config_json or "{}")
    except Exception:
        config_json = {}
    return {
        "id": setting.id,
        "source_name": setting.source_name,
        "display_name": setting.display_name,
        "description": default_config.get("description", ""),
        "source_type": default_config.get("source_type", ""),
        "enabled": bool(setting.enabled),
        "runnable": bool(setting.runnable),
        "status": setting.status,
        "requires_api_key": bool(default_config.get("requires_api_key", False)),
        "supports_auto_search": bool(default_config.get("supports_auto_search", False)),
        "fetches_external_url": bool(default_config.get("fetches_external_url", False)),
        "cooldown_minutes": int(setting.cooldown_minutes or 0),
        "last_run_at": setting.last_run_at.isoformat() if setting.last_run_at else None,
        "last_status": setting.last_status or "",
        "last_error": setting.last_error or "",
        "config_json": config_json,
        "safety_level": default_config.get("safety_level", "disabled"),
        "safety_notes": setting.safety_notes or default_config.get("safety_notes", ""),
        "message": default_config.get("message", ""),
        "created_at": setting.created_at.isoformat() if setting.created_at else None,
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
    }
