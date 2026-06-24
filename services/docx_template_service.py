from copy import deepcopy
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


DOCX_TEMPLATE_DIR = Path("templates/docx")
GENERATED_TEMPLATE_DIR = DOCX_TEMPLATE_DIR / "generated"

DOCX_TEMPLATE_CATALOG = [
    {
        "template_id": "ats_classic_docx",
        "display_name": "ATS Classic DOCX",
        "description": "Programmatic one-column DOCX renderer with conservative ATS-friendly spacing and headings.",
        "ats_safety_level": "high",
        "visual_density": "medium",
        "supports_docx": True,
        "experimental": True,
    },
    {
        "template_id": "ats_modern_docx",
        "display_name": "ATS Modern DOCX",
        "description": "Programmatic one-column DOCX renderer with slightly stronger hierarchy and more whitespace.",
        "ats_safety_level": "high",
        "visual_density": "medium",
        "supports_docx": True,
        "experimental": True,
    },
]

SECTION_ORDER = [
    "professional_summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "languages",
]

SECTION_TITLES = {
    "professional_summary": "Professional Summary",
    "skills": "Skills",
    "experience": "Experience",
    "projects": "Projects",
    "education": "Education",
    "certifications": "Certifications",
    "languages": "Languages",
}


def ensure_builtin_docx_templates() -> list[dict]:
    """Create local generated sample DOCX files for the built-in renderer catalog."""
    GENERATED_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    sample_cv = {
        "contact": {
            "full_name": "Sample Candidate",
            "target_title": "Target Role",
            "email": "candidate@example.com",
            "phone": "+1 555 555 5555",
            "location": "Remote",
            "linkedin": "https://linkedin.com/in/sample",
            "github": "https://github.com/sample",
        },
        "professional_summary": "Short ATS-friendly summary generated locally by the built-in DOCX template service.",
        "skills": {"Core": ["Python", "SQL", "REST APIs"], "Tools": ["Git", "Docker"]},
        "experience": [
            {
                "title": "Example Role",
                "company": "Example Organization",
                "start_date": "2025",
                "end_date": "Present",
                "bullets": ["Rendered with python-docx only.", "No external template files are required."],
            }
        ],
        "education": [{"school": "Example University", "degree": "Example Degree"}],
    }
    catalog = get_docx_template_catalog()
    for template in catalog:
        output_path = GENERATED_TEMPLATE_DIR / f"{template['template_id']}_sample.docx"
        if not output_path.exists() or output_path.stat().st_size == 0:
            render_cv_with_docx_template(sample_cv, template["template_id"], str(output_path), {"sample": True})
    return catalog


def get_docx_template_catalog() -> list[dict]:
    return deepcopy(DOCX_TEMPLATE_CATALOG)


def render_cv_with_docx_template(
    structured_cv: dict,
    template_id: str,
    output_path: str,
    metadata: dict | None = None,
) -> dict:
    warnings: list[str] = []
    template = _get_template(template_id)
    if not template:
        return {
            "success": False,
            "template_id": template_id,
            "output_path": "",
            "warnings": [f"Unknown DOCX template_id: {template_id}"],
            "message": "Unknown DOCX template.",
        }

    if not isinstance(structured_cv, dict):
        return {
            "success": False,
            "template_id": template_id,
            "output_path": "",
            "warnings": ["structured_cv must be a dictionary."],
            "message": "Invalid structured CV.",
        }

    if not output_path:
        return {
            "success": False,
            "template_id": template_id,
            "output_path": "",
            "warnings": ["output_path is required."],
            "message": "Missing output path.",
        }

    try:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        document = Document()
        style = _style_for_template(template_id)
        _configure_document(document, style)
        _render_header(document, structured_cv, style)
        _render_sections(document, structured_cv, style)

        metadata = metadata if isinstance(metadata, dict) else {}
        if metadata:
            document.core_properties.comments = "Rendered by Job Application Assistant DOCX template service."

        document.save(str(destination))
        if not destination.exists() or destination.stat().st_size == 0:
            return {
                "success": False,
                "template_id": template_id,
                "output_path": "",
                "warnings": ["Rendered DOCX file was not created or is empty."],
                "message": "DOCX rendering failed.",
            }
        return {
            "success": True,
            "template_id": template_id,
            "output_path": str(destination),
            "warnings": warnings,
            "message": "DOCX rendered successfully.",
        }
    except Exception as exc:
        return {
            "success": False,
            "template_id": template_id,
            "output_path": "",
            "warnings": [str(exc)],
            "message": "DOCX rendering failed.",
        }


def _get_template(template_id: str) -> dict | None:
    for template in DOCX_TEMPLATE_CATALOG:
        if template["template_id"] == template_id:
            return deepcopy(template)
    return None


def _style_for_template(template_id: str) -> dict:
    if template_id == "ats_modern_docx":
        return {
            "margin": 0.72,
            "name_size": 19,
            "title_size": 11,
            "contact_size": 9,
            "body_size": 10.2,
            "heading_size": 11.5,
            "heading_space_before": 10,
            "heading_space_after": 2,
            "item_space_after": 3,
            "bullet_space_after": 1.6,
            "separator": True,
            "align_header": WD_ALIGN_PARAGRAPH.LEFT,
        }
    return {
        "margin": 0.62,
        "name_size": 17,
        "title_size": 10.5,
        "contact_size": 8.8,
        "body_size": 10,
        "heading_size": 10.8,
        "heading_space_before": 7,
        "heading_space_after": 1,
        "item_space_after": 1.5,
        "bullet_space_after": 0.8,
        "separator": True,
        "align_header": WD_ALIGN_PARAGRAPH.LEFT,
    }


def _configure_document(document: Document, style: dict) -> None:
    section = document.sections[0]
    margin = Inches(float(style["margin"]))
    section.top_margin = margin
    section.bottom_margin = margin
    section.left_margin = margin
    section.right_margin = margin

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Arial"
    normal_style.font.size = Pt(float(style["body_size"]))


def _render_header(document: Document, structured_cv: dict, style: dict) -> None:
    contact = _dict(structured_cv.get("contact"))
    full_name = _clean(contact.get("full_name"))
    target_title = _clean(contact.get("target_title"))
    contact_line = _contact_line(contact)

    if full_name:
        paragraph = document.add_paragraph()
        paragraph.alignment = style["align_header"]
        run = paragraph.add_run(full_name)
        run.bold = True
        run.font.size = Pt(float(style["name_size"]))

    if target_title:
        paragraph = document.add_paragraph()
        paragraph.alignment = style["align_header"]
        run = paragraph.add_run(target_title)
        run.bold = True
        run.font.size = Pt(float(style["title_size"]))

    if contact_line:
        paragraph = document.add_paragraph()
        paragraph.alignment = style["align_header"]
        run = paragraph.add_run(contact_line)
        run.font.size = Pt(float(style["contact_size"]))

    if full_name or target_title or contact_line:
        _add_separator(document, style)


def _render_sections(document: Document, structured_cv: dict, style: dict) -> None:
    for section_key in SECTION_ORDER:
        renderer = {
            "professional_summary": _summary_items,
            "skills": _skills_items,
            "experience": _experience_items,
            "projects": _project_items,
            "education": _education_items,
            "certifications": _certification_items,
            "languages": _language_items,
        }[section_key]
        items = renderer(structured_cv)
        if not items:
            continue
        _add_heading(document, SECTION_TITLES[section_key], style)
        for item in items:
            if item["type"] == "heading":
                _add_item_heading(document, item["text"], style)
            elif item["type"] == "bullet":
                _add_bullet(document, item["text"], style)
            else:
                _add_paragraph(document, item["text"], style)


def _add_heading(document: Document, text: str, style: dict) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(float(style["heading_space_before"]))
    paragraph.paragraph_format.space_after = Pt(float(style["heading_space_after"]))
    run = paragraph.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(float(style["heading_size"]))
    if style.get("separator"):
        _add_separator(document, style)


def _add_separator(document: Document, style: dict) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(float(style["heading_space_after"]))
    run = paragraph.add_run("_" * 72)
    run.font.size = Pt(5)


def _add_item_heading(document: Document, text: str, style: dict) -> None:
    if not text:
        return
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(float(style["item_space_after"]))
    run = paragraph.add_run(text)
    run.bold = True
    run.font.size = Pt(float(style["body_size"]))


def _add_paragraph(document: Document, text: str, style: dict) -> None:
    if not text:
        return
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(float(style["item_space_after"]))
    run = paragraph.add_run(text)
    run.font.size = Pt(float(style["body_size"]))


def _add_bullet(document: Document, text: str, style: dict) -> None:
    if not text:
        return
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(float(style["bullet_space_after"]))
    run = paragraph.add_run(text)
    run.font.size = Pt(float(style["body_size"]))


def _summary_items(structured_cv: dict) -> list[dict]:
    summary = _clean(
        structured_cv.get("professional_summary")
        or structured_cv.get("summary")
        or structured_cv.get("career_objective")
        or structured_cv.get("technical_summary")
    )
    return [{"type": "paragraph", "text": summary}] if summary else []


def _skills_items(structured_cv: dict) -> list[dict]:
    skills = structured_cv.get("skills") or structured_cv.get("technical_skills") or structured_cv.get("core_skills")
    items = []
    if isinstance(skills, dict):
        for category, values in skills.items():
            flattened = _flatten(values)
            if flattened:
                items.append({"type": "paragraph", "text": f"{_label(category)}: {', '.join(flattened)}"})
    else:
        flattened = _flatten(skills)
        if flattened:
            items.append({"type": "paragraph", "text": ", ".join(flattened)})
    return items


def _experience_items(structured_cv: dict) -> list[dict]:
    records = _list(structured_cv.get("experience")) + _list(structured_cv.get("internship_experience"))
    items = []
    for record in records:
        if not isinstance(record, dict):
            continue
        heading = _join_non_empty([
            record.get("title") or record.get("role") or record.get("position"),
            record.get("company") or record.get("organization"),
            record.get("location"),
            _date_range(record),
        ], " | ")
        if heading:
            items.append({"type": "heading", "text": heading})
        for bullet in _list(record.get("bullets")):
            items.append({"type": "bullet", "text": _clean(bullet)})
        description = _clean(record.get("description"))
        if description:
            items.append({"type": "paragraph", "text": description})
    return items


def _project_items(structured_cv: dict) -> list[dict]:
    items = []
    for record in _list(structured_cv.get("projects")):
        if not isinstance(record, dict):
            continue
        heading = _join_non_empty([record.get("name") or record.get("title"), _date_range(record)], " | ")
        if heading:
            items.append({"type": "heading", "text": heading})
        technologies = _flatten(record.get("technologies"))
        if technologies:
            items.append({"type": "paragraph", "text": f"Technologies: {', '.join(technologies)}"})
        description = _clean(record.get("description"))
        if description:
            items.append({"type": "paragraph", "text": description})
        for bullet in _list(record.get("bullets")):
            items.append({"type": "bullet", "text": _clean(bullet)})
    return items


def _education_items(structured_cv: dict) -> list[dict]:
    items = []
    for record in _list(structured_cv.get("education")):
        if not isinstance(record, dict):
            continue
        heading = _join_non_empty([
            record.get("school") or record.get("institution") or record.get("university"),
            record.get("degree"),
            record.get("department") or record.get("field"),
            _date_range(record),
        ], " | ")
        if heading:
            items.append({"type": "heading", "text": heading})
        for detail in _list(record.get("details")):
            items.append({"type": "bullet", "text": _clean(detail)})
    return items


def _certification_items(structured_cv: dict) -> list[dict]:
    items = []
    for record in _list(structured_cv.get("certifications")):
        if not isinstance(record, dict):
            continue
        line = _join_non_empty([
            record.get("name") or record.get("certification"),
            record.get("issuer") or record.get("organization"),
            record.get("date"),
            record.get("link"),
        ], " | ")
        if line:
            items.append({"type": "paragraph", "text": line})
    return items


def _language_items(structured_cv: dict) -> list[dict]:
    items = []
    for record in _list(structured_cv.get("languages")):
        if isinstance(record, dict):
            line = _join_non_empty([record.get("language"), record.get("level")], " - ")
        else:
            line = _clean(record)
        if line:
            items.append({"type": "paragraph", "text": line})
    return items


def _contact_line(contact: dict) -> str:
    return _join_non_empty([
        contact.get("email"),
        contact.get("phone"),
        contact.get("location"),
        contact.get("linkedin"),
        contact.get("github"),
        contact.get("portfolio"),
    ], " | ")


def _date_range(record: dict) -> str:
    return _join_non_empty([
        record.get("start_date") or record.get("start"),
        record.get("end_date") or record.get("end"),
    ], " - ")


def _join_non_empty(values: list[Any], separator: str) -> str:
    return separator.join(_clean(value) for value in values if _clean(value))


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _flatten(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    if isinstance(value, dict):
        flattened = []
        for nested in value.values():
            flattened.extend(_flatten(nested))
        return flattened
    if isinstance(value, str):
        return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    return []


def _label(value: Any) -> str:
    return _clean(value).replace("_", " ").title()
