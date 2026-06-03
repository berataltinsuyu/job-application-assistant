# Job Application Assistant | İş Başvuru Asistanı

An advanced AI assistant designed to optimize CVs, analyze job compatibility, compute ATS scores, and generate interview preparation materials.

CV dosyaları ve iş ilanları üzerinden uyum analizi, ATS puanlaması, kapak yazısı, başvuru e-postaları ve kişiselleştirilmiş mülakat hazırlığı yapan yapay zeka destekli başvuru asistanı.

---

## 🚀 Features | Özellikler

- **URL Extractor**: Scrape job description from public URLs / URL üzerinden iş ilanı metni ayıklama.
- **ATS Compatibilty**: Compute score, format warnings & keyword gaps / ATS uyumluluk puanı ve eksik anahtar kelimeler.
- **CV Optimization**: Rewrite sections and draft tailored CV improvements / CV iyileştirme önerileri ve bölüm bazlı yeniden yazma.
- **Outreach & Letter**: Generate cover letters and application email drafts / Kapak yazısı ve iş başvurusu e-posta taslakları oluşturma.
- **Interview Prep**: CV-specific personalized coach QA guides / Adaya ve pozisyona özel mülakat soruları hazırlama.
- **Dashboard & History**: Sleek sidebar layout & log records / Gelişmiş gösterge paneli ve geçmiş işlemleri yönetme.

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
```

### 3. Start Backend | Backend'i Başlatma

```bash
uvicorn main:app --reload
```

### 4. Start Frontend | Streamlit'i Başlatma

```bash
streamlit run streamlit_app.py
```
