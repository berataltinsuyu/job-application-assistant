# Job Application Assistant

AI-assisted job application document generator that turns a CV and job description into ATS-friendly tailored CVs, cover letters, recruiter emails, and interview prep materials. The project uses a FastAPI backend with a consolidated Streamlit UI.

The current UI has six main pages:

- Dashboard
- Job Prep Workspace
- ATS CV Builder
- CV Tools
- Application Materials
- History

## Key Features

- Global CV upload reused across ATS CV Builder, CV Tools, Application Materials, and Job Prep Workspace material generation.
- Global job description input with optional safe manual URL extraction.
- Job Prep Workspace for adding a posting, scoring fit, reviewing job intelligence, generating tailored application materials, and optionally keeping status notes.
- Advanced mock/source tools with `manual_mock`, `manual_import`, and disabled placeholders for future real sources.
- ATS CV Builder with locked contact fields, preview, and DOCX/PDF/TXT exports.
- CV Quality Check and Structure Validation for generated ATS/tailored CVs.
- Adaptation Level controls: Conservative, Balanced, and Strong.
- CV Tools for CV analysis, ATS score, improvement suggestions, and section rewrite.
- Application Materials for cover letters, application emails, interview prep, and personalized interview questions.
- History page for reviewing and deleting previous AI outputs.

## Architecture Overview

- `main.py`: FastAPI application setup and router registration.
- `routers/`: HTTP API routes for CV analysis, ATS CV generation, job monitoring, manual URL extraction, and history.
- `services/`: Business logic for AI prompts, source registry, manual URL extraction, job monitoring, scoring, asset generation, and exports.
- `services/job_sources/`: Safe job source adapter registry. Phase 3A contains only a runnable mock adapter.
- `services/cv_quality_service.py`: Deterministic quality and structure checks for generated CV output.
- `models.py`: SQLAlchemy models for history, source settings, monitored jobs, intelligence reports, pipeline records, and generated assets.
- `database.py`: SQLite session setup and compatibility migrations.
- `streamlit_app.py`: Consolidated six-page Streamlit UI.
- `scratch/`: Local smoke tests and demo utilities.

## Tech Stack

- Python
- FastAPI
- Streamlit
- SQLAlchemy
- SQLite
- Google Gemini API for AI-generated analysis/materials
- python-docx / reportlab / PyMuPDF-related export helpers
- requests and BeautifulSoup for the manual, user-triggered URL extraction flow only

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
```

Create a `.env` file when using AI features:

```bash
GEMINI_API_KEY=your_api_key_here
API_BASE_URL=http://127.0.0.1:8000
```

`GEMINI_API_KEY` is required for AI generation. Local source registry checks, demo seeding, and release smoke tests do not require Gemini.

## Run Backend

```bash
venv/bin/python -m uvicorn main:app --reload
```

Backend default URL:

```text
http://127.0.0.1:8000
```

## Run Streamlit

```bash
venv/bin/streamlit run streamlit_app.py
```

Streamlit default URL:

```text
http://localhost:8501
```

## Demo Flow

1. Start the backend.
2. Start Streamlit.
3. Upload a CV in the sidebar.
4. Paste a job description, or open the collapsed "Extract from URL" helper and click Extract for one user-provided URL.
5. Open Job Prep Workspace.
6. Add the target posting manually in Add Job.
7. Analyze the job and review match/intelligence details.
8. Generate a tailored CV, cover letter, and application email.
9. Use Application Materials for interview prep.
10. Review CV quality warnings and structure validation.
11. Preview/download generated assets.
12. Optionally use advanced mock search, source settings, or pipeline notes for demos/testing.
13. Review outputs in History.

Optional demo data:

```bash
venv/bin/python scratch/seed_demo_data.py
```

The demo seed is idempotent, uses fictional data, does not call Gemini, and does not fetch URLs.

## Phase Summary

- Phase 2A-2E: Job Prep Workspace foundation, manual import, scoring, intelligence, optional pipeline notes, generated assets, preview/download, and consolidated Streamlit navigation.
- Phase 3A: Safe Job Source Adapter Foundation with source settings persistence, registry validation, cooldown metadata, safe run orchestration, and a Sources tab.
- Final Demo Polish: Demo seed helper, release smoke test, presentation guide, clearer dashboard workflow, and refined empty states.
- Phase 4A: CV quality checker, structure validator, adaptation-level controls, cleaner generated CV filenames, richer template metadata, and a future DOCX template placeholder folder.
- Phase 4B-1: Standalone DOCX template service foundation with local `python-docx` renderers.
- Phase 4B-2: Template DOCX UI Integration in both the ATS CV Builder page and the Job Prep Workspace tailored CV generation workflow. Programmatic DOCX remains the default and fallback. Built-in templates: ATS Classic DOCX and ATS Modern DOCX generated completely locally.
- Phase 4C: Visual Polish & Preview Guidance for the built-in DOCX templates (Classic vs Modern), rendering layout corrections, interactive template select guidelines in the UI, and CV quality/structure validation tuning to minimize false positives and guardrail adaptation levels against fake claims.



## Job Sources

Current sources:

- `manual_mock`: enabled, runnable, local mock data only.
- `manual_import`: enabled, manual-only, not runnable as a monitoring source.

Disabled placeholders:

- `company_careers_placeholder`
- `techcareer_placeholder`
- `youthall_placeholder`
- `linkedin_placeholder`
- `kariyer_placeholder`

Placeholders are disabled and `not_implemented`. They cannot run or fetch external URLs.

## Manual URL Extraction

The app supports safe manual URL extraction:

- The user pastes one job posting URL.
- The user explicitly clicks Extract.
- The backend performs one normal HTTP GET with a timeout.
- If readable HTML is available, extracted text can populate the global job description or manual import description.
- If the page is blocked, unsupported, non-HTML, or unavailable, the UI shows a clean fallback asking the user to paste manually.

This is not crawling, monitoring, or job-board scraping.

## CV Quality And Adaptation

Generated ATS and tailored CV outputs now include deterministic review metadata:

- CV Quality Check flags contact corruption, missing contact fields, overly long summaries, repeated sections, weak bullets, dense skill lines, and suspicious senior/exaggerated claims.
- Structure Validation flags likely title/company swaps, date text inside title/company fields, school/degree mixing, social URL platform mismatches, duplicated skills, and related field-mixing risks.
- Adaptation Level controls how assertively the CV is tailored:
  - Conservative: minimal repositioning and safest wording.
  - Balanced: default, uses truthful transferable framing.
  - Strong: more ATS-focused wording while still forbidding invented facts.

Generated CV filenames are lowercase and readable, for example `ats_cv_modern_clean_20260624_164012.pdf` or `tailored_cv_classic_ats_20260624_164012.pdf`.

The folder `templates/docx/` is reserved for future DOCX placeholder rendering. Phase 4B-1 adds local built-in DOCX rendering foundations generated programmatically with `python-docx`, but does not add UI controls, external DOCX templates, designer templates, or font files.

## Safety Policy

- No real job board scraping is implemented.
- Search Profile source adapters do not fetch LinkedIn, Kariyer.net, Techcareer, Youthall, Indeed, company career pages, or other job-board URLs.
- Job URLs are stored as text unless the user explicitly uses the manual URL extraction helper.
- No browser automation is used for job extraction.
- No login bypass, CAPTCHA bypass, Cloudflare bypass, proxy, evasion, or hidden background scheduler is implemented.
- Source adapters must explicitly declare whether they fetch external URLs.
- Future adapters should only be added after reviewing public access, robots.txt, source terms, and rate limits.

## Current Limitations

- Real job-board adapters are placeholders only.
- AI generation requires a configured Gemini API key.
- Manual URL extraction can fail on protected or script-heavy pages; paste the description manually in that case.
- Quality checks are heuristic and deterministic; they help review generated CVs but do not replace human proofreading.
- The future DOCX template folder is a compatibility foundation only, not a final template rendering system.
- ATS and match scores are helpful estimates, not official employer ATS results.
- Generated materials should be reviewed by the user before use.

## Validation

Compile:

```bash
venv/bin/python -m compileall services routers streamlit_app.py main.py models.py database.py
```

Regression and release checks:

```bash
venv/bin/python scratch/smoke_test_2e_regression.py
venv/bin/python scratch/smoke_test_2e_fixes.py
venv/bin/python scratch/smoke_test_release.py
venv/bin/python scratch/smoke_test_cv_quality.py
venv/bin/python scratch/smoke_test_cv_export_qa.py
venv/bin/python scratch/seed_demo_data.py
```

`scratch/smoke_test_release.py` and `scratch/smoke_test_cv_export_qa.py` are offline and do not require Gemini or network access.
The export QA covers DOCX (programmatic and templates), ReportLab PDF, TXT, filename validation, and metadata compatibility checks.

To perform manual testing with a real CV and job description, follow the checklist in [USER_TEST_CHECKLIST.md](file:///Users/berataltinsuyu/Desktop/job-application-assistant/USER_TEST_CHECKLIST.md).

## Future Roadmap

- Add reviewed, terms-aware source adapters only after a safety review.
- Improve generated asset templates and export formatting.
- Add richer filtering and optional status-note reporting.
- Add optional notification or scheduling workflows only with explicit user controls and strict rate limits.
