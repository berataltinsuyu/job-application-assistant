# Job Application Assistant

An AI-assisted job application workspace for reviewing a CV against a job description, tracking applications, and generating application materials. The project uses a FastAPI backend with a consolidated Streamlit UI.

The current UI has six main pages:

- Dashboard
- Job Workspace
- ATS CV Builder
- CV Tools
- Application Materials
- History

## Key Features

- Global CV upload reused across ATS CV Builder, CV Tools, Application Materials, and Job Workspace material generation.
- Global job description input with optional safe manual URL extraction.
- Job Workspace for manual job import, search profiles, source settings, job scoring, job intelligence, pipeline notes, and generated assets.
- Safe Source Adapter Foundation with `manual_mock`, `manual_import`, and disabled placeholders for future real sources.
- ATS CV Builder with locked contact fields, preview, and DOCX/PDF/TXT exports.
- CV Tools for CV analysis, ATS score, improvement suggestions, and section rewrite.
- Application Materials for cover letters, application emails, interview prep, and personalized interview questions.
- History page for reviewing and deleting previous AI outputs.

## Architecture Overview

- `main.py`: FastAPI application setup and router registration.
- `routers/`: HTTP API routes for CV analysis, ATS CV generation, job monitoring, manual URL extraction, and history.
- `services/`: Business logic for AI prompts, source registry, manual URL extraction, job monitoring, scoring, asset generation, and exports.
- `services/job_sources/`: Safe job source adapter registry. Phase 3A contains only a runnable mock adapter.
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
5. Open Job Workspace.
6. Create or use a Search Profile with `manual_mock`.
7. Add a job manually in Add Job.
8. Analyze the job and review match/intelligence details.
9. Update pipeline stage, priority, next action, and notes.
10. Generate a tailored CV, cover letter, and application email.
11. Preview/download generated assets.
12. Review outputs in History.

Optional demo data:

```bash
venv/bin/python scratch/seed_demo_data.py
```

The demo seed is idempotent, uses fictional data, does not call Gemini, and does not fetch URLs.

## Phase Summary

- Phase 2A-2E: Job Workspace foundation, manual import, scoring, intelligence, pipeline, generated assets, preview/download, and consolidated Streamlit navigation.
- Phase 3A: Safe Job Source Adapter Foundation with source settings persistence, registry validation, cooldown metadata, safe run orchestration, and a Sources tab.
- Final Demo Polish: Demo seed helper, release smoke test, presentation guide, clearer dashboard workflow, and refined empty states.

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
venv/bin/python scratch/seed_demo_data.py
```

`scratch/smoke_test_release.py` is offline and does not require Gemini or network access.

## Future Roadmap

- Add reviewed, terms-aware source adapters only after a safety review.
- Improve generated asset templates and export formatting.
- Add richer filtering and pipeline reporting.
- Add optional notification or scheduling workflows only with explicit user controls and strict rate limits.
