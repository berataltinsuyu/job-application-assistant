import json
import os
import sys
import uuid
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from main import app
from models import JobApplicationAsset
from services.job_application_asset_service import serialize_asset
from services.docx_template_service import render_cv_with_docx_template, get_docx_template_catalog
from services.ats_cv_schema import get_empty_ats_cv_schema
from docx import Document

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


# Recreate Streamlit's local helper functions to verify metadata extraction works without crash
def unwrap_asset_structured_json(asset: dict) -> dict:
    structured = asset.get("structured_json") if isinstance(asset, dict) else {}
    return structured if isinstance(structured, dict) else {}


def get_asset_quality_report(asset: dict) -> dict:
    structured = unwrap_asset_structured_json(asset)
    return structured.get("quality_report") if isinstance(structured.get("quality_report"), dict) else {}


def get_asset_structure_report(asset: dict) -> dict:
    structured = unwrap_asset_structured_json(asset)
    return structured.get("structure_report") if isinstance(structured.get("structure_report"), dict) else {}


def test_ats_cv_builder_exports() -> None:
    cv = valid_mock_cv()
    payload = {
        "ats_cv_json": json.dumps(cv, ensure_ascii=False),
        "template_id": "classic_ats",
        "language": "English",
        "one_page": "false",
        "enabled_sections": "",
        "export_style": "standard",
    }

    # 1. Programmatic DOCX
    p_docx_payload = dict(payload)
    p_docx_payload["docx_render_mode"] = "programmatic"
    res = client.post("/ats-cv/export-docx", data=p_docx_payload)
    assert_true(res.status_code == 200, f"Programmatic DOCX failed: {res.status_code}")
    assert_true(len(res.content) > 0, "Programmatic DOCX empty")

    # 2. Template DOCX - Classic
    t_classic_payload = dict(payload)
    t_classic_payload["docx_render_mode"] = "template"
    t_classic_payload["docx_template_id"] = "ats_classic_docx"
    res = client.post("/ats-cv/export-docx", data=t_classic_payload)
    assert_true(res.status_code == 200, f"Template DOCX Classic failed: {res.status_code}")
    assert_true(len(res.content) > 0, "Template DOCX Classic empty")

    # 3. Template DOCX - Modern
    t_modern_payload = dict(payload)
    t_modern_payload["docx_render_mode"] = "template"
    t_modern_payload["docx_template_id"] = "ats_modern_docx"
    res = client.post("/ats-cv/export-docx", data=t_modern_payload)
    assert_true(res.status_code == 200, f"Template DOCX Modern failed: {res.status_code}")
    assert_true(len(res.content) > 0, "Template DOCX Modern empty")

    # 4. PDF Export (offline supported via ReportLab)
    res = client.post("/ats-cv/export-pdf", data=payload)
    assert_true(res.status_code == 200, f"PDF export failed: {res.status_code}")
    assert_true(len(res.content) > 0, "PDF export empty")

    # 5. TXT Export
    res = client.post("/ats-cv/export-txt", data=payload)
    assert_true(res.status_code == 200, f"TXT export failed: {res.status_code}")
    assert_true(len(res.content) > 0, "TXT export empty")

    # 6. Unknown Template ID returns clean error
    bad_payload = dict(payload)
    bad_payload["docx_render_mode"] = "template"
    bad_payload["docx_template_id"] = "unknown_template_style"
    res = client.post("/ats-cv/export-docx", data=bad_payload)
    assert_true(res.status_code == 400, f"Expected 400 on unknown template, got {res.status_code}")
    assert_true("fallback" in res.json()["detail"].lower(), "Traceback/unclean error exposed")


def test_generated_asset_compatibility() -> None:
    # Verify we can serialize an asset and that helpers extract report safely.
    # 1. Simulate an asset with full metadata
    meta = {
        "quality_report": {
            "quality_score": 90,
            "issues": [],
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "summary": "Looks clean."
        },
        "structure_report": {
            "structure_score": 95,
            "issues": []
        },
        "adaptation_level": "strong",
        "docx_render_mode": "template",
        "docx_template_id": "ats_modern_docx"
    }

    mock_db_asset = JobApplicationAsset(
        id=123,
        job_id=1,
        asset_type="tailored_cv",
        title="Tailored CV",
        content_text="Mock plain text content",
        structured_json=json.dumps(meta),
        file_path="generated_assets/tailored_cv_ats_modern_docx_20260624_120000.docx",
        export_format="docx",
        template_id="ats_modern_docx",
        language="English",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    serialized = serialize_asset(mock_db_asset)
    assert_true(serialized["structured_json"] == meta, "Metadata serialization mismatch")

    # Test helpers on new asset dict
    q_rep = get_asset_quality_report(serialized)
    s_rep = get_asset_structure_report(serialized)
    assert_true(q_rep.get("quality_score") == 90, "Failed to get quality score from metadata")
    assert_true(s_rep.get("structure_score") == 95, "Failed to get structure score from metadata")

    # 2. Simulate old asset without new metadata keys
    old_meta = {
        "target_role": "Backend Engineer",
        "ats_score_before": 45
    }
    mock_db_asset_old = JobApplicationAsset(
        id=124,
        job_id=1,
        asset_type="tailored_cv",
        title="Old Tailored CV",
        content_text="Mock old content",
        structured_json=json.dumps(old_meta),
        file_path="generated_assets/tailored_cv_old.docx",
        export_format="docx",
        created_at=datetime.utcnow()
    )
    serialized_old = serialize_asset(mock_db_asset_old)
    q_rep_old = get_asset_quality_report(serialized_old)
    s_rep_old = get_asset_structure_report(serialized_old)
    assert_true(q_rep_old == {}, "Old asset quality report should be empty dictionary")
    assert_true(s_rep_old == {}, "Old asset structure report should be empty dictionary")

    # 3. Simulate asset with invalid JSON string in db
    mock_db_asset_invalid = JobApplicationAsset(
        id=125,
        job_id=1,
        asset_type="tailored_cv",
        structured_json="invalid { json",
        created_at=datetime.utcnow()
    )
    serialized_invalid = serialize_asset(mock_db_asset_invalid)
    assert_true(serialized_invalid["structured_json"] is None, "Invalid JSON should serialize to None")
    assert_true(get_asset_quality_report(serialized_invalid) == {}, "Invalid JSON quality report should be empty")
    assert_true(get_asset_structure_report(serialized_invalid) == {}, "Invalid JSON structure report should be empty")


def test_filename_validation() -> None:
    # Import filename generator helpers
    from services.job_application_asset_service import _cv_asset_filename
    from routers.ats_cv_builder import _cv_export_filename

    names = [
        _cv_asset_filename("Tailored CV", "Ats Modern Docx", "docx"),
        _cv_export_filename("ATS CV", "Classic ATS", "pdf")
    ]

    for name in names:
        assert_true(name == name.lower(), f"Filename must be lowercase: {name}")
        assert_true(" " not in name, f"Filename must not contain spaces: {name}")
        # check pattern
        assert_true(name.startswith("tailored_cv_") or name.startswith("ats_cv_"), f"Unexpected prefix: {name}")
        # check safe chars
        assert_true(re.match(r"^[a-z0-9_\.]+$", name) is not None, f"Invalid characters in filename: {name}")
        # check no personal name
        assert_true("alex" not in name and "candidate" not in name, f"Filename contains candidate name: {name}")


def test_file_content_sanity() -> None:
    # Render with docx templates to temporary files, and check their content
    os.makedirs("scratch", exist_ok=True)
    cv = valid_mock_cv()
    
    classic_temp = f"scratch/test_sanity_classic_{uuid.uuid4().hex}.docx"
    modern_temp = f"scratch/test_sanity_modern_{uuid.uuid4().hex}.docx"

    try:
        # Render Classic
        res_classic = render_cv_with_docx_template(
            structured_cv=cv,
            template_id="ats_classic_docx",
            output_path=classic_temp
        )
        assert_true(res_classic["success"], f"Classic render failed: {res_classic}")

        # Render Modern
        res_modern = render_cv_with_docx_template(
            structured_cv=cv,
            template_id="ats_modern_docx",
            output_path=modern_temp
        )
        assert_true(res_modern["success"], f"Modern render failed: {res_modern}")

        # Read contents with python-docx and do sanity checks
        for temp_file in (classic_temp, modern_temp):
            doc = Document(temp_file)
            full_text = []
            for p in doc.paragraphs:
                full_text.append(p.text)
            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        full_text.append(cell.text)
            
            combined_text = "\n".join(full_text)
            
            # 1. Non-empty readable text
            assert_true(len(combined_text.strip()) > 50, f"File {temp_file} has insufficient text")
            assert_true("Alex Candidate" in combined_text, f"Candidate name missing from {temp_file}")
            
            # 2. Contact fields are not character-spaced
            assert_true("A l e x" not in combined_text, f"Contact field is character-spaced: {combined_text}")
            
            # 3. LinkedIn/GitHub remain exact
            assert_true("https://linkedin.com/in/alexcandidate" in combined_text, f"LinkedIn URL corrupted: {combined_text}")
            assert_true("https://github.com/alexcandidate" in combined_text, f"GitHub URL corrupted: {combined_text}")
            
            # 4. No empty repeated section headings
            # Section headers should not be repeated or blank
            headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading") or p.text.isupper()]
            non_empty_headings = [h.strip() for h in headings if h.strip()]
            assert_true(len(headings) == len(non_empty_headings), f"Found empty section headings: {headings}")

    finally:
        for f in (classic_temp, modern_temp):
            if os.path.exists(f):
                os.remove(f)


if __name__ == "__main__":
    print("Running QA Export and Preview tests...")
    test_ats_cv_builder_exports()
    print("ATS CV Builder exports: PASS")
    test_generated_asset_compatibility()
    print("Generated asset compatibility: PASS")
    test_filename_validation()
    print("Filename validation: PASS")
    test_file_content_sanity()
    print("File content sanity checks: PASS")
    print("\nAll QA export and preview stability tests completed successfully!")
