import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.ats_cv_postprocessing import clean_structured_cv_before_export
from services.ats_cv_schema import get_empty_ats_cv_schema
from services.ats_cv_export_service import build_plain_text_preview, render_ats_cv_to_docx, render_ats_cv_to_pdf
from services.ats_cv_templates import get_ats_cv_template


def run_tests():
    print("==================================================")
    print("Running Structured CV Data Cleanup Smoke Tests")
    print("==================================================")

    # 1. Initialize schema fixture
    cv = get_empty_ats_cv_schema()
    cv["contact"]["full_name"] = "Alice Developer"

    # A. Company/title cleanup fixtures
    cv["experience"] = [
        {
            "role": "Backend Developer Intern",
            "company": "Example Software Studio - Backend Developer Intern",
            "start_date": "2023-06",
            "end_date": "2023-09",
            "description": "Developing features.",
            "bullets": [],
        },
        {
            "role": "Product Analyst",
            "company": "Product Analyst | Acme Games",
            "start_date": "2022-01",
            "end_date": "2022-12",
            "description": "Analyzing products.",
            "bullets": [],
        },
        {
            "role": "Software Engineer",
            "company": "Acme Software",
            "start_date": "2021-01",
            "end_date": "2021-12",
            "description": "Writing code.",
            "bullets": [],
        },
        {
            "role": "Payment Systems Application Development Intern",
            "company": "Example Bank – Payment Systems Application Development Intern",
            "start_date": "2023-09",
            "end_date": "2024-06",
            "description": "Developing banking systems.",
            "bullets": [],
        }
    ]

    # B. Project cleanup fixtures
    cv["projects"] = [
        {
            "name": "Demo Project (GitHub",
            "description": "Cool web project",
            "technologies": ["Python"],
            "bullets": [],
        },
        {
            "name": "API Platform (GitHub Link",
            "description": "Secure APIs",
            "technologies": ["Go"],
            "bullets": [],
        },
        {
            "name": "Data Tool (Repository",
            "description": "Processing data",
            "technologies": ["Rust"],
            "bullets": [],
        },
        {
            "name": "Another Project |",
            "description": "Dangling sep",
            "technologies": ["JS"],
            "bullets": [],
        }
    ]

    # C. Certification cleanup fixtures
    cv["certifications"] = [
        {
            "name": "Data Analytics Essentials — Cisco (Certificate | Google",
            "issuer": "Cisco",
            "date": "2022",
            "link": "",
        },
        {
            "name": "Some Course (Certificate | Some Issuer",
            "issuer": "Some Issuer",
            "date": "2023",
            "link": "",
        },
        {
            "name": "Cloud Fundamentals (Certification | Provider",
            "issuer": "Provider",
            "date": "2023",
            "link": "",
        },
        {
            "name": "Google Data Analytics Certificate — Google",
            "issuer": "Google",
            "date": "2023",
            "link": "",
        },
        # Duplicate test
        {
            "name": "Cloud Fundamentals (Certification | Provider",
            "issuer": "Provider",
            "date": "2023",
            "link": "http://example.com/cert", # Better formed record (has link)
        }
    ]

    # 2. Run clean_structured_cv_before_export
    cleaned_cv = clean_structured_cv_before_export(cv)

    # 3. Assertions
    print("\n--- Running Assertions on Structured Data ---\n")

    # A. Company/title assertions
    exp = cleaned_cv["experience"]
    print(f"Company 1: '{exp[0]['company']}' (Expected: 'Example Software Studio')")
    assert exp[0]["company"] == "Example Software Studio"

    print(f"Company 2: '{exp[1]['company']}' (Expected: 'Acme Games')")
    assert exp[1]["company"] == "Acme Games"

    print(f"Company 3: '{exp[2]['company']}' (Expected: 'Acme Software' - unchanged)")
    assert exp[2]["company"] == "Acme Software"

    print(f"Company 4: '{exp[3]['company']}' (Expected: 'Example Bank')")
    assert exp[3]["company"] == "Example Bank"

    # B. Project assertions
    proj = cleaned_cv["projects"]
    print(f"Project 1: '{proj[0]['name']}' (Expected: 'Demo Project (GitHub)')")
    assert proj[0]["name"] == "Demo Project (GitHub)"

    print(f"Project 2: '{proj[1]['name']}' (Expected: 'API Platform (GitHub Link)')")
    assert proj[1]["name"] == "API Platform (GitHub Link)"

    print(f"Project 3: '{proj[2]['name']}' (Expected: 'Data Tool (Repository)')")
    assert proj[2]["name"] == "Data Tool (Repository)"

    print(f"Project 4: '{proj[3]['name']}' (Expected: 'Another Project')")
    assert proj[3]["name"] == "Another Project"

    # C. Certification assertions
    certs = cleaned_cv["certifications"]
    for c in certs:
        print(f"Cert: name='{c['name']}', issuer='{c['issuer']}'")
        assert "(Certificate |" not in c["name"]
        assert "(Certification |" not in c["name"]
        assert "(Cert |" not in c["name"]

    # We expect 4 certifications after deduplication (duplicates merged/selected best)
    print(f"Total certifications count: {len(certs)} (Expected: 4)")
    assert len(certs) == 4

    # The better-formed Cloud Fundamentals (with link) should have been kept
    cloud_cert = next(c for c in certs if "Cloud Fundamentals" in c["name"])
    print(f"Cloud Cert link: '{cloud_cert.get('link')}' (Expected: 'http://example.com/cert')")
    assert cloud_cert.get("link") == "http://example.com/cert"

    # D. Export preview & render asserts
    print("\n--- Running Assertions on Render Output ---\n")
    template = get_ats_cv_template("classic_ats")
    text_preview = build_plain_text_preview(cleaned_cv, template, "English")
    print("Generated Text Preview:")
    print("-" * 40)
    print(text_preview)
    print("-" * 40)

    # Check text preview content
    assert "Example Software Studio - Backend Developer Intern" not in text_preview
    assert "Example Bank – Payment Systems" not in text_preview
    assert "Google Data Analytics Certificate — Google | Google" not in text_preview
    assert "Some Course (Certificate" not in text_preview
    assert "Cloud Fundamentals (Certification" not in text_preview

    # Test PDF rendering (smoketest to make sure it doesn't crash)
    pdf_bytes = render_ats_cv_to_pdf(cleaned_cv, template, "English")
    print(f"PDF bytes size: {len(pdf_bytes)} bytes")
    assert len(pdf_bytes) > 0

    # Test DOCX rendering (smoketest to make sure it doesn't crash)
    docx_bytes = render_ats_cv_to_docx(cleaned_cv, template, "English")
    print(f"DOCX bytes size: {len(docx_bytes)} bytes")
    assert len(docx_bytes) > 0

    print("\nAll structured CV cleanup tests passed successfully!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
