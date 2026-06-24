import json
import hashlib
import re
import requests
import os
import streamlit as st
from datetime import datetime
from fpdf import FPDF
from urllib.parse import urlencode

from services.ats_cv_postprocessing import (
    extract_contact_fields_from_cv_text,
    extract_proper_nouns_from_cv_text,
)
from services.file_parser_service import extract_text_from_docx, extract_text_from_pdf

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
        "nav_job_url": "Linkten İlan Çıkar",
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
        "nav_job_monitoring": "🛰️ İş İlanı Takip Agentı",
        "nav_history": "📜 Geçmiş",
        "nav_job_workspace": "💼 İş Alanı",
        "nav_cv_tools": "🔍 CV Araçları",
        "nav_application_materials": "✉️ Başvuru Materyalleri",
        "override_inputs_title": "⚙️ Genel Dosyaları Geçersiz Kıl / Özel Giriş Kullan (İsteğe Bağlı)",
        "override_cv_label": "Bu sayfa için farklı bir CV yükle (İsteğe Bağlı):",
        "override_job_label": "Bu sayfa için farklı bir iş ilanı girin (İsteğe Bağlı):",
        # Job Workspace tab labels
        "tab_jobs": "İlanlar",
        "tab_add_job": "İlan Ekle",
        "tab_search_profiles": "Arama Profilleri",
        "tab_sources": "Kaynaklar",
        "tab_pipeline": "Pipeline",
        "tab_assets": "Materyaller",
        "job_workspace_desc": "İş ilanlarınızı yönetin, arama profillerini takip edin, başvuru sürecini izleyin ve başvuru materyalleri oluşturun.",
        
        # Validation & Warnings
        "please_upload_cv": "⚠️ Lütfen sol menüden bir CV dosyası yükleyin.",
        "please_enter_job_desc": "⚠️ Lütfen sol menüye bir iş ilanı metni girin.",
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
        "db_demo_workflow": "Demo Akışı",
        "db_demo_step_1": "1. CV yükleyin.",
        "db_demo_step_2": "2. İş açıklamasını yapıştırın veya tek tıklamayla manuel linkten çıkarmayı deneyin.",
        "db_demo_step_3": "3. Job Workspace içinde manuel ilan ekleyin.",
        "db_demo_step_4": "4. İlanı analiz edin ve eşleşme skorunu inceleyin.",
        "db_demo_step_5": "5. Pipeline aşamasını, önceliği ve notları güncelleyin.",
        "db_demo_step_6": "6. Özelleştirilmiş CV, kapak yazısı ve başvuru e-postası oluşturun.",
        "db_recent_history": "⏱️ Son İşlem Geçmişi",
        "db_no_history": "Geçmişte işlem bulunmamaktadır. Sol menüyü kullanarak ilk analizini başlat!",
        
        # Pages specific
        "job_url_desc": "İsteğe bağlı olarak tek bir bağlantıdan ilan metnini çıkarmayı deneyin. Başarısız olursa manuel yapıştırın.",
        "job_url_label": "İş İlanı URL'sini Girin:",
        "btn_extract_job": "Çıkar",
        "set_active_job": "Aktif İş İlanı Olarak Ayarla",
        "extraction_success": "İş ilanı başarıyla çıkarıldı!",
        "extraction_save_success": "İş ilanı kaydedildi! Sol menüdeki kutuya aktarıldı.",
        
        # Status & Spinners
        "status_complete": "İşlem tamamlandı!",
        "status_error": "Bir hata oluştu:",
        "spinner_job": "İlan açıklaması çıkarılıyor...",
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

        # Job Monitoring Agent
        "job_monitoring_desc": "Düşük frekanslı iş ilanı alarmları oluşturun, güvenli mock takip çalıştırın, ilanları profilinize göre puanlayın ve kaydedilen/reddedilen/başvurulan fırsatları takip edin. Gerçek ilan kaynağı adaptörleri sonraki fazlarda eklenecektir.",
        "jm_alert_form": "Alarm Profili",
        "jm_alert_name": "Alarm adı",
        "jm_keywords": "Anahtar kelimeler",
        "jm_keywords_help": "Virgülle ayırabilirsiniz.",
        "jm_location": "Konum",
        "jm_seniority": "Kıdem",
        "jm_job_type": "İş tipi",
        "jm_work_model": "Çalışma modeli",
        "jm_sources": "Kaynaklar",
        "jm_excluded_keywords": "Hariç tutulacak anahtar kelimeler",
        "jm_min_score": "Minimum eşleşme skoru",
        "jm_active": "Aktif",
        "jm_create_alert": "Alarm oluştur",
        "jm_existing_alerts": "Mevcut Alarm Profilleri",
        "jm_run_now": "Şimdi çalıştır",
        "jm_deactivate": "Pasifleştir",
        "jm_job_results": "İlan Sonuçları",
        "jm_run_history": "Çalıştırma Geçmişi",
        "jm_status_filter": "Durum filtresi",
        "jm_all_statuses": "Tüm durumlar",
        "jm_save": "Kaydet",
        "jm_reject": "Reddet",
        "jm_mark_applied": "Başvuruldu olarak işaretle",
        "jm_archive": "Arşivle",
        "jm_placeholder": "Başvuru materyallerini doğrudan buradan oluşturabilirsiniz.",
        "jm_assets_section": "Başvuru Materyali Oluştur",
        "jm_upload_cv": "CV Dosyası Yükle (PDF/DOCX)",
        "jm_lang_select": "Çıktı Dili",
        "jm_template_select": "CV Şablonu",
        "jm_tone_select": "E-posta/Kapak Yazısı Tonu",
        "jm_generate_cv": "Özelleştirilmiş CV Oluştur",
        "jm_generate_cover": "Kapak Yazısı Oluştur",
        "jm_generate_email": "Başvuru E-postası Oluştur",
        "jm_existing_assets": "Oluşturulmuş Materyaller",
        "jm_asset_type": "Materyal Tipi",
        "jm_created_at": "Oluşturulma Tarihi",
        "jm_export_format": "Format",
        "jm_download": "İndir",
        "jm_preview": "Önizleme",
        "jm_cv_uploaded_success": "CV başarıyla analiz için yüklendi.",
        "jm_alert_deactivated": "Alarm profili pasifleştirildi.",
        "jm_run_complete": "Mock takip çalışması tamamlandı.",
        "jm_status_updated": "İlan durumu güncellendi.",
        "jm_no_alerts": "Henüz alarm profili yok.",
        "jm_no_jobs": "Henüz izlenen ilan yok. Add Job sekmesinden manuel ilan ekleyin veya Search Profiles sekmesinde manual_mock çalıştırın.",
        "jm_no_pipeline_jobs": "Henüz pipeline kaydı yok. Bir ilan ekleyip Jobs sekmesinden aşama, öncelik ve notları kaydedin.",
        "jm_no_assets": "Henüz materyal oluşturulmadı. Bir ilan açın, global CV yükleyin ve Generate Materials bölümünden başlayın.",
        "jm_no_job_assets": "Bu ilan için henüz materyal oluşturulmadı.",
        "jm_search_profile_help": "Search Profile, manual_mock kaynağından güvenli demo sonuçları üretir. Gerçek iş ilanı kaynakları bu fazda çalıştırılmaz.",
        "jm_global_cv_default": "Global CV varsayılan olarak kullanılır",
        "jm_global_cv_missing": "Sidebar'da global CV yok. Materyal oluşturmak için CV yükleyin veya isteğe bağlı override kullanın.",
        "jm_add_job_next_step": "Başlık, şirket ve ilan açıklaması yeterlidir. URL yalnızca metin olarak saklanır.",
        "jm_no_runs": "Henüz çalıştırma geçmişi yok.",
        "jm_manual_import": "Manuel İlan Ekle",
        "jm_manual_import_desc": "Gerçek bir iş ilanını manuel olarak yapıştırın. Uygulama ilanı kaydeder, seçilen alert profiline göre puanlar ve durumunu takip etmenizi sağlar. URL yalnızca metin olarak saklanır; bu fazda ilan sitelerinden otomatik veri çekilmez.",
        "jm_select_alert_optional": "Puanlama için alert profili seçin (isteğe bağlı)",
        "jm_no_alert_selected": "Alert profili yok",
        "jm_job_title": "İlan başlığı",
        "jm_company": "Şirket",
        "jm_source": "Kaynak",
        "jm_job_url": "İlan URL",
        "jm_posted_date": "Yayın tarihi",
        "jm_job_description": "İlan açıklaması",
        "jm_add_manual_job": "Manuel ilan ekle",
        "jm_extract_desc_from_url": "Linkten ilan açıklaması çıkar",
        "jm_manual_job_added": "Manuel ilan kaydedildi.",
        "jm_duplicate_updated": "Bu ilan zaten vardı; mevcut kayıt güncellendi, yeni kopya oluşturulmadı.",
        "jm_rescore": "Yeniden puanla",
        "jm_rescore_profile": "Yeniden puanlama profili",
        "jm_rescored": "İlan yeniden puanlandı.",
        "jm_source_filter": "Kaynak filtresi",
        "jm_sources_phase3a_note": "Phase 3A kaynak adaptör altyapısını hazırlar. Şu anda yalnızca manual_mock çalıştırılabilir. Gerçek iş ilanı kaynakları henüz uygulanmamıştır.",
        "jm_source_settings_saved": "Kaynak ayarları kaydedildi.",
        "jm_source_test": "Kaynağı Test Et",
        "jm_source_update": "Ayarları Kaydet",
        "jm_source_disabled": "Devre Dışı",
        "jm_source_enabled": "Aktif",
        "jm_alert_filter": "Alert profili filtresi",
        "jm_min_score_filter": "Minimum skor filtresi",
        "jm_all_sources": "Tüm kaynaklar",
        "jm_all_alerts": "Tüm alert profilleri",
        "jm_detected_family": "İş Ailesi",
        "jm_detected_seniority": "Kıdem Seviyesi",
        "jm_recommendation": "Başvuru Önerisi",
        "jm_role_summary": "Rol Özeti",
        "jm_match_reason": "Eşleşme Gerekçesi",
        "jm_strengths": "Güçlü Yönler",
        "jm_gaps": "Geliştirilmesi Gereken Yönler",
        "jm_missing_keywords_lbl": "Eksik Anahtar Kelimeler",
        "jm_suggested_cv_focus": "Önerilen CV Odağı",
        "jm_suggested_project_focus": "Önerilen Proje Odağı",
        "jm_suggested_skill_focus": "Önerilen Yetkinlik Odağı",
        "jm_risk_notes": "Risk / Dikkat Edilmesi Gereken Hususlar",
        "jm_interview_focus": "Mülakat Hazırlık Konuları",
        "jm_analyze_job": "İlanı analiz et",
        "jm_analysis_report": "İlan Analiz Raporu",
        "jm_select_alert_for_analysis": "Analiz için alert profili seçin",
        "jm_use_associated_alert": "İlanın mevcut alert profilini kullan",
        "jm_analysis_complete": "İlan analizi tamamlandı.",
        "jm_pipeline_title": "Başvuru Takip Süreci",
        "jm_pipeline_stage": "Süreç Aşaması",
        "jm_pipeline_priority": "Öncelik",
        "jm_pipeline_materials": "Belgelerin Durumu",
        "jm_pipeline_deadline": "Son Başvuru Tarihi",
        "jm_pipeline_applied_at": "Başvuru Tarihi",
        "jm_pipeline_next_action": "Sonraki Adım",
        "jm_pipeline_next_action_date": "Sonraki Adım Tarihi",
        "jm_pipeline_interview_date": "Mülakat Tarihi",
        "jm_pipeline_contact_person": "İletişim Kişisi",
        "jm_pipeline_contact_email": "İletişim E-postası",
        "jm_pipeline_notes": "Başvuru Notları",
        "jm_save_pipeline": "Süreci Kaydet",
        "jm_pipeline_updated": "Başvuru süreci güncellendi.",
        "jm_pipeline_overview": "Süreç Genel Bakış",
        "jm_upcoming_actions": "Yaklaşan Adımlar",
        "jm_upcoming_deadlines": "Yaklaşan Son Başvurular",
        "jm_high_priority": "Yüksek Öncelikli İlanlar",

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
        "score_improvement": "İyileşme",
        "used_keywords": "Doğrudan Kullanılan Anahtar Kelimeler",
        "transferable_keywords": "Aktarılabilir Anahtar Kelimeler",
        "risky_keywords_not_added": "Doğrudan Eklenmeyen Riskli Anahtar Kelimeler",
        "optimization_summary": "Optimizasyon Özeti",
        "target_role": "Hedef Pozisyon",
        "alignment_confidence": "Uyum Güveni",
        "adaptation_notes": "Uyarlama Notları",
        "ats_score_explanation": "ATS Skoru Açıklaması",
        "before_reason": "Önceki Skor Nedeni",
        "after_reason": "Sonraki Skor Nedeni",
        "improvement_reasons": "İyileştirme Nedenleri",
        "remaining_gaps": "Kalan Eksikler",
        "ats_score_disclaimer": "Bu skor tahmini bir ATS uygunluk skorudur, resmi bir ATS sonucu değildir.",
        "ats_cv_generic_note": "Bu oluşturucu, yüklenen CV’yi iş ilanına göre uyarlar. İletişim bilgileri ve özel isimler yüklenen CV’den kilitlenir ve oluşturma öncesinde düzenlenebilir.",
        "locked_contact_fields": "Kilitli İletişim Bilgileri",
        "locked_contact_warning": "Ad, e-posta veya telefon alanlarından biri boş. CV’den çıkarılamadıysa oluşturma öncesinde elle doldurabilirsiniz.",
        "locked_proper_nouns": "Kilitli Özel İsimler",
        "locked_full_name": "Ad Soyad",
        "locked_email": "E-posta",
        "locked_phone": "Telefon",
        "locked_location": "Konum",
        "locked_linkedin": "LinkedIn",
        "locked_github": "GitHub",
        "locked_portfolio": "Portföy",
        "optimize_one_page": "Tek sayfaya optimize et",
        "export_style": "Dışa Aktarım Stili",
        "export_style_standard": "Standart",
        "export_style_balanced": "Dengeli Tek Sayfa",
        "balanced_one_page_help": "Dengeli Tek Sayfa, önemli bilgileri koruyarak CV’yi ATS uyumlu şekilde tek sayfaya sığdırmaya çalışır.",
        "export_sections": "Dışa Aktarılacak Bölümler",
        "adaptation_level": "Uyarlama Seviyesi",
        "adaptation_conservative": "Temkinli",
        "adaptation_balanced": "Dengeli",
        "adaptation_strong": "Güçlü",
        "cv_quality_check": "CV Kalite Kontrolü",
        "structure_validation": "Yapı Doğrulama",
        "cv_quality_score": "CV Kalite Skoru",
        "structure_score": "Yapı Skoru",
        "needs_review": "İnceleme gerekli",
        "looks_clean": "Temiz görünüyor. Yine de göndermeden önce kontrol edin.",
        "critical_section_warning": "Kritik bölümleri devre dışı bırakmak CV'nin etkisini azaltabilir.",
        "key_section_warning": "Deneyim, Eğitim veya Yetenekler bölümlerini devre dışı bırakmak ATS uygunluğunu azaltabilir.",
        "contact": "Contact",
        "summary_section": "Summary",
        "skills_section": "Skills",
        "experience_section": "Experience",
        "projects_section": "Projects",
        "education_section": "Education",
        "certifications_section": "Certifications",
        "languages_section": "Languages",
        
        # History
        "history_desc": "Geçmiş başvuru değerlendirmelerinizi, analizleri ve taslakları inceleyin, filtreleyin veya silin.",
        "filter_op": "İşlem tipine göre filtrele:",
        "cv_file_label": "CV Dosyası:",
        "job_excerpt": "İş İlanı Özeti:",
        "output_label": "Oluşturulan Çıktı:",
        "all": "Hepsi",
        "record_deleted": "Kayıt silindi.",
        "all_deleted": "Tüm geçmiş kayıtları başarıyla silindi.",
        "docx_render_mode_label": "DOCX Oluşturma Modu",
        "docx_render_mode_prog": "Programatik DOCX",
        "docx_render_mode_tpl": "Şablon DOCX",
        "docx_template_select": "DOCX Şablonu Seçin",
        "docx_template_experimental_note": "Şablon DOCX deneyseldir ve ATS dostu tutulmuştur. Göndermeden önce formatı kontrol edin.",
        "docx_template_warning": "Şablon DOCX oluşturulamadı. Lütfen Programatik DOCX modunu kullanın.",
        "docx_template_guidance": "Şablon rehberi",
        "docx_best_for": "En uygun kullanım",
        "docx_style": "Stil",
        "docx_strengths": "Güçlü yönler",
        "docx_cautions": "Dikkat edilmesi gerekenler",
        "docx_recommended_for": "Önerilen roller",
        "docx_not_recommended_for": "Önerilmeyen durumlar",
        "docx_ats_safety": "ATS güvenliği",
        "docx_visual_density": "Görsel yoğunluk",
        "docx_layout": "Yerleşim"
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
        "nav_job_url": "Extract from URL",
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
        "nav_job_monitoring": "🛰️ Job Monitoring Agent",
        "nav_history": "📜 History",
        "nav_job_workspace": "💼 Job Workspace",
        "nav_cv_tools": "🔍 CV Tools",
        "nav_application_materials": "✉️ Application Materials",
        "override_inputs_title": "⚙️ Override Global CV / Job Description (Optional)",
        "override_cv_label": "Upload a different CV for this page (Optional):",
        "override_job_label": "Enter a different job description for this page (Optional):",
        # Job Workspace tab labels
        "tab_jobs": "Jobs",
        "tab_add_job": "Add Job",
        "tab_search_profiles": "Search Profiles",
        "tab_sources": "Sources",
        "tab_pipeline": "Pipeline",
        "tab_assets": "Assets",
        "job_workspace_desc": "Manage your job listings, track search alerts, view pipeline progress, and generate custom application materials.",
        
        # Validation & Warnings
        "please_upload_cv": "⚠️ Please upload your CV in the sidebar.",
        "please_enter_job_desc": "⚠️ Please provide a job description in the sidebar.",
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
        "db_demo_workflow": "Demo Workflow",
        "db_demo_step_1": "1. Upload a CV.",
        "db_demo_step_2": "2. Paste a job description or manually extract one link with a click.",
        "db_demo_step_3": "3. Add a job in Job Workspace.",
        "db_demo_step_4": "4. Analyze the job and review the match score.",
        "db_demo_step_5": "5. Update pipeline stage, priority, and notes.",
        "db_demo_step_6": "6. Generate a tailored CV, cover letter, and application email.",
        "db_recent_history": "⏱️ Recent History Highlights",
        "db_no_history": "No operations found in history. Start analyzing your first application using the side menu!",
        
        # Pages specific
        "job_url_desc": "Optionally try extracting job text from one link. If it fails, paste the description manually.",
        "job_url_label": "Enter Job Posting URL:",
        "btn_extract_job": "Extract",
        "set_active_job": "Set as Active Job Description",
        "extraction_success": "Job description extracted successfully!",
        "extraction_save_success": "Job description saved! You can view it on the sidebar now.",
        
        # Status & Spinners
        "status_complete": "Operation completed!",
        "status_error": "An error occurred:",
        "spinner_job": "Extracting job description...",
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

        # Job Monitoring Agent
        "job_monitoring_desc": "Create low-frequency job alerts, run safe mock monitoring, score jobs against your profile, and track saved/rejected/applied opportunities. Real job board adapters will be added in later phases.",
        "jm_alert_form": "Alert Profile",
        "jm_alert_name": "Alert name",
        "jm_keywords": "Keywords",
        "jm_keywords_help": "Comma-separated values are supported.",
        "jm_location": "Location",
        "jm_seniority": "Seniority",
        "jm_job_type": "Job type",
        "jm_work_model": "Work model",
        "jm_sources": "Sources",
        "jm_excluded_keywords": "Excluded keywords",
        "jm_min_score": "Minimum match score",
        "jm_active": "Active",
        "jm_create_alert": "Create alert",
        "jm_existing_alerts": "Existing Alert Profiles",
        "jm_run_now": "Run now",
        "jm_deactivate": "Deactivate",
        "jm_job_results": "Job Results",
        "jm_run_history": "Run History",
        "jm_status_filter": "Status filter",
        "jm_all_statuses": "All statuses",
        "jm_save": "Save",
        "jm_reject": "Reject",
        "jm_mark_applied": "Mark applied",
        "jm_archive": "Archive",
        "jm_placeholder": "You can generate application materials directly from here.",
        "jm_assets_section": "Generate Application Materials",
        "jm_upload_cv": "Upload CV File (PDF/DOCX)",
        "jm_lang_select": "Output Language",
        "jm_template_select": "CV Template",
        "jm_tone_select": "Email/Cover Letter Tone",
        "jm_generate_cv": "Generate Tailored CV",
        "jm_generate_cover": "Generate Cover Letter",
        "jm_generate_email": "Generate Application Email",
        "jm_existing_assets": "Generated Materials",
        "jm_asset_type": "Material Type",
        "jm_created_at": "Created At",
        "jm_export_format": "Format",
        "jm_download": "Download",
        "jm_preview": "Preview",
        "jm_cv_uploaded_success": "CV successfully uploaded for analysis.",
        "jm_alert_deactivated": "Alert profile deactivated.",
        "jm_run_complete": "Mock monitoring run completed.",
        "jm_status_updated": "Job status updated.",
        "jm_no_alerts": "No alert profiles yet.",
        "jm_no_jobs": "No monitored jobs yet. Add one manually in Add Job or run a Search Profile with manual_mock.",
        "jm_no_pipeline_jobs": "No pipeline records yet. Add a job, then save stage, priority, and notes from the Jobs tab.",
        "jm_no_assets": "No assets generated yet. Open a job, upload a global CV, and use Generate Materials.",
        "jm_no_job_assets": "No assets generated yet for this job.",
        "jm_search_profile_help": "Search Profiles can run the safe manual_mock source for demo data. Real job board sources are not runnable in this phase.",
        "jm_global_cv_default": "Uses global CV by default",
        "jm_global_cv_missing": "No global CV uploaded in the sidebar. Upload one or use the optional override before generating materials.",
        "jm_add_job_next_step": "Title, company, and description are enough to start. URLs are stored as text only.",
        "jm_no_runs": "No run history yet.",
        "jm_manual_import": "Manual Job Import",
        "jm_manual_import_desc": "Paste a real job posting manually. The app will store it, score it against a selected alert profile, and let you track its status. The URL is stored only as text; the app does not scrape job boards in this phase.",
        "jm_select_alert_optional": "Select alert profile for scoring (optional)",
        "jm_no_alert_selected": "No alert profile",
        "jm_job_title": "Job title",
        "jm_company": "Company",
        "jm_source": "Source",
        "jm_job_url": "Job URL",
        "jm_posted_date": "Posted date",
        "jm_job_description": "Job description",
        "jm_add_manual_job": "Add manual job",
        "jm_extract_desc_from_url": "Extract description from URL",
        "jm_manual_job_added": "Manual job saved.",
        "jm_duplicate_updated": "This job already existed; the existing record was updated instead of duplicated.",
        "jm_rescore": "Rescore",
        "jm_rescore_profile": "Rescore profile",
        "jm_rescored": "Job rescored.",
        "jm_source_filter": "Source filter",
        "jm_sources_phase3a_note": "Phase 3A prepares the source adapter system. Only manual_mock is runnable. Real job board adapters are not implemented yet.",
        "jm_source_settings_saved": "Source settings saved.",
        "jm_source_test": "Test Source",
        "jm_source_update": "Save Settings",
        "jm_source_disabled": "Disabled",
        "jm_source_enabled": "Enabled",
        "jm_alert_filter": "Alert profile filter",
        "jm_min_score_filter": "Minimum score filter",
        "jm_all_sources": "All sources",
        "jm_all_alerts": "All alert profiles",
        "jm_detected_family": "Job Family",
        "jm_detected_seniority": "Seniority Level",
        "jm_recommendation": "Recommendation",
        "jm_role_summary": "Role Summary",
        "jm_match_reason": "Match Reason",
        "jm_strengths": "Candidate Strengths",
        "jm_gaps": "Candidate Gaps",
        "jm_missing_keywords_lbl": "Missing Keywords",
        "jm_suggested_cv_focus": "Suggested CV Focus",
        "jm_suggested_project_focus": "Suggested Project Focus",
        "jm_suggested_skill_focus": "Suggested Skill Focus",
        "jm_risk_notes": "Risk Notes / Warnings",
        "jm_interview_focus": "Interview Focus Areas",
        "jm_analyze_job": "Analyze job",
        "jm_analysis_report": "Job Analysis Report",
        "jm_select_alert_for_analysis": "Select alert profile for analysis",
        "jm_use_associated_alert": "Use job's current alert profile",
        "jm_analysis_complete": "Job analysis completed.",
        "jm_pipeline_title": "Application Pipeline",
        "jm_pipeline_stage": "Application Stage",
        "jm_pipeline_priority": "Priority",
        "jm_pipeline_materials": "Materials Status",
        "jm_pipeline_deadline": "Application Deadline",
        "jm_pipeline_applied_at": "Applied At",
        "jm_pipeline_next_action": "Next Action",
        "jm_pipeline_next_action_date": "Next Action Date",
        "jm_pipeline_interview_date": "Interview Date",
        "jm_pipeline_contact_person": "Contact Person",
        "jm_pipeline_contact_email": "Contact Email",
        "jm_pipeline_notes": "Application Notes",
        "jm_save_pipeline": "Save Pipeline",
        "jm_pipeline_updated": "Application pipeline updated.",
        "jm_pipeline_overview": "Pipeline Overview",
        "jm_upcoming_actions": "Upcoming Actions",
        "jm_upcoming_deadlines": "Upcoming Deadlines",
        "jm_high_priority": "High Priority Jobs",

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
        "score_improvement": "Improvement",
        "used_keywords": "Directly Used Keywords",
        "transferable_keywords": "Transferable Keywords",
        "risky_keywords_not_added": "Risky Keywords Not Added",
        "optimization_summary": "Optimization Summary",
        "target_role": "Target Role",
        "alignment_confidence": "Alignment Confidence",
        "adaptation_notes": "Adaptation Notes",
        "ats_score_explanation": "ATS Score Explanation",
        "before_reason": "Before Reason",
        "after_reason": "After Reason",
        "improvement_reasons": "Improvement Reasons",
        "remaining_gaps": "Remaining Gaps",
        "ats_score_disclaimer": "This is an estimated ATS relevance score, not an official ATS result.",
        "ats_cv_generic_note": "This builder adapts the uploaded CV to the job description. Contact fields and proper nouns are locked from the uploaded CV and can be edited before generation.",
        "locked_contact_fields": "Locked Contact Fields",
        "locked_contact_warning": "Full name, email, or phone is empty. If extraction missed it, you can fill it manually before generation.",
        "locked_proper_nouns": "Locked Proper Nouns",
        "locked_full_name": "Full Name",
        "locked_email": "Email",
        "locked_phone": "Phone",
        "locked_location": "Location",
        "locked_linkedin": "LinkedIn",
        "locked_github": "GitHub",
        "locked_portfolio": "Portfolio",
        "optimize_one_page": "Optimize for one page",
        "export_style": "Export Style",
        "export_style_standard": "Standard",
        "export_style_balanced": "Balanced One Page",
        "balanced_one_page_help": "Balanced One Page keeps the CV ATS-friendly while trying to fit content onto one page without removing key information.",
        "export_sections": "Export Sections",
        "adaptation_level": "Adaptation Level",
        "adaptation_conservative": "Conservative",
        "adaptation_balanced": "Balanced",
        "adaptation_strong": "Strong",
        "cv_quality_check": "CV Quality Check",
        "structure_validation": "Structure Validation",
        "cv_quality_score": "CV Quality Score",
        "structure_score": "Structure Score",
        "needs_review": "Needs review",
        "looks_clean": "Looks clean. Still review before sending.",
        "critical_section_warning": "Disabling critical sections may reduce the CV's effectiveness.",
        "key_section_warning": "Disabling Experience, Education, or Skills may reduce ATS relevance.",
        "contact": "Contact",
        "summary_section": "Summary",
        "skills_section": "Skills",
        "experience_section": "Experience",
        "projects_section": "Projects",
        "education_section": "Education",
        "certifications_section": "Certifications",
        "languages_section": "Languages",
        
        # History
        "history_desc": "Browse, filter, review, and delete records of past evaluations and drafts.",
        "filter_op": "Filter by operation type:",
        "cv_file_label": "CV Filename:",
        "job_excerpt": "Job Description Excerpt:",
        "output_label": "Generated Output:",
        "all": "All",
        "record_deleted": "Record deleted.",
        "all_deleted": "All history deleted successfully.",
        "docx_render_mode_label": "DOCX Render Mode",
        "docx_render_mode_prog": "Programmatic DOCX",
        "docx_render_mode_tpl": "Template DOCX",
        "docx_template_select": "Select DOCX Template",
        "docx_template_experimental_note": "Template DOCX is experimental and ATS-friendly. Review formatting before sending.",
        "docx_template_warning": "Template DOCX rendering failed. Please fallback to Programmatic DOCX mode.",
        "docx_template_guidance": "Template guidance",
        "docx_best_for": "Best for",
        "docx_style": "Style",
        "docx_strengths": "Strengths",
        "docx_cautions": "Cautions",
        "docx_recommended_for": "Recommended for",
        "docx_not_recommended_for": "Not recommended for",
        "docx_ats_safety": "ATS safety",
        "docx_visual_density": "Visual density",
        "docx_layout": "Layout"
    }
}

# Ensure session state variables exist
if "global_job_text" not in st.session_state:
    st.session_state.global_job_text = ""
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "en"

ATS_LOCKED_CONTACT_DEFAULTS = {
    "locked_full_name": "",
    "locked_email": "",
    "locked_phone": "",
    "locked_location": "",
    "locked_linkedin": "",
    "locked_github": "",
    "locked_portfolio": "",
}

ATS_LOCKED_PROPER_NOUNS = {
    "schools": [],
    "companies": [],
    "projects": [],
    "certifications": [],
}

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

with st.sidebar.expander(t("nav_job_url"), expanded=False):
    st.caption(t("job_url_desc"))
    sidebar_job_url = st.text_input(t("job_url_label"), placeholder="https://...", key="sidebar_job_url")
    if st.button(t("btn_extract_job"), key="sidebar_btn_extract_job"):
        if not sidebar_job_url.strip():
            st.warning("Geçerli bir http/https URL girin." if st.session_state.ui_lang == "tr" else "Enter a valid http/https URL.")
        else:
            with st.spinner(t("spinner_job")):
                result = None
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/extract-job-description",
                        json={"url": sidebar_job_url, "language": "Turkish" if st.session_state.ui_lang == "tr" else "English"},
                        timeout=15,
                    )
                    if response.status_code == 200:
                        result = response.json()
                    else:
                        st.warning(
                            "Bu sayfa otomatik çıkarılamadı. Lütfen ilan açıklamasını manuel yapıştırın."
                            if st.session_state.ui_lang == "tr"
                            else "Could not extract this page automatically. Please paste the job description manually."
                        )
                except Exception:
                    st.warning(
                        "Bu sayfa otomatik çıkarılamadı. Lütfen ilan açıklamasını manuel yapıştırın."
                        if st.session_state.ui_lang == "tr"
                        else "Could not extract this page automatically. Please paste the job description manually."
                    )
            if result and result.get("success"):
                extracted_text = result.get("text") or result.get("extracted_text") or ""
                st.session_state["global_job_desc_input"] = extracted_text
                st.session_state.global_job_text = extracted_text
                if result.get("title"):
                    st.caption(result.get("title"))
                st.success(t("extraction_success"))
                st.rerun()
            elif result:
                fallback_msg = (
                    "Bu sayfa otomatik çıkarılamadı. Lütfen ilan açıklamasını manuel yapıştırın."
                    if st.session_state.ui_lang == "tr"
                    else "Could not extract this page automatically. Please paste the job description manually."
                )
                st.warning(result.get("message") or fallback_msg)

global_language = st.sidebar.selectbox(
    t("output_lang"),
    ["Turkish", "English"],
    key="global_language"
)

st.sidebar.markdown("---")

# Navigation Menu Options translated
menu_map = {
    "📊 Dashboard": "nav_dashboard",
    "💼 Job Workspace": "nav_job_workspace",
    "📄 ATS CV Builder": "nav_ats_cv_builder",
    "🔍 CV Tools": "nav_cv_tools",
    "✉️ Application Materials": "nav_application_materials",
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


def extract_uploaded_cv_text(uploaded_cv) -> str:
    if uploaded_cv is None:
        return ""

    file_bytes = uploaded_cv.getvalue()
    if not file_bytes:
        return ""

    try:
        if uploaded_cv.type == "application/pdf" or uploaded_cv.name.lower().endswith(".pdf"):
            return extract_text_from_pdf(file_bytes).strip()
        if (
            uploaded_cv.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or uploaded_cv.name.lower().endswith(".docx")
        ):
            return extract_text_from_docx(file_bytes).strip()
    except Exception:
        return ""

    return ""


def sync_ats_locked_fields_from_uploaded_cv(uploaded_cv) -> None:
    contact_keys = {
        "locked_full_name": "full_name",
        "locked_email": "email",
        "locked_phone": "phone",
        "locked_location": "location",
        "locked_linkedin": "linkedin",
        "locked_github": "github",
        "locked_portfolio": "portfolio",
    }

    if uploaded_cv is None:
        st.session_state["ats_cv_locked_source_fingerprint"] = ""
        st.session_state["cached_contact"] = {}
        st.session_state["cached_proper_nouns"] = ATS_LOCKED_PROPER_NOUNS.copy()
        st.session_state["cached_proper_nouns_json"] = json.dumps(ATS_LOCKED_PROPER_NOUNS, ensure_ascii=False, indent=2)
        for locked_key in contact_keys:
            st.session_state[f"ats_cv_{locked_key}"] = ""
        st.session_state["ats_cv_locked_proper_nouns"] = ATS_LOCKED_PROPER_NOUNS.copy()
        st.session_state["ats_cv_locked_proper_nouns_json"] = json.dumps(ATS_LOCKED_PROPER_NOUNS, ensure_ascii=False, indent=2)
        return

    file_bytes = uploaded_cv.getvalue()
    fingerprint = f"{uploaded_cv.name}:{len(file_bytes)}:{hashlib.sha256(file_bytes).hexdigest()}"

    # If fingerprint is different, extract again
    if st.session_state.get("ats_cv_locked_source_fingerprint") != fingerprint:
        cv_text = extract_uploaded_cv_text(uploaded_cv)
        st.session_state["cv_extraction_failed"] = not cv_text
        extracted_contact = extract_contact_fields_from_cv_text(cv_text) if cv_text else {}
        extracted_proper_nouns = extract_proper_nouns_from_cv_text(cv_text) if cv_text else ATS_LOCKED_PROPER_NOUNS.copy()
        
        st.session_state["cached_contact"] = extracted_contact
        st.session_state["cached_proper_nouns"] = extracted_proper_nouns
        st.session_state["cached_proper_nouns_json"] = json.dumps(extracted_proper_nouns, ensure_ascii=False, indent=2)
        st.session_state["ats_cv_locked_source_fingerprint"] = fingerprint

        # For a new CV upload, we must populate/overwrite the widget state
        for locked_key, contact_key in contact_keys.items():
            st.session_state[f"ats_cv_{locked_key}"] = extracted_contact.get(contact_key, "")
    else:
        # If fingerprint matches, we only populate the widget key if it got deleted (e.g. after switching pages)
        cached_contact = st.session_state.setdefault("cached_contact", {})
        for locked_key, contact_key in contact_keys.items():
            if f"ats_cv_{locked_key}" not in st.session_state:
                st.session_state[f"ats_cv_{locked_key}"] = cached_contact.get(contact_key, "")

    st.session_state["ats_cv_locked_proper_nouns"] = st.session_state.setdefault("cached_proper_nouns", ATS_LOCKED_PROPER_NOUNS.copy())
    if "ats_cv_locked_proper_nouns_json" not in st.session_state:
        st.session_state["ats_cv_locked_proper_nouns_json"] = st.session_state.get(
            "cached_proper_nouns_json",
            json.dumps(st.session_state["ats_cv_locked_proper_nouns"], ensure_ascii=False, indent=2)
        )


def get_effective_inputs(page_id: str, require_cv=True, require_job=True):
    """
    Returns (cv_file_dict_or_none, job_text, has_error, effective_cv_obj).
    Reuses global CV and job description by default.
    Provides optional override inputs in an expander.
    """
    has_error = False
    effective_cv_file = None
    effective_job_text = ""
    effective_cv_obj = None

    # Status summary
    st.markdown("##### " + t("nav_title") + " Settings")
    col1, col2 = st.columns(2)
    with col1:
        if global_cv is not None:
            st.caption(f"✓ Using global CV: **{global_cv.name}**")
            effective_cv_file = {
                "cv_file": (global_cv.name, global_cv.getvalue(), global_cv.type)
            }
            effective_cv_obj = global_cv
        else:
            st.caption("⚠️ No global CV uploaded in sidebar.")
            
    with col2:
        if st.session_state.get("global_job_desc_input", "").strip():
            st.caption("✓ Using global job description from sidebar.")
            effective_job_text = st.session_state.global_job_desc_input.strip()
        else:
            st.caption("⚠️ No global job description in sidebar.")

    # Optional override section
    override_exp = st.expander(t("override_inputs_title"), expanded=False)
    with override_exp:
        override_cv = st.file_uploader(
            t("override_cv_label"),
            type=["pdf", "docx"],
            key=f"override_cv_{page_id}"
        )
        if override_cv is not None:
            effective_cv_file = {
                "cv_file": (override_cv.name, override_cv.getvalue(), override_cv.type)
            }
            effective_cv_obj = override_cv
            st.info(f"Using override CV: {override_cv.name}")

        override_job = st.text_area(
            t("override_job_label"),
            value="",
            height=120,
            key=f"override_job_{page_id}"
        )
        if override_job.strip():
            effective_job_text = override_job.strip()
            st.info("Using override job description.")

    if require_cv and effective_cv_file is None:
        st.warning(t("please_upload_cv"))
        has_error = True

    if require_job and not effective_job_text:
        st.warning(t("please_enter_job_desc"))
        has_error = True

    return effective_cv_file, effective_job_text, has_error, effective_cv_obj


def validate_inputs(require_cv=True, require_job=True):
    if require_cv and global_cv is None:
        st.warning(t("please_upload_cv"))
        return False
    if require_job and not st.session_state.global_job_text.strip():
        st.warning(t("please_enter_job_desc"))
        return False
    return True


def parse_comma_values(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").replace("\n", ",").split(",") if item.strip()]


def api_json(method: str, path: str, timeout: int = 20, **kwargs):
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.exceptions.Timeout:
        st.error("Generation took too long. Please try again or check backend logs." if "assets" in path and method.upper() == "POST" else "Request took too long. Please try again.")
        return None
    except Exception as exc:
        st.error(f"{t('status_error')} {str(exc)}")
        return None

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        st.error(f"{t('status_error')} {detail}")
        return None

    try:
        return response.json()
    except Exception:
        return None


def compact_datetime(value: str) -> str:
    if not value:
        return "N/A"
    return str(value).replace("T", " ")[:16]

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


def adaptation_level_options():
    return [
        (t("adaptation_conservative"), "conservative"),
        (t("adaptation_balanced"), "balanced"),
        (t("adaptation_strong"), "strong"),
    ]


def safe_cv_filename(asset_type: str, template_id: str, extension: str) -> str:
    safe_asset_type = re.sub(r"[^a-z0-9_]+", "_", str(asset_type or "ats_cv").lower()).strip("_")
    safe_template_id = re.sub(r"[^a-z0-9_]+", "_", str(template_id or "classic_ats").lower()).strip("_")
    safe_extension = re.sub(r"[^a-z0-9]+", "", str(extension or "pdf").lower()) or "pdf"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{safe_asset_type}_{safe_template_id}_{timestamp}.{safe_extension}"


def unwrap_asset_structured_json(asset: dict) -> dict:
    structured = asset.get("structured_json") if isinstance(asset, dict) else {}
    return structured if isinstance(structured, dict) else {}


def get_asset_quality_report(asset: dict) -> dict:
    structured = unwrap_asset_structured_json(asset)
    return structured.get("quality_report") if isinstance(structured.get("quality_report"), dict) else {}


def get_asset_structure_report(asset: dict) -> dict:
    structured = unwrap_asset_structured_json(asset)
    return structured.get("structure_report") if isinstance(structured.get("structure_report"), dict) else {}


def render_docx_template_guidance_expander(template_info: dict) -> None:
    if not isinstance(template_info, dict) or not template_info:
        return
    with st.expander(t("docx_template_guidance"), expanded=False):
        st.markdown(f"**{t('docx_best_for')}:** {template_info.get('best_for', '')}")
        st.markdown(f"**{t('docx_style')}:** {template_info.get('visual_style', '')}")
        st.markdown(f"**{t('docx_layout')}:** {template_info.get('layout', '')}")
        st.markdown(f"**{t('docx_strengths')}:** {template_info.get('strengths', '')}")
        st.markdown(f"**{t('docx_cautions')}:** {template_info.get('cautions', '')}")
        st.markdown(f"**{t('docx_recommended_for')}:** {template_info.get('recommended_for', '')}")
        st.markdown(f"**{t('docx_not_recommended_for')}:** {template_info.get('not_recommended_for', '')}")
        st.markdown(f"**{t('docx_ats_safety')}:** {str(template_info.get('ats_safety_level', '')).upper()}")
        st.markdown(f"**{t('docx_visual_density')}:** {str(template_info.get('visual_density', '')).upper()}")


def render_quality_report(report: dict, title: str, score_key: str) -> None:
    report = report if isinstance(report, dict) else {}
    score = report.get(score_key)
    issues = report.get("issues", []) if isinstance(report.get("issues"), list) else []
    label = title
    if score is not None:
        label = f"{title} - {score}/100"
    with st.expander(label, expanded=bool(report.get("critical_count"))):
        if score is not None:
            st.metric(title, score)
        st.write(report.get("summary") or t("looks_clean"))
        if not issues:
            st.success(t("looks_clean"))
            return
        for issue in issues:
            severity = issue.get("severity", "info")
            message = f"**{severity.upper()} / {issue.get('category', 'general')}:** {issue.get('message', '')}"
            fix = issue.get("suggested_fix")
            if fix:
                message += f"\n\n{fix}"
            if severity == "critical":
                st.warning(message)
            elif severity == "warning":
                st.info(message)
            else:
                st.caption(message)


def quality_badge(asset: dict) -> str:
    report = get_asset_quality_report(asset)
    if not report:
        return ""
    score = report.get("quality_score")
    critical_count = int(report.get("critical_count") or 0)
    if critical_count:
        return f" | {t('needs_review')} | Q:{score}"
    return f" | Q:{score}"


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

def fetch_ats_cv_export(
    endpoint: str,
    ats_cv: dict,
    template_id: str,
    language: str,
    one_page: bool = False,
    enabled_sections: list[str] | None = None,
    export_style: str = "standard",
    docx_render_mode: str = "programmatic",
    docx_template_id: str = "",
) -> bytes | None:
    try:
        response = requests.post(
            f"{API_BASE_URL}/ats-cv/{endpoint}",
            data={
                "ats_cv_json": json.dumps(ats_cv, ensure_ascii=False),
                "template_id": template_id,
                "language": language,
                "one_page": str(one_page).lower(),
                "enabled_sections": json.dumps(enabled_sections) if enabled_sections is not None else "",
                "export_style": export_style,
                "docx_render_mode": docx_render_mode,
                "docx_template_id": docx_template_id,
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

    st.markdown(f"### {t('db_demo_workflow')}")
    st.write("\n".join([
        f"- {t('db_demo_step_1')}",
        f"- {t('db_demo_step_2')}",
        f"- {t('db_demo_step_3')}",
        f"- {t('db_demo_step_4')}",
        f"- {t('db_demo_step_5')}",
        f"- {t('db_demo_step_6')}",
    ]))

    st.markdown(f"### {t('db_features')}")
    col_feat1, col_feat2 = st.columns(2)
    with col_feat1:
        st.info(f"**🔍 {t('nav_cv_tools')}**\n\nUse the global CV and job description for CV analysis, ATS scoring, improvement suggestions, and section rewrites.")
        st.success(f"**💼 {t('nav_job_workspace')}**\n\nTrack jobs, manage pipeline notes, analyze roles, and generate job-specific materials from saved listings.")
    with col_feat2:
        st.warning(f"**✉️ {t('nav_application_materials')}**\n\nGenerate cover letters, application emails, and interview prep using the shared inputs.")
        st.info(f"**📄 {t('nav_ats_cv_builder')}**\n\nBuild ATS-friendly CV exports while preserving locked contact fields from the uploaded CV.")

    st.markdown(f"### {t('db_recent_history')}")
    if history_data:
        for idx, item in enumerate(history_data[:5]):
            st.markdown(f"**#{item['id']}** - **{item['request_type'].upper()}** | 📅 {item['created_at'].split('T')[0]} | 📂 {item.get('cv_filename') or 'None'}")
    else:
        st.info(t("db_no_history"))


elif selected_page_key == "🔍 CV Tools":
    st.header(t("nav_cv_tools"))
    
    cv_files, job_text, has_error, effective_cv_obj = get_effective_inputs("cv_tools", require_cv=True, require_job=True)
    
    if not has_error:
        tab1, tab2, tab3, tab4 = st.tabs([
            t("nav_cv_analysis"),
            t("nav_ats_score"),
            t("nav_cv_improvement"),
            t("nav_rewrite_section")
        ])
        
        with tab1:
            st.subheader(t("nav_cv_analysis"))
            if st.button(t("btn_analyze"), key="cv_tools_analyze_btn"):
                with st.spinner(t("spinner_analyze")):
                    try:
                        data = {
                            "job_text": job_text,
                            "language": global_language
                        }
                        response = requests.post(
                            f"{API_BASE_URL}/analyze",
                            files=cv_files,
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

        with tab2:
            st.subheader(t("nav_ats_score"))
            if st.button(t("btn_calculate_ats"), key="cv_tools_ats_btn"):
                with st.spinner(t("spinner_ats")):
                    try:
                        data = {
                            "job_text": job_text,
                            "language": global_language
                        }
                        response = requests.post(
                            f"{API_BASE_URL}/ats-score",
                            files=cv_files,
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

        with tab3:
            st.subheader(t("nav_cv_improvement"))
            if st.button(t("btn_gen_improvements"), key="cv_tools_improv_btn"):
                with st.spinner(t("spinner_improvements")):
                    try:
                        data = {
                            "job_text": job_text,
                            "language": global_language
                        }
                        response = requests.post(
                            f"{API_BASE_URL}/cv-improvement",
                            files=cv_files,
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

        with tab4:
            st.subheader(t("nav_rewrite_section"))
            sec_type = st.selectbox(t("select_section"), ["summary", "skills", "projects", "experience"], key="cv_tools_rewrite_sec_type")
            rewrite_tone = st.selectbox(t("select_tone"), ["professional", "confident", "concise"], key="cv_tools_rewrite_tone")
            
            if st.button(t("btn_rewrite"), key="cv_tools_rewrite_btn"):
                with st.spinner(t("spinner_rewrite")):
                    try:
                        data = {
                            "job_text": job_text,
                            "section_type": sec_type,
                            "language": global_language,
                            "tone": rewrite_tone
                        }
                        response = requests.post(
                            f"{API_BASE_URL}/rewrite-cv-section",
                            files=cv_files,
                            data=data
                        )
                        if response.status_code == 200:
                            res = response.json()
                            result = res["result"]
                            
                            st.success(t("status_complete"))
                            st.subheader(f"{t('nav_rewrite_section')} - {result.get('section_type').upper()} ({rewrite_tone.title()})")
                            st.text_area(t("output_label"), value=result.get("rewritten_content"), height=250, key="cv_tools_rewritten_val")
                            
                            st.subheader(t("rationale"))
                            st.info(result.get("explanation", ""))
                            
                            st.markdown("---")
                            render_download_buttons(t("nav_rewrite_section"), result, "cv_rewrite_report")
                        else:
                            st.error(response.text)
                    except Exception as e:
                        st.error(f"{t('status_error')} {str(e)}")


elif selected_page_key == "📄 ATS CV Builder":
    st.header(t("ats_cv_builder"))
    st.write(t("ats_cv_builder_next_phase"))
    st.info(t("ats_cv_generic_note"))

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
        st.caption(
            " | ".join(filter(None, [
                f"Style: {selected_template.get('style_level')}",
                f"ATS safety: {selected_template.get('ats_safety_level')}",
                f"Density: {selected_template.get('visual_density')}",
            ]))
        )

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
        adaptation_options = adaptation_level_options()
        selected_adaptation_label = st.selectbox(
            t("adaptation_level"),
            [label for label, _ in adaptation_options],
            index=1,
            key="ats_cv_adaptation_level_label",
        )
        selected_adaptation_level = dict(adaptation_options).get(selected_adaptation_label, "balanced")

        sync_ats_locked_fields_from_uploaded_cv(global_cv)

        if global_cv is not None and st.session_state.get("cv_extraction_failed"):
            st.warning("⚠️ Lütfen dikkat: Özgeçmişten metin/iletişim bilgileri otomatik ayıklanamadı. İletişim alanlarını manuel olarak doldurabilirsiniz. / Note: Could not extract contact fields automatically from the uploaded CV. Please fill them in manually.")

        st.subheader(t("locked_contact_fields"))
        locked_contact_values = {}
        locked_contact_rows = [
            ("locked_full_name", "locked_email"),
            ("locked_phone", "locked_location"),
            ("locked_linkedin", "locked_github"),
            ("locked_portfolio", None),
        ]
        for left_key, right_key in locked_contact_rows:
            left_col, right_col = st.columns(2)
            st.session_state.setdefault(f"ats_cv_{left_key}", ATS_LOCKED_CONTACT_DEFAULTS[left_key])
            with left_col:
                locked_contact_values[left_key] = st.text_input(
                    t(left_key),
                    key=f"ats_cv_{left_key}",
                )
            if right_key:
                st.session_state.setdefault(f"ats_cv_{right_key}", ATS_LOCKED_CONTACT_DEFAULTS[right_key])
                with right_col:
                    locked_contact_values[right_key] = st.text_input(
                        t(right_key),
                        key=f"ats_cv_{right_key}",
                    )

        # Update cached_contact so manual edits are not lost when switching pages!
        cached_contact = st.session_state.setdefault("cached_contact", {})
        contact_keys = {
            "locked_full_name": "full_name",
            "locked_email": "email",
            "locked_phone": "phone",
            "locked_location": "location",
            "locked_linkedin": "linkedin",
            "locked_github": "github",
            "locked_portfolio": "portfolio",
        }
        for k, ck in contact_keys.items():
            if k in locked_contact_values:
                cached_contact[ck] = locked_contact_values[k]

        if not all(locked_contact_values.get(key, "").strip() for key in ["locked_full_name", "locked_email", "locked_phone"]):
            st.warning(t("locked_contact_warning"))

        st.session_state.setdefault(
            "ats_cv_locked_proper_nouns_json",
            json.dumps(st.session_state.get("ats_cv_locked_proper_nouns", ATS_LOCKED_PROPER_NOUNS), ensure_ascii=False, indent=2),
        )
        with st.expander(t("locked_proper_nouns"), expanded=False):
            locked_proper_nouns_json = st.text_area(
                t("locked_proper_nouns"),
                key="ats_cv_locked_proper_nouns_json",
                height=160,
            )

        # Update cached_proper_nouns so manual edits are not lost when switching pages!
        try:
            parsed_proper_nouns = json.loads(locked_proper_nouns_json)
            if isinstance(parsed_proper_nouns, list):
                st.session_state["cached_proper_nouns"] = parsed_proper_nouns
                st.session_state["cached_proper_nouns_json"] = locked_proper_nouns_json
        except Exception:
            pass

        if st.button(t("generate_ats_cv")):
            if validate_inputs(require_cv=True, require_job=True):
                with st.spinner(t("spinner_tailored")):
                    try:
                        ats_cv_generate_data = {
                            "job_description": st.session_state.global_job_text,
                            "template_id": selected_template.get("id"),
                            "language": ats_cv_language,
                            "adaptation_level": selected_adaptation_level,
                            "locked_proper_nouns_json": locked_proper_nouns_json,
                        }
                        ats_cv_generate_data.update(locked_contact_values)
                        response = requests.post(
                            f"{API_BASE_URL}/ats-cv/generate",
                            files=get_cv_files(),
                            data=ats_cv_generate_data
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.ats_cv_builder_result = result
                            st.session_state.ats_cv_builder_language = result.get("language", ats_cv_language)
                            st.session_state.ats_cv_builder_template_id = selected_template.get("id")
                            st.session_state.ats_cv_builder_adaptation_level = result.get("adaptation_level", selected_adaptation_level)
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
            quality_report = stored_result.get("quality_report", {})
            structure_report = stored_result.get("structure_report", {})

            if not validation.get("is_valid", False):
                st.warning(", ".join(validation.get("errors", [])))

            before_score = metadata.get("ats_score_before", 0)
            after_score = metadata.get("ats_score_after", 0)
            try:
                improvement_score = int(after_score) - int(before_score)
            except Exception:
                improvement_score = 0

            col_before, col_after, col_improvement = st.columns(3)
            with col_before:
                st.metric(t("ats_score_before"), before_score)
            with col_after:
                st.metric(t("ats_score_after"), after_score)
            with col_improvement:
                st.metric(t("score_improvement"), improvement_score)

            contact = ats_cv.get("contact", {})
            col_role, col_title, col_confidence = st.columns(3)
            with col_role:
                st.write(f"**{t('target_role')}**")
                st.write(metadata.get("target_role") or "-")
            with col_title:
                st.write("**Target Title**" if st.session_state.ui_lang == "en" else "**Hedef CV Başlığı**")
                st.write(contact.get("target_title") or "-")
            with col_confidence:
                st.write(f"**{t('alignment_confidence')}**")
                st.write(metadata.get("alignment_confidence") or "-")

            quality_col, structure_col = st.columns(2)
            with quality_col:
                q_score = quality_report.get("quality_score") if isinstance(quality_report, dict) else None
                st.metric(t("cv_quality_score"), q_score if q_score is not None else "-")
            with structure_col:
                s_score = structure_report.get("structure_score") if isinstance(structure_report, dict) else None
                st.metric(t("structure_score"), s_score if s_score is not None else "-")

            render_quality_report(quality_report, t("cv_quality_check"), "quality_score")
            render_quality_report(structure_report, t("structure_validation"), "structure_score")

            with st.expander(t("used_keywords"), expanded=False):
                st.write(", ".join(metadata.get("job_keywords_used", [])) or "-")

            with st.expander(t("transferable_keywords"), expanded=False):
                write_non_empty_list(metadata.get("transferable_keywords_used", []))

            with st.expander(t("missing_keywords"), expanded=False):
                write_non_empty_list(metadata.get("missing_keywords", []))

            with st.expander(t("risky_keywords_not_added"), expanded=False):
                write_non_empty_list(metadata.get("risky_keywords_not_added", []))

            st.subheader(t("optimization_summary"))
            st.write(metadata.get("optimization_summary", ""))

            st.subheader(t("ats_score_explanation"))
            st.caption(t("ats_score_disclaimer"))
            score_explanation = metadata.get("ats_score_explanation", {}) if isinstance(metadata.get("ats_score_explanation"), dict) else {}
            st.write(f"**{t('before_reason')}:** {score_explanation.get('before_reason') or '-'}")
            st.write(f"**{t('after_reason')}:** {score_explanation.get('after_reason') or '-'}")
            with st.expander(t("improvement_reasons"), expanded=False):
                write_non_empty_list(score_explanation.get("improvement_reasons", []))
            with st.expander(t("remaining_gaps"), expanded=False):
                write_non_empty_list(score_explanation.get("remaining_gaps", []))

            with st.expander(t("adaptation_notes"), expanded=False):
                write_non_empty_list(metadata.get("adaptation_notes", []))

            st.markdown("---")
            st.header(t("generated_ats_cv_preview"))
            render_ats_cv_preview(ats_cv)

            st.markdown("---")
            st.subheader(t("export_sections"))
            export_style_label_map = {
                t("export_style_standard"): "standard",
                t("export_style_balanced"): "balanced_one_page",
            }
            selected_export_style_label = st.selectbox(
                t("export_style"),
                list(export_style_label_map.keys()),
                key="ats_cv_export_style"
            )
            selected_export_style = export_style_label_map[selected_export_style_label]
            one_page_export = selected_export_style == "balanced_one_page"
            if one_page_export:
                st.caption(t("balanced_one_page_help"))

            section_options = [
                ("contact", t("contact")),
                ("summary", t("summary_section")),
                ("skills", t("skills_section")),
                ("experience", t("experience_section")),
                ("projects", t("projects_section")),
                ("education", t("education_section")),
                ("certifications", t("certifications_section")),
                ("languages", t("languages_section")),
            ]
            enabled_export_sections = []
            section_cols = st.columns(4)
            for index, (section_key, label) in enumerate(section_options):
                with section_cols[index % 4]:
                    if st.checkbox(label, value=True, key=f"ats_cv_export_section_{section_key}"):
                        enabled_export_sections.append(section_key)

            if "contact" not in enabled_export_sections:
                st.warning(t("critical_section_warning"))
            if any(section not in enabled_export_sections for section in ["experience", "education", "skills"]):
                st.warning(t("key_section_warning"))
            if not enabled_export_sections:
                st.warning("Select at least one export section." if st.session_state.ui_lang == "en" else "En az bir dışa aktarma bölümü seçin.")

            # DOCX Render Mode selector
            render_mode_options = [t("docx_render_mode_prog"), t("docx_render_mode_tpl")]
            selected_render_mode_label = st.radio(
                t("docx_render_mode_label"),
                render_mode_options,
                index=0,
                key="ats_cv_docx_render_mode"
            )
            docx_render_mode = "template" if selected_render_mode_label == t("docx_render_mode_tpl") else "programmatic"

            selected_template_id_for_docx = export_template_id
            if docx_render_mode == "template":
                st.info(t("docx_template_experimental_note"))
                try:
                    tpl_catalog_res = requests.get(f"{API_BASE_URL}/ats-cv/docx-templates")
                    if tpl_catalog_res.status_code == 200:
                        tpl_catalog = tpl_catalog_res.json().get("catalog", [])
                    else:
                        tpl_catalog = []
                except Exception:
                    tpl_catalog = []

                if tpl_catalog:
                    tpl_options = {item["display_name"]: item for item in tpl_catalog}
                    selected_tpl_disp = st.selectbox(t("docx_template_select"), list(tpl_options.keys()), key="ats_cv_docx_template_select")
                    selected_template_info = tpl_options[selected_tpl_disp]
                    selected_template_id_for_docx = selected_template_info["template_id"]
                    st.caption(selected_template_info.get("description", ""))
                    render_docx_template_guidance_expander(selected_template_info)
                else:
                    st.warning("No DOCX templates available. Using default.")

            col_docx, col_pdf, col_txt = st.columns(3)
            can_export = bool(enabled_export_sections)
            docx_bytes = fetch_ats_cv_export(
                "export-docx", ats_cv, export_template_id, export_language,
                one_page_export, enabled_export_sections, selected_export_style,
                docx_render_mode=docx_render_mode, docx_template_id=selected_template_id_for_docx
            ) if can_export else None
            pdf_bytes = fetch_ats_cv_export(
                "export-pdf", ats_cv, export_template_id, export_language,
                one_page_export, enabled_export_sections, selected_export_style
            ) if can_export else None
            txt_bytes = fetch_ats_cv_export(
                "export-txt", ats_cv, export_template_id, export_language,
                one_page_export, enabled_export_sections, selected_export_style
            ) if can_export else None

            with col_docx:
                if docx_bytes:
                    st.download_button(
                        label=t("download_docx_cv"),
                        data=docx_bytes,
                        file_name=safe_cv_filename("ats_cv", selected_template_id_for_docx, "docx"),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            with col_pdf:
                if pdf_bytes:
                    st.download_button(
                        label=t("download_pdf_cv"),
                        data=pdf_bytes,
                        file_name=safe_cv_filename("ats_cv", export_template_id, "pdf"),
                        mime="application/pdf"
                    )
            with col_txt:
                if txt_bytes:
                    st.download_button(
                        label=t("download_txt_cv"),
                        data=txt_bytes,
                        file_name=safe_cv_filename("ats_cv", export_template_id, "txt"),
                        mime="text/plain"
                    )


elif selected_page_key == "✉️ Application Materials":
    st.header(t("nav_application_materials"))
    
    cv_files, job_text, has_error, effective_cv_obj = get_effective_inputs("app_materials", require_cv=False, require_job=True)
    
    if not has_error:
        tab1, tab2, tab3, tab4 = st.tabs([
            t("nav_cover_letter"),
            t("nav_app_email"),
            t("nav_interview_prep"),
            t("nav_personalized_interview")
        ])
        
        with tab1:
            st.subheader(t("nav_cover_letter"))
            cl_tone = st.selectbox(t("select_tone"), ["professional", "friendly", "confident", "formal", "short"], key="app_materials_cl_tone")
            
            if cv_files is None:
                st.warning(t("please_upload_cv"))
            else:
                if st.button(t("btn_gen_cover_letter"), key="app_materials_cl_btn"):
                    with st.spinner(t("spinner_cover_letter")):
                        try:
                            data = {
                                "job_text": job_text,
                                "tone": cl_tone,
                                "language": global_language
                            }
                            response = requests.post(
                                f"{API_BASE_URL}/cover-letter",
                                files=cv_files,
                                data=data
                            )
                            if response.status_code == 200:
                                res = response.json()
                                result = res["result"]
                                
                                st.success(t("status_complete"))
                                st.text_area(t("nav_cover_letter"), value=result, height=350, key="app_materials_cl_val")
                                
                                st.markdown("---")
                                render_download_buttons(t("nav_cover_letter"), result, "cover_letter")
                            else:
                                st.error(response.text)
                        except Exception as e:
                            st.error(f"{t('status_error')} {str(e)}")

        with tab2:
            st.subheader(t("nav_app_email"))
            comp_name = st.text_input(t("company_name"), placeholder="e.g. Acme Corp", key="app_materials_email_comp")
            pos_title = st.text_input(t("position_title"), placeholder="e.g. Backend Developer", key="app_materials_email_pos")
            email_tone = st.selectbox(t("select_tone"), ["professional", "friendly", "concise"], key="app_materials_email_tone")
            
            if cv_files is None:
                st.warning(t("please_upload_cv"))
            else:
                if st.button(t("btn_gen_email"), key="app_materials_email_btn"):
                    with st.spinner(t("spinner_email")):
                        try:
                            data = {
                                "job_text": job_text,
                                "language": global_language,
                                "tone": email_tone,
                                "company_name": comp_name or "",
                                "position_title": pos_title or ""
                            }
                            response = requests.post(
                                f"{API_BASE_URL}/application-email",
                                files=cv_files,
                                data=data
                            )
                            if response.status_code == 200:
                                res = response.json()
                                result = res["result"]
                                
                                st.success(t("templates_ready"))
                                
                                st.subheader(f"{t('email_subject')}: {result.get('subject')}")
                                st.text_area(t("email_body"), value=result.get("email_body"), height=250, key="app_materials_email_val")
                                
                                st.subheader(t("linkedin_msg"))
                                st.text_area(t("linkedin_msg"), value=result.get("short_linkedin_message"), height=120, key="app_materials_linkedin_val")
                                
                                st.subheader(t("follow_up_msg"))
                                st.text_area(t("follow_up_msg"), value=result.get("follow_up_message"), height=180, key="app_materials_followup_val")
                                
                                st.markdown("---")
                                render_download_buttons(t("nav_app_email"), result, "application_email")
                            else:
                                st.error(response.text)
                        except Exception as e:
                            st.error(f"{t('status_error')} {str(e)}")

        with tab3:
            st.subheader(t("nav_interview_prep"))
            if st.button(t("btn_gen_prep"), key="app_materials_prep_btn"):
                with st.spinner(t("spinner_prep")):
                    try:
                        data = {
                            "job_text": job_text,
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

        with tab4:
            st.subheader(t("nav_personalized_interview"))
            prep_diff = st.selectbox(t("difficulty"), ["easy", "medium", "hard"], key="app_materials_prep_diff")
            
            if cv_files is None:
                st.warning(t("please_upload_cv"))
            else:
                if st.button(t("btn_gen_custom_prep"), key="app_materials_custom_prep_btn"):
                    with st.spinner(t("spinner_personalized_prep")):
                        try:
                            data = {
                                "job_text": job_text,
                                "language": global_language,
                                "difficulty": prep_diff
                            }
                            response = requests.post(
                                f"{API_BASE_URL}/personalized-interview-prep",
                                files=cv_files,
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


elif selected_page_key == "💼 Job Workspace":
    st.header(t("nav_job_workspace"))
    st.write(t("job_workspace_desc") if "job_workspace_desc" in TRANSLATIONS[st.session_state.ui_lang] else "Manage your job listings, track search alerts, view pipeline progress, and generate custom application materials.")

    alerts = api_json("GET", "/job-monitoring/alerts") or []
    sources_payload = api_json("GET", "/job-monitoring/sources", timeout=30) or {}
    source_settings = sources_payload.get("sources", [])
    source_names = [source.get("source_name") for source in source_settings if source.get("source_name")]
    enabled_runnable_sources = [
        source.get("source_name") for source in source_settings
        if source.get("enabled") and source.get("runnable") and source.get("status") == "active"
    ]

    tab_jobs, tab_add, tab_profiles, tab_sources, tab_pipeline, tab_assets = st.tabs([
        t("tab_jobs") if "tab_jobs" in TRANSLATIONS[st.session_state.ui_lang] else "Jobs",
        t("tab_add_job") if "tab_add_job" in TRANSLATIONS[st.session_state.ui_lang] else "Add Job",
        t("tab_search_profiles") if "tab_search_profiles" in TRANSLATIONS[st.session_state.ui_lang] else "Search Profiles",
        t("tab_sources") if "tab_sources" in TRANSLATIONS[st.session_state.ui_lang] else "Sources",
        t("tab_pipeline") if "tab_pipeline" in TRANSLATIONS[st.session_state.ui_lang] else "Pipeline",
        t("tab_assets") if "tab_assets" in TRANSLATIONS[st.session_state.ui_lang] else "Assets"
    ])

    # Helper function to read asset file bytes safely
    def get_local_asset_bytes_inline(f_path: str) -> bytes | None:
        if not f_path:
            return None
        try:
            s_dir = os.path.abspath("generated_assets")
            r_path = os.path.abspath(f_path)
            if r_path.startswith(s_dir + os.sep) or r_path == s_dir:
                if os.path.exists(r_path):
                    with open(r_path, "rb") as f:
                        return f.read()
        except Exception:
            pass
        return None

    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "json": "application/json",
        "text": "text/plain"
    }

    # --- Tab 1: Jobs ---
    with tab_jobs:
        status_options = [t("jm_all_statuses"), "new", "saved", "rejected", "applied", "archived"]
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            status_filter = st.selectbox(t("jm_status_filter"), status_options, key="jw_status_filter")
        with filter_col2:
            source_filter = st.selectbox(t("jm_source_filter"), [t("jm_all_sources")] + (source_names or ["manual_mock", "manual_import"]), key="jw_source_filter")
        with filter_col3:
            alert_filter_options = [(t("jm_all_alerts"), None)] + [
                (f"#{alert.get('id')} - {alert.get('name')}", alert.get("id")) for alert in alerts
            ]
            selected_alert_filter = st.selectbox(t("jm_alert_filter"), [label for label, _ in alert_filter_options], key="jw_alert_filter")
            selected_alert_filter_id = dict(alert_filter_options).get(selected_alert_filter)
        with filter_col4:
            min_score_filter = st.slider(t("jm_min_score_filter"), 0, 100, 0, key="jw_min_score_filter")

        query_params = {}
        if status_filter != t("jm_all_statuses"):
            query_params["status"] = status_filter
        if source_filter != t("jm_all_sources"):
            query_params["source"] = source_filter
        if selected_alert_filter_id is not None:
            query_params["alert_profile_id"] = selected_alert_filter_id
        if min_score_filter > 0:
            query_params["min_match_score"] = min_score_filter

        jobs_path = "/job-monitoring/jobs"
        if query_params:
            jobs_path += f"?{urlencode(query_params)}"
        jobs = api_json("GET", jobs_path) or []

        if not jobs:
            st.info(t("jm_no_jobs"))
        else:
            for job in jobs:
                title = job.get("title") or "Untitled"
                company = job.get("company") or "N/A"
                score = job.get("match_score", 0)
                job_status = job.get("status")
                
                # Fetch pipeline data
                pipeline_data = None
                try:
                    pipe_url = f"{API_BASE_URL}/job-monitoring/jobs/{job.get('id')}/pipeline"
                    pipe_res = requests.get(pipe_url, timeout=5)
                    if pipe_res.status_code == 200:
                        pipeline_data = pipe_res.json().get("pipeline")
                except Exception:
                    pass
                
                stage_val = pipeline_data.get("application_stage", "not_started") if pipeline_data else "not_started"
                priority_val = pipeline_data.get("application_priority", "medium") if pipeline_data else "medium"
                
                stage_labels = {
                    "not_started": "⚪",
                    "preparing": "🟡 Prep",
                    "applied": "🔵 Applied",
                    "screening": "🟠 Screen",
                    "interview": "🟣 Int",
                    "technical_interview": "🟤 Tech",
                    "offer": "🟢 Offer",
                    "rejected": "🔴 Rej",
                    "withdrawn": "⚫ Wdr",
                    "archived": "⚪ Arc"
                }
                priority_labels = {
                    "low": "🟢 Low",
                    "medium": "🟡 Med",
                    "high": "🔴 High"
                }
                
                stage_str = stage_labels.get(stage_val, stage_val)
                priority_str = priority_labels.get(priority_val, priority_val)
                
                card_title = f"{title} - {company} | {score}% | {job_status} | {stage_str} | {priority_str}"
                with st.expander(card_title, expanded=False):
                    # Job Details Section
                    st.markdown("#### 📋 Job Details")
                    col_meta, col_score = st.columns([2, 1])
                    with col_meta:
                        st.write(f"**{t('jm_location')}:** {job.get('location') or 'N/A'}")
                        st.write(f"**{t('jm_sources')}:** {job.get('source')}")
                        st.write(f"**{t('jm_work_model')}:** {job.get('work_model') or 'N/A'}")
                        st.write(f"**{t('jm_job_type')}:** {job.get('job_type') or 'N/A'}")
                        if job.get("url"):
                            st.link_button("Open Job / İlanı Aç", job.get("url"), key=f"jw_open_job_{job.get('id')}")
                    with col_score:
                        st.metric("Match Score", f"{score}%")
                        st.write(f"**Status:** {job_status}")
                        
                    description = job.get("description") or ""
                    if description:
                        with st.expander("Show Full Description / Tam Açıklamayı Göster", expanded=False):
                            st.write(description)
                    
                    # Score / Keywords Section
                    st.markdown("#### 🎯 Score / Keywords")
                    st.write(f"**{t('matched_keywords')}:** {', '.join(job.get('matched_keywords', [])) or 'N/A'}")
                    st.write(f"**{t('missing_keywords')}:** {', '.join(job.get('missing_keywords', [])) or 'N/A'}")
                    st.info(job.get("match_summary") or "No match summary available.")
                    
                    # Rescore Section
                    if alerts:
                        rescore_options = [
                            (f"#{alert.get('id')} - {alert.get('name')}", alert.get("id")) for alert in alerts
                        ]
                        current_alert_id = job.get("alert_profile_id")
                        current_index = next(
                            (idx for idx, (_, alert_id) in enumerate(rescore_options) if alert_id == current_alert_id),
                            0,
                        )
                        rescore_col1, rescore_col2 = st.columns([3, 1])
                        with rescore_col1:
                            selected_rescore_label = st.selectbox(
                                t("jm_rescore_profile"),
                                [label for label, _ in rescore_options],
                                index=current_index,
                                key=f"jw_rescore_profile_{job.get('id')}",
                            )
                        with rescore_col2:
                            st.write("")
                            st.write("")
                            if st.button(t("jm_rescore"), key=f"jw_rescore_btn_{job.get('id')}"):
                                selected_rescore_id = dict(rescore_options).get(selected_rescore_label)
                                result = api_json(
                                    "POST",
                                    f"/job-monitoring/jobs/{job.get('id')}/rescore",
                                    json={"alert_profile_id": selected_rescore_id},
                                )
                                if result:
                                    st.success(f"{t('jm_rescored')} Match: {result.get('match_score', 0)}%")
                                    st.rerun()
                                    
                    # Analyze Job Section
                    st.markdown("#### 🧠 Analyze Job")
                    intel = None
                    try:
                        intel_url = f"{API_BASE_URL}/job-monitoring/jobs/{job.get('id')}/intelligence"
                        intel_res = requests.get(intel_url, timeout=5)
                        if intel_res.status_code == 200:
                            intel = intel_res.json()
                    except Exception:
                        pass
                        
                    col_an1, col_an2 = st.columns([3, 1])
                    with col_an1:
                        if alerts:
                            analyze_options = [(t("jm_use_associated_alert"), None)] + [
                                (f"#{alert.get('id')} - {alert.get('name')}", alert.get("id")) for alert in alerts
                            ]
                            selected_analyze_label = st.selectbox(
                                t("jm_select_alert_for_analysis"),
                                [label for label, _ in analyze_options],
                                key=f"jw_analyze_profile_sel_{job.get('id')}"
                            )
                            selected_analyze_id = dict(analyze_options).get(selected_analyze_label)
                        else:
                            selected_analyze_id = None
                    with col_an2:
                        st.write("")
                        st.write("")
                        if st.button(t("jm_analyze_job"), key=f"jw_analyze_btn_{job.get('id')}"):
                            payload = {}
                            if selected_analyze_id is not None:
                                payload["alert_profile_id"] = selected_analyze_id
                            result = api_json("POST", f"/job-monitoring/jobs/{job.get('id')}/analyze", json=payload)
                            if result:
                                st.success(t("jm_analysis_complete"))
                                st.rerun()
                                
                    if intel and intel.get("intelligence"):
                        report = intel["intelligence"]
                        with st.expander(t("jm_analysis_report"), expanded=True):
                            lang = st.session_state.get("ui_lang", "en")
                            family_labels_en = {
                                "software_backend": "Software Backend", "frontend": "Frontend", "fullstack": "Fullstack",
                                "ai_ml_llm": "AI / ML / LLM", "data_analytics": "Data Analytics", "business_analyst": "Business Analyst",
                                "product_project": "Product / Project Management", "fintech_payment": "Fintech / Payment",
                                "risk_fraud_compliance": "Risk / Fraud / Compliance", "cybersecurity": "Cybersecurity",
                                "devops_cloud": "DevOps / Cloud", "corporate_applications": "Corporate Applications",
                                "sales_operations": "Sales Operations", "general": "General",
                            }
                            family_labels_tr = {
                                "software_backend": "Yazılım Arka Uç (Backend)", "frontend": "Ön Uç (Frontend)", "fullstack": "Tam Yığın (Fullstack)",
                                "ai_ml_llm": "Yapay Zeka / ML / LLM", "data_analytics": "Veri Analitiği", "business_analyst": "İş Analisti",
                                "product_project": "Ürün / Proje Yönetimi", "fintech_payment": "Finansal Teknolojiler / Ödeme",
                                "risk_fraud_compliance": "Risk / Dolandırıcılık / Uyum", "cybersecurity": "Siber Güvenlik",
                                "devops_cloud": "DevOps / Bulut", "corporate_applications": "Kurumsal Uygulamalar",
                                "sales_operations": "Satış Operasyonları", "general": "Genel",
                            }
                            seniority_labels_en = {
                                "internship": "Internship", "entry_level": "Entry Level", "junior": "Junior",
                                "mid": "Mid Level", "senior": "Senior", "lead_manager": "Lead / Manager", "unknown": "Unknown",
                            }
                            seniority_labels_tr = {
                                "internship": "Staj", "entry_level": "Başlangıç Seviyesi", "junior": "Junior / Küçük",
                                "mid": "Mid / Orta Seviye", "senior": "Senior / Kıdemli", "lead_manager": "Lider / Yönetici", "unknown": "Bilinmiyor",
                            }
                            rec_labels_en = {
                                "strong_apply": "🟢 Strong Apply", "apply": "🟢 Apply", "apply_with_tailored_cv": "🟡 Apply with Tailored CV",
                                "low_match": "🟠 Low Match", "not_recommended": "🔴 Not Recommended",
                            }
                            rec_labels_tr = {
                                "strong_apply": "🟢 Güçlü Başvuru", "apply": "🟢 Başvur", "apply_with_tailored_cv": "🟡 Özelleştirilmiş CV ile Başvur",
                                "low_match": "🟠 Düşük Eşleşme", "not_recommended": "🔴 Önerilmiyor",
                            }
                            
                            family_lbl = (family_labels_tr if lang == "tr" else family_labels_en).get(report.get("job_family"), report.get("job_family"))
                            seniority_lbl = (seniority_labels_tr if lang == "tr" else seniority_labels_en).get(report.get("seniority_assessment"), report.get("seniority_assessment"))
                            rec_lbl = (rec_labels_tr if lang == "tr" else rec_labels_en).get(report.get("application_recommendation"), report.get("application_recommendation"))
                            
                            st.markdown(f"**Family:** `{family_lbl}` | **Seniority:** `{seniority_lbl}` | **Rec:** `{rec_lbl}`")
                            st.markdown(f"**Summary:** {report.get('role_summary', '')}")
                            st.markdown(f"**Strengths:** {', '.join(report.get('candidate_strengths', []))}")
                            st.markdown(f"**Gaps:** {', '.join(report.get('candidate_gaps', []))}")
                            
                    # Pipeline / Notes Section
                    st.markdown("#### 📅 Pipeline / Notes")
                    p_stage = pipeline_data.get("application_stage", "not_started") if pipeline_data else "not_started"
                    p_priority = pipeline_data.get("application_priority", "medium") if pipeline_data else "medium"
                    p_mat = pipeline_data.get("application_materials_status", "not_started") if pipeline_data else "not_started"
                    
                    stages_list = ["not_started", "preparing", "applied", "screening", "interview", "technical_interview", "offer", "rejected", "withdrawn", "archived"]
                    priorities_list = ["low", "medium", "high"]
                    mat_list = ["not_started", "cv_needed", "cover_letter_needed", "ready", "submitted"]
                    
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        stage_idx = next((i for i, x in enumerate(stages_list) if x == p_stage), 0)
                        new_stage = st.selectbox(t("jm_pipeline_stage"), stages_list, index=stage_idx, key=f"jw_f_stage_{job.get('id')}")
                    with col_f2:
                        priority_idx = next((i for i, x in enumerate(priorities_list) if x == p_priority), 1)
                        new_priority = st.selectbox(t("jm_pipeline_priority"), priorities_list, index=priority_idx, key=f"jw_f_priority_{job.get('id')}")
                    with col_f3:
                        mat_idx = next((i for i, x in enumerate(mat_list) if x == p_mat), 0)
                        new_mat = st.selectbox(t("jm_pipeline_materials"), mat_list, index=mat_idx, key=f"jw_f_mat_{job.get('id')}")
                        
                    col_d1, col_d2, col_d3 = st.columns(3)
                    with col_d1:
                        new_deadline = st.text_input(t("jm_pipeline_deadline"), value=pipeline_data.get("application_deadline", "") if pipeline_data else "", key=f"jw_f_dead_{job.get('id')}", placeholder="YYYY-MM-DD")
                    with col_d2:
                        new_applied_at = st.text_input(t("jm_pipeline_applied_at"), value=pipeline_data.get("applied_at", "") if pipeline_data else "", key=f"jw_f_app_{job.get('id')}", placeholder="YYYY-MM-DD")
                    with col_d3:
                        new_next_date = st.text_input(t("jm_pipeline_next_action_date"), value=pipeline_data.get("next_action_date", "") if pipeline_data else "", key=f"jw_f_next_d_{job.get('id')}", placeholder="YYYY-MM-DD")
                        
                    new_next_action = st.text_input(t("jm_pipeline_next_action"), value=pipeline_data.get("next_action", "") if pipeline_data else "", key=f"jw_f_next_act_{job.get('id')}")
                    new_notes = st.text_area(t("jm_pipeline_notes"), value=pipeline_data.get("application_notes", "") if pipeline_data else "", height=100, key=f"jw_f_notes_{job.get('id')}")
                    
                    col_save, col_del = st.columns([3, 1])
                    with col_save:
                        if st.button(t("jm_save_pipeline"), key=f"jw_save_pipe_btn_{job.get('id')}"):
                            payload = {
                                "application_stage": new_stage,
                                "application_priority": new_priority,
                                "application_materials_status": new_mat,
                                "application_deadline": new_deadline,
                                "applied_at": new_applied_at,
                                "next_action": new_next_action,
                                "next_action_date": new_next_date,
                                "application_notes": new_notes,
                            }
                            result = api_json("PATCH", f"/job-monitoring/jobs/{job.get('id')}/pipeline", json=payload)
                            if result:
                                st.success(t("jm_pipeline_updated"))
                                st.rerun()
                                
                    st.write("")
                    # Status short actions
                    status_cols = st.columns(4)
                    status_actions = [
                        (t("jm_save"), "saved"),
                        (t("jm_reject"), "rejected"),
                        (t("jm_mark_applied"), "applied"),
                        (t("jm_archive"), "archived"),
                    ]
                    for col_act, (act_label, next_status) in zip(status_cols, status_actions):
                        with col_act:
                            if st.button(act_label, key=f"jw_status_{job.get('id')}_{next_status}"):
                                result = api_json(
                                    "PATCH",
                                    f"/job-monitoring/jobs/{job.get('id')}/status",
                                    json={"status": next_status},
                                )
                                if result:
                                    st.success(t("jm_status_updated"))
                                    st.rerun()

                    # Generate Materials Section
                    st.markdown("#### 📝 Generate Materials")
                    effective_cv_file = None
                    
                    if global_cv is not None:
                        st.write(f"{t('jm_global_cv_default')}: {global_cv.name}")
                        effective_cv_file = {
                            "cv_file": (global_cv.name, global_cv.getvalue(), global_cv.type)
                        }
                    else:
                        st.warning(t("jm_global_cv_missing"))
                        
                    override_exp = st.expander(t("override_inputs_title"), expanded=False)
                    with override_exp:
                        override_cv = st.file_uploader(
                            t("override_cv_label"),
                            type=["pdf", "docx"],
                            key=f"jw_cv_override_{job.get('id')}"
                        )
                        if override_cv is not None:
                            effective_cv_file = {
                                "cv_file": (override_cv.name, override_cv.getvalue(), override_cv.type)
                            }
                            st.info(f"Using override CV: {override_cv.name}")
                            
                    lang_select = st.selectbox(t("jm_lang_select"), ["English", "Turkish"], key=f"jw_lang_sel_{job.get('id')}")
                    templates_res = api_json("GET", "/ats-cv/templates", timeout=30)
                    if templates_res and "templates" in templates_res:
                        template_options = [tmpl.get("id") for tmpl in templates_res.get("templates", [])]
                    else:
                        template_options = ["classic_ats", "modern_clean", "creative_visual"]
                    template_select = st.selectbox(t("jm_template_select"), template_options, key=f"jw_tmpl_sel_{job.get('id')}")
                    one_page_select = st.checkbox("One-Page CV" if lang_select == "English" else "Tek Sayfa CV", value=False, key=f"jw_onepage_sel_{job.get('id')}")
                    jw_adaptation_options = adaptation_level_options()
                    jw_adaptation_label = st.selectbox(
                        t("adaptation_level"),
                        [label for label, _ in jw_adaptation_options],
                        index=1,
                        key=f"jw_adaptation_sel_{job.get('id')}",
                    )
                    jw_adaptation_level = dict(jw_adaptation_options).get(jw_adaptation_label, "balanced")
                    tone_select = st.selectbox(t("jm_tone_select"), ["professional", "friendly", "concise"], key=f"jw_tone_sel_{job.get('id')}")

                    # Output Format and optional DOCX controls
                    jw_format_options = ["PDF", "DOCX"]
                    jw_format_select = st.selectbox(
                        "Output Format" if lang_select == "English" else "Çıktı Formatı",
                        jw_format_options,
                        index=0,
                        key=f"jw_fmt_sel_{job.get('id')}"
                    )

                    jw_docx_render_mode = "programmatic"
                    jw_docx_template_id = ""
                    if jw_format_select == "DOCX":
                        selected_jw_render_mode_label = st.radio(
                            t("docx_render_mode_label"),
                            [t("docx_render_mode_prog"), t("docx_render_mode_tpl")],
                            index=0,
                            key=f"jw_docx_render_mode_sel_{job.get('id')}"
                        )
                        jw_docx_render_mode = "template" if selected_jw_render_mode_label == t("docx_render_mode_tpl") else "programmatic"
                        if jw_docx_render_mode == "template":
                            st.info(t("docx_template_experimental_note"))
                            try:
                                tpl_catalog_res = requests.get(f"{API_BASE_URL}/ats-cv/docx-templates")
                                if tpl_catalog_res.status_code == 200:
                                    tpl_catalog = tpl_catalog_res.json().get("catalog", [])
                                else:
                                    tpl_catalog = []
                            except Exception:
                                tpl_catalog = []

                            if tpl_catalog:
                                tpl_options = {item["display_name"]: item for item in tpl_catalog}
                                selected_tpl_disp = st.selectbox(t("docx_template_select"), list(tpl_options.keys()), key=f"jw_docx_template_sel_{job.get('id')}")
                                selected_template_info = tpl_options[selected_tpl_disp]
                                jw_docx_template_id = selected_template_info["template_id"]
                                st.caption(selected_template_info.get("description", ""))
                                render_docx_template_guidance_expander(selected_template_info)
                            else:
                                st.warning("No DOCX templates available. Using default.")

                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    is_disabled = (effective_cv_file is None)
                    
                    with btn_col1:
                        if st.button(t("jm_generate_cv"), key=f"jw_btn_cv_{job.get('id')}", disabled=is_disabled):
                            data = {
                                "template_id": template_select,
                                "language": lang_select,
                                "output_format": jw_format_select.lower(),
                                "one_page": str(one_page_select).lower(),
                                "adaptation_level": jw_adaptation_level,
                                "docx_render_mode": jw_docx_render_mode,
                                "docx_template_id": jw_docx_template_id,
                            }
                            with st.spinner("Generating tailored CV..."):
                                res = api_json("POST", f"/job-monitoring/jobs/{job.get('id')}/assets/tailored-cv", timeout=90, files=effective_cv_file, data=data)
                                if res:
                                    st.success("CV generated successfully!")
                                    st.rerun()
                    with btn_col2:
                        if st.button(t("jm_generate_cover"), key=f"jw_btn_cover_{job.get('id')}", disabled=is_disabled):
                            data = {"language": lang_select, "tone": tone_select}
                            with st.spinner("Generating cover letter..."):
                                res = api_json("POST", f"/job-monitoring/jobs/{job.get('id')}/assets/cover-letter", timeout=90, files=effective_cv_file, data=data)
                                if res:
                                    st.success("Cover Letter generated successfully!")
                                    st.rerun()
                    with btn_col3:
                        if st.button(t("jm_generate_email"), key=f"jw_btn_email_{job.get('id')}", disabled=is_disabled):
                            data = {"language": lang_select, "tone": tone_select}
                            with st.spinner("Generating email..."):
                                res = api_json("POST", f"/job-monitoring/jobs/{job.get('id')}/assets/application-email", timeout=90, files=effective_cv_file, data=data)
                                if res:
                                    st.success("Email generated successfully!")
                                    st.rerun()
                                    
                    # Job Specific Generated Assets List
                    st.markdown("#### 📁 Generated Assets")
                    assets_res = api_json("GET", f"/job-monitoring/jobs/{job.get('id')}/assets", timeout=30)
                    job_assets = assets_res.get("assets", []) if assets_res else []
                    if not job_assets:
                        st.caption(t("jm_no_job_assets"))
                    else:
                        job_assets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                        limit_assets = job_assets[:5]
                        has_more = len(job_assets) > 5
                        show_all = st.checkbox("Show all assets / Tüm materyalleri göster", value=False, key=f"jw_show_all_assets_job_{job.get('id')}") if has_more else False
                        display_assets = job_assets if show_all else limit_assets
                        
                        for asset in display_assets:
                            a_type = asset.get("asset_type")
                            a_lang = asset.get("language")
                            a_created = asset.get("created_at", "")[:16].replace("T", " ")
                            a_fmt = asset.get("export_format") or "txt"
                            asset_label = f"📄 {a_type.upper()} | {a_lang} | {a_fmt.upper()} | {a_created}{quality_badge(asset)}"
                            
                            col_a1, col_a2, col_a3 = st.columns([3, 1, 1])
                            with col_a1:
                                st.write(asset_label)
                            with col_a2:
                                if st.button(t("jm_preview"), key=f"jw_prev_asset_btn_{asset.get('id')}"):
                                    st.session_state["preview_asset_id"] = asset.get("id")
                                    fetched = api_json("GET", f"/job-monitoring/assets/{asset.get('id')}", timeout=30)
                                    if fetched and "asset" in fetched:
                                        st.session_state["preview_asset_dict"] = fetched.get("asset")
                                        st.rerun()
                            with col_a3:
                                f_path = asset.get("file_path")
                                f_bytes = get_local_asset_bytes_inline(f_path)
                                f_name = os.path.basename(f_path) if f_path else f"{a_type}_{job.get('id')}.{a_fmt}"
                                if f_bytes is None:
                                    f_bytes = (asset.get("content_text") or "").encode("utf-8")
                                    f_name = f"{a_type}_{job.get('id')}.txt"
                                    a_fmt = "txt"
                                st.download_button(
                                    t("jm_download"),
                                    data=f_bytes,
                                    file_name=f_name,
                                    mime=media_types.get(a_fmt.lower(), "application/octet-stream"),
                                    key=f"jw_dl_asset_btn_{asset.get('id')}"
                                )
                                
                            if st.session_state.get("preview_asset_id") == asset.get("id"):
                                p_dict = st.session_state.get("preview_asset_dict")
                                if p_dict:
                                    with st.container():
                                        st.info(f"**Previewing:** {p_dict.get('asset_type').upper()} ({p_dict.get('language')})")
                                        content = p_dict.get("content_text")
                                        if not content and p_dict.get("file_path"):
                                            content = "Metin içeriği bulunamadı, fiziksel dosyayı indirin."
                                        st.text_area("Content Preview", content or "", height=250, key=f"jw_preview_textarea_{asset.get('id')}")
                                        if p_dict.get("asset_type") == "tailored_cv":
                                            render_quality_report(get_asset_quality_report(p_dict), t("cv_quality_check"), "quality_score")
                                            render_quality_report(get_asset_structure_report(p_dict), t("structure_validation"), "structure_score")
                                        if st.button("Close Preview / Önizlemeyi Kapat", key=f"jw_close_prev_{asset.get('id')}"):
                                            st.session_state["preview_asset_id"] = None
                                            st.session_state["preview_asset_dict"] = None
                                            st.rerun()

    # --- Tab 2: Add Job ---
    with tab_add:
        st.subheader(t("jm_manual_import"))
        st.write(t("jm_manual_import_desc"))
        st.caption(t("jm_add_job_next_step"))
        
        alert_options = [(t("jm_no_alert_selected"), None)] + [
            (f"#{alert.get('id')} - {alert.get('name')}", alert.get("id")) for alert in alerts
        ]

        with st.expander(t("jm_extract_desc_from_url"), expanded=False):
            st.caption(t("job_url_desc"))
            helper_url = st.text_input(
                t("job_url_label"),
                value=st.session_state.get("jw_add_job_url", ""),
                placeholder="https://...",
                key="jw_add_job_extract_url",
            )
            if st.button(t("btn_extract_job"), key="jw_add_job_extract_btn"):
                if not helper_url.strip():
                    st.warning("Geçerli bir http/https URL girin." if st.session_state.ui_lang == "tr" else "Enter a valid http/https URL.")
                else:
                    with st.spinner(t("spinner_job")):
                        result = api_json(
                            "POST",
                            "/extract-job-description",
                            json={"url": helper_url, "language": "Turkish" if st.session_state.ui_lang == "tr" else "English"},
                            timeout=15,
                        )
                    if result and result.get("success"):
                        st.session_state["jw_add_job_url"] = result.get("url") or helper_url
                        st.session_state["jw_add_job_description"] = result.get("text") or result.get("extracted_text") or ""
                        if result.get("title"):
                            st.caption(result.get("title"))
                        st.success(t("extraction_success"))
                        st.rerun()
                    elif result:
                        fallback_msg = (
                            "Bu sayfa otomatik çıkarılamadı. Lütfen ilan açıklamasını manuel yapıştırın."
                            if st.session_state.ui_lang == "tr"
                            else "Could not extract this page automatically. Please paste the job description manually."
                        )
                        st.warning(result.get("message") or fallback_msg)
        
        with st.form("jw_manual_import_form"):
            selected_alert_label = st.selectbox(
                t("jm_select_alert_optional"),
                [label for label, _ in alert_options],
                key="jw_add_job_alert_select"
            )
            selected_alert_id = dict(alert_options).get(selected_alert_label)

            manual_title = st.text_input(t("jm_job_title"), key="jw_add_job_title")
            manual_company = st.text_input(t("jm_company"), key="jw_add_job_company")
            manual_location = st.text_input(t("jm_location"), key="jw_add_job_location")
            manual_url = st.text_input(t("jm_job_url"), placeholder="https://...", key="jw_add_job_url")
            manual_description = st.text_area(t("jm_job_description"), height=220, key="jw_add_job_description")

            with st.expander("Advanced options / Gelişmiş Seçenekler", expanded=False):
                col_work, col_type, col_seniority = st.columns(3)
                with col_work:
                    work_model_choice = st.selectbox(t("jm_work_model"), ["", "Remote", "Hybrid", "On-site", "Custom"], key="jw_add_job_work_model")
                    work_model_custom = st.text_input("Custom work model", key="jw_add_job_work_model_custom") if work_model_choice == "Custom" else ""
                with col_type:
                    job_type_choice = st.selectbox(t("jm_job_type"), ["", "Full-time", "Internship", "Contract", "Part-time", "Custom"], key="jw_add_job_job_type")
                    job_type_custom = st.text_input("Custom job type", key="jw_add_job_job_type_custom") if job_type_choice == "Custom" else ""
                with col_seniority:
                    seniority_choice = st.selectbox(t("jm_seniority"), ["", "Intern", "Junior", "Entry level", "Mid", "Senior", "Custom"], key="jw_add_job_seniority")
                    seniority_custom = st.text_input("Custom seniority", key="jw_add_job_seniority_custom") if seniority_choice == "Custom" else ""

                manual_source = st.text_input(t("jm_source"), value="manual_import", key="jw_add_job_source")
                manual_posted_at = st.text_input(t("jm_posted_date"), placeholder="YYYY-MM-DD", key="jw_add_job_posted_at")

            add_manual_job = st.form_submit_button(t("jm_add_manual_job"))

        if add_manual_job:
            payload = {
                "alert_profile_id": selected_alert_id,
                "title": manual_title,
                "company": manual_company,
                "location": manual_location,
                "work_model": work_model_custom if work_model_choice == "Custom" else work_model_choice,
                "seniority": seniority_custom if seniority_choice == "Custom" else seniority_choice,
                "job_type": job_type_custom if job_type_choice == "Custom" else job_type_choice,
                "description": manual_description,
                "url": manual_url,
                "source": manual_source or "manual_import",
                "posted_at": manual_posted_at,
            }
            result = api_json("POST", "/job-monitoring/jobs/manual", json=payload)
            if result:
                if result.get("duplicate"):
                    st.info(t("jm_duplicate_updated"))
                st.success(f"{t('jm_manual_job_added')} Match: {result.get('match_score', 0)}%")
                st.rerun()

    # --- Tab 3: Search Profiles ---
    with tab_profiles:
        st.subheader("Job Search Profile Form / İş Arama Profili")
        st.caption(t("jm_search_profile_help"))
        
        with st.form("jw_create_search_profile_form"):
            alert_name = st.text_input(t("jm_alert_name"), placeholder="e.g. Backend roles, AI/ML roles...")
            
            selected_role_families = st.multiselect(
                "Target Role Families / Hedef Rol Aileleri",
                ["Backend", "Frontend", "Fullstack", "AI / ML / LLM", "Data Analyst", "Business Analyst", "Product / Project", "Corporate Applications", "DevOps / Cloud", "Cybersecurity", "Fintech / Payment", "Risk / Fraud / Compliance", "Internship / Junior", "Other"]
            )
            
            selected_keywords = st.multiselect(
                "Suggested Keywords / Önerilen Anahtar Kelimeler",
                ["Python", "SQL", "API", "RESTful API", "FastAPI", ".NET", "ASP.NET Core", "Java", "React", "Angular", "Power Apps", "Power Automate", "SharePoint", "SAP", "Salesforce", "Qlik", "AI", "LLM", "RAG", "ChromaDB", "Docker", "Azure", "Git", "Postman"]
            )
            custom_keywords_text = st.text_input("Custom Keywords (comma-separated) / Özel Anahtar Kelimeler (virgülle ayrılmış)")
            
            selected_locations = st.multiselect(
                t("jm_location"),
                ["Istanbul", "Remote", "Hybrid", "Turkey", "Europe", "Other"]
            )
            custom_location_text = st.text_input("Custom Location / Özel Konum") if "Other" in selected_locations else ""
            
            selected_seniority = st.multiselect(
                t("jm_seniority"),
                ["Intern", "Entry Level", "Junior", "Mid", "Senior"]
            )
            
            selected_job_type = st.multiselect(
                t("jm_job_type"),
                ["Full-time", "Internship", "Contract", "Part-time", "Freelance"]
            )
            
            selected_work_model = st.multiselect(
                t("jm_work_model"),
                ["Remote", "Hybrid", "On-site"]
            )
            
            sources = st.multiselect(
                t("jm_sources"),
                enabled_runnable_sources,
                default=enabled_runnable_sources,
                help=t("jm_sources_phase3a_note"),
            )
            
            selected_excluded = st.multiselect(
                t("jm_excluded_keywords"),
                ["senior", "lead", "manager", "director", "unpaid", "commission-only"]
            )
            custom_excluded_text = st.text_input("Custom Excluded Keywords (comma-separated) / Özel Hariç Tutulacak Kelimeler")
            
            min_match_score = st.slider(t("jm_min_score"), 0, 100, 40)
            is_active = st.checkbox(t("jm_active"), value=True)
            
            create_alert = st.form_submit_button("Create Search Profile / Arama Profili Oluştur")

        if create_alert:
            keywords = selected_role_families + selected_keywords + [k.strip() for k in custom_keywords_text.split(",") if k.strip()]
            excluded = selected_excluded + [k.strip() for k in custom_excluded_text.split(",") if k.strip()]
            
            location_str = ", ".join(selected_locations)
            if "Other" in selected_locations and custom_location_text:
                location_str = location_str.replace("Other", custom_location_text)
                
            seniority_str = ", ".join(selected_seniority)
            job_type_str = ", ".join(selected_job_type)
            work_model_str = ", ".join(selected_work_model)
            
            payload = {
                "name": alert_name,
                "keywords": keywords,
                "location": location_str,
                "seniority": seniority_str,
                "job_type": job_type_str,
                "work_model": work_model_str,
                "sources": sources,
                "excluded_keywords": excluded,
                "min_match_score": min_match_score,
                "is_active": is_active,
            }
            result = api_json("POST", "/job-monitoring/alerts", json=payload)
            if result:
                st.success("Search Profile created successfully! / Arama profili başarıyla oluşturuldu!")
                st.rerun()

        st.markdown("---")
        st.subheader("Existing Search Profiles / Mevcut Profiller")
        if not alerts:
            st.info(t("jm_no_alerts"))
        else:
            for alert in alerts:
                status_label = "active" if alert.get("is_active") else "inactive"
                with st.expander(f"#{alert.get('id')} - {alert.get('name')} ({status_label})", expanded=False):
                    st.write(f"**{t('jm_keywords')}:** {', '.join(alert.get('keywords', [])) or 'N/A'}")
                    st.write(f"**{t('jm_location')}:** {alert.get('location') or 'N/A'}")
                    st.write(f"**{t('jm_seniority')}:** {alert.get('seniority') or 'N/A'}")
                    st.write(f"**{t('jm_job_type')}:** {alert.get('job_type') or 'N/A'}")
                    st.write(f"**{t('jm_work_model')}:** {alert.get('work_model') or 'N/A'}")
                    st.write(f"**{t('jm_sources')}:** {', '.join(alert.get('sources', []))}")
                    st.write(f"**{t('jm_min_score')}:** {alert.get('min_match_score')}")
                    st.write(f"**Created / Updated:** {compact_datetime(alert.get('created_at'))} / {compact_datetime(alert.get('updated_at'))}")

                    col_run, col_deactivate = st.columns(2)
                    with col_run:
                        if st.button(t("jm_run_now"), key=f"jw_run_{alert.get('id')}", disabled=not alert.get("is_active")):
                            result = api_json("POST", f"/job-monitoring/alerts/{alert.get('id')}/run")
                            if result:
                                run = result.get("run", {})
                                st.success(f"{t('jm_run_complete')} New jobs: {run.get('new_jobs_count', 0)}")
                                st.rerun()
                    with col_deactivate:
                        if st.button(t("jm_deactivate"), key=f"jw_deactivate_{alert.get('id')}", disabled=not alert.get("is_active")):
                            result = api_json("DELETE", f"/job-monitoring/alerts/{alert.get('id')}")
                            if result:
                                st.success(t("jm_alert_deactivated"))
                                st.rerun()

        # Run History Expander at bottom
        st.markdown("---")
        with st.expander(t("jm_run_history"), expanded=False):
            runs = api_json("GET", "/job-monitoring/runs") or []
            if not runs:
                st.info(t("jm_no_runs"))
            else:
                run_rows = [
                    {
                        "id": run.get("id"),
                        "alert_profile_id": run.get("alert_profile_id"),
                        "started_at": compact_datetime(run.get("started_at")),
                        "finished_at": compact_datetime(run.get("finished_at")),
                        "status": run.get("status"),
                        "source_count": run.get("source_count"),
                        "jobs_found": run.get("jobs_found"),
                        "new_jobs_count": run.get("new_jobs_count"),
                        "error_message": run.get("error_message"),
                    }
                    for run in runs
                ]
                st.dataframe(run_rows, use_container_width=True)

    # --- Tab 4: Sources ---
    with tab_sources:
        st.subheader(t("tab_sources"))
        st.info(t("jm_sources_phase3a_note"))

        if not source_settings:
            st.warning("No source settings returned by API.")
        else:
            source_rows = [
                {
                    "display_name": source.get("display_name"),
                    "source_name": source.get("source_name"),
                    "status": source.get("status"),
                    "enabled": source.get("enabled"),
                    "runnable": source.get("runnable"),
                    "cooldown_minutes": source.get("cooldown_minutes"),
                    "last_run_at": source.get("last_run_at") or "",
                    "last_status": source.get("last_status") or "",
                    "last_error": source.get("last_error") or "",
                    "fetches_external_url": source.get("fetches_external_url"),
                }
                for source in source_settings
            ]
            st.dataframe(source_rows, use_container_width=True)

            for source in source_settings:
                source_name = source.get("source_name")
                title_bits = [
                    source.get("display_name") or source_name,
                    f"`{source_name}`",
                    t("jm_source_enabled") if source.get("enabled") else t("jm_source_disabled"),
                    f"status: {source.get('status')}",
                ]
                with st.expander(" | ".join(title_bits), expanded=source_name == "manual_mock"):
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.write(f"**Type:** {source.get('source_type')}")
                        st.write(f"**Runnable:** {source.get('runnable')}")
                        st.write(f"**Auto search:** {source.get('supports_auto_search')}")
                    with col_s2:
                        st.write(f"**Requires API key:** {source.get('requires_api_key')}")
                        st.write(f"**Fetches external URL:** {source.get('fetches_external_url')}")
                        st.write(f"**Safety:** {source.get('safety_level')}")
                    with col_s3:
                        st.write(f"**Last run:** {source.get('last_run_at') or '-'}")
                        st.write(f"**Last status:** {source.get('last_status') or '-'}")
                        st.write(f"**Last error:** {source.get('last_error') or '-'}")

                    st.caption(source.get("description") or "")
                    st.info(source.get("safety_notes") or "")
                    if source.get("message"):
                        st.warning(source.get("message"))

                    can_edit_enabled = source.get("status") != "not_implemented"
                    with st.form(f"jw_source_settings_form_{source_name}"):
                        new_enabled = st.checkbox(
                            t("jm_source_enabled"),
                            value=bool(source.get("enabled")),
                            disabled=not can_edit_enabled,
                            key=f"jw_source_enabled_{source_name}",
                        )
                        new_cooldown = st.number_input(
                            "Cooldown minutes / Bekleme süresi (dk)",
                            min_value=0,
                            max_value=1440,
                            value=int(source.get("cooldown_minutes") or 0),
                            step=1,
                            key=f"jw_source_cooldown_{source_name}",
                        )
                        config_value = json.dumps(source.get("config_json") or {}, ensure_ascii=False, indent=2)
                        with st.expander("Advanced config / Gelişmiş yapılandırma", expanded=False):
                            config_text = st.text_area(
                                "config_json",
                                value=config_value,
                                height=120,
                                key=f"jw_source_config_{source_name}",
                            )
                        save_source = st.form_submit_button(t("jm_source_update"))

                    if save_source:
                        try:
                            parsed_config = json.loads(config_text or "{}")
                        except Exception:
                            st.error("config_json must be valid JSON.")
                            parsed_config = None
                        if parsed_config is not None:
                            payload = {
                                "enabled": new_enabled,
                                "cooldown_minutes": int(new_cooldown),
                                "config_json": parsed_config,
                            }
                            result = api_json("PATCH", f"/job-monitoring/sources/{source_name}", json=payload)
                            if result:
                                st.success(t("jm_source_settings_saved"))
                                st.rerun()

                    test_col, _ = st.columns([1, 3])
                    with test_col:
                        if st.button(t("jm_source_test"), key=f"jw_source_test_{source_name}"):
                            test_result = api_json("POST", f"/job-monitoring/sources/{source_name}/test")
                            if test_result and test_result.get("success"):
                                st.success(test_result.get("message"))
                            elif test_result:
                                st.warning(test_result.get("message"))

    # --- Tab 5: Pipeline ---
    with tab_pipeline:
        st.subheader("Application Pipeline / Başvuru Takip")
        pipeline_jobs = api_json("GET", "/job-monitoring/pipeline") or []
        if not pipeline_jobs:
            st.info(t("jm_no_pipeline_jobs"))
        else:
            stages_count = {}
            high_priority_jobs = []
            upcoming_actions = []
            upcoming_deadlines = []
            
            for pj in pipeline_jobs:
                j = pj.get("job", {})
                p = pj.get("pipeline", {})
                
                stage = p.get("application_stage", "not_started")
                stages_count[stage] = stages_count.get(stage, 0) + 1
                
                if p.get("application_priority") == "high":
                    high_priority_jobs.append((j, p))
                if p.get("next_action_date"):
                    upcoming_actions.append((j, p))
                if p.get("application_deadline"):
                    upcoming_deadlines.append((j, p))
            
            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Preparing / Hazırlanıyor", stages_count.get("preparing", 0))
            with stat_cols[1]:
                st.metric("Applied / Başvuruldu", stages_count.get("applied", 0))
            with stat_cols[2]:
                st.metric("Interview / Mülakat", stages_count.get("interview", 0))
            with stat_cols[3]:
                st.metric("Offers / Teklifler", stages_count.get("offer", 0))
                
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                st.markdown(f"### 🔥 {t('jm_high_priority')}")
                if not high_priority_jobs:
                    st.write("No high priority jobs. / Yüksek öncelikli iş yok.")
                for j, p in high_priority_jobs[:5]:
                    st.write(f"- **{j.get('title')}** at *{j.get('company')}* (`{j.get('status')}`)")
            with sub_col2:
                st.markdown(f"### 📅 {t('jm_upcoming_actions')}")
                upcoming_actions.sort(key=lambda x: x[1].get("next_action_date", ""))
                if not upcoming_actions:
                    st.write("No upcoming actions. / Yaklaşan eylem yok.")
                for j, p in upcoming_actions[:5]:
                    st.write(f"- **{p.get('next_action_date')}**: {p.get('next_action')} (*{j.get('title')}*)")
            with sub_col3:
                st.markdown(f"### ⚠️ {t('jm_upcoming_deadlines')}")
                upcoming_deadlines.sort(key=lambda x: x[1].get("application_deadline", ""))
                if not upcoming_deadlines:
                    st.write("No upcoming deadlines. / Yaklaşan son tarih yok.")
                for j, p in upcoming_deadlines[:5]:
                    st.write(f"- **{p.get('application_deadline')}**: Apply to *{j.get('company')}*")

    # --- Tab 6: Assets ---
    with tab_assets:
        st.subheader("All Generated Assets / Tüm Oluşturulan Materyaller")
        assets_res = api_json("GET", "/job-monitoring/assets", timeout=30)
        all_assets = assets_res.get("assets", []) if assets_res else []
        if not all_assets:
            st.info(t("jm_no_assets"))
        else:
            all_assets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            jobs = api_json("GET", "/job-monitoring/jobs") or []
            jobs_map = {j.get("id"): j for j in jobs}
            
            limit_all_assets = all_assets[:5]
            has_more_all = len(all_assets) > 5
            show_all_assets = st.checkbox("Show all assets / Tüm materyalleri göster", value=False, key="jw_show_all_assets_global") if has_more_all else False
            display_all_assets = all_assets if show_all_assets else limit_all_assets
            
            for asset in display_all_assets:
                a_type = asset.get("asset_type")
                a_lang = asset.get("language")
                a_created = asset.get("created_at", "")[:16].replace("T", " ")
                a_fmt = asset.get("export_format") or "txt"
                
                j_id = asset.get("job_id")
                job_obj = jobs_map.get(j_id, {})
                job_title = job_obj.get("title") or "Unknown Job"
                job_company = job_obj.get("company") or "Unknown Company"
                
                asset_label = f"📄 {a_type.upper()} | {job_title} - {job_company} | {a_lang} | {a_fmt.upper()} | {a_created}{quality_badge(asset)}"
                
                col_a1, col_a2, col_a3 = st.columns([3, 1, 1])
                with col_a1:
                    st.write(asset_label)
                with col_a2:
                    if st.button(t("jm_preview"), key=f"jw_global_prev_asset_btn_{asset.get('id')}"):
                        st.session_state["preview_global_asset_id"] = asset.get("id")
                        fetched = api_json("GET", f"/job-monitoring/assets/{asset.get('id')}", timeout=30)
                        if fetched and "asset" in fetched:
                            st.session_state["preview_global_asset_dict"] = fetched.get("asset")
                            st.rerun()
                with col_a3:
                    f_path = asset.get("file_path")
                    f_bytes = get_local_asset_bytes_inline(f_path)
                    f_name = os.path.basename(f_path) if f_path else f"{a_type}_{j_id}.{a_fmt}"
                    if f_bytes is None:
                        f_bytes = (asset.get("content_text") or "").encode("utf-8")
                        f_name = f"{a_type}_{j_id}.txt"
                        a_fmt = "txt"
                    st.download_button(
                        t("jm_download"),
                        data=f_bytes,
                        file_name=f_name,
                        mime=media_types.get(a_fmt.lower(), "application/octet-stream"),
                        key=f"jw_global_dl_asset_btn_{asset.get('id')}"
                    )
                    
                if st.session_state.get("preview_global_asset_id") == asset.get("id"):
                    p_dict = st.session_state.get("preview_global_asset_dict")
                    if p_dict:
                        with st.container():
                            st.info(f"**Previewing:** {p_dict.get('asset_type').upper()} ({p_dict.get('language')})")
                            content = p_dict.get("content_text")
                            if not content and p_dict.get("file_path"):
                                content = "Metin içeriği bulunamadı, fiziksel dosyayı indirin."
                            st.text_area("Content Preview", content or "", height=250, key=f"jw_global_preview_textarea_{asset.get('id')}")
                            if p_dict.get("asset_type") == "tailored_cv":
                                render_quality_report(get_asset_quality_report(p_dict), t("cv_quality_check"), "quality_score")
                                render_quality_report(get_asset_structure_report(p_dict), t("structure_validation"), "structure_score")
                            if st.button("Close Preview / Önizlemeyi Kapat", key=f"jw_global_close_prev_{asset.get('id')}"):
                                st.session_state["preview_global_asset_id"] = None
                                st.session_state["preview_global_asset_dict"] = None
                                st.rerun()


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
