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
