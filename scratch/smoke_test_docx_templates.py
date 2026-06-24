import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.docx_template_service import (  # noqa: E402
    ensure_builtin_docx_templates,
    get_docx_template_catalog,
    render_cv_with_docx_template,
)


OUTPUT_DIR = ROOT / "scratch" / "generated_docx_tests"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def simple_structured_cv() -> dict:
    return {
        "contact": {
            "full_name": "Alex Candidate",
            "target_title": "Junior Backend Developer",
            "email": "alex@example.com",
            "phone": "+1 555 555 5555",
            "location": "Remote",
            "linkedin": "https://linkedin.com/in/alexcandidate",
            "github": "https://github.com/alexcandidate",
        },
        "professional_summary": "Junior backend developer with project-based Python, API, SQL, testing, and documentation experience.",
        "skills": {
            "Programming": ["Python", "SQL"],
            "Backend": ["REST APIs", "FastAPI"],
            "Tools": ["Git", "Docker"],
        },
        "experience": [
            {
                "title": "Backend Developer Intern",
                "company": "Example Software Studio",
                "location": "Remote",
                "start_date": "2025",
                "end_date": "2026",
                "bullets": [
                    "Built REST API endpoints for internal demo services.",
                    "Documented testing notes and integration behavior.",
                ],
            }
        ],
        "projects": [
            {
                "name": "API Tracker",
                "technologies": ["Python", "FastAPI", "SQLite"],
                "description": "Built a small API tracking project.",
                "bullets": ["Implemented endpoints, validation logic, and SQL queries."],
            }
        ],
        "education": [
            {
                "school": "Example University",
                "degree": "BS Computer Engineering",
                "start_date": "2021",
                "end_date": "2025",
            }
        ],
        "certifications": [{"name": "Python Foundations", "issuer": "Example Academy", "date": "2025"}],
        "languages": [{"language": "English", "level": "Professional"}],
    }


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ensured = ensure_builtin_docx_templates()
    catalog = get_docx_template_catalog()
    ensured_ids = {item["template_id"] for item in ensured}
    catalog_ids = {item["template_id"] for item in catalog}
    expected_ids = {"ats_classic_docx", "ats_modern_docx"}

    assert_true(expected_ids.issubset(ensured_ids), "ensure_builtin_docx_templates missing expected templates.")
    assert_true(expected_ids.issubset(catalog_ids), "get_docx_template_catalog missing expected templates.")

    cv = simple_structured_cv()
    for template_id in sorted(expected_ids):
        output_path = OUTPUT_DIR / f"{template_id}.docx"
        result = render_cv_with_docx_template(
            structured_cv=cv,
            template_id=template_id,
            output_path=str(output_path),
            metadata={"smoke_test": True},
        )
        assert_true(result["success"] is True, f"{template_id} render failed: {result}")
        assert_true(output_path.exists(), f"{template_id} output file was not created.")
        assert_true(output_path.stat().st_size > 0, f"{template_id} output file is empty.")

    unknown_result = render_cv_with_docx_template(
        structured_cv=cv,
        template_id="unknown_template",
        output_path=str(OUTPUT_DIR / "unknown.docx"),
    )
    assert_true(unknown_result["success"] is False, "Unknown template should return success=false.")
    assert_true("Unknown" in unknown_result["message"], "Unknown template failure should be clean.")

    print("docx template smoke: ok")


if __name__ == "__main__":
    main()
