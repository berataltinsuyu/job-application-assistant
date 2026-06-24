import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.cv_quality_service import analyze_cv_output_quality, validate_cv_structure


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def messages(report: dict) -> str:
    return " | ".join(issue.get("message", "") for issue in report.get("issues", []))


def test_character_spaced_name() -> None:
    report = analyze_cv_output_quality(
        "B E R A T A L T I N S U Y U\nberat@example.com\n+90 555 555 55 55\nIstanbul",
        {"contact": {"email": "berat@example.com", "phone": "+90 555 555 55 55", "location": "Istanbul"}},
    )
    assert_true(report["critical_count"] >= 1, "Character-spaced name should be critical.")
    assert_true("character-spaced" in messages(report), "Character-spaced message missing.")


def test_duplicate_social_urls() -> None:
    text = "Email: a@example.com\nPhone: +1 555 555 5555\nLocation: Remote\nhttps://linkedin.com/in/example\nhttps://linkedin.com/in/example"
    report = analyze_cv_output_quality(
        text,
        {"contact": {"email": "a@example.com", "phone": "+1 555 555 5555", "location": "Remote", "linkedin": "https://linkedin.com/in/example"}},
    )
    assert_true(report["warning_count"] >= 1, "Duplicated LinkedIn should be warned.")


def test_linkedin_reused_as_github() -> None:
    report = analyze_cv_output_quality(
        "A Candidate\na@example.com\n+1 555 555 5555\nRemote",
        {
            "contact": {
                "email": "a@example.com",
                "phone": "+1 555 555 5555",
                "location": "Remote",
                "linkedin": "https://linkedin.com/in/example",
                "github": "https://linkedin.com/in/example",
            }
        },
    )
    assert_true(report["critical_count"] >= 1, "LinkedIn reused as GitHub should be critical.")


def test_split_phone_and_missing_email() -> None:
    report = analyze_cv_output_quality(
        "Candidate\n1 2 3 4 5 6 7 8 9 0\nRemote",
        {"contact": {"phone": "1 2 3 4 5 6 7 8 9 0", "location": "Remote"}},
    )
    assert_true(report["critical_count"] >= 1, "Missing email should be critical.")
    assert_true(report["warning_count"] >= 1, "Split phone should be warned.")


def test_title_company_swap_and_dates() -> None:
    report = validate_cv_structure(
        {
            "contact": {"linkedin": "https://linkedin.com/in/example", "github": "https://github.com/example"},
            "experience": [
                {
                    "title": "Example Technologies 2024",
                    "company": "Backend Developer Present",
                    "bullets": ["Built APIs."],
                }
            ],
        }
    )
    text = messages(report)
    assert_true(report["structure_score"] < 100, "Field-mixing issues should reduce structure score.")
    assert_true("title looks like a company" in text, "Company-like title should be detected.")
    assert_true("company looks like a job title" in text, "Title-like company should be detected.")
    assert_true("Date-like value" in text, "Date inside title/company should be detected.")


def test_clean_cv_high_score() -> None:
    structured = {
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
        "skills": {"programming": ["Python", "SQL"], "backend": ["REST API", "FastAPI"], "tools": ["Git"]},
        "experience": [
            {
                "title": "Backend Developer Intern",
                "company": "Example Software Studio",
                "start_date": "2025",
                "end_date": "2026",
                "bullets": ["Built REST API endpoints for demo services.", "Documented testing notes and integration behavior."],
            }
        ],
        "projects": [{"name": "API Tracker", "description": "Built a small API tracking project.", "bullets": ["Implemented endpoints and SQL queries."]}],
        "education": [{"school": "Example University", "degree": "BS Computer Engineering"}],
        "certifications": [{"name": "Python Foundations", "issuer": "Example Academy"}],
    }
    text = """
Alex Candidate
Junior Backend Developer
alex@example.com | +1 555 555 5555 | Remote
https://linkedin.com/in/alexcandidate | https://github.com/alexcandidate
Professional Summary
Junior backend developer with project-based Python, API, SQL, testing, and documentation experience.
Skills
Python, SQL, REST API, FastAPI, Git
Experience
- Built REST API endpoints for demo services.
- Documented testing notes and integration behavior.
Projects
- Implemented endpoints and SQL queries.
Education
Example University | BS Computer Engineering
"""
    quality = analyze_cv_output_quality(text, structured)
    structure = validate_cv_structure(structured)
    assert_true(quality["quality_score"] >= 80, f"Clean CV quality too low: {quality}")
    assert_true(structure["structure_score"] >= 90, f"Clean CV structure too low: {structure}")


def main() -> None:
    test_character_spaced_name()
    test_duplicate_social_urls()
    test_linkedin_reused_as_github()
    test_split_phone_and_missing_email()
    test_title_company_swap_and_dates()
    test_clean_cv_high_score()
    print("cv quality smoke: ok")


if __name__ == "__main__":
    main()
