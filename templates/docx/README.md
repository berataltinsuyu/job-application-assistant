# Future DOCX Template Compatibility

This folder is reserved for future template-based DOCX rendering.

No external DOCX templates, downloaded assets, or font files are included in Phase 4A. Current CV exports still use the existing programmatic rendering pipeline.

Future template-based rendering may use placeholder replacement with a library such as `docxtpl`.

Planned placeholders:

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

Future templates should remain ATS-aware:

- Prefer one-column layouts.
- Avoid icons, embedded text boxes, images, and decorative tables for core CV content.
- Keep section labels readable and conventional.
- Preserve contact fields exactly as provided by the CV parsing and locked-field flow.
