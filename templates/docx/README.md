# DOCX Templates and Visual Styles

This directory acts as the reference boundary and local storage for built-in DOCX template files.

No external templates, downloaded font files, or binary packaging dependencies are required. All template rendering is compiled dynamically on-the-fly via the local `python-docx` service foundation.

## Built-In Templates

### 1. ATS Classic DOCX (`ats_classic_docx`)
*   **Aesthetic:** Compact, traditional, conservative layout. Left-aligned header.
*   **ATS Safety:** Maximum safety level. Single-column, strict section boundaries, clear text separators.
*   **Best For:** Banking, corporate IT, finance, operations, backend development, and traditional enterprise submissions.
*   **Visual Style:** Strict text-first layout, conventional Pt sizing (Pt 16 for name, Pt 10.5 for target title, Pt 9 for contact details, and Pt 10 body text), thin custom separators.

### 2. ATS Modern DOCX (`ats_modern_docx`)
*   **Aesthetic:** Modern, centered, elegant layout with improved whitespace distribution.
*   **ATS Safety:** High safety level. Single-column flow, native paragraph borders, clean bullet dividers (` • `).
*   **Best For:** Startups, software engineering, machine learning/AI roles, data science, product design, and creative tech submissions.
*   **Visual Style:** Balanced spacing (Pt 20 name, Pt 11 target title, Pt 9 contact details, and Pt 10 body text), thin light-gray separators, and centered contact coordinates.

---

## Technical Configuration

Placeholder rendering coordinates map directly to standard JSON keys parsed by the service:

```text
{{FULL_NAME}}
{{TARGET_TITLE}}
{{EMAIL}}
{{PHONE}}
{{LOCATION}}
{{LINKEDIN}}
{{GITHUB}}
{{PORTFOLIO}}
{{SUMMARY}}
{{SKILLS}}
{{EXPERIENCE}}
{{PROJECTS}}
{{EDUCATION}}
{{CERTIFICATIONS}}
{{LANGUAGES}}
```

All templates are restricted to single-column, table-free core content layouts to ensure flawless parsing by automated talent acquisition systems.
