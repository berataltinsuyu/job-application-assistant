import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from main import app
from services.ats_cv_schema import get_empty_ats_cv_schema

client = TestClient(app)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def valid_mock_cv() -> dict:
    cv = get_empty_ats_cv_schema()
    cv["contact"] = {
        "full_name": "Alex Candidate",
        "target_title": "Junior Backend Developer",
        "email": "alex@example.com",
        "phone": "+1 555 555 5555",
        "location": "Remote",
        "linkedin": "https://linkedin.com/in/alexcandidate",
        "github": "https://github.com/alexcandidate",
        "portfolio": ""
    }
    cv["professional_summary"] = "Junior backend developer with project-based Python, API, SQL, testing, and documentation experience."
    cv["career_objective"] = "To build reliable backend services and APIs."
    cv["technical_summary"] = "Python, SQL, REST APIs, FastAPI, Git, Docker."
    cv["skills"] = {
        "technical_skills": ["Python", "SQL"],
        "core_skills": ["REST APIs", "FastAPI"],
        "tools": ["Git", "Docker"],
        "databases": [],
        "cloud": [],
        "soft_skills": []
    }
    cv["experience"] = [
        {
            "company": "Example Software Studio",
            "role": "Backend Developer Intern",
            "location": "Remote",
            "start_date": "2025",
            "end_date": "2026",
            "bullets": [
                "Built REST API endpoints for internal demo services.",
                "Documented testing notes and integration behavior.",
            ],
        }
    ]
    cv["projects"] = [
        {
            "name": "API Tracker",
            "description": "Built a small API tracking project.",
            "technologies": ["Python", "FastAPI", "SQLite"],
            "bullets": ["Implemented endpoints, validation logic, and SQL queries."],
            "link": ""
        }
    ]
    cv["education"] = [
        {
            "school": "Example University",
            "degree": "BS Computer Engineering",
            "department": "",
            "start_date": "2021",
            "end_date": "2025",
            "details": []
        }
    ]
    cv["certifications"] = [{"name": "Python Foundations", "issuer": "Example Academy", "date": "2025", "link": ""}]
    cv["languages"] = [{"language": "English", "level": "Professional"}]
    cv["ats_metadata"] = {
        "target_role": "Junior Backend Developer",
        "target_company": "",
        "job_family": "Technology",
        "job_keywords_used": ["Python", "SQL"],
        "transferable_keywords_used": [],
        "missing_keywords": [],
        "risky_keywords_not_added": [],
        "ats_score_before": 50,
        "ats_score_after": 85,
        "optimization_summary": "Added tech stack detail.",
        "alignment_confidence": "high",
        "adaptation_notes": [],
        "ats_score_explanation": {
            "before_reason": "Minimal content.",
            "after_reason": "Included structured role keywords.",
            "improvement_reasons": [],
            "remaining_gaps": []
        }
    }
    return cv


def main() -> None:
    # 1. Test Catalog Endpoint
    catalog_res = client.get("/ats-cv/docx-templates")
    assert_true(catalog_res.status_code == 200, f"Catalog failed: {catalog_res.status_code}")
    catalog_data = catalog_res.json()
    assert_true("catalog" in catalog_data, "Catalog key not in response")
    
    templates = catalog_data["catalog"]
    expected_ids = {"ats_classic_docx", "ats_modern_docx"}
    catalog_ids = {t["template_id"] for t in templates}
    assert_true(expected_ids.issubset(catalog_ids), "Missing expected templates in catalog response")
    print("Catalog endpoint check: OK")

    # 2. Test Programmatic Export (Backward Compatibility)
    cv = valid_mock_cv()
    prog_payload = {
        "ats_cv_json": json.dumps(cv, ensure_ascii=False),
        "template_id": "classic_ats",
        "language": "English",
        "one_page": "false",
        "enabled_sections": "",
        "export_style": "standard",
        "docx_render_mode": "programmatic",
        "docx_template_id": ""
    }
    prog_res = client.post("/ats-cv/export-docx", data=prog_payload)
    assert_true(prog_res.status_code == 200, f"Programmatic export failed: {prog_res.status_code} - {prog_res.text}")
    assert_true(len(prog_res.content) > 0, "Programmatic export returned empty content")
    print("Programmatic export check: OK")

    # 3. Test Template Export (Modern)
    tpl_payload = {
        "ats_cv_json": json.dumps(cv, ensure_ascii=False),
        "template_id": "classic_ats",
        "language": "English",
        "one_page": "false",
        "enabled_sections": "",
        "export_style": "standard",
        "docx_render_mode": "template",
        "docx_template_id": "ats_modern_docx"
    }
    tpl_res = client.post("/ats-cv/export-docx", data=tpl_payload)
    assert_true(tpl_res.status_code == 200, f"Template export failed: {tpl_res.status_code} - {tpl_res.text}")
    assert_true(len(tpl_res.content) > 0, "Template export returned empty content")
    print("Template export (Modern) check: OK")

    # 4. Test Unknown Template Fallback Error Handling
    bad_payload = dict(tpl_payload)
    bad_payload["docx_template_id"] = "unknown_template_style"
    bad_res = client.post("/ats-cv/export-docx", data=bad_payload)
    assert_true(bad_res.status_code == 400, f"Expected 400 on unknown template, got {bad_res.status_code}")
    assert_true("fallback" in bad_res.json()["detail"].lower(), f"Unexpected error detail: {bad_res.json()['detail']}")
    print("Unknown template error check: OK")

    print("\nAll integration smoke tests passed successfully!")


if __name__ == "__main__":
    main()
