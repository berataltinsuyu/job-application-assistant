import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_imports() -> None:
    import main  # noqa: F401

    print("import main: ok")


def test_source_registry() -> None:
    from services.job_sources import (
        can_run_source,
        get_available_sources,
        get_source_adapter,
        validate_source_can_run,
    )

    sources = {source["source_name"]: source for source in get_available_sources()}
    expected = {
        "manual_mock",
        "manual_import",
        "company_careers_placeholder",
        "techcareer_placeholder",
        "youthall_placeholder",
        "linkedin_placeholder",
        "kariyer_placeholder",
    }
    assert_true(expected.issubset(set(sources)), "Source registry is missing expected Phase 3A sources.")

    manual_mock = sources["manual_mock"]
    assert_true(manual_mock["enabled"] is True, "manual_mock must be enabled.")
    assert_true(manual_mock["runnable"] is True, "manual_mock must be runnable.")
    assert_true(manual_mock["fetches_external_url"] is False, "manual_mock must not fetch external URLs.")
    assert_true(validate_source_can_run("manual_mock") is True, "manual_mock should pass run validation.")
    assert_true(get_source_adapter("manual_mock") is not None, "manual_mock should return an adapter.")

    manual_import = sources["manual_import"]
    assert_true(manual_import["enabled"] is True, "manual_import must be enabled.")
    assert_true(manual_import["runnable"] is False, "manual_import must remain manual-only.")
    assert_true(manual_import["fetches_external_url"] is False, "manual_import must not fetch external URLs.")
    can_import_run, import_reason = can_run_source("manual_import")
    assert_true(can_import_run is False, "manual_import must not be runnable.")
    assert_true("not a runnable" in (import_reason or ""), "manual_import should report a clear reason.")
    assert_true(get_source_adapter("manual_import") is None, "manual_import must not return an adapter.")

    for name, source in sources.items():
        if name.endswith("_placeholder"):
            assert_true(source["enabled"] is False, f"{name} must be disabled.")
            assert_true(source["runnable"] is False, f"{name} must not be runnable.")
            assert_true(source["status"] == "not_implemented", f"{name} must be not_implemented.")
            assert_true(source["fetches_external_url"] is False, f"{name} must not fetch external URLs.")
            can_run, reason = can_run_source(name)
            assert_true(can_run is False, f"{name} must not run.")
            assert_true(reason is not None, f"{name} should provide a clear run-blocking reason.")

    print("source registry: ok")


def test_source_adapter_static_safety() -> None:
    source_dir = ROOT / "services" / "job_sources"
    banned_tokens = [
        "requests.get",
        "requests.post",
        "httpx.get",
        "httpx.post",
        "BeautifulSoup",
        "trafilatura",
        "selenium",
        "playwright",
        "webdriver",
    ]
    offenders = []
    for path in source_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned_tokens:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)} contains {token}")

    assert_true(not offenders, "Job source adapters must not fetch URLs or automate browsers: " + "; ".join(offenders))
    print("job source adapter static safety: ok")


def test_manual_url_extraction_boundary() -> None:
    from services import job_description_service

    assert_true(
        hasattr(job_description_service, "extract_job_description_from_url"),
        "Manual URL extraction service is missing.",
    )
    fn = job_description_service.extract_job_description_from_url
    source = inspect.getsource(fn)
    assert_true("requests.get" in source, "Manual extraction should contain the single user-triggered GET.")
    assert_true("timeout" in source, "Manual extraction must use a timeout.")

    source_adapter_dir = ROOT / "services" / "job_sources"
    extraction_refs = []
    for path in source_adapter_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "extract_job_description_from_url" in text:
            extraction_refs.append(str(path.relative_to(ROOT)))

    assert_true(
        not extraction_refs,
        "Job source adapters must not call manual URL extraction: " + ", ".join(extraction_refs),
    )
    print("manual URL extraction boundary: ok")


def main() -> None:
    test_imports()
    test_source_registry()
    test_source_adapter_static_safety()
    test_manual_url_extraction_boundary()
    print("release smoke: ok")


if __name__ == "__main__":
    main()
