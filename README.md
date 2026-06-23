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

DOCX export is recommended when users want to edit the CV after generation.

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
