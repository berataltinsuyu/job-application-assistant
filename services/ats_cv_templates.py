from copy import deepcopy


ATS_CV_TEMPLATES = [
    {
        "id": "classic_ats",
        "template_id": "classic_ats",
        "name": "Classic ATS",
        "display_name": "Classic ATS",
        "description": (
            "A safe, single-column ATS-friendly resume template suitable for corporate, "
            "banking, IT, backend, business analyst, and general professional applications."
        ),
        "style_level": "classic",
        "ats_safety_level": "high",
        "supports_one_page": True,
        "supports_docx": True,
        "supports_pdf": True,
        "supports_txt": True,
        "supports_photo": False,
        "visual_density": "medium",
        "recommended_use_cases": [
            "General ATS-safe applications",
            "Corporate and banking roles",
            "Junior and internship applications",
        ],
        "best_for": [
            "corporate",
            "banking",
            "IT",
            "backend",
            "business analyst",
            "ERP",
            "internship",
            "junior roles",
        ],
        "section_order": [
            "contact",
            "professional_summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
            "languages",
        ],
        "ats_notes": [
            "Uses a one-column structure for predictable ATS parsing.",
            "Avoids icons, graphics, and tables that can confuse resume scanners.",
            "Uses clear headings and standard sections.",
            "Keeps content in a keyword-friendly layout for job-specific optimization.",
        ],
    },
    {
        "id": "modern_clean",
        "template_id": "modern_clean",
        "name": "Modern Clean",
        "display_name": "Modern Clean",
        "description": (
            "A clean and professional one-column CV template with slightly more modern "
            "spacing while remaining ATS compatible."
        ),
        "style_level": "modern",
        "ats_safety_level": "high",
        "supports_one_page": True,
        "supports_docx": True,
        "supports_pdf": True,
        "supports_txt": True,
        "supports_photo": False,
        "visual_density": "medium",
        "recommended_use_cases": [
            "Technology roles",
            "Business analyst roles",
            "Modern but conservative applications",
        ],
        "best_for": [
            "software developer",
            "business analyst",
            "product",
            "IT specialist",
            "corporate applications",
            "technology roles",
        ],
        "section_order": [
            "contact",
            "title",
            "professional_summary",
            "core_skills",
            "experience",
            "projects",
            "education",
            "certifications",
            "languages",
        ],
        "ats_notes": [
            "Keeps a one-column structure with clean spacing.",
            "Avoids icons, graphics, and tables.",
            "Uses clear headings and standard sections for scanner compatibility.",
            "Supports a keyword-friendly layout while keeping a modern presentation.",
        ],
    },
    {
        "id": "technical_developer",
        "template_id": "technical_developer",
        "name": "Technical Developer",
        "display_name": "Technical Developer",
        "description": (
            "An ATS-friendly developer-focused CV template that highlights technical "
            "skills and projects before work experience."
        ),
        "style_level": "technical",
        "ats_safety_level": "high",
        "supports_one_page": True,
        "supports_docx": True,
        "supports_pdf": True,
        "supports_txt": True,
        "supports_photo": False,
        "visual_density": "high",
        "recommended_use_cases": [
            "Backend and frontend developer roles",
            "API and software engineering roles",
            "Project-heavy technical applications",
        ],
        "best_for": [
            "backend developer",
            "frontend developer",
            "full-stack developer",
            "software engineer",
            "API developer",
            "junior developer",
            "intern developer",
        ],
        "section_order": [
            "contact",
            "technical_summary",
            "technical_skills",
            "projects",
            "experience",
            "education",
            "certifications",
            "languages",
        ],
        "ats_notes": [
            "Uses a one-column structure that preserves reading order.",
            "Avoids icons, graphics, and tables that can reduce ATS accuracy.",
            "Uses clear technical headings and standard resume sections.",
            "Places technical keywords and project evidence where scanners can read them easily.",
        ],
    },
    {
        "id": "junior_internship",
        "template_id": "junior_internship",
        "name": "Junior / Internship Focus",
        "display_name": "Junior / Internship Focus",
        "description": (
            "An ATS-friendly CV template for students, interns, fresh graduates, and "
            "junior candidates. It highlights education, technical skills, projects, "
            "and internship experience."
        ),
        "style_level": "compact",
        "ats_safety_level": "high",
        "supports_one_page": True,
        "supports_docx": True,
        "supports_pdf": True,
        "supports_txt": True,
        "supports_photo": False,
        "visual_density": "medium",
        "recommended_use_cases": [
            "Internship applications",
            "Fresh graduate applications",
            "Education and project-led profiles",
        ],
        "best_for": [
            "internship",
            "fresh graduate",
            "junior developer",
            "student",
            "trainee",
            "new graduate",
        ],
        "section_order": [
            "contact",
            "career_objective",
            "education",
            "technical_skills",
            "projects",
            "internship_experience",
            "certifications",
            "languages",
        ],
        "ats_notes": [
            "Uses a one-column structure for reliable ATS parsing.",
            "Avoids icons, graphics, and tables.",
            "Uses clear headings and standard sections tailored to junior profiles.",
            "Prioritizes education, skills, and projects for keyword-friendly matching.",
        ],
    },
    {
        "id": "modern_professional",
        "template_id": "modern_professional",
        "name": "Modern Professional",
        "display_name": "Modern Professional",
        "description": (
            "A polished general-purpose ATS-friendly one-column CV template with stronger "
            "header hierarchy, thin section rules, and professional spacing."
        ),
        "style_level": "visual",
        "ats_safety_level": "high",
        "supports_one_page": True,
        "supports_docx": True,
        "supports_pdf": True,
        "supports_txt": True,
        "supports_photo": False,
        "visual_density": "medium",
        "recommended_use_cases": [
            "Product roles",
            "Business analyst roles",
            "Corporate IT roles",
            "Business roles",
            "New graduate applications",
        ],
        "best_for": [
            "product roles",
            "business analyst",
            "corporate IT",
            "business roles",
            "operations",
            "junior professional",
            "new graduate",
        ],
        "section_order": [
            "contact",
            "title",
            "professional_summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
            "languages",
        ],
        "ats_notes": [
            "Keeps the main CV body in one column.",
            "Uses text-based headings and thin rules instead of icons or graphics.",
            "Preserves standard section names and reading order for ATS compatibility.",
            "Best reviewed as DOCX/PDF before submission because it is more visually styled.",
        ],
    },
    {
        "id": "compact_technical",
        "template_id": "compact_technical",
        "name": "Compact Technical",
        "display_name": "Compact Technical",
        "description": (
            "A compact, technical, ATS-safe CV template with dense but readable "
            "spacing, strong section rules, and clear skills/project emphasis."
        ),
        "style_level": "technical",
        "ats_safety_level": "high",
        "supports_one_page": True,
        "supports_docx": True,
        "supports_pdf": True,
        "supports_txt": True,
        "supports_photo": False,
        "visual_density": "high",
        "recommended_use_cases": [
            "Backend developer roles",
            "Software engineering roles",
            "Data and AI technical roles",
            "ATS-heavy submissions",
        ],
        "best_for": [
            "backend developer",
            "software engineer",
            "data engineer",
            "AI engineer",
            "API developer",
            "technical internship",
        ],
        "section_order": [
            "contact",
            "technical_summary",
            "technical_skills",
            "projects",
            "experience",
            "education",
            "certifications",
            "languages",
        ],
        "ats_notes": [
            "Uses compact one-column structure for ATS parsing.",
            "Places technical skills and projects high in the document.",
            "Avoids icons, text boxes, decorative tables, and multi-column body content.",
            "Suitable when content needs to fit into a concise technical CV.",
        ],
    },
    {
        "id": "visual_photo_optional",
        "template_id": "visual_photo_optional",
        "name": "Visual Photo Optional",
        "display_name": "Visual Photo Optional",
        "description": (
            "A polished one-column CV template with optional modest header photo support "
            "for local/Turkish/corporate submissions where photo CVs are acceptable."
        ),
        "style_level": "visual",
        "ats_safety_level": "medium",
        "supports_one_page": True,
        "supports_docx": True,
        "supports_pdf": True,
        "supports_txt": True,
        "supports_photo": True,
        "visual_density": "medium",
        "recommended_use_cases": [
            "Turkish/local applications",
            "Corporate roles where photo CVs are accepted",
            "More visual but still structured submissions",
        ],
        "best_for": [
            "Turkish applications",
            "local corporate roles",
            "photo-acceptable submissions",
            "visual professional CVs",
        ],
        "section_order": [
            "contact",
            "title",
            "professional_summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
            "languages",
        ],
        "ats_notes": [
            "Photo support is optional and disabled by default.",
            "Main content remains one-column and text-based.",
            "Use the photo only where the target market or employer accepts photo CVs.",
            "For strict ATS or photo-blind processes, export without photo.",
        ],
    },
]


def get_ats_cv_templates() -> list[dict]:
    """Return all predefined ATS CV templates."""
    return deepcopy(ATS_CV_TEMPLATES)


def get_ats_cv_template(template_id: str) -> dict:
    """Return one ATS CV template by id."""
    for template in ATS_CV_TEMPLATES:
        if template["id"] == template_id:
            return deepcopy(template)

    valid_ids = ", ".join(template["id"] for template in ATS_CV_TEMPLATES)
    raise ValueError(f"ATS CV template '{template_id}' was not found. Valid templates: {valid_ids}.")


def validate_template_id(template_id: str) -> bool:
    """Return True when template_id matches a predefined ATS CV template."""
    return any(template["id"] == template_id for template in ATS_CV_TEMPLATES)
