import json
import re
import requests
import streamlit as st
from datetime import datetime
from fpdf import FPDF

API_BASE_URL = "http://127.0.0.1:8000"

# --- Translations Dictionary ---
TRANSLATIONS = {
    "tr": {
        "app_title": "💼 Yapay Zeka Destekli İş Başvuru Asistanı",
        "sidebar_uploads": "📂 Genel Dosyalar ve Ayarlar",
        "upload_cv": "Özgeçmiş Yükle (PDF/DOCX)",
        "job_desc": "İş İlanı Metni",
        "output_lang": "Çıktı Dili",
        "ui_language": "Arayüz Dili (UI Language)",
        "nav_title": "Özellikler",
        
        # Navigation items
        "nav_dashboard": "📊 Panel",
        "nav_job_url": "🔗 İlan Linkinden Metin Çıkarma",
        "nav_cv_analysis": "🔍 CV Analizi",
        "nav_ats_score": "🎯 ATS Skoru",
        "nav_ats_cv_builder": "📄 ATS CV Oluşturucu",
        "nav_job_keywords": "🔑 İlan Anahtar Kelimeleri",
        "nav_cv_improvement": "💡 CV İyileştirme",
        "nav_tailored_cv": "📝 İlana Özel CV Taslağı",
        "nav_rewrite_section": "✍️ CV Bölümü Yeniden Yazma",
        "nav_cover_letter": "✉️ Kapak Yazısı",
        "nav_app_email": "📧 Başvuru E-postası",
        "nav_interview_prep": "🤝 Mülakat Hazırlığı",
        "nav_personalized_interview": "🎯 Kişiselleştirilmiş Mülakat",
        "nav_history": "📜 Geçmiş",
        
        # Validation & Warnings
        "please_upload_cv": "⚠️ Lütfen sol menüden bir CV dosyası yükleyin.",
        "please_enter_job_desc": "⚠️ Lütfen sol menüye bir iş ilanı metni girin (veya Linkten Çıkarıcıyı kullanın).",
        "btn_analyze": "CV Analiz Et",
        "btn_calculate_ats": "ATS Skorunu Hesapla",
        "btn_extract_keywords": "Anahtar Kelimeleri Çıkar",
        "btn_gen_improvements": "İyileştirme Önerileri Oluştur",
        "btn_gen_tailored": "Uyumlanmış CV Taslağı Oluştur",
        "btn_rewrite": "Bölümü Yeniden Yaz",
        "btn_gen_cover_letter": "Kapak Yazısı Oluştur",
        "btn_gen_email": "Şablonları Oluştur",
        "btn_gen_prep": "Mülakat Rehberi Hazırla",
        "btn_gen_custom_prep": "Kişisel Mülakat Soruları Hazırla",
        "btn_refresh": "Listeyi Yenile",
        "btn_clear_history": "⚠️ Tüm Geçmişi Temizle",
        "confirm_clear": "Tüm kayıtları silmek istiyorum",
        
        # Download buttons
        "download_json": "📥 Raporu İndir (.json)",
        "download_txt": "📥 Metin Olarak İndir (.txt)",
        "download_pdf": "📥 PDF Olarak İndir (.pdf)",
        "download_docx_cv": "DOCX İndir",
        "download_pdf_cv": "PDF İndir",
        "download_txt_cv": "TXT İndir",
        
        # Dashboard
        "dashboard_desc": "Uyum puanlarını, analizleri takip edin ve geçmiş başvurularınızı yönetin.",
        "db_operations": "Toplam İşlem",
        "db_latest_match": "Son Uyum Skoru",
        "db_latest_ats": "Son ATS Skoru",
        "db_features": "🚀 Özellikler Genel Bakış",
        "db_recent_history": "⏱️ Son İşlem Geçmişi",
        "db_no_history": "Geçmişte işlem bulunmamaktadır. Sol menüyü kullanarak ilk analizini başlat!",
        
        # Pages specific
        "job_url_desc": "İş ilanının bulunduğu sayfanın linkini girerek ilan detaylarını otomatik olarak ayıklayın (LinkedIn vb. ilan siteleri dahil).",
        "job_url_label": "İş İlanı URL'sini Girin:",
        "btn_extract_job": "İlan Detaylarını Çıkar",
        "set_active_job": "Aktif İş İlanı Olarak Ayarla",
        "extraction_success": "İş ilanı başarıyla çıkarıldı!",
        "extraction_save_success": "İş ilanı kaydedildi! Sol menüdeki kutuya aktarıldı.",
        
        # Status & Spinners
        "status_complete": "İşlem tamamlandı!",
        "status_error": "Bir hata oluştu:",
        "spinner_job": "İş ilanı sayfası getiriliyor ve taranıyor...",
        "spinner_analyze": "CV ve İş İlanı uyumu analiz ediliyor...",
        "spinner_ats": "ATS tarayıcısı çalıştırılıyor...",
        "spinner_keywords": "İş ilanı işleniyor...",
        "spinner_improvements": "Özgeçmiş bölümleri analiz ediliyor...",
        "spinner_tailored": "Uyumlu CV taslağı hazırlanıyor...",
        "spinner_rewrite": "Bölüm yeniden yazılıyor...",
        "spinner_cover_letter": "Kapak yazısı oluşturuluyor...",
        "spinner_email": "E-posta şablonları hazırlanıyor...",
        "spinner_prep": "Mülakat soruları ve yanıt ipuçları hazırlanıyor...",
        "spinner_personalized_prep": "CV ve iş ilanına göre kişiselleştirilmiş mülakat rehberi hazırlanıyor...",
        
        # CV Analysis Titles
        "fit_score": "Uyum Skoru",
        "summary": "Genel Özet",
        "strengths": "Güçlü Yönler",
        "weaknesses": "Eksik ve Zayıf Yönler",
        "cv_improvements": "CV İyileştirme Önerileri",
        "strategy": "Başvuru Stratejisi",
        "recommendation": "Genel Sonuç",
        
        # ATS Page Titles
        "matched_keywords": "Eşleşen Anahtar Kelimeler",
        "missing_keywords": "Eksik Anahtar Kelimeler",
        "keyword_recs": "Anahtar Kelime Önerileri",
        "format_warnings": "Biçimlendirme Uyarıları",
        
        # Job Keywords Titles
        "role_summary": "Rol Özeti",
        "must_have": "Olmazsa Olmaz Yetkinlikler",
        "nice_to_have": "Tercih Sebebi Yetkinlikler",
        "tech_keywords": "Teknik Anahtar Kelimeler",
        "soft_skills": "Sosyal Beceriler",
        "responsibilities": "Sorumluluklar",
        
        # Improvements Page Titles
        "priority_actions": "Öncelikli Eylemler",
        "missing_sections": "Eksik CV Bölümleri",
        "skills_suggestions": "Yetenekler Bölümü Önerileri",
        "projects_suggestions": "Projeler Bölümü Önerileri",
        "experience_suggestions": "Deneyim Bölümü Önerileri",
        
        # Tailored CV Page Titles
        "tailored_summary": "Özelleştirilmiş Profil Özeti",
        "tailored_skills": "Özelleştirilmiş Yetenekler",
        "tailored_projects": "Öne Çıkarılan Projeler",
        "tailored_experience": "Uyumlanmış İş Deneyimi Maddeleri",
        "education": "Eğitim Bölümü",
        "warnings": "Eksik Bilgi Uyarıları",
        
        # Section rewrite inputs
        "select_section": "Yeniden yazılacak CV bölümünü seçin:",
        "select_tone": "Yazı tonunu seçin:",
        "rationale": "Yapay Zeka Açıklaması",
        
        # Application email inputs
        "company_name": "Şirket Adı (İsteğe bağlı):",
        "position_title": "Pozisyon Adı (İsteğe bağlı):",
        "templates_ready": "Başvuru şablonları başarıyla oluşturuldu!",
        "email_subject": "E-posta Konusu",
        "email_body": "Başvuru E-postası",
        "linkedin_msg": "Kısa LinkedIn Mesajı",
        "follow_up_msg": "Takip E-postası Şablonu",
        
        # Interview prep titles
        "tech_questions": "Teknik Sorular",
        "hr_questions": "İK / Davranışsal Sorular",
        "challenge_questions": "Zorlayıcı Sorular",
        "prep_tips": "Hazırlık Önerileri",
        "cv_questions": "Özgeçmiş Odaklı Sorular",
        "weak_questions": "Zayıf Alanları Sorgulayan Sorular",
        "sample_answers": "Örnek Cevaplar",
        "prep_plan": "Mülakat Hazırlık Planı",
        "difficulty": "Mülakat Zorluğu Seçin:",
        
        # Job Recommendations
        "nav_job_recommendations": "💼 CV’ye Uygun İş İlanları",
        "location_label": "Lokasyon / Şehir:",
        "remote_label": "Uzaktan Çalışma Tercihi (Remote)",
        "find_suitable_jobs": "Uygun İş İlanlarını Bul",
        "candidate_profile": "Aday Profili",
        "search_queries": "Arama Sorguları",
        "recommended_jobs": "Önerilen İş İlanları",
        "spinner_recommendations": "Özgeçmişinize uygun iş ilanları aranıyor ve listeleniyor...",
        "no_apply_link": "Başvuru linki bulunamadı.",
        "no_jobs_found": "Birden fazla arama denenmesine rağmen iş ilanı bulunamadı. 'software engineer' gibi daha genel bir pozisyon adı veya 'United States' gibi daha geniş bir lokasyon deneyin.",
        "tried_searches": "Denenen Aramalar",
        "tried_providers_label": "Denenen Sağlayıcılar",
        "provider_label": "İş Arama Sağlayıcısı:",
        "missing_key_warning": "Gerçek iş ilanı araması için geçerli bir API anahtarı gereklidir. Lütfen .env dosyasına API anahtarlarınızı ekleyin.",

        # ATS CV Builder
        "ats_cv_builder": "ATS CV Oluşturucu",
        "choose_cv_template": "CV Şablonu Seç",
        "template_description": "Şablon Açıklaması",
        "best_for": "En Uygun Kullanım",
        "section_order": "Bölüm Sırası",
        "ats_notes": "ATS Notları",
        "ats_cv_builder_next_phase": "İş ilanına özel ATS uyumlu CV oluşturun, önizleyin ve DOCX/PDF olarak indirin.",
        "generate_ats_cv": "ATS CV Oluştur",
        "generated_ats_cv_preview": "Oluşturulan ATS CV Önizlemesi",
        "ats_score_before": "Önceki ATS Skoru",
        "ats_score_after": "Sonraki ATS Skoru",
        "used_keywords": "Doğrudan Kullanılan Anahtar Kelimeler",
        "transferable_keywords": "Aktarılabilir Anahtar Kelimeler",
        "risky_keywords_not_added": "Doğrudan Eklenmeyen Riskli Anahtar Kelimeler",
        "optimization_summary": "Optimizasyon Özeti",
        "target_role": "Hedef Pozisyon",
        "alignment_confidence": "Uyum Güveni",
        "adaptation_notes": "Uyarlama Notları",
        
        # History
        "history_desc": "Geçmiş başvuru değerlendirmelerinizi, analizleri ve taslakları inceleyin, filtreleyin veya silin.",
        "filter_op": "İşlem tipine göre filtrele:",
        "cv_file_label": "CV Dosyası:",
        "job_excerpt": "İş İlanı Özeti:",
        "output_label": "Oluşturulan Çıktı:",
        "all": "Hepsi",
        "record_deleted": "Kayıt silindi.",
        "all_deleted": "Tüm geçmiş kayıtları başarıyla silindi."
    },
    "en": {
        "app_title": "💼 AI Job Application Assistant",
        "sidebar_uploads": "📂 Global Uploads & Settings",
        "upload_cv": "Upload CV (PDF/DOCX)",
        "job_desc": "Job Description",
        "output_lang": "Output Language",
        "ui_language": "UI Language / Arayüz Dili",
        "nav_title": "Features",
        
        # Navigation items
        "nav_dashboard": "📊 Dashboard",
        "nav_job_url": "🔗 Job URL Extractor",
        "nav_cv_analysis": "🔍 CV Analysis",
        "nav_ats_score": "🎯 ATS Score",
        "nav_ats_cv_builder": "📄 ATS CV Builder",
        "nav_job_keywords": "🔑 Job Keywords",
        "nav_cv_improvement": "💡 CV Improvement",
        "nav_tailored_cv": "📝 Tailored CV",
        "nav_rewrite_section": "✍️ Rewrite CV Section",
        "nav_cover_letter": "✉️ Cover Letter",
        "nav_app_email": "📧 Application Email",
        "nav_interview_prep": "🤝 Interview Prep",
        "nav_personalized_interview": "🎯 Personalized Interview",
        "nav_history": "📜 History",
        
        # Validation & Warnings
        "please_upload_cv": "⚠️ Please upload your CV in the sidebar.",
        "please_enter_job_desc": "⚠️ Please provide a job description in the sidebar (or use Job URL Extractor).",
        "btn_analyze": "Analyze Match",
        "btn_calculate_ats": "Calculate ATS Score",
        "btn_extract_keywords": "Extract Job Keywords",
        "btn_gen_improvements": "Generate Improvement Suggestions",
        "btn_gen_tailored": "Generate Tailored Draft",
        "btn_rewrite": "Rewrite CV Section",
        "btn_gen_cover_letter": "Generate Cover Letter",
        "btn_gen_email": "Generate Templates",
        "btn_gen_prep": "Generate Prep Guide",
        "btn_gen_custom_prep": "Generate Custom QA",
        "btn_refresh": "Refresh List",
        "btn_clear_history": "⚠️ Clear Entire History Now",
        "confirm_clear": "I want to delete ALL records",
        
        # Download buttons
        "download_json": "📥 Download JSON Report",
        "download_txt": "📥 Download as Text (.txt)",
        "download_pdf": "📥 Download as PDF (.pdf)",
        "download_docx_cv": "Download DOCX",
        "download_pdf_cv": "Download PDF",
        "download_txt_cv": "Download TXT",
        
        # Dashboard
        "dashboard_desc": "Track match scores, resume feedback, and manage your past applications.",
        "db_operations": "Total Operations",
        "db_latest_match": "Latest Match Score",
        "db_latest_ats": "Latest ATS Score",
        "db_features": "🚀 Features Overview",
        "db_recent_history": "⏱️ Recent History Highlights",
        "db_no_history": "No operations found in history. Start analyzing your first application using the side menu!",
        
        # Pages specific
        "job_url_desc": "Enter a public job posting link to scrape details automatically (including LinkedIn, tech boards, and general sites).",
        "job_url_label": "Enter Job Posting URL:",
        "btn_extract_job": "Extract Job Details",
        "set_active_job": "Set as Active Job Description",
        "extraction_success": "Job description extracted successfully!",
        "extraction_save_success": "Job description saved! You can view it on the sidebar now.",
        
        # Status & Spinners
        "status_complete": "Operation completed!",
        "status_error": "An error occurred:",
        "spinner_job": "Fetching and parsing job page...",
        "spinner_analyze": "Analyzing CV and Job compatibility...",
        "spinner_ats": "Running ATS scanner...",
        "spinner_keywords": "Processing job description...",
        "spinner_improvements": "Analyzing CV sections...",
        "spinner_tailored": "Drafting tailored CV layout...",
        "spinner_rewrite": "Rewriting section...",
        "spinner_cover_letter": "Writing cover letter...",
        "spinner_email": "Drafting emails...",
        "spinner_prep": "Generating interview QA...",
        "spinner_personalized_prep": "Analyzing CV alignment and generating questions...",
        
        # CV Analysis Titles
        "fit_score": "Fit Score",
        "summary": "Summary",
        "strengths": "Strengths",
        "weaknesses": "Weaknesses & Skill Gaps",
        "cv_improvements": "CV Improvements",
        "strategy": "Application Strategy",
        "recommendation": "Final Recommendation",
        
        # ATS Page Titles
        "matched_keywords": "Matched Keywords",
        "missing_keywords": "Missing Keywords",
        "keyword_recs": "Keyword Recommendations",
        "format_warnings": "Formatting Warnings",
        
        # Job Keywords Titles
        "role_summary": "Role Summary",
        "must_have": "Must-Have Skills",
        "nice_to_have": "Nice-to-Have Skills",
        "tech_keywords": "Technical Keywords",
        "soft_skills": "Soft Skills",
        "responsibilities": "Responsibilities",
        
        # Improvements Page Titles
        "priority_actions": "Priority Actions",
        "missing_sections": "Missing Sections",
        "skills_suggestions": "Skills Section Suggestions",
        "projects_suggestions": "Project Section Suggestions",
        "experience_suggestions": "Experience Section Suggestions",
        
        # Tailored CV Page Titles
        "tailored_summary": "Tailored Profile Summary",
        "tailored_skills": "Tailored Skills List",
        "tailored_projects": "Tailored Projects Highlight",
        "tailored_experience": "Tailored Experience Bulletpoints",
        "education": "Education Section",
        "warnings": "Warnings/Missing Facts",
        
        # Section rewrite inputs
        "select_section": "Select CV section to rewrite:",
        "select_tone": "Select tone:",
        "rationale": "AI Rationale / Explanation",
        
        # Application email inputs
        "company_name": "Company Name (Optional):",
        "position_title": "Position Title (Optional):",
        "templates_ready": "Email templates generated!",
        "email_subject": "Email Subject",
        "email_body": "Main Application Email",
        "linkedin_msg": "LinkedIn Message",
        "follow_up_msg": "Follow-up Email Template",
        
        # Interview prep titles
        "tech_questions": "Technical Questions",
        "hr_questions": "HR / Behavioral Questions",
        "challenge_questions": "Challenging Questions",
        "prep_tips": "Preparation Tips",
        "cv_questions": "CV-Specific Questions",
        "weak_questions": "Weak Area & Stress Testing Questions",
        "sample_answers": "Sample Complete Responses",
        "prep_plan": "Preparation Step-by-Step Plan",
        "difficulty": "Select Difficulty Level:",
        
        # Job Recommendations
        "nav_job_recommendations": "💼 Job Recommendations",
        "location_label": "Location / City:",
        "remote_label": "Remote Preference",
        "find_suitable_jobs": "Find Suitable Jobs",
        "candidate_profile": "Candidate Profile",
        "search_queries": "Search Queries",
        "recommended_jobs": "Recommended Jobs",
        "spinner_recommendations": "Searching and evaluating suitable job postings...",
        "no_apply_link": "No apply link available.",
        "no_jobs_found": "No jobs found after trying multiple search queries. Try a broader role title such as 'software engineer' or a wider location such as 'United States'.",
        "tried_searches": "Tried Searches",
        "tried_providers_label": "Tried Providers",
        "provider_label": "Job Search Provider:",
        "missing_key_warning": "Real job search requires a valid API key. Please configure your API keys in your .env file.",

        # ATS CV Builder
        "ats_cv_builder": "ATS CV Builder",
        "choose_cv_template": "Choose CV Template",
        "template_description": "Template Description",
        "best_for": "Best For",
        "section_order": "Section Order",
        "ats_notes": "ATS Notes",
        "ats_cv_builder_next_phase": "Generate, preview, and download job-specific ATS-friendly CVs as DOCX/PDF.",
        "generate_ats_cv": "Generate ATS CV",
        "generated_ats_cv_preview": "Generated ATS CV Preview",
        "ats_score_before": "ATS Score Before",
        "ats_score_after": "ATS Score After",
        "used_keywords": "Directly Used Keywords",
        "transferable_keywords": "Transferable Keywords",
        "risky_keywords_not_added": "Risky Keywords Not Added",
        "optimization_summary": "Optimization Summary",
        "target_role": "Target Role",
        "alignment_confidence": "Alignment Confidence",
        "adaptation_notes": "Adaptation Notes",
        
        # History
        "history_desc": "Browse, filter, review, and delete records of past evaluations and drafts.",
        "filter_op": "Filter by operation type:",
        "cv_file_label": "CV Filename:",
        "job_excerpt": "Job Description Excerpt:",
        "output_label": "Generated Output:",
        "all": "All",
        "record_deleted": "Record deleted.",
        "all_deleted": "All history deleted successfully."
    }
}

# Ensure session state variables exist
if "global_job_text" not in st.session_state:
    st.session_state.global_job_text = ""
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "en"

# --- Sidebar UI Language selector ---
ui_lang_choice = st.sidebar.radio(
    "UI Language / Arayüz Dili",
    ["Türkçe", "English"],
    index=0 if st.session_state.ui_lang == "tr" else 1
)
st.session_state.ui_lang = "tr" if ui_lang_choice == "Türkçe" else "en"

def t(key):
    return TRANSLATIONS[st.session_state.ui_lang].get(key, key)

st.title(t("app_title"))

# --- Sidebar Configuration panel ---
st.sidebar.markdown("---")
st.sidebar.subheader(t("sidebar_uploads"))

global_cv = st.sidebar.file_uploader(
    t("upload_cv"),
    type=["pdf", "docx"],
    key="global_cv"
)

global_job_desc = st.sidebar.text_area(
    t("job_desc"),
    value=st.session_state.global_job_text,
    height=160,
    key="global_job_desc_input"
)
st.session_state.global_job_text = global_job_desc

global_language = st.sidebar.selectbox(
    t("output_lang"),
    ["Turkish", "English"],
    key="global_language"
)

st.sidebar.markdown("---")

# Navigation Menu Options translated
menu_map = {
    "📊 Dashboard": "nav_dashboard",
    "🔗 Job URL Extractor": "nav_job_url",
    "🔍 CV Analysis": "nav_cv_analysis",
    "🎯 ATS Score": "nav_ats_score",
    "📄 ATS CV Builder": "nav_ats_cv_builder",
    "🔑 Job Keywords": "nav_job_keywords",
    "💡 CV Improvement": "nav_cv_improvement",
    "📝 Tailored CV": "nav_tailored_cv",
    "✍️ Rewrite CV Section": "nav_rewrite_section",
    "✉️ Cover Letter": "nav_cover_letter",
    "📧 Application Email": "nav_app_email",
    "🤝 Interview Prep": "nav_interview_prep",
    "🎯 Personalized Interview": "nav_personalized_interview",
    "💼 Job Recommendations": "nav_job_recommendations",
    "📜 History": "nav_history"
}

menu_options = [t(menu_map[key]) for key in menu_map.keys()]
page_choice = st.sidebar.radio(
    t("nav_title"),
    menu_options
)

# Reverse lookup selection
selected_page_key = None
for original_key, translation_key in menu_map.items():
    if t(translation_key) == page_choice:
        selected_page_key = original_key
        break

# Helper functions
def get_cv_files():
    if global_cv is not None:
        return {
            "cv_file": (
                global_cv.name,
                global_cv.getvalue(),
                global_cv.type
            )
        }
    return None

def validate_inputs(require_cv=True, require_job=True):
    if require_cv and global_cv is None:
        st.warning(t("please_upload_cv"))
        return False
    if require_job and not st.session_state.global_job_text.strip():
        st.warning(t("please_enter_job_desc"))
        return False
    return True

# --- PDF Generation and Formatting utilities ---
class ReportPDF(FPDF):
    def __init__(self, title_text, footer_text):
        super().__init__()
        self.title_text = title_text
        self.footer_text = footer_text
        
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, self.title_text, border=0, new_x="LMARGIN", new_y="NEXT", align='C')
        self.set_font('helvetica', 'I', 8)
        created_str = f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.cell(0, 5, created_str, border=0, new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'{self.footer_text} | Page {self.page_no()}/{{nb}}', align='C')

def sanitize_text_for_pdf(text: str) -> str:
    """Return text that can be written safely with fpdf2's core Helvetica font."""
    if text is None:
        return ""

    text = str(text)
    replacements = {
        "🎯": "",
        "💼": "",
        "🔍": "",
        "📊": "",
        "🔑": "",
        "💡": "",
        "📝": "",
        "✍️": "",
        "✍": "",
        "📧": "",
        "🤝": "",
        "📁": "",
        "📂": "",
        "📥": "",
        "📜": "",
        "🔗": "",
        "✉️": "",
        "✉": "",
        "🚀": "",
        "⏱️": "",
        "⏱": "",
        "⚠️": "Warning:",
        "⚠": "Warning:",
        "✅": "",
        "❌": "",
        "•": "-",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove remaining emoji, variation selectors, and unsupported symbol glyphs.
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    text = re.sub(r"[\u200d\ufe0f]", "", text)

    # Helvetica core fonts can render Latin-1 Turkish chars, but not these.
    turkish_fallback_table = str.maketrans({
        'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'İ': 'I',
        'ş': 's', 'Ş': 'S'
    })
    text = text.translate(turkish_fallback_table)

    # Final guard for fpdf2 core fonts: drop any remaining non-Latin-1 chars.
    return text.encode("latin-1", errors="ignore").decode("latin-1")

def create_pdf_bytes(title: str, content: str, is_turkish_ui: bool = True) -> bytes:
    footer_text = (
        "Job Application Assistant tarafindan olusturulmustur."
        if is_turkish_ui else
        "Generated by Job Application Assistant."
    )
    safe_title = sanitize_text_for_pdf(title)
    safe_footer = sanitize_text_for_pdf(footer_text)

    pdf = ReportPDF(safe_title, safe_footer)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    
    safe_content = sanitize_text_for_pdf(content)
    for line in safe_content.splitlines():
        pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
        
    return bytes(pdf.output())

def format_result_as_text(title: str, result: dict | list | str) -> str:
    if isinstance(result, str):
        return f"=== {title.upper()} ===\n\n{result}"
    
    lines = [
        f"========================================",
        f" {title.upper()}",
        f"========================================\n"
    ]
    
    def process_item(item, indent=0):
        padding = "  " * indent
        if isinstance(item, dict):
            for key, val in item.items():
                clean_key = str(key).replace("_", " ").title()
                if isinstance(val, (dict, list)):
                    lines.append(f"\n{padding}• {clean_key}:")
                    process_item(val, indent + 1)
                else:
                    lines.append(f"{padding}• {clean_key}: {val}")
        elif isinstance(item, list):
            for val in item:
                if isinstance(val, (dict, list)):
                    process_item(val, indent)
                    lines.append("")
                else:
                    lines.append(f"{padding}- {val}")
        else:
            lines.append(f"{padding}{item}")

    process_item(result)
    return "\n".join(lines)

def render_download_buttons(title: str, raw_result: dict | str, filename_base: str):
    is_tr = (st.session_state.ui_lang == "tr")
    
    if isinstance(raw_result, str):
        json_data = json.dumps({"title": title, "result": raw_result}, indent=2, ensure_ascii=False)
    else:
        json_data = json.dumps(raw_result, indent=2, ensure_ascii=False)
        
    txt_content = format_result_as_text(title, raw_result)
    pdf_bytes = create_pdf_bytes(title, txt_content, is_turkish_ui=is_tr)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label=t("download_json"),
            data=json_data,
            file_name=f"{filename_base}.json",
            mime="application/json"
        )
    with col2:
        st.download_button(
            label=t("download_txt"),
            data=txt_content,
            file_name=f"{filename_base}.txt",
            mime="text/plain"
        )
    with col3:
        st.download_button(
            label=t("download_pdf"),
            data=pdf_bytes,
            file_name=f"{filename_base}.pdf",
            mime="application/pdf"
        )

def write_non_empty_list(items):
    if not items:
        st.write("-")
        return

    for item in items:
        st.markdown(f"- {item}")

def render_ats_cv_preview(ats_cv: dict):
    contact = ats_cv.get("contact", {})
    st.subheader("Contact")
    contact_lines = []
    for key in ["full_name", "target_title", "email", "phone", "location", "linkedin", "github", "portfolio"]:
        value = contact.get(key)
        if value:
            contact_lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
    st.markdown("  \n".join(contact_lines) if contact_lines else "-")

    summary_sections = [
        ("Professional Summary", "professional_summary"),
        ("Career Objective", "career_objective"),
        ("Technical Summary", "technical_summary"),
    ]
    for title, key in summary_sections:
        value = ats_cv.get(key)
        if value:
            st.subheader(title)
            st.write(value)

    st.subheader("Skills")
    skills = ats_cv.get("skills", {})
    if isinstance(skills, dict):
        for skill_group, items in skills.items():
            if items:
                st.markdown(f"**{skill_group.replace('_', ' ').title()}**")
                st.write(", ".join(items))
    else:
        st.write("-")

    st.subheader("Experience")
    for item in ats_cv.get("experience", []):
        role = item.get("role", "")
        company = item.get("company", "")
        dates = " - ".join(filter(None, [item.get("start_date", ""), item.get("end_date", "")]))
        heading = " | ".join(filter(None, [role, company, item.get("location", ""), dates]))
        if heading:
            st.markdown(f"**{heading}**")
        write_non_empty_list(item.get("bullets", []))

    st.subheader("Projects")
    for item in ats_cv.get("projects", []):
        if item.get("name"):
            st.markdown(f"**{item.get('name')}**")
        if item.get("description"):
            st.write(item.get("description"))
        if item.get("technologies"):
            st.write(", ".join(item.get("technologies", [])))
        write_non_empty_list(item.get("bullets", []))
        if item.get("link"):
            st.write(item.get("link"))

    st.subheader("Education")
    for item in ats_cv.get("education", []):
        heading = " | ".join(filter(None, [
            item.get("school", ""),
            item.get("degree", ""),
            item.get("department", ""),
            " - ".join(filter(None, [item.get("start_date", ""), item.get("end_date", "")])),
        ]))
        if heading:
            st.markdown(f"**{heading}**")
        write_non_empty_list(item.get("details", []))

    st.subheader("Certifications")
    certifications = ats_cv.get("certifications", [])
    if certifications:
        for item in certifications:
            cert_line = " | ".join(filter(None, [
                item.get("name", ""),
                item.get("issuer", ""),
                item.get("date", ""),
                item.get("link", ""),
            ]))
            st.markdown(f"- {cert_line}" if cert_line else "-")
    else:
        st.write("-")

    st.subheader("Languages")
    languages = ats_cv.get("languages", [])
    if languages:
        for item in languages:
            language_line = " - ".join(filter(None, [item.get("language", ""), item.get("level", "")]))
            st.markdown(f"- {language_line}" if language_line else "-")
    else:
        st.write("-")

def fetch_ats_cv_export(endpoint: str, ats_cv: dict, template_id: str, language: str) -> bytes | None:
    try:
        response = requests.post(
            f"{API_BASE_URL}/ats-cv/{endpoint}",
            data={
                "ats_cv_json": json.dumps(ats_cv, ensure_ascii=False),
                "template_id": template_id,
                "language": language,
            }
        )
        if response.status_code == 200:
            return response.content
        st.error(f"Error {response.status_code}: {response.text}")
    except Exception:
        st.error(t("status_error"))
    return None

# Custom Premium Styling injection
st.markdown("""
<style>
    .stButton>button {
        background: linear-gradient(135deg, #6366F1 0%, #06B6D4 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 18px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        color: white;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }
    .dashboard-banner {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(6, 182, 212, 0.12) 100%);
        border-left: 5px solid #6366F1;
        padding: 20px;
        border-radius: 4px 16px 16px 4px;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# --- Pages Layouts ---

if selected_page_key == "📊 Dashboard":
    st.markdown(f'<div class="dashboard-banner"><h1>{t("nav_dashboard")}</h1><p>{t("dashboard_desc")}</p></div>', unsafe_allow_html=True)
    
    try:
        response = requests.get(f"{API_BASE_URL}/history")
        history_data = response.json() if response.status_code == 200 else []
    except Exception:
        history_data = []

    total_history = len(history_data)
    latest_ats_score = "N/A"
    latest_match_score = "N/A"
    
    for item in history_data:
        req_type = item.get("request_type")
        res = item.get("result")
        if req_type == "ats_score" and latest_ats_score == "N/A" and isinstance(res, dict):
            latest_ats_score = f"{res.get('ats_score', 'N/A')}%"
        elif req_type == "analyze" and latest_match_score == "N/A" and isinstance(res, dict):
            latest_match_score = f"{res.get('match_score', 'N/A')}%"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><h3 style="margin:0;">{t("db_operations")}</h3><h1 style="color:#6366F1;margin:5px 0 0 0;">{total_history}</h1></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3 style="margin:0;">{t("db_latest_match")}</h3><h1 style="color:#10B981;margin:5px 0 0 0;">{latest_match_score}</h1></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3 style="margin:0;">{t("db_latest_ats")}</h3><h1 style="color:#06B6D4;margin:5px 0 0 0;">{latest_ats_score}</h1></div>', unsafe_allow_html=True)

    st.markdown(f"### {t('db_features')}")
    col_feat1, col_feat2 = st.columns(2)
    with col_feat1:
        st.info(f"**🔍 {t('nav_cv_analysis')} & {t('nav_ats_score')}**\n\nUpload CV and get detailed reports and score indicators dynamically.")
        st.success(f"**📝 {t('nav_tailored_cv')} & {t('nav_cover_letter')}**\n\nWrite customized matching proposals and targeted connection templates.")
    with col_feat2:
        st.warning(f"**🔗 {t('nav_job_url')}**\n\nScrape details directly from link urls without copying contents manually.")
        st.help(f"**🤝 {t('nav_interview_prep')} & {t('nav_personalized_interview')}**\n\nGenerate guides tailored specific to your experiences.")

    st.markdown(f"### {t('db_recent_history')}")
    if history_data:
        for idx, item in enumerate(history_data[:5]):
            st.markdown(f"**#{item['id']}** - **{item['request_type'].upper()}** | 📅 {item['created_at'].split('T')[0]} | 📂 {item.get('cv_filename') or 'None'}")
    else:
        st.info(t("db_no_history"))


elif selected_page_key == "🔗 Job URL Extractor":
    st.header(t("nav_job_url"))
    st.write(t("job_url_desc"))

    job_url = st.text_input(t("job_url_label"), placeholder="https://...")

    if st.button(t("btn_extract_job")):
        if not job_url.strip():
            st.warning("Please enter a URL / Lütfen geçerli bir URL girin.")
        else:
            with st.spinner(t("spinner_job")):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/extract-job-description",
                        json={"job_url": job_url}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            st.success(t("extraction_success"))
                            extracted_text = result.get("extracted_text", "")
                            st.text_area(t("job_desc"), value=extracted_text, height=300)
                            
                            if st.button(t("set_active_job")):
                                st.session_state.global_job_text = extracted_text
                                st.success(t("extraction_save_success"))
                                st.rerun()
                        else:
                            st.error(result.get("message"))
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "🔍 CV Analysis":
    st.header(t("nav_cv_analysis"))
    
    if validate_inputs():
        if st.button(t("btn_analyze")):
            with st.spinner(t("spinner_analyze")):
                try:
                    files = get_cv_files()
                    data = {"job_text": st.session_state.global_job_text}
                    response = requests.post(
                        f"{API_BASE_URL}/analyze",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        st.metric(t("fit_score"), f"{result.get('match_score', 'N/A')}%")
                        
                        st.subheader(t("summary"))
                        st.write(result.get("summary", ""))

                        st.subheader(t("strengths"))
                        for item in result.get("strengths", []):
                            st.write(f"✅ {item}")

                        st.subheader(t("weaknesses"))
                        for item in result.get("weaknesses", []):
                            st.write(f"⚠️ {item}")

                        st.subheader(t("cv_improvements"))
                        for item in result.get("cv_improvements", []):
                            st.write(f"💡 {item}")

                        st.subheader(t("strategy"))
                        st.write(result.get("application_strategy", ""))

                        st.subheader(t("recommendation"))
                        st.write(result.get("final_recommendation", ""))
                        
                        st.markdown("---")
                        render_download_buttons(t("nav_cv_analysis"), result, "cv_analysis_report")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "🎯 ATS Score":
    st.header(t("nav_ats_score"))

    if validate_inputs():
        if st.button(t("btn_calculate_ats")):
            with st.spinner(t("spinner_ats")):
                try:
                    files = get_cv_files()
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "language": global_language
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/ats-score",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        st.metric(t("nav_ats_score"), f"{result.get('ats_score', 0)}%")
                        
                        st.subheader(t("matched_keywords"))
                        st.write(", ".join(result.get("matched_keywords", [])))
                        
                        st.subheader(t("missing_keywords"))
                        for kw in result.get("missing_keywords", []):
                            st.markdown(f"- ❌ {kw}")
                            
                        st.subheader(t("keyword_recs"))
                        for rec in result.get("keyword_recommendations", []):
                            st.markdown(f"- 💡 {rec}")
                            
                        st.subheader(t("format_warnings"))
                        for warn in result.get("format_warnings", []):
                            st.markdown(f"- ⚠️ {warn}")
                            
                        st.subheader(t("summary"))
                        st.write(result.get("summary", ""))
                        
                        st.markdown("---")
                        render_download_buttons(t("nav_ats_score"), result, "ats_score_report")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "📄 ATS CV Builder":
    st.header(t("ats_cv_builder"))
    st.write(t("ats_cv_builder_next_phase"))

    try:
        response = requests.get(f"{API_BASE_URL}/ats-cv/templates")
        if response.status_code == 200:
            templates = response.json().get("templates", [])
        else:
            st.error(f"Error {response.status_code}: {response.text}")
            templates = []
    except Exception as e:
        st.error(f"{t('status_error')} {str(e)}")
        templates = []

    if templates:
        template_by_name = {template["name"]: template for template in templates}
        selected_template_name = st.selectbox(
            t("choose_cv_template"),
            list(template_by_name.keys())
        )
        selected_template = template_by_name[selected_template_name]

        st.subheader(t("template_description"))
        st.write(selected_template.get("description", ""))

        st.subheader(t("best_for"))
        for item in selected_template.get("best_for", []):
            st.markdown(f"- {item}")

        st.subheader(t("section_order"))
        for index, section in enumerate(selected_template.get("section_order", []), start=1):
            st.markdown(f"{index}. `{section}`")

        st.subheader(t("ats_notes"))
        for note in selected_template.get("ats_notes", []):
            st.markdown(f"- {note}")

        ats_cv_language_options = ["Turkish", "English"]
        ats_cv_language = st.selectbox(
            t("output_lang"),
            ats_cv_language_options,
            index=ats_cv_language_options.index(global_language) if global_language in ats_cv_language_options else 0,
            key="ats_cv_output_language"
        )

        if st.button(t("generate_ats_cv")):
            if validate_inputs(require_cv=True, require_job=True):
                with st.spinner(t("spinner_tailored")):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/ats-cv/generate",
                            files=get_cv_files(),
                            data={
                                "job_description": st.session_state.global_job_text,
                                "template_id": selected_template.get("id"),
                                "language": ats_cv_language,
                            }
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.ats_cv_builder_result = result
                            st.session_state.ats_cv_builder_language = result.get("language", ats_cv_language)
                            st.session_state.ats_cv_builder_template_id = selected_template.get("id")
                            st.success(t("status_complete"))
                        else:
                            st.error(f"Error {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(f"{t('status_error')} {str(e)}")

        stored_result = st.session_state.get("ats_cv_builder_result")
        if stored_result:
            ats_cv = stored_result.get("ats_cv", {})
            validation = stored_result.get("validation", {})
            metadata = ats_cv.get("ats_metadata", {})
            export_template = stored_result.get("template", selected_template)
            export_template_id = (
                st.session_state.get("ats_cv_builder_template_id")
                or export_template.get("id")
                or selected_template.get("id")
            )
            export_language = st.session_state.get("ats_cv_builder_language", ats_cv_language)

            if not validation.get("is_valid", False):
                st.warning(", ".join(validation.get("errors", [])))

            col_before, col_after, col_role = st.columns(3)
            with col_before:
                st.metric(t("ats_score_before"), metadata.get("ats_score_before", 0))
            with col_after:
                st.metric(t("ats_score_after"), metadata.get("ats_score_after", 0))
            with col_role:
                st.metric(t("target_role"), metadata.get("target_role") or "-")

            st.subheader(t("used_keywords"))
            st.write(", ".join(metadata.get("job_keywords_used", [])) or "-")

            st.subheader(t("transferable_keywords"))
            write_non_empty_list(metadata.get("transferable_keywords_used", []))

            st.subheader(t("missing_keywords"))
            write_non_empty_list(metadata.get("missing_keywords", []))

            st.subheader(t("risky_keywords_not_added"))
            write_non_empty_list(metadata.get("risky_keywords_not_added", []))

            st.subheader(t("optimization_summary"))
            st.write(metadata.get("optimization_summary", ""))

            st.subheader(t("alignment_confidence"))
            st.write(metadata.get("alignment_confidence") or "-")

            st.subheader(t("adaptation_notes"))
            write_non_empty_list(metadata.get("adaptation_notes", []))

            st.markdown("---")
            st.header(t("generated_ats_cv_preview"))
            render_ats_cv_preview(ats_cv)

            st.markdown("---")
            col_docx, col_pdf, col_txt = st.columns(3)
            docx_bytes = fetch_ats_cv_export("export-docx", ats_cv, export_template_id, export_language)
            pdf_bytes = fetch_ats_cv_export("export-pdf", ats_cv, export_template_id, export_language)
            txt_bytes = fetch_ats_cv_export("export-txt", ats_cv, export_template_id, export_language)

            with col_docx:
                if docx_bytes:
                    st.download_button(
                        label=t("download_docx_cv"),
                        data=docx_bytes,
                        file_name=f"ats_cv_{export_template_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            with col_pdf:
                if pdf_bytes:
                    st.download_button(
                        label=t("download_pdf_cv"),
                        data=pdf_bytes,
                        file_name=f"ats_cv_{export_template_id}.pdf",
                        mime="application/pdf"
                    )
            with col_txt:
                if txt_bytes:
                    st.download_button(
                        label=t("download_txt_cv"),
                        data=txt_bytes,
                        file_name=f"ats_cv_{export_template_id}.txt",
                        mime="text/plain"
                    )


elif selected_page_key == "🔑 Job Keywords":
    st.header(t("nav_job_keywords"))

    if validate_inputs(require_cv=False):
        if st.button(t("btn_extract_keywords")):
            with st.spinner(t("spinner_keywords")):
                try:
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "language": global_language
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/job-keywords",
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        st.subheader(f"{result.get('role_title', 'N/A')} ({result.get('experience_level', 'N/A')})")
                        st.write(result.get("role_summary", ""))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"### {t('must_have')}")
                            for skill in result.get("must_have_skills", []):
                                st.write(f"- 🎯 {skill}")
                            st.markdown(f"### {t('nice_to_have')}")
                            for skill in result.get("nice_to_have_skills", []):
                                st.write(f"- ⭐ {skill}")
                        with col2:
                            st.markdown(f"### {t('tech_keywords')}")
                            st.write(", ".join(result.get("technical_keywords", [])))
                            st.markdown(f"### {t('soft_skills')}")
                            st.write(", ".join(result.get("soft_skills", [])))
                        
                        st.subheader(t("responsibilities"))
                        for resp in result.get("responsibilities", []):
                            st.write(f"- {resp}")
                            
                        st.markdown("---")
                        render_download_buttons(t("nav_job_keywords"), result, "job_keywords_report")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "💡 CV Improvement":
    st.header(t("nav_cv_improvement"))

    if validate_inputs():
        if st.button(t("btn_gen_improvements")):
            with st.spinner(t("spinner_improvements")):
                try:
                    files = get_cv_files()
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "language": global_language
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/cv-improvement",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        st.subheader(t("summary"))
                        st.write(result.get("overall_feedback", ""))
                        
                        st.subheader(t("priority_actions"))
                        for act in result.get("priority_actions", []):
                            st.markdown(f"🔥 **{act}**")
                            
                        st.subheader(t("missing_sections"))
                        for sec in result.get("missing_sections", []):
                            st.markdown(f"- ❌ {sec}")
                            
                        st.subheader(t("skills_suggestions"))
                        for sug in result.get("skills_section_suggestions", []):
                            st.markdown(f"- {sug}")
                            
                        st.subheader(t("projects_suggestions"))
                        for sug in result.get("project_section_suggestions", []):
                            st.markdown(f"- {sug}")
                            
                        st.subheader(t("experience_suggestions"))
                        for sug in result.get("experience_section_suggestions", []):
                            st.markdown(f"- {sug}")
                            
                        st.markdown("---")
                        render_download_buttons(t("nav_cv_improvement"), result, "cv_improvements_report")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "📝 Tailored CV":
    st.header(t("nav_tailored_cv"))

    if validate_inputs():
        if st.button(t("btn_gen_tailored")):
            with st.spinner(t("spinner_tailored")):
                try:
                    files = get_cv_files()
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "language": global_language
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/tailored-cv",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        st.subheader(t("tailored_summary"))
                        st.write(result.get("profile_summary", ""))
                        
                        st.subheader(t("tailored_skills"))
                        st.write(", ".join(result.get("skills", [])))
                        
                        st.subheader(t("tailored_projects"))
                        for prj in result.get("projects", []):
                            st.markdown(f"**{prj.get('name')}**")
                            st.write(prj.get("description"))
                            st.write("---")
                            
                        st.subheader(t("tailored_experience"))
                        for bullet in result.get("experience_bullets", []):
                            st.write(f"- {bullet}")
                            
                        st.subheader(t("education"))
                        st.write(result.get("education_section", ""))
                        
                        if result.get("warnings"):
                            st.warning("⚠️ " + t("warnings") + ": " + ", ".join(result.get("warnings", [])))
                        
                        st.markdown("---")
                        render_download_buttons(t("nav_tailored_cv"), result, "tailored_cv")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "✍️ Rewrite CV Section":
    st.header(t("nav_rewrite_section"))

    sec_type = st.selectbox(t("select_section"), ["summary", "skills", "projects", "experience"])
    rewrite_tone = st.selectbox(t("select_tone"), ["professional", "confident", "concise"])

    if validate_inputs():
        if st.button(t("btn_rewrite")):
            with st.spinner(t("spinner_rewrite")):
                try:
                    files = get_cv_files()
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "section_type": sec_type,
                        "language": global_language,
                        "tone": rewrite_tone
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/rewrite-cv-section",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        st.subheader(f"{t('nav_rewrite_section')} - {result.get('section_type').upper()} ({rewrite_tone.title()})")
                        st.text_area(t("output_label"), value=result.get("rewritten_content"), height=250)
                        
                        st.subheader(t("rationale"))
                        st.info(result.get("explanation", ""))
                        
                        st.markdown("---")
                        render_download_buttons(t("nav_rewrite_section"), result, "cv_rewrite_report")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "✉️ Cover Letter":
    st.header(t("nav_cover_letter"))

    cl_tone = st.selectbox(t("select_tone"), ["professional", "friendly", "confident", "formal", "short"])

    if validate_inputs():
        if st.button(t("btn_gen_cover_letter")):
            with st.spinner(t("spinner_cover_letter")):
                try:
                    files = get_cv_files()
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "tone": cl_tone,
                        "language": global_language
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/cover-letter",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        st.text_area(t("nav_cover_letter"), value=result, height=350)
                        
                        st.markdown("---")
                        render_download_buttons(t("nav_cover_letter"), result, "cover_letter")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "📧 Application Email":
    st.header(t("nav_app_email"))

    comp_name = st.text_input(t("company_name"), placeholder="e.g. Acme Corp")
    pos_title = st.text_input(t("position_title"), placeholder="e.g. Backend Developer")
    email_tone = st.selectbox(t("select_tone"), ["professional", "friendly", "concise"])

    if validate_inputs():
        if st.button(t("btn_gen_email")):
            with st.spinner(t("spinner_email")):
                try:
                    files = get_cv_files()
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "language": global_language,
                        "tone": email_tone,
                        "company_name": comp_name or "",
                        "position_title": pos_title or ""
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/application-email",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("templates_ready"))
                        
                        st.subheader(f"{t('email_subject')}: {result.get('subject')}")
                        st.text_area(t("email_body"), value=result.get("email_body"), height=250)
                        
                        st.subheader(t("linkedin_msg"))
                        st.text_area(t("linkedin_msg"), value=result.get("short_linkedin_message"), height=120)
                        
                        st.subheader(t("follow_up_msg"))
                        st.text_area(t("follow_up_msg"), value=result.get("follow_up_message"), height=180)
                        
                        st.markdown("---")
                        render_download_buttons(t("nav_app_email"), result, "application_email")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "🤝 Interview Prep":
    st.header(t("nav_interview_prep"))

    if validate_inputs(require_cv=False):
        if st.button(t("btn_gen_prep")):
            with st.spinner(t("spinner_prep")):
                try:
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "language": global_language
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/interview-prep",
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        
                        st.subheader(t("tech_questions"))
                        for idx, item in enumerate(result.get("technical_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader(t("hr_questions"))
                        for idx, item in enumerate(result.get("hr_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()

                        st.subheader(t("challenge_questions"))
                        for idx, item in enumerate(result.get("challenging_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader(t("prep_tips"))
                        for tip in result.get("preparation_tips", []):
                            st.write(f"- {tip}")
                            
                        st.markdown("---")
                        render_download_buttons(t("nav_interview_prep"), result, "interview_prep")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "🎯 Personalized Interview":
    st.header(t("nav_personalized_interview"))

    prep_diff = st.selectbox(t("difficulty"), ["easy", "medium", "hard"])

    if validate_inputs():
        if st.button(t("btn_gen_custom_prep")):
            with st.spinner(t("spinner_personalized_prep")):
                try:
                    files = get_cv_files()
                    data = {
                        "job_text": st.session_state.global_job_text,
                        "language": global_language,
                        "difficulty": prep_diff
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/personalized-interview-prep",
                        files=files,
                        data=data
                    )
                    if response.status_code == 200:
                        res = response.json()
                        result = res["result"]
                        
                        st.success(t("status_complete"))
                        
                        st.subheader(t("tech_questions"))
                        for idx, item in enumerate(result.get("technical_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader(t("cv_questions"))
                        for idx, item in enumerate(result.get("cv_based_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()

                        st.subheader(t("weak_questions"))
                        for idx, item in enumerate(result.get("weak_area_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader(t("sample_answers"))
                        for sa in result.get("sample_answers", []):
                            st.markdown(f"**Q: {sa.get('question')}**")
                            st.write(f"💬 Sample Answer: {sa.get('sample_answer')}")
                            st.divider()

                        st.subheader(t("prep_plan"))
                        for step in result.get("preparation_plan", []):
                            st.write(f"- 📋 {step}")
                            
                        st.markdown("---")
                        render_download_buttons(t("nav_personalized_interview"), result, "personalized_interview_prep")
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "💼 Job Recommendations":
    st.header(t("nav_job_recommendations"))
    
    if validate_inputs(require_cv=True, require_job=False):
        col_loc, col_remote = st.columns([2, 1])
        with col_loc:
            location_input = st.text_input(t("location_label"), value="")
        with col_remote:
            st.write("")
            st.write("")
            remote_preference = st.checkbox(t("remote_label"), value=False)
            
        col_provider, col_lang = st.columns(2)
        with col_provider:
            provider_choice = st.selectbox(
                t("provider_label"),
                ["Auto", "SerpAPI Google Jobs", "Jooble", "Adzuna"],
                key="rec_provider_choice"
            )
        with col_lang:
            result_lang = st.selectbox(t("output_lang"), ["Turkish", "English"], key="rec_result_lang")
            
        provider_map = {
            "Auto": "auto",
            "SerpAPI Google Jobs": "serpapi",
            "Jooble": "jooble",
            "Adzuna": "adzuna"
        }
        provider_param = provider_map[provider_choice]
        
        if st.button(t("find_suitable_jobs")):
            with st.spinner(t("spinner_recommendations")):
                try:
                    files = get_cv_files()
                    data = {
                        "location": location_input,
                        "remote": str(remote_preference).lower(),
                        "language": result_lang,
                        "provider": provider_param
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/job-recommendations/recommended-jobs",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        res = response.json()
                        st.success(t("status_complete"))
                        
                        profile = res.get("candidate_profile", {})
                        st.subheader(f"👤 {t('candidate_profile')}")
                        st.write(f"**{t('summary')}:** {profile.get('profile_summary', '')}")
                        st.write(f"**Experience Level:** {profile.get('experience_level', '')}")
                        st.write(f"**Target Roles:** {', '.join(profile.get('target_roles', []))}")
                        st.write(f"**Technical Skills:** {', '.join(profile.get('technical_skills', []))}")
                        st.write(f"**Soft Skills:** {', '.join(profile.get('soft_skills', []))}")
                        st.write(f"**Preferred Job Types:** {', '.join(profile.get('preferred_job_types', []))}")
                        st.write("---")
                        
                        queries = res.get("search_queries", [])
                        st.subheader(f"🔍 {t('search_queries')}")
                        for q in queries:
                            st.write(f"- {q}")
                        st.write("---")
                        
                        tried_q = res.get("tried_queries", [])
                        if tried_q:
                            st.subheader(f"🔄 {t('tried_searches')}")
                            for idx, tq in enumerate(tried_q):
                                st.write(
                                    f"**{idx+1}.** Query: `{tq.get('query')}` | "
                                    f"Location: `{tq.get('location') or 'Anywhere'}` | "
                                    f"Remote: `{tq.get('remote')}` | "
                                    f"Results: `{tq.get('result_count')}`"
                                )
                            st.write("---")
                            
                        tried_prov = res.get("tried_providers", [])
                        if tried_prov:
                            st.subheader(f"🔌 {t('tried_providers_label')}")
                            for tp in tried_prov:
                                status_emoji = "✅" if tp.get("status") == "success" else "❌"
                                st.write(
                                    f"- **{tp.get('provider').upper()}**: {status_emoji} "
                                    f"Status: `{tp.get('status')}` | "
                                    f"Results: `{tp.get('result_count')}`"
                                )
                            st.write("---")
                        
                        rec_jobs = res.get("recommended_jobs", [])
                        summary = res.get("summary", "")
                        st.subheader(f"💼 {t('recommended_jobs')}")
                        if summary:
                            st.info(summary)
                            
                        for idx, job in enumerate(rec_jobs):
                            with st.expander(
                                f"🎯 Match {job.get('match_score')}% | {job.get('title')} at {job.get('company')} ({job.get('location')})"
                            ):
                                st.markdown(f"**Source / Kaynak:** {job.get('source', 'N/A')}")
                                if job.get("via"):
                                    st.markdown(f"**Via / Aracılığıyla:** {job.get('via')}")
                                if job.get("posted_date"):
                                    st.markdown(f"**Posted / Yayınlanma:** {job.get('posted_date')}")
                                    
                                st.markdown(f"##### {t('strengths')}")
                                st.write(", ".join(job.get("matched_skills", [])))
                                
                                st.markdown(f"##### {t('weaknesses')}")
                                st.write(", ".join(job.get("missing_skills", [])))
                                
                                st.markdown(f"##### Rationale / Açıklama")
                                st.write(job.get("why_good_match", ""))
                                
                                st.markdown(f"##### Application Tip / Başvuru İpucu")
                                st.write(job.get("application_tip", ""))
                                
                                url = job.get("url", "")
                                st.markdown("##### Apply Link / Başvuru Linki")
                                if url:
                                    st.link_button("🔗 Open Job / İlanı Aç", url)
                                else:
                                    st.info(t("no_apply_link"))
                                    
                        st.markdown("---")
                        render_download_buttons(t("nav_job_recommendations"), res, "job_recommendations_report")
                    else:
                        try:
                            err_detail = response.json().get("detail", "")
                        except Exception:
                            err_detail = response.text
                            
                        if "serpapi" in err_detail.lower():
                            st.error(t("missing_key_warning"))
                        else:
                            st.error(f"{t('status_error')} {err_detail}")
                except Exception as e:
                    st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "📜 History":
    st.header(t("nav_history"))
    st.write(t("history_desc"))

    history_items = []
    
    st.subheader(t("filter_op"))
    filter_type = st.selectbox(
        t("filter_op"),
        [t("all"), "analyze", "cover_letter", "interview", "ats_score", "ats_cv_builder", "job_keywords", "cv_improvement", "tailored_cv", "cv_rewrite", "application_email", "personalized_interview", "cv_profile", "ranked_jobs", "recommended_jobs", "job_search"],
        label_visibility="collapsed"
    )
    
    col_a, col_b = st.columns([1, 4])
    with col_a:
        if st.button(t("btn_refresh")):
            st.rerun()
    with col_b:
        confirm_clear = st.checkbox(t("confirm_clear"))
        if confirm_clear:
            if st.button(t("btn_clear_history")):
                try:
                    res = requests.delete(f"{API_BASE_URL}/history")
                    if res.status_code == 200:
                        st.success(t("all_deleted"))
                        st.rerun()
                    else:
                        st.error(res.text)
                except Exception as e:
                    st.error(str(e))

    try:
        url = f"{API_BASE_URL}/history"
        if filter_type != t("all") and filter_type != "all":
            url += f"?request_type={filter_type}"
        response = requests.get(url)
        history_items = response.json() if response.status_code == 200 else []
    except Exception as e:
        st.error(f"{t('status_error')} {str(e)}")

    st.markdown("---")
    
    if not history_items:
        st.info("No records found for this selection.")
    else:
        for item in history_items:
            with st.expander(
                f"ID #{item['id']} - [{item['request_type'].upper()}] - {item['created_at'].split('T')[0]} {item['created_at'].split('T')[1][:5]}"
            ):
                st.write(f"**{t('cv_file_label')}** {item.get('cv_filename') or 'N/A'}")
                st.write(f"**{t('job_excerpt')}**")
                st.text(item.get("job_text")[:200] + "..." if item.get("job_text") else "N/A")
                
                st.write(f"**{t('output_label')}**")
                raw_res = item.get("result")
                if item.get("request_type") == "ats_cv_builder" and isinstance(raw_res, dict):
                    history_ats_cv = raw_res.get("ats_cv", {})
                    history_template = raw_res.get("template", {})
                    history_metadata = history_ats_cv.get("ats_metadata", {})
                    history_contact = history_ats_cv.get("contact", {})

                    st.write(f"**Template:** {history_template.get('name', 'N/A')}")
                    st.write(f"**{t('target_role')}:** {history_metadata.get('target_role') or 'N/A'}")
                    st.write(f"**Target Title:** {history_contact.get('target_title') or 'N/A'}")
                    st.write(
                        f"**{t('ats_score_before')}:** {history_metadata.get('ats_score_before', 0)} | "
                        f"**{t('ats_score_after')}:** {history_metadata.get('ats_score_after', 0)}"
                    )
                    st.write(f"**{t('optimization_summary')}:** {history_metadata.get('optimization_summary', '')}")
                    st.markdown("##### Metadata")
                    st.json(history_metadata)
                    st.markdown("##### Preview")
                    render_ats_cv_preview(history_ats_cv)
                else:
                    st.json(raw_res) if isinstance(raw_res, dict) else st.write(raw_res)
                
                # Expandable Download Buttons for History Details
                st.markdown("##### Downloads")
                render_download_buttons(item['request_type'], raw_res, f"history_{item['request_type']}_{item['id']}")
                
                # Delete Single Record Button
                if st.button(f"🗑️ Delete Record #{item['id']}", key=f"del_{item['id']}"):
                    try:
                        res = requests.delete(f"{API_BASE_URL}/history/{item['id']}")
                        if res.status_code == 200:
                            st.success(t("record_deleted"))
                            st.rerun()
                        else:
                            st.error(res.text)
                    except Exception as e:
                        st.error(str(e))
