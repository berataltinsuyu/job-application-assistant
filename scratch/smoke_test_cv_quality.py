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
    assert_true("character-spaced" in messages(report).lower(), "Character-spaced message missing.")


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
    assert_true(report["warning_count"] >= 1, "Phone split should be warned.")


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
    assert_true("Title field may contain organization text" in text, "Company-like title should be detected.")
    assert_true("Company field may contain a role title" in text, "Title-like company should be detected.")
    assert_true("Date appears inside company/title field" in text, "Date inside title/company should be detected.")


def test_domain_names_no_false_positives() -> None:
    # Company containing "Software" or "Technologies" should not trigger title mixing if it looks like a real company
    report = validate_cv_structure(
        {
            "contact": {"linkedin": "https://linkedin.com/in/example", "github": "https://github.com/example"},
            "experience": [
                {
                    "title": "Payment Systems Engineer",  # "Payment Systems" shouldn't trigger company warnings
                    "company": "Acme Software Solutions",  # "Software Solutions" shouldn't trigger title warnings
                    "bullets": ["Built backend APIs."],
                }
            ],
        }
    )
    text = messages(report)
    assert_true("Title field may contain organization text" not in text, "Payment Systems Engineer should not trigger company warning.")
    assert_true("Company field may contain a role title" not in text, "Acme Software Solutions should not trigger title warning.")
    assert_true(report["structure_score"] == 100, f"Clean structure should be 100, got: {report['structure_score']}. Issues: {text}")


def test_one_warning_score_reduction() -> None:
    # A single warning should only reduce the score slightly (e.g. 100 - 7 = 93)
    report = validate_cv_structure(
        {
            "contact": {"linkedin": "https://linkedin.com/in/example", "github": "https://github.com/example"},
            "experience": [
                {
                    "title": "Backend Developer",
                    "company": "Acme Corp 2024",  # triggers Date warning
                    "bullets": ["Built APIs."],
                }
            ],
        }
    )
    assert_true(report["structure_score"] == 93, f"Single warning score should be 93, got: {report['structure_score']}")


def test_suspicious_senior_claims() -> None:
    # Truthfulness warnings should flag "senior architect" claims
    report = analyze_cv_output_quality(
        "Candidate\nSenior Architect\nemail@example.com\n+1 555 555 5555\nRemote",
        {
            "contact": {
                "full_name": "Candidate",
                "target_title": "Senior Architect",
                "email": "email@example.com",
                "phone": "+1 555 555 5555",
                "location": "Remote",
            }
        },
    )
    text = messages(report)
    assert_true("Potentially unsupported senior claim detected" in text, f"Should detect senior claims in: {text}")
    assert_true(report["warning_count"] >= 1, "Should flag senior claim warning.")


def test_duplicate_social_swaps_detected() -> None:
    # Swapped socials should be flagged as critical
    report = validate_cv_structure(
        {
            "contact": {
                "linkedin": "https://github.com/example",
                "github": "https://linkedin.com/in/example",
            }
        }
    )
    text = messages(report)
    assert_true("LinkedIn/GitHub fields may be swapped" in text, f"Swapped socials should be detected in: {text}")


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
    assert_true(quality["quality_score"] >= 85, f"Clean CV quality too low: {quality}")
    assert_true(structure["structure_score"] >= 95, f"Clean CV structure too low: {structure}")


def main() -> None:
    test_character_spaced_name()
    test_duplicate_social_urls()
    test_linkedin_reused_as_github()
    test_split_phone_and_missing_email()
    test_title_company_swap_and_dates()
    test_domain_names_no_false_positives()
    test_one_warning_score_reduction()
    test_suspicious_senior_claims()
    test_duplicate_social_swaps_detected()
    test_clean_cv_high_score()
    print("cv quality smoke: ok")


if __name__ == "__main__":
    main()
