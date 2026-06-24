# USER TEST CHECKLIST

This checklist provides a guide for validating the Job Application Assistant with a real CV and job description, focused on generating tailored application materials.

## 1. Setup
- [ ] Start the FastAPI backend: `venv/bin/python main.py`
- [ ] Start the Streamlit application: `streamlit run streamlit_app.py`
- [ ] Open the app in your browser (usually `http://localhost:8501`).
- [ ] Upload your base CV (PDF or DOCX format) in the sidebar.
- [ ] Paste or extract your target job description in the sidebar (or try extracting from a URL).

## 2. ATS CV Builder Test
- [ ] Navigate to the **ATS CV Builder** page.
- [ ] Generate an optimized CV with **Conservative** adaptation level. Check that wording is safely restricted to directly supported facts.
- [ ] Generate an optimized CV with **Balanced** adaptation level. Check that transferable skills are used.
- [ ] Generate an optimized CV with **Strong** adaptation level. Check that the wording is confident but does not invent senior roles.
- [ ] Export as **Programmatic DOCX**. Verify the export matches expectations.
- [ ] Export as **Template DOCX Classic** and **Template DOCX Modern**. Verify layout structures.
- [ ] Export as **PDF**. Check visual rendering.
- [ ] Export as **TXT**. Check content hierarchy.
- [ ] Inspect the **CV Quality Score** and **Structure Validation** panels. Check that warnings make sense and score calculation is correct.

## 3. Job Prep Workspace Test
- [ ] Navigate to the **Job Prep Workspace** page.
- [ ] Go to the **Add Job** tab and add a job manually.
- [ ] Switch to the **Jobs** tab, click **Analyze**, and verify the match score.
- [ ] Expand the job card and generate a **Tailored CV as PDF**.
- [ ] Generate a **Tailored CV as DOCX Programmatic** and **Tailored CV as DOCX Template** (Modern or Classic).
- [ ] Generate a **Cover Letter** (try different tones).
- [ ] Generate an **Application Email**.
- [ ] Go to the **Assets** tab (or job drawer) to preview and download all generated assets. Confirm previews display correctly and downloads function.
- [ ] Optionally open **Pipeline (Optional)** and verify status/notes can still be saved without making tracking the main workflow.

## 4. What to Inspect Manually
- [ ] **Name Spacing:** Ensure names are not character-spaced (e.g. "B E R A T").
- [ ] **Phone Formatting:** Ensure phone numbers are normal digits and not split into separated digits.
- [ ] **LinkedIn/GitHub:** Check that contact links remain exact and are not swapped or corrupted.
- [ ] **Title/Company/Date fields:** Ensure job titles and company names are not mixed or swapped, and dates do not leak into them.
- [ ] **Summary Exaggeration:** Check that the AI-generated professional summary remains truthful to your experience.
- [ ] **Skills Relevance:** Verify listed skills match your CV and target job keywords.
- [ ] **Bullet Quality:** Read through tailored experience bullets to ensure active verbs and high impact.
- [ ] **ATS-Friendly Layout:** Check page density, margins, bullet points, and section separators.
- [ ] **One-Page Behavior:** If "Optimize for one page" was checked, check if the content fits properly.
- [ ] **DOCX Opening:** Open downloaded `.docx` files in MS Word or Google Docs to ensure no corruption.
- [ ] **PDF Readability:** Ensure the PDF exports are completely readable.

## 5. Pass/Fail Notes
- **Acceptable (Pass):**
  - High score (~85-100) for a clean CV.
  - Mild warnings for minor formatting details that do not affect the output file.
  - Strong adaptation level using confident words (e.g., "hands-on exposure", "project-based experience") that are backed by the base CV.
  - Classic and Modern DOCX templates open correctly and exhibit clear formatting.
- **Considered a Bug (Fail):**
  - Critical contact details (email, phone, LinkedIn) corrupted or swapped.
  - Completely invented job titles, degrees, or certifications.
  - UI crash (red error boxes/tracebacks) when previewing or downloading assets.
  - Missing section headers or headers generated with empty names.
- **Content Preference:**
  - If a generated bullet is grammatically correct but doesn't perfectly match your voice, this is a content preference. You can adjust the adaptation level or manually edit your CV.
