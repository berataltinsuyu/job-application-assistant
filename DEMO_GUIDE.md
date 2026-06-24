# Demo Guide

This guide is for a short live presentation of the Job Application Assistant.

## Start

1. Start the backend:

```bash
venv/bin/python -m uvicorn main:app --reload
```

2. Start Streamlit:

```bash
venv/bin/streamlit run streamlit_app.py
```

3. Optional: seed local demo data:

```bash
venv/bin/python scratch/seed_demo_data.py
```

## Demo Steps

1. Open Streamlit and show the six-page sidebar: Dashboard, Job Workspace, ATS CV Builder, CV Tools, Application Materials, History.
2. Upload a CV in the sidebar.
3. Paste a job description, or open "Extract from URL" and click Extract for one user-provided URL.
4. Explain that extraction is manual, single-request, and falls back to paste if blocked.
5. Open Job Workspace.
6. In Search Profiles, create a profile with role families, suggested keywords, custom keywords, and `manual_mock`.
7. Run the profile and show mock jobs.
8. In Add Job, manually add a job. Keep simple fields visible and advanced fields collapsed.
9. In Jobs, expand a job card, rescore or analyze it, and review the intelligence report.
10. Update pipeline stage, priority, next action, and notes.
11. Generate Tailored CV.
12. Generate Cover Letter.
13. Generate Application Email.
14. Preview and download generated assets.
15. Open History and show previous outputs.

## What To Say

- "The app uses one global CV and one global job description across the workspace."
- "Job Workspace is the main operational screen: search profiles, manual import, source settings, pipeline, and assets are all in one place."
- "Only `manual_mock` is runnable as a source today. `manual_import` is manual-only, and real job-board sources are disabled placeholders."
- "Manual URL extraction is allowed only when the user clicks Extract for a single URL. It is not crawling or monitoring."
- "Generated materials are drafts and should be reviewed before sending."

## Known Limitations

- Real job-board scraping is not implemented.
- Some websites block manual extraction; paste the job description manually when that happens.
- Gemini-backed generation requires `GEMINI_API_KEY`.
- Scores are estimates, not official ATS results.

## Troubleshooting

- Backend not reachable: confirm `uvicorn` is running at `http://127.0.0.1:8000`.
- Streamlit cannot call API: check `API_BASE_URL` in `.env` or sidebar/runtime config.
- AI generation fails: verify `GEMINI_API_KEY`.
- No jobs visible: run `scratch/seed_demo_data.py`, add a manual job, or run a `manual_mock` Search Profile.
- No assets visible: upload a CV, open a job, and generate materials from the expanded job card.

## Safety Note

Manual URL extraction performs one user-triggered request for one pasted URL. The app does not crawl search results, fetch monitored job URLs automatically, bypass login/CAPTCHA/Cloudflare, use browser automation, or use proxies/evasion.
