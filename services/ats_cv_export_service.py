from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Inches, Pt
from fastapi import HTTPException
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


SECTION_TITLES = {
    "English": {
        "professional_summary": "Professional Summary",
        "career_objective": "Career Objective",
        "technical_summary": "Technical Summary",
        "skills": "Skills",
        "core_skills": "Core Skills",
        "technical_skills": "Technical Skills",
        "experience": "Experience",
        "internship_experience": "Internship Experience",
        "projects": "Projects",
        "education": "Education",
        "certifications": "Certifications",
        "languages": "Languages",
    },
    "Turkish": {
        "professional_summary": "Profesyonel Özet",
        "career_objective": "Kariyer Hedefi",
        "technical_summary": "Teknik Özet",
        "skills": "Yetenekler",
        "core_skills": "Temel Yetkinlikler",
        "technical_skills": "Teknik Yetenekler",
        "experience": "Deneyim",
        "internship_experience": "Staj Deneyimi",
        "projects": "Projeler",
        "education": "Eğitim",
        "certifications": "Sertifikalar",
        "languages": "Diller",
    },
}

PDF_FONT_NAME = "Helvetica"
PDF_BOLD_FONT_NAME = "Helvetica-Bold"


def render_ats_cv_to_docx(ats_cv: dict, template: dict, language: str) -> bytes:
    try:
        document = Document()
        _configure_docx(document)
        template_style = _template_style(template)

        contact = render_contact(ats_cv, language)
        if contact["full_name"]:
            paragraph = document.add_paragraph()
            run = paragraph.add_run(contact["full_name"])
            run.bold = True
            run.font.size = Pt(18)

        if contact["target_title"]:
            paragraph = document.add_paragraph()
            run = paragraph.add_run(contact["target_title"])
            run.bold = True
            run.font.size = Pt(11)

        if contact["contact_line"]:
            document.add_paragraph(contact["contact_line"])

        for section in _ordered_sections(ats_cv, template, language):
            _add_docx_section(document, section, template_style, language)

        output = BytesIO()
        document.save(output)
        return output.getvalue()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(exc)}") from exc


def render_ats_cv_to_pdf(ats_cv: dict, template: dict, language: str) -> bytes:
    try:
        _register_pdf_fonts()
        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
        )
        styles = _pdf_styles()
        template_style = _template_style(template)
        story = []

        contact = render_contact(ats_cv, language)
        if contact["full_name"]:
            story.append(Paragraph(escape(contact["full_name"]), styles["Name"]))
        if contact["target_title"]:
            story.append(Paragraph(escape(contact["target_title"]), styles["TargetTitle"]))
        if contact["contact_line"]:
            story.append(Paragraph(escape(contact["contact_line"]), styles["Contact"]))
        if story:
            story.append(Spacer(1, 0.16 * inch))

        for section in _ordered_sections(ats_cv, template, language):
            story.append(Spacer(1, template_style["pdf_section_spacing"]))
            story.append(Paragraph(escape(_heading_text(section["heading"], language)), styles["SectionHeading"]))
            if template_style["heading_separator"]:
                story.append(Paragraph("________________________________________", styles["Separator"]))
            for item in section["items"]:
                if item["type"] == "paragraph":
                    story.append(Paragraph(escape(item["text"]), styles["Body"]))
                elif item["type"] == "heading":
                    story.append(Paragraph(escape(item["text"]), styles["ItemHeading"]))
                elif item["type"] == "bullet":
                    story.append(Paragraph(f"- {escape(item['text'])}", styles["Bullet"]))
            story.append(Spacer(1, template_style["pdf_section_after_spacing"]))

        document.build(story)
        return output.getvalue()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(exc)}") from exc


def build_plain_text_preview(ats_cv: dict, template: dict, language: str) -> str:
    contact = render_contact(ats_cv, language)
    lines = []

    if contact["full_name"]:
        lines.append(contact["full_name"])
    if contact["target_title"]:
        lines.append(contact["target_title"])
    if contact["contact_line"]:
        lines.append(contact["contact_line"])

    for section in _ordered_sections(ats_cv, template, language):
        if lines:
            lines.append("")
        lines.append(_heading_text(section["heading"], language))
        if _template_style(template)["heading_separator"]:
            lines.append("-" * len(_heading_text(section["heading"], language)))
        for item in section["items"]:
            if item["type"] == "bullet":
                lines.append(f"- {item['text']}")
            else:
                lines.append(item["text"])

    return "\n".join(lines).strip()


def render_contact(ats_cv: dict, language: str) -> dict:
    contact = ats_cv.get("contact", {}) if isinstance(ats_cv, dict) else {}
    contact_parts = []
    for key in ["email", "phone", "location", "linkedin", "github", "portfolio"]:
        value = _clean_text(contact.get(key))
        if value:
            contact_parts.append(value)

    return {
        "full_name": _clean_text(contact.get("full_name")),
        "target_title": _clean_text(contact.get("target_title")),
        "contact_line": " | ".join(contact_parts),
    }


def render_summary(ats_cv: dict, language: str, section_key: str = "professional_summary") -> dict | None:
    value = _clean_text(ats_cv.get(section_key))
    if not value:
        return None
    return {
        "key": section_key,
        "heading": _section_title(section_key, language),
        "items": [{"type": "paragraph", "text": value}],
    }


def render_skills(ats_cv: dict, language: str, section_key: str = "skills") -> dict | None:
    skills = ats_cv.get("skills", {})
    if not isinstance(skills, dict):
        return None

    items = []
    if section_key in {"technical_skills", "core_skills"}:
        skill_groups = [section_key]
    else:
        skill_groups = ["technical_skills", "core_skills", "tools", "databases", "cloud", "soft_skills"]

    single_group_section = section_key in {"technical_skills", "core_skills"}

    for group in skill_groups:
        values = _clean_list(skills.get(group, []))
        if values:
            text = ", ".join(values) if single_group_section else f"{_skill_group_title(group, language)}: {', '.join(values)}"
            items.append({
                "type": "paragraph",
                "text": text,
            })

    if not items:
        return None

    return {
        "key": "skills",
        "heading": _section_title(section_key, language),
        "items": items,
    }


def render_experience(ats_cv: dict, language: str, section_key: str = "experience") -> dict | None:
    records = ats_cv.get("experience", [])
    if not isinstance(records, list):
        return None

    items = []
    for record in records:
        if not isinstance(record, dict):
            continue
        heading = _join_non_empty([
            record.get("role"),
            record.get("company"),
            record.get("location"),
            _date_range(record.get("start_date"), record.get("end_date")),
        ])
        bullets = _clean_list(record.get("bullets", []))
        if heading:
            items.append({"type": "heading", "text": heading})
        for bullet in bullets:
            items.append({"type": "bullet", "text": bullet})

    if not items:
        return None

    return {
        "key": "experience",
        "heading": _section_title(section_key, language),
        "items": items,
    }


def render_projects(ats_cv: dict, language: str) -> dict | None:
    records = ats_cv.get("projects", [])
    if not isinstance(records, list):
        return None

    items = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = _clean_text(record.get("name"))
        description = _clean_text(record.get("description"))
        technologies = _clean_list(record.get("technologies", []))
        bullets = _clean_list(record.get("bullets", []))
        link = _clean_text(record.get("link"))

        if name:
            items.append({"type": "heading", "text": name})
        if description:
            items.append({"type": "paragraph", "text": description})
        if technologies:
            label = "Technologies" if _language_key(language) == "English" else "Teknolojiler"
            items.append({"type": "paragraph", "text": f"{label}: {', '.join(technologies)}"})
        for bullet in bullets:
            items.append({"type": "bullet", "text": bullet})
        if link:
            items.append({"type": "paragraph", "text": link})

    if not items:
        return None

    return {
        "key": "projects",
        "heading": _section_title("projects", language),
        "items": items,
    }


def render_education(ats_cv: dict, language: str) -> dict | None:
    records = ats_cv.get("education", [])
    if not isinstance(records, list):
        return None

    items = []
    for record in records:
        if not isinstance(record, dict):
            continue
        heading = _join_non_empty([
            record.get("school"),
            record.get("degree"),
            record.get("department"),
            _date_range(record.get("start_date"), record.get("end_date")),
        ])
        details = _clean_list(record.get("details", []))
        if heading:
            items.append({"type": "heading", "text": heading})
        for detail in details:
            items.append({"type": "bullet", "text": detail})

    if not items:
        return None

    return {
        "key": "education",
        "heading": _section_title("education", language),
        "items": items,
    }


def render_certifications(ats_cv: dict, language: str) -> dict | None:
    records = ats_cv.get("certifications", [])
    if not isinstance(records, list):
        return None

    items = []
    for record in records:
        if not isinstance(record, dict):
            continue
        line = _join_non_empty([
            record.get("name"),
            record.get("issuer"),
            record.get("date"),
            record.get("link"),
        ])
        if line:
            items.append({"type": "bullet", "text": line})

    if not items:
        return None

    return {
        "key": "certifications",
        "heading": _section_title("certifications", language),
        "items": items,
    }


def render_languages(ats_cv: dict, language: str) -> dict | None:
    records = ats_cv.get("languages", [])
    if not isinstance(records, list):
        return None

    items = []
    for record in records:
        if not isinstance(record, dict):
            continue
        line = _join_non_empty([record.get("language"), record.get("level")], separator=" - ")
        if line:
            items.append({"type": "bullet", "text": line})

    if not items:
        return None

    return {
        "key": "languages",
        "heading": _section_title("languages", language),
        "items": items,
    }


def _ordered_sections(ats_cv: dict, template: dict, language: str) -> list[dict]:
    sections = []
    used_keys = set()

    for section_key in template.get("section_order", []):
        section = _render_section_by_key(ats_cv, language, section_key)
        if section and section["key"] not in used_keys:
            sections.append(section)
            used_keys.add(section["key"])

    return sections


def _render_section_by_key(ats_cv: dict, language: str, section_key: str) -> dict | None:
    if section_key in {"contact", "title"}:
        return None
    if section_key in {"professional_summary", "career_objective", "technical_summary"}:
        return render_summary(ats_cv, language, section_key)
    if section_key in {"skills", "core_skills", "technical_skills"}:
        return render_skills(ats_cv, language, section_key)
    if section_key in {"experience", "internship_experience"}:
        return render_experience(ats_cv, language, section_key)
    if section_key == "projects":
        return render_projects(ats_cv, language)
    if section_key == "education":
        return render_education(ats_cv, language)
    if section_key == "certifications":
        return render_certifications(ats_cv, language)
    if section_key == "languages":
        return render_languages(ats_cv, language)
    return None


def _configure_docx(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Arial"
    normal_style.font.size = Pt(10.5)


def _add_docx_section(document: Document, section: dict, template_style: dict, language: str) -> None:
    heading = document.add_paragraph()
    heading.paragraph_format.space_before = Pt(template_style["docx_section_space_before"])
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run(_heading_text(section["heading"], language))
    run.bold = True
    run.font.size = Pt(11)

    if template_style["heading_separator"]:
        separator = document.add_paragraph()
        separator.paragraph_format.space_after = Pt(3)
        separator.add_run("-" * 48)

    for item in section["items"]:
        if item["type"] == "heading":
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(1)
            run = paragraph.add_run(item["text"])
            run.bold = True
        elif item["type"] == "bullet":
            paragraph = document.add_paragraph(style="List Bullet")
            paragraph.paragraph_format.space_after = Pt(1)
            paragraph.add_run(item["text"])
        else:
            paragraph = document.add_paragraph(item["text"])
            paragraph.paragraph_format.space_after = Pt(2)


def _register_pdf_fonts() -> None:
    global PDF_FONT_NAME, PDF_BOLD_FONT_NAME

    if PDF_FONT_NAME != "Helvetica":
        return

    regular_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    bold_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    regular_path = _first_existing_path(regular_paths)
    bold_path = _first_existing_path(bold_paths)

    if regular_path:
        pdfmetrics.registerFont(TTFont("ATSCVFont", regular_path))
        PDF_FONT_NAME = "ATSCVFont"

    if bold_path:
        pdfmetrics.registerFont(TTFont("ATSCVFont-Bold", bold_path))
        PDF_BOLD_FONT_NAME = "ATSCVFont-Bold"
    elif regular_path:
        PDF_BOLD_FONT_NAME = "ATSCVFont"


def _pdf_styles() -> dict:
    styles = getSampleStyleSheet()
    return {
        "Name": ParagraphStyle(
            "ATSName",
            parent=styles["Normal"],
            fontName=PDF_BOLD_FONT_NAME,
            fontSize=17,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=3,
        ),
        "TargetTitle": ParagraphStyle(
            "ATSTargetTitle",
            parent=styles["Normal"],
            fontName=PDF_BOLD_FONT_NAME,
            fontSize=10.5,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=3,
        ),
        "Contact": ParagraphStyle(
            "ATSContact",
            parent=styles["Normal"],
            fontName=PDF_FONT_NAME,
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
            spaceAfter=5,
        ),
        "SectionHeading": ParagraphStyle(
            "ATSSectionHeading",
            parent=styles["Normal"],
            fontName=PDF_BOLD_FONT_NAME,
            fontSize=10.5,
            leading=13,
            alignment=TA_LEFT,
            spaceBefore=7,
            spaceAfter=3,
        ),
        "Separator": ParagraphStyle(
            "ATSSeparator",
            parent=styles["Normal"],
            fontName=PDF_FONT_NAME,
            fontSize=7,
            leading=8,
            spaceAfter=3,
        ),
        "ItemHeading": ParagraphStyle(
            "ATSItemHeading",
            parent=styles["Normal"],
            fontName=PDF_BOLD_FONT_NAME,
            fontSize=9.5,
            leading=12,
            spaceBefore=2,
            spaceAfter=1,
        ),
        "Body": ParagraphStyle(
            "ATSBody",
            parent=styles["Normal"],
            fontName=PDF_FONT_NAME,
            fontSize=9.3,
            leading=12,
            spaceAfter=2,
        ),
        "Bullet": ParagraphStyle(
            "ATSBullet",
            parent=styles["Normal"],
            fontName=PDF_FONT_NAME,
            fontSize=9.3,
            leading=12,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=1,
        ),
    }


def _language_key(language: str) -> str:
    return "Turkish" if str(language).lower() == "turkish" else "English"


def _section_title(section_key: str, language: str) -> str:
    lang = _language_key(language)
    return SECTION_TITLES[lang].get(section_key, section_key.replace("_", " ").title())


def _heading_text(text: str, language: str) -> str:
    if _language_key(language) == "Turkish":
        return text.translate(str.maketrans({"i": "İ", "ı": "I"})).upper()
    return text.upper()


def _skill_group_title(group: str, language: str) -> str:
    titles = {
        "English": {
            "technical_skills": "Technical Skills",
            "core_skills": "Core Skills",
            "tools": "Tools",
            "databases": "Databases",
            "cloud": "Cloud",
            "soft_skills": "Soft Skills",
        },
        "Turkish": {
            "technical_skills": "Teknik Yetenekler",
            "core_skills": "Temel Yetkinlikler",
            "tools": "Araçlar",
            "databases": "Veritabanları",
            "cloud": "Bulut",
            "soft_skills": "Sosyal Beceriler",
        },
    }
    return titles[_language_key(language)].get(group, group.replace("_", " ").title())


def _clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_list(values) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_clean_text(value) for value in values if _clean_text(value)]


def _join_non_empty(values, separator: str = " | ") -> str:
    return separator.join(_clean_text(value) for value in values if _clean_text(value))


def _date_range(start_date, end_date) -> str:
    return _join_non_empty([start_date, end_date], separator=" - ")


def _first_existing_path(paths: list[str]) -> str:
    for path in paths:
        if Path(path).exists():
            return path
    return ""


def _template_style(template: dict) -> dict:
    template_id = template.get("id", "classic_ats")
    styles = {
        "classic_ats": {
            "docx_section_space_before": 8,
            "pdf_section_spacing": 0,
            "pdf_section_after_spacing": 0.10 * inch,
            "heading_separator": False,
        },
        "modern_clean": {
            "docx_section_space_before": 12,
            "pdf_section_spacing": 0.05 * inch,
            "pdf_section_after_spacing": 0.14 * inch,
            "heading_separator": True,
        },
        "technical_developer": {
            "docx_section_space_before": 7,
            "pdf_section_spacing": 0,
            "pdf_section_after_spacing": 0.08 * inch,
            "heading_separator": False,
        },
        "junior_internship": {
            "docx_section_space_before": 7,
            "pdf_section_spacing": 0,
            "pdf_section_after_spacing": 0.09 * inch,
            "heading_separator": False,
        },
    }
    return styles.get(template_id, styles["classic_ats"])
