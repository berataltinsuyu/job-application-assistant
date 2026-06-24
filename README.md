# Job Application Assistant | İş Başvuru Asistanı

An advanced AI assistant designed to optimize CVs, analyze job compatibility, compute ATS scores, and generate interview preparation materials. Now supports PDF exports and a bilingual user interface.

CV dosyaları ve iş ilanları üzerinden uyum analizi, ATS puanlaması, kapak yazısı, başvuru e-postaları ve kişiselleştirilmiş mülakat hazırlığı yapan yapay zeka destekli başvuru asistanı. Artık PDF rapor çıktısı almayı ve çift dilli arayüzü desteklemektedir.

---

## 🚀 Features | Özellikler

- **PDF, TXT, & JSON Exports**: Download all reports and documents as JSON, TXT, and PDF / Tüm rapor ve taslakları JSON, TXT ve PDF formatında indirme.
- **Job Recommendations**: Real-time internet job postings search and ranking using SerpAPI Google Jobs / SerpAPI Google Jobs ile internetten gerçek zamanlı iş ilanı arama ve sıralama.
- **URL Extractor**: Scrape job description from public URLs / URL üzerinden iş ilanı metni ayıklama.
- **ATS Compatibilty**: Compute score, format warnings & keyword gaps / ATS uyumluluk puanı ve eksik anahtar kelimeler.
- **CV Optimization**: Rewrite sections and draft tailored CV improvements / CV iyileştirme önerileri ve bölüm bazlı yeniden yazma.
- **Outreach & Letter**: Generate cover letters and application email drafts / Kapak yazısı ve iş başvurusu e-posta taslakları oluşturma.
- **Interview Prep**: CV-specific personalized coach QA guides / Adaya ve pozisyona özel mülakat soruları hazırlama.
- **Dashboard & History**: Sleek sidebar layout & log records / Gelişmiş gösterge paneli ve geçmiş işlemleri yönetme.

---

## ATS CV Builder

The app includes an ATS CV Builder foundation with predefined ATS-friendly templates.

Current templates:
- Classic ATS
- Modern Clean
- Technical Developer
- Junior / Internship Focus

ATS CV Builder now supports:
- Template-based ATS CV generation
- Structured preview
- DOCX export
- PDF export
- ATS-friendly one-column templates
- Template-aware section order
- ATS score before/after estimates
- Keyword optimization summary
- Polished template-specific DOCX/PDF rendering
- Balanced one-page export optimization
- ATS score explanation
- Export section controls

DOCX export is recommended when users want to edit the CV after generation.
The ATS score is an estimated relevance score, not an official ATS result.

---

## Phase 2A - Job Monitoring Agent

Phase 2A adds a generic, ethical foundation for low-frequency job monitoring.

What it does:
- Creates reusable job alert profiles with keywords, location, seniority, job type, work model, excluded keywords, sources, active/passive state, and a minimum match score.
- Runs safe mock/manual monitoring through the `manual_mock` source adapter.
- Scores normalized job records deterministically against each alert profile.
- Stores monitored jobs, run history, match summaries, matched keywords, missing keywords, and job workflow status.
- Lets users mark monitored jobs as `new`, `saved`, `rejected`, `applied`, or `archived`.

How to create an alert profile:
1. Open **Job Monitoring Agent** in the Streamlit sidebar.
2. Enter an alert name and comma-separated keywords.
3. Optionally add location, seniority, job type, work model, and excluded keywords.
4. Keep the source as `manual_mock` for Phase 2A.
5. Choose a minimum match score, then create the alert.

How to run mock/manual monitoring:
1. In the existing alert profiles list, click **Run now**.
2. The backend calls only `ManualMockJobSourceAdapter`.
3. Matching jobs are stored and shown in the job results section.
4. Re-running the same alert updates existing jobs by `alert_profile_id + source + source_job_id` instead of creating duplicates.

How match scoring works:
- The scorer checks alert keywords against the mock job title and description.
- Location, seniority, job type, and work model add deterministic filter-based score contributions when provided.
- Excluded keywords reduce the score when found in the title or description.
- Scores are clamped from 0 to 100.
- Gemini or other LLMs are not used for Phase 2A job monitoring scores.

Current limitations:
- No real scraping is implemented yet.
- Only the `manual_mock` source adapter exists in Phase 2A.
- ATS CV Builder, cover letter, and application email actions are placeholders until later phases.

Future phases:
- Add carefully reviewed real source adapters.
- Connect monitored jobs to tailored CV, cover letter, and application email generation.
- Add scheduling, notifications, and richer filtering only after safety constraints are defined.

Safety policy:
- Future source adapters must respect public access, robots.txt, rate limits, and source terms.
- Do not bypass login, CAPTCHA, Cloudflare, paywalls, or access controls.
- Do not use proxies, evasion techniques, hidden browser automation, or aggressive polling.
- Keep monitoring low-frequency and user-controlled.

### Phase 2B - Manual Job Import

Phase 2B makes the Job Monitoring Agent useful with real postings while still avoiding scraping.

How to create an alert profile:
1. Open **Job Monitoring Agent**.
2. Create an alert with keywords, optional filters, excluded keywords, and a minimum match score.
3. Keep `manual_mock` as the alert source for mock monitoring.

How to manually add a job posting:
1. Open **Manual Job Import** inside the Job Monitoring Agent page.
2. Optionally select an alert profile for scoring.
3. Paste the job title, company, location, work model, seniority, job type, source label, URL, posted date, and job description.
4. Click **Add manual job**.

Manual job scoring:
- If an alert profile is selected, the existing deterministic matcher scores the pasted title and description against alert keywords and filters.
- If no alert profile is selected, the job is stored with a `0` score and the summary states that no alert profile was selected.
- Manual jobs can be rescored later against any existing alert profile from the job card.

Duplicate handling:
- Manual imports generate a deterministic `source_job_id` from title, company, URL, and description content.
- Repeating the same manual import updates the existing monitored job instead of creating a duplicate.
- Existing job workflow status is preserved when a duplicate is updated.

Current limitation:
- The app does not fetch URL content automatically.
- URLs are stored only as user-provided text.
- Users must paste the job description manually.

Safety policy:
- No real scraping is implemented in Phase 2B.
- No login bypass, CAPTCHA bypass, Cloudflare bypass, proxy evasion, or hidden browser automation is implemented.
- Manual import stores only user-provided job data.

### Phase 2C - Job Detail Intelligence

Phase 2C adds an intelligence layer to each monitored job, providing detailed application insights before CV/Cover Letter generation is implemented in Phase 2E.

What it does:
- Analyzes a monitored job posting and generates insights:
  - **Job Family Detection:** Classifies roles into specific areas like `software_backend`, `frontend`, `fullstack`, `ai_ml_llm`, `data_analytics`, `business_analyst`, `product_project`, `fintech_payment`, `risk_fraud_compliance`, `cybersecurity`, `devops_cloud`, `corporate_applications`, `sales_operations`, or `general`.
  - **Seniority Assessment:** Evaluates requirements to identify seniority (internship, entry level, junior, mid, senior, lead/manager).
  - **Role Summary:** Drafts a concise 2-4 sentence summary of the job description.
  - **Match Reason:** Explains why the job matches the alert profile in practical terms (or gives general context if no profile is selected).
  - **Strengths & Gaps:** Lists candidate strengths (based on matched keywords and filters) and gaps (based on missing keywords and seniority mismatches).
  - **CV, Project & Skill Focus:** Recommends specific CV phrasing, generic project categories, and key skills to highlight.
  - **Application Recommendation:** Recommends action (strong apply, apply, apply with tailored CV, low match, not recommended).
  - **Risk Notes:** Flags potential risks (e.g., claiming MLOps or direct cybersecurity ownership without support).
  - **Interview Focus Areas:** Lists likely interview topics to prepare for.

How to analyze a job:
1. Open any monitored job card in **Job Monitoring Agent**.
2. Click **Analyze job**. Optionally, choose a different alert profile from the selector dropdown to evaluate the job against a new target profile.
3. Once completed, the analysis results are displayed inside the **Job Analysis Report** expander panel.
4. Re-running the analysis updates the existing report for that job.

Scoring & Analysis Rules:
- All analysis runs **locally and deterministically** by default.
- Gemini LLM generation is optional and disabled by default. It can be enabled by setting `JOB_INTELLIGENCE_USE_LLM=true` in `.env` (requires a valid `GEMINI_API_KEY`).
- No external requests are made; URLs are stored as text and not fetched.

Safety Policy:
- No web scraping is triggered.
- No automated page fetches or external requests are made.

### Phase 2D - Application Pipeline & Notes

Phase 2D adds an application tracking layer so users can manage the full application lifecycle for monitored jobs, log actions, and view a pipeline overview dashboard.

What it does:
- Tracks key lifecycle stages: `not_started`, `preparing`, `applied`, `screening`, `interview`, `technical_interview`, `offer`, `rejected`, `withdrawn`, `archived`.
- Logs job priority: `low`, `medium`, `high`.
- Logs material status (CV, cover letter): `not_started`, `cv_needed`, `cover_letter_needed`, `ready`, `submitted`.
- Stores detailed metadata: deadlines, next actions, next action dates, interview dates, contact details, and application notes.
- Synchronizes status buttons (applied, rejected, archived) with pipeline stages automatically (e.g. clicking "Mark Applied" sets the pipeline stage to "applied" and logs the applied date).
- Displays a **Pipeline Overview Dashboard** grouping jobs by stage, listing high-priority jobs, and highlighting upcoming actions and deadlines.

How to track/update a job:
1. Open any monitored job card.
2. Expand the **Pipeline / Notes** panel.
3. Edit the stage, priority, deadline, contact details, next actions, and notes.
4. Click **Save Pipeline** to commit changes.
5. Badges for the current stage, priority, next action, and materials status are displayed in the job metadata section.

Safety Policy:
- No web scraping is triggered.
- No automated external requests are made; URLs remain stored text.

### Phase 2E - Job-to-Application Asset Generator

Phase 2E enables users to generate tailored application materials (CV, Cover Letter, Application Email) directly from any monitored or manually imported job description, incorporating detailed job intelligence context.

What it does:
- Generates tailored CVs using the existing ATS CV Builder pipeline and templates, aligning experience truthfully to the job description and protecting locked candidate details/proper nouns.
- Generates customized Cover Letters reusing existing prompt setups with job intelligence context.
- Generates professional Application Emails, LinkedIn cold messages, and follow-up templates.
- Persists all generated assets in a new SQLite table `job_application_assets`.
- Physically saves all generated documents (PDF, DOCX, TXT, JSON) to the `generated_assets/` folder in the project root.
- Allows users to preview generated contents and download them directly from the Streamlit UI.
- Automatically synchronizes the pipeline's `application_materials_status` (e.g., updates to `cover_letter_needed` after generating CV, and `ready` once all necessary materials are available).

How to generate materials:
1. Open any monitored job card.
2. Expand the **Generate Application Materials / Başvuru Materyali Oluştur** panel.
3. Upload a CV file (PDF or DOCX format).
4. Choose the output language, CV template, and tone.
5. Click **Generate Tailored CV**, **Generate Cover Letter**, or **Generate Application Email**.
6. View the live preview on screen, and click **Download** to save the generated file to your local computer.
7. Any previously generated materials for the selected job are listed at the bottom of the panel for quick retrieval and download.

Safety & Limitations:
- User must upload their CV manually as the source of truth; no unverified claims or fake experience are invented.
- No web scraping is triggered; job URLs remain stored text.

---

## 🛠️ Run & Setup | Kurulum ve Çalıştırma

### 1. Installation | Kurulum

```bash
git clone https://github.com/berataltinsuyu/job-application-assistant.git
cd job-application-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration | Yapılandırma

Create a `.env` file in the root directory / Proje dizininde bir `.env` dosyası oluşturun:
```env
GEMINI_API_KEY=your_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here
JOOBLE_API_KEY=your_jooble_key_here
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here
```

> [!NOTE]
> Real job search supports SerpAPI Google Jobs, Jooble API, and Adzuna API. Configure the respective environment keys to activate each search provider. LinkedIn URLs are handled on a best-effort basis and may require manual job description input due to access restrictions. / Gerçek iş ilanı araması; SerpAPI Google Jobs, Jooble API ve Adzuna API sağlayıcılarını destekler. Sağlayıcıları aktif etmek için ilgili API anahtarlarını ekleyin. LinkedIn URL'leri en iyi çaba esasına göre işlenir ve kısıtlamalar nedeniyle manuel ilan girişi gerektirebilir.

### 3. Start Backend | Backend'i Başlatma

```bash
uvicorn main:app --reload
```

### 4. Start Frontend | Streamlit'i Başlatma

```bash
streamlit run streamlit_app.py
```
