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
        "nav_job_workspace": "💼 İlan Hazırlık Alanı",
        "nav_cv_tools": "🔍 CV Araçları",
        "nav_application_materials": "✉️ Başvuru Materyalleri",
        "override_inputs_title": "⚙️ Genel Dosyaları Geçersiz Kıl / Özel Giriş Kullan (İsteğe Bağlı)",
        "override_cv_label": "Bu sayfa için farklı bir CV yükle (İsteğe Bağlı):",
        "override_job_label": "Bu sayfa için farklı bir iş ilanı girin (İsteğe Bağlı):",
        # Job Workspace tab labels
        "tab_add_job": "İlan Ekle",
        "tab_jobs": "İlanlar",
        "tab_assets": "Çıktılar",
        "tab_search_profiles": "Mock Arama (Gelişmiş)",
        "tab_sources": "Kaynaklar (Gelişmiş)",
        "tab_pipeline": "Pipeline (Opsiyonel)",
        "job_workspace_desc": "Bu alanı iş ilanını eklemek, uygunluğu analiz etmek ve ilana özel başvuru dokümanları üretmek için kullanın.",

        # Validation & Warnings
        "please_upload_cv": "Devam etmek için sol menüden bir CV yükleyin.",
        "please_enter_job_desc": "Devam etmek için sol menüye bir iş ilanı metni girin.",
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
        "dashboard_desc": "CV ve iş ilanını kullanarak ATS uyumlu özelleştirilmiş CV, kapak yazısı, recruiter e-postası ve mülakat hazırlığı çıktıları üreten yapay zekâ destekli başvuru dokümanı aracı.",
        "db_operations": "Toplam İşlem",
        "db_latest_match": "Son Uyum Skoru",
        "db_latest_ats": "Son ATS Skoru",
        "db_features": "🚀 Özellikler Genel Bakış",
        "db_demo_workflow": "CV + İş İlanı → Başvuru Dokümanları",
        "db_demo_step_1": "1. CV yükleyin.",
        "db_demo_step_2": "2. İş açıklamasını yapıştırın veya tek tıklamayla manuel linkten çıkarmayı deneyin.",
        "db_demo_step_3": "3. Uygunluk ve ATS analizini inceleyin.",
        "db_demo_step_4": "4. ATS uyumlu özelleştirilmiş CV oluşturun.",
        "db_demo_step_5": "5. Kapak yazısı oluşturun.",
        "db_demo_step_6": "6. Recruiter/başvuru e-postası ve mülakat hazırlığı üretin.",
        "db_demo_step_7": "7. Çıktıları DOCX/PDF/TXT olarak indirin.",
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
        "job_monitoring_desc": "Gelişmiş demo araçlarıyla mock ilan çalıştırmaları yapın ve kayıtlı ilanları başvuru dokümanı üretimi için puanlayın. Gerçek ilan kaynağı adaptörleri sonraki fazlarda eklenecektir.",
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
        "jm_no_jobs": "Henüz ilan yok. İlan Ekle sekmesinden hedef ilanınızı yapıştırın veya gelişmiş mock arama ile demo veri oluşturun.",
        "jm_no_pipeline_jobs": "Henüz opsiyonel pipeline notu yok. Bir ilan ekleyip İlanlar sekmesinden durum, öncelik ve notları kaydedebilirsiniz.",
        "jm_no_assets": "Henüz materyal oluşturulmadı. Bir ilan açın, global CV yükleyin ve Generate Materials bölümünden başlayın.",
        "jm_no_job_assets": "Bu ilan için henüz materyal oluşturulmadı.",
        "jm_search_profile_help": "Gelişmiş demo aracı: manual_mock kaynağından güvenli örnek ilanlar üretir. Gerçek iş ilanı kaynakları bu fazda çalıştırılmaz.",
        "jm_global_cv_default": "Global CV varsayılan olarak kullanılır",
        "jm_global_cv_missing": "Sol menüden henüz CV yüklenmedi. Materyal oluşturmak için CV yükleyin veya isteğe bağlı override kullanın.",
        "jm_add_job_next_step": "Başlık, şirket ve ilan açıklaması yeterlidir. URL yalnızca metin olarak saklanır.",
        "jm_no_runs": "Henüz çalıştırma geçmişi yok.",
        "jm_manual_import": "Manuel İlan Ekle",
        "jm_manual_import_desc": "Hedef iş ilanını manuel olarak yapıştırın. Uygulama ilanı kaydeder, uygunluk skorunu hesaplar ve ilana özel başvuru dokümanları üretmenizi sağlar. URL yalnızca metin olarak saklanır; bu fazda ilan sitelerinden otomatik veri çekilmez.",
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
        "jm_sources_phase3a_note": "Mock kaynak çalıştırma, kaynak ayarları ve opsiyonel pipeline notları test ve gelecekteki ilan kaynağı entegrasyonları için gelişmiş araçlar olarak tutulur. Şu anda yalnızca manual_mock çalıştırılabilir.",
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
        "jm_pipeline_title": "Opsiyonel Başvuru Notları",
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
        "jm_save_pipeline": "Notları Kaydet",
        "jm_pipeline_updated": "Opsiyonel başvuru notları güncellendi.",
        "jm_pipeline_overview": "Notlar Genel Bakış",
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
        "ats_cv_builder_next_phase": "CV ve iş ilanını kullanarak ATS uyumlu, ilana özel CV oluşturun.",
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
        "ats_cv_generic_note": "İletişim bilgileri ve özel isimler CV’den korunur; gerekirse oluşturmadan önce düzenleyebilirsiniz.",
        "locked_contact_fields": "Kilitli İletişim Bilgileri",
        "locked_fields_protection": "Kilitli bilgiler ve özel isim koruması",
        "contact_summary_empty": "İletişim özeti henüz çıkarılamadı.",
        "locked_contact_warning": "Ad, e-posta veya telefon alanlarından biri boş. CV’den çıkarılamadıysa oluşturma öncesinde elle doldurabilirsiniz.",
        "locked_proper_nouns": "Kilitli Özel İsimler",
        "locked_full_name": "Ad Soyad",
        "locked_email": "E-posta",
        "locked_phone": "Telefon",
        "locked_location": "Konum",
        "locked_linkedin": "LinkedIn",
        "locked_github": "GitHub",
        "locked_portfolio": "Portföy",
        "optimize_one_page": "Tek sayfaya sığdırmayı dene",
        "export_style": "Dışa Aktarım Stili",
        "export_style_standard": "Standart",
        "export_style_balanced": "Tek sayfaya sığdırmayı dene",
        "balanced_one_page_help": "Tam içerik için Standart, kompakt çıktı için Tek sayfaya sığdırmayı dene seçeneğini kullanın.",
        "export_sections": "Dışa Aktarılacak Bölümler",
        "main_settings": "Ana Ayarlar",
        "template_guidance": "Şablon önerisi",
        "export_download": "Dışa Aktar / İndir",
        "advanced_export_options": "Gelişmiş dışa aktarma seçenekleri",
        "photo_status": "Fotoğraf durumu",
        "photo_included_yes": "Fotoğraf eklenecek: Evet",
        "photo_included_no": "Fotoğraf eklenecek: Hayır",
        "quality_and_structure": "Kalite ve Yapı",
        "keyword_analysis": "Anahtar Kelime Analizi",
        "ats_explanation_notes": "ATS Açıklaması ve İyileştirme Notları",
        "adaptation_quality": "Uyarlama Kalitesi",
        "advanced_technical_details": "Gelişmiş / Teknik Detaylar",
        "adaptation_quality_missing": "Uyarlama kalite raporu bulunmuyor.",
        "adaptation_domain": "Alan",
        "summary_alignment": "Özet",
        "skills_alignment": "Yetenekler",
        "experience_alignment": "Deneyim",
        "project_alignment": "Projeler",
        "adaptation_level": "Uyarlama Seviyesi",
        "adaptation_conservative": "Kaynak CV’ye en yakın",
        "adaptation_balanced": "Dengeli uyarlama",
        "adaptation_strong": "İlana daha güçlü uyarlama",
        "adaptation_strong_help": "Güçlü uyarlama başlık, özet, yetenek ve madde vurgularını ilana göre belirginleştirir; doğrulanmamış deneyim eklemez.",
        "cv_quality_check": "CV Kalite Kontrolü",
        "structure_validation": "Yapı Doğrulama",
        "cv_quality_score": "CV Kalite Skoru",
        "structure_score": "Yapı Skoru",
        "needs_review": "İnceleme gerekli",
        "looks_clean": "Temiz görünüyor. Yine de göndermeden önce kontrol edin.",
        "quality_metadata_missing": "Bu eski çıktı için kalite metadatası bulunmuyor.",
        "docx_preview_limited": "DOCX önizleme sınırlı olabilir. Formatı kontrol etmek için dosyayı indirip açın.",
        "critical_section_warning": "Kritik bölümleri devre dışı bırakmak CV'nin etkisini azaltabilir.",
        "key_section_warning": "Deneyim, Eğitim veya Yetenekler bölümlerini devre dışı bırakmak ATS uygunluğunu azaltabilir.",
        "contact": "İletişim",
        "summary_section": "Özet",
        "skills_section": "Yetenekler",
        "experience_section": "Deneyim",
        "projects_section": "Projeler",
        "education_section": "Eğitim",
        "certifications_section": "Sertifikalar",
        "languages_section": "Yabancı Diller",

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
        "docx_layout": "Yerleşim",
        "docx_supports_photo": "Fotoğraf desteği",
        "cv_photo_optional": "CV Fotoğrafı (Opsiyonel)",
        "include_photo_cv": "Fotoğrafı CV’ye ekle",
        "photo_template_warning": "Bu şablon fotoğraf içermez.",
        "photo_template_ready": "Seçili şablon fotoğrafı başlık alanına ekleyebilir. Fotoğraf opsiyoneldir ve varsayılan olarak kapalıdır.",
        "photo_best_result_note": "Fotoğraf opsiyoneldir. Kare veya portre fotoğraf önerilir.",
        "no_global_cv": "Sol menüden henüz CV yüklenmedi.",
        "no_global_job_desc": "Sol menüye henüz iş ilanı metni girilmedi.",
        "input_status": "Girdi Durumu",
        "contact_fields_missing": "Bazı iletişim alanları CV’den otomatik çıkarılamadı. Oluşturmadan önce elle doldurabilirsiniz.",
        "db_feat_cv_tools": "CV analizi, ATS puanlaması, iyileştirme önerileri ve bölüm yeniden yazma için ortak CV ve iş ilanı verilerini kullanın.",
        "db_feat_job_workspace": "İş ilanını ekleyin, uygunluğu analiz edin ve kaydedilmiş ilandan özel başvuru dokümanları oluşturun.",
        "db_feat_app_materials": "Ortak girdileri kullanarak kapak yazıları, başvuru e-postaları ve mülakat hazırlık rehberleri oluşturun.",
        "db_feat_ats_cv_builder": "Yüklenen CV'deki iletişim bilgilerini koruyarak ATS uyumlu CV çıktıları (DOCX/PDF/TXT) oluşturun.",
        "export_cv": "Dışa Aktar",
        "professional_summary": "Profesyonel Özet",
        "career_objective": "Kariyer Hedefi",
        "technical_summary": "Teknik Özet",
        "cv_output_lang": "CV Çıktı Dili",
        "using_global_cv": "✓ Ortak CV kullanılıyor: **{name}**",
        "using_global_job": "✓ Ortak iş ilanı metni kullanılıyor.",
        "using_override_cv": "Farklı CV kullanılıyor: {name}",
        "using_override_job": "Farklı iş ilanı metni kullanılıyor.",
        "target_title_lbl": "Hedef CV Başlığı"
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
        "nav_job_workspace": "💼 Job Prep Workspace",
        "nav_cv_tools": "🔍 CV Tools",
        "nav_application_materials": "✉️ Application Materials",
        "override_inputs_title": "⚙️ Override Global CV / Job Description (Optional)",
        "override_cv_label": "Upload a different CV for this page (Optional):",
        "override_job_label": "Enter a different job description for this page (Optional):",
        # Job Workspace tab labels
        "tab_add_job": "Add Job",
        "tab_jobs": "Jobs",
        "tab_assets": "Assets",
        "tab_search_profiles": "Mock Search (Advanced)",
        "tab_sources": "Sources (Advanced)",
        "tab_pipeline": "Pipeline (Optional)",
        "job_workspace_desc": "Use this workspace to add a job posting, analyze fit, and generate tailored application materials.",

        # Validation & Warnings
        "please_upload_cv": "Upload a CV from the sidebar to continue.",
        "please_enter_job_desc": "Enter a job description in the sidebar to continue.",
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
        "dashboard_desc": "AI-assisted job application document generator that turns a CV and job description into ATS-friendly tailored CVs, cover letters, recruiter emails, and interview prep materials.",
        "db_operations": "Total Operations",
        "db_latest_match": "Latest Match Score",
        "db_latest_ats": "Latest ATS Score",
        "db_features": "🚀 Features Overview",
        "db_demo_workflow": "CV + Job Description → Tailored Application Materials",
        "db_demo_step_1": "1. Upload a CV.",
        "db_demo_step_2": "2. Paste a job description or manually extract one link with a click.",
        "db_demo_step_3": "3. Analyze match and ATS alignment.",
        "db_demo_step_4": "4. Generate an ATS-friendly tailored CV.",
        "db_demo_step_5": "5. Generate a cover letter.",
        "db_demo_step_6": "6. Generate a recruiter/application email and interview prep.",
        "db_demo_step_7": "7. Download the outputs as DOCX/PDF/TXT.",
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
        "job_monitoring_desc": "Use advanced demo tools for mock job runs and score saved postings for application material generation. Real job board adapters will be added in later phases.",
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
        "jm_no_jobs": "No jobs yet. Paste a target posting in Add Job or use the advanced mock search for demo data.",
        "jm_no_pipeline_jobs": "No optional pipeline notes yet. Add a job, then save status, priority, and notes from the Jobs tab if useful.",
        "jm_no_assets": "No assets generated yet. Open a job, upload a global CV, and use Generate Materials.",
        "jm_no_job_assets": "No assets generated yet for this job.",
        "jm_search_profile_help": "Advanced demo tool: run the safe manual_mock source for sample postings. Real job board sources are not runnable in this phase.",
        "jm_global_cv_default": "Uses global CV by default",
        "jm_global_cv_missing": "No global CV uploaded in sidebar. Upload one or use the optional override before generating materials.",
        "jm_add_job_next_step": "Title, company, and description are enough to start. URLs are stored as text only.",
        "jm_no_runs": "No run history yet.",
        "jm_manual_import": "Manual Job Import",
        "jm_manual_import_desc": "Paste the target job posting manually. The app stores it, scores fit, and lets you generate tailored application materials. The URL is stored only as text; the app does not scrape job boards in this phase.",
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
        "jm_sources_phase3a_note": "Advanced tools such as mock source runs, source settings, and optional pipeline notes are available for testing and future job-board integrations. Only manual_mock is runnable today.",
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
        "jm_pipeline_title": "Optional Application Notes",
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
        "jm_save_pipeline": "Save Notes",
        "jm_pipeline_updated": "Optional application notes updated.",
        "jm_pipeline_overview": "Notes Overview",
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
        "ats_cv_builder_next_phase": "Generate an ATS-friendly tailored CV from your CV and the job description.",
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
        "ats_cv_generic_note": "Contact details and proper nouns are preserved from the CV and can be edited before generation.",
        "locked_contact_fields": "Locked Contact Fields",
        "locked_fields_protection": "Locked fields and proper-name protection",
        "contact_summary_empty": "No contact summary extracted yet.",
        "locked_contact_warning": "Full name, email, or phone is empty. If extraction missed it, you can fill it manually before generation.",
        "locked_proper_nouns": "Locked Proper Nouns",
        "locked_full_name": "Full Name",
        "locked_email": "Email",
        "locked_phone": "Phone",
        "locked_location": "Location",
        "locked_linkedin": "LinkedIn",
        "locked_github": "GitHub",
        "locked_portfolio": "Portfolio",
        "optimize_one_page": "Try to fit into one page",
        "export_style": "Export Style",
        "export_style_standard": "Standard",
        "export_style_balanced": "Try to fit into one page",
        "balanced_one_page_help": "Choose Standard for full content, or Try to fit into one page for a compact export.",
        "export_sections": "Export Sections",
        "main_settings": "Main Settings",
        "template_guidance": "Template guidance",
        "export_download": "Export / Download",
        "advanced_export_options": "Advanced export options",
        "photo_status": "Photo status",
        "photo_included_yes": "Photo included: Yes",
        "photo_included_no": "Photo included: No",
        "quality_and_structure": "Quality and Structure",
        "keyword_analysis": "Keyword Analysis",
        "ats_explanation_notes": "ATS Explanation and Improvement Notes",
        "adaptation_quality": "Adaptation Quality",
        "advanced_technical_details": "Advanced / Technical Details",
        "adaptation_quality_missing": "Adaptation quality report is not available.",
        "adaptation_domain": "Domain",
        "summary_alignment": "Summary",
        "skills_alignment": "Skills",
        "experience_alignment": "Experience",
        "project_alignment": "Projects",
        "adaptation_level": "Adaptation Level",
        "adaptation_conservative": "Closest to source CV",
        "adaptation_balanced": "Balanced tailoring",
        "adaptation_strong": "Stronger job-specific tailoring",
        "adaptation_strong_help": "Strong adapts title, summary, skills, and bullet emphasis to the job without inventing experience.",
        "cv_quality_check": "CV Quality Check",
        "structure_validation": "Structure Validation",
        "cv_quality_score": "CV Quality Score",
        "structure_score": "Structure Score",
        "needs_review": "Needs review",
        "looks_clean": "Looks clean. Still review before sending.",
        "quality_metadata_missing": "Quality metadata is not available for this older asset.",
        "docx_preview_limited": "DOCX preview may be limited. Please download and open the file to review formatting.",
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
        "docx_layout": "Layout",
        "docx_supports_photo": "Photo support",
        "cv_photo_optional": "CV Photo (Optional)",
        "include_photo_cv": "Include photo in CV",
        "photo_template_warning": "This template does not include a photo.",
        "photo_template_ready": "The selected template can place the photo in the header. Photo is optional and off by default.",
        "photo_best_result_note": "Optional photo. Best with square or portrait images.",
        "no_global_cv": "No global CV uploaded in sidebar.",
        "no_global_job_desc": "No global job description in sidebar.",
        "input_status": "Input Status",
        "contact_fields_missing": "Some contact fields could not be extracted automatically. You can fill them before generating.",
        "db_feat_cv_tools": "Use the global CV and job description for CV analysis, ATS scoring, improvement suggestions, and section rewrites.",
        "db_feat_job_workspace": "Add a job posting, analyze fit, and generate job-specific application materials from saved listings.",
        "db_feat_app_materials": "Generate cover letters, application emails, and interview prep using the shared inputs.",
        "db_feat_ats_cv_builder": "Build ATS-friendly CV exports while preserving locked contact fields from the uploaded CV.",
        "export_cv": "Export",
        "professional_summary": "Professional Summary",
        "career_objective": "Career Objective",
        "technical_summary": "Technical Summary",
        "cv_output_lang": "CV Output Language",
        "using_global_cv": "✓ Using global CV: **{name}**",
        "using_global_job": "✓ Using global job description from sidebar.",
        "using_override_cv": "Using override CV: {name}",
        "using_override_job": "Using override job description.",
        "target_title_lbl": "Target Title"
    }
}

# Ensure session state variables exist
if "global_job_text" not in st.session_state:
    st.session_state.global_job_text = ""
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "en"
if "show_ats_cv_export_dialog" not in st.session_state:
    st.session_state.show_ats_cv_export_dialog = False

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

TEMPLATE_TRANSLATIONS = {
    "classic_ats": {
        "description": "Kurumsal, bankacılık, BT, arka uç, iş analisti ve genel profesyonel başvurular için uygun, güvenli, tek sütunlu ATS uyumlu özgeçmiş şablonu.",
        "best_for": [
            "kurumsal", "bankacılık", "BT", "arka uç", "iş analisti", "ERP", "staj", "başlangıç rolleri"
        ],
        "ats_notes": [
            "Öngörülebilir ATS ayrıştırması için tek sütunlu yapı kullanır.",
            "Özgeçmiş tarayıcılarını şaşırtabilecek simgelerden, grafiklerden ve tablolardan kaçınır.",
            "Net başlıklar ve standart bölümler kullanır.",
            "İçeriği anahtar kelime dostu bir düzende tutar."
        ]
    },
    "modern_clean": {
        "description": "ATS uyumlu kalırken biraz daha modern boşluklara sahip temiz ve profesyonel tek sütunlu bir CV şablonu.",
        "best_for": [
            "yazılım geliştirici", "iş analisti", "ürün", "BT uzmanı", "kurumsal başvurular", "teknoloji rolleri"
        ],
        "ats_notes": [
            "Temiz boşluklu tek sütunlu bir yapıyı korur.",
            "Simgelerden, grafiklerden ve tablolardan kaçınır.",
            "Tarayıcı uyumluluğu için net başlıklar ve standart bölümler kullanır.",
            "Modern bir sunum sürdürürken anahtar kelime dostu düzeni destekler."
        ]
    },
    "technical_developer": {
        "description": "İş deneyiminden önce teknik becerileri ve projeleri öne çıkaran, geliştirici odaklı ATS uyumlu bir CV şablonu.",
        "best_for": [
            "arka uç geliştirici", "ön uç geliştirici", "full-stack geliştirici", "yazılım mühendisi", "API geliştirici", "başlangıç seviyesi geliştirici", "stajyer geliştirici"
        ],
        "ats_notes": [
            "Okuma sırasını koruyan tek sütunlu bir yapı kullanır.",
            "ATS doğruluğunu azaltabilecek simgelerden, grafiklerden ve tablolardan kaçınır.",
            "Net teknik başlıklar ve standart özgeçmiş bölümleri kullanır.",
            "Anahtar kelimeleri ve proje kanıtlarını tarayıcıların kolayca okuyabileceği yerlere yerleştirir."
        ]
    },
    "junior_internship": {
        "description": "Öğrenciler, stajyerler, yeni mezunlar ve başlangıç seviyesindeki adaylar için ATS uyumlu bir CV şablonu. Eğitim, teknik yetenekler, projeler ve staj deneyimini öne çıkarır.",
        "best_for": [
            "staj", "yeni mezun", "başlangıç seviyesi geliştirici", "öğrenci", "stajyer"
        ],
        "ats_notes": [
            "Güvenilir ATS ayrıştırması için tek sütunlu yapı kullanır.",
            "Simgelerden, grafiklerden ve tablolardan kaçınır.",
            "Başlangıç seviyesi profillere özel net başlıklar ve standart bölümler kullanır.",
            "Anahtar kelime eşleşmesi için eğitim, yetenekler ve projelere öncelik verir."
        ]
    }
}


TEMPLATE_METADATA_EXT = {
    "en": {
        "modern_professional": {
            "description": "A polished general-purpose ATS-friendly one-column CV template with stronger header hierarchy, thin section rules, and professional spacing.",
            "best_for": [
                "product roles", "business analyst", "corporate IT", "business roles", "operations", "junior professional", "new graduate"
            ],
            "recommended_for": "Product managers, business analysts, operations, corporate IT, and new graduates.",
            "not_recommended_for": "Highly academic research or creative design-heavy roles (unless clean corporate layout is preferred).",
            "cautions": "Ensure section rules (thin lines) render correctly in your PDF/DOCX readers before applying.",
            "ats_notes": [
                "Keeps the main CV body in one column.",
                "Uses text-based headings and thin rules instead of icons or graphics.",
                "Preserves standard section names and reading order for ATS compatibility.",
                "Best reviewed as DOCX/PDF before submission because it is more visually styled."
            ]
        },
        "compact_technical": {
            "description": "A compact, technical, ATS-safe CV template with dense but readable spacing, strong section rules, and clear skills/project emphasis.",
            "best_for": [
                "backend developer", "software engineer", "data engineer", "AI engineer", "API developer", "technical internship"
            ],
            "recommended_for": "Backend developers, software engineers, data & AI scientists, and technical applications with lots of projects.",
            "not_recommended_for": "Non-technical marketing, sales, or executive business roles where project detail is less important.",
            "cautions": "Highly dense layout. Keep bullets concise to prevent readability issues.",
            "ats_notes": [
                "Uses compact one-column structure for ATS parsing.",
                "Places technical skills and projects high in the document.",
                "Avoids icons, text boxes, decorative tables, and multi-column body content.",
                "Suitable when content needs to fit into a concise technical CV."
            ]
        },
        "visual_photo_optional": {
            "description": "A polished one-column CV template with optional modest header photo support for local/Turkish/corporate submissions where photo CVs are acceptable. Works best with square or portrait photos.",
            "best_for": [
                "Turkish applications", "local corporate roles", "photo-acceptable submissions", "visual professional CVs"
            ],
            "recommended_for": "Turkish and local corporate applications where a photo CV is customary.",
            "not_recommended_for": "Strict US/UK ATS-heavy or photo-blind application processes.",
            "cautions": "Always use a high-quality professional portrait photo. Avoid casual selfies.",
            "ats_notes": [
                "Photo support is optional and disabled by default.",
                "Main content remains one-column and text-based.",
                "Use the photo only where the target market or employer accepts photo CVs.",
                "Square or portrait photos render best; uploaded images are cropped without stretching.",
                "For strict ATS or photo-blind processes, export without photo."
            ]
        },
        "classic_ats": {
            "description": "A safe, single-column ATS-friendly resume template suitable for corporate, banking, IT, backend, business analyst, and general professional applications.",
            "best_for": ["corporate", "banking", "IT", "backend", "business analyst", "ERP", "internship", "junior roles"],
            "recommended_for": "Corporate, banking, finance, IT, and traditional corporate job applications.",
            "not_recommended_for": "Highly creative agencies or design-focused roles.",
            "cautions": "Very traditional layout; may feel plain but offers maximum ATS compatibility.",
            "ats_notes": [
                "Uses a one-column structure for predictable ATS parsing.",
                "Avoids icons, graphics, and tables that can confuse resume scanners.",
                "Uses clear headings and standard sections.",
                "Keeps content in a keyword-friendly layout for job-specific optimization."
            ]
        },
        "modern_clean": {
            "description": "A clean and professional one-column CV template with slightly more modern spacing while remaining ATS compatible.",
            "best_for": ["software developer", "business analyst", "product", "IT specialist", "corporate applications", "technology roles"],
            "recommended_for": "Technology, product, and modern corporate applications.",
            "not_recommended_for": "Creative design roles requiring complex multi-column layouts.",
            "cautions": "Slightly wider margins; keep text aligned properly.",
            "ats_notes": [
                "Keeps a one-column structure with clean spacing.",
                "Avoids icons, graphics, and tables.",
                "Uses clear headings and standard sections for scanner compatibility.",
                "Supports a keyword-friendly layout while keeping a modern presentation."
            ]
        },
        "technical_developer": {
            "description": "An ATS-friendly developer-focused CV template that highlights technical skills and projects before work experience.",
            "best_for": ["backend developer", "frontend developer", "full-stack developer", "software engineer", "API developer", "junior developer", "intern developer"],
            "recommended_for": "Software developers, junior engineers, and recent technical graduates.",
            "not_recommended_for": "Non-technical or executive business management roles.",
            "cautions": "Experience is placed below projects/skills; not ideal for candidates with 10+ years of experience.",
            "ats_notes": [
                "Uses a one-column structure that preserves reading order.",
                "Avoids icons, graphics, and tables that can reduce ATS accuracy.",
                "Uses clear technical headings and standard resume sections.",
                "Places technical keywords and project evidence where scanners can read them easily."
            ]
        },
        "junior_internship": {
            "description": "An ATS-friendly CV template for students, interns, fresh graduates, and junior candidates. It highlights education, technical skills, projects, and internship experience.",
            "best_for": ["internship", "fresh graduate", "junior developer", "student", "trainee", "new graduate"],
            "recommended_for": "Students applying for internships, fresh graduates, and entry-level applicants.",
            "not_recommended_for": "Mid-level or senior professionals with extensive work histories.",
            "cautions": "Education is placed at the top; senior profiles should avoid this template.",
            "ats_notes": [
                "Uses a one-column structure for reliable ATS parsing.",
                "Avoids icons, graphics, and tables.",
                "Uses clear headings and standard sections tailored to junior profiles.",
                "Prioritizes education, skills, and projects for keyword-friendly matching."
            ]
        }
    },
    "tr": {
        "modern_professional": {
            "description": "Cilalı, genel amaçlı, ATS uyumlu tek sütunlu CV şablonu. Güçlü başlık hiyerarşisi, ince bölüm çizgileri ve profesyonel boşluklar içerir.",
            "best_for": [
                "ürün rolleri", "iş analisti", "kurumsal BT", "iş rolleri", "operasyonlar", "başlangıç seviyesi profesyonel", "yeni mezun"
            ],
            "recommended_for": "Ürün yöneticileri, iş analistleri, operasyon, kurumsal BT ve yeni mezunlar.",
            "not_recommended_for": "Akademik araştırmalar veya yaratıcı tasarım odaklı roller (sade kurumsal düzen tercih edilmiyorsa).",
            "cautions": "Başvurmadan önce bölüm çizgilerinin (ince çizgiler) PDF/DOCX okuyucunuzda düzgün göründüğünden emin olun.",
            "ats_notes": [
                "Ana CV gövdesini tek sütunda tutar.",
                "Simgeler veya grafikler yerine metin tabanlı başlıklar ve ince çizgiler kullanır.",
                "ATS uyumluluğu için standart bölüm adlarını ve okuma sırasını korur.",
                "Daha görsel tasarıma sahip olduğundan, göndermeden önce DOCX/PDF olarak incelenmesi önerilir."
            ]
        },
        "compact_technical": {
            "description": "Kompakt, teknik, ATS açısından güvenli CV şablonu. Yoğun ama okunabilir boşluklar, güçlü bölüm çizgileri ve net beceri/proje vurgusu sunar.",
            "best_for": [
                "arka uç geliştirici", "yazılım mühendisi", "veri mühendisi", "yapay zeka mühendisi", "API geliştirici", "teknik staj"
            ],
            "recommended_for": "Arka uç geliştiriciler, yazılım mühendisleri, veri ve yapay zeka bilimcileri ve bol projeli teknik başvurular.",
            "not_recommended_for": "Proje detaylarının daha az önemli olduğu teknik olmayan pazarlama, satış veya yönetici iş rolleri.",
            "cautions": "Çok yoğun düzen. Okunabilirlik sorunlarını önlemek için madde işaretlerini kısa tutun.",
            "ats_notes": [
                "ATS ayrıştırması için kompakt tek sütunlu yapı kullanır.",
                "Teknik becerileri ve projeleri belgede üst sıralara yerleştirir.",
                "Simgelerden, metin kutularından, dekoratif tablolardan ve çok sütunlu gövde içeriğinden kaçınır.",
                "İçeriğin kısa ve öz bir teknik CV'ye sığdırılması gerektiğinde uygundur."
            ]
        },
        "visual_photo_optional": {
            "description": "Seçmeli mütevazı başlık fotoğraf desteğine sahip cilalı tek sütunlu CV şablonu. Fotoğraflı özgeçmişlerin kabul edildiği yerel/Türkçe/kurumsal başvurular için tasarlanmıştır. Kare veya dikey fotoğraflarla en iyi şekilde çalışır.",
            "best_for": [
                "Türkçe başvurular", "yerel kurumsal roller", "fotoğraf kabul eden başvurular", "görsel profesyonel özgeçmişler"
            ],
            "recommended_for": "Fotoğraflı CV'nin geleneksel olduğu Türkiye ve yerel kurumsal başvurular.",
            "not_recommended_for": "Katı ABD/İngiltere ATS ağırlıklı veya fotoğrafsız başvuru süreçleri.",
            "cautions": "Her zaman yüksek kaliteli profesyonel bir portre fotoğrafı kullanın. Günlük özçekimlerden kaçının.",
            "ats_notes": [
                "Fotoğraf desteği isteğe bağlıdır ve varsayılan olarak kapalıdır.",
                "Ana içerik tek sütunlu ve metin tabanlı kalır.",
                "Fotoğrafı yalnızca hedef pazar veya işveren fotoğraflı CV'leri kabul ediyorsa kullanın.",
                "Kare veya dikey fotoğraflar en iyi sonucu verir; yüklenen görseller bozulmadan kırpılır.",
                "Kesin ATS taraması veya fotoğrafsız süreçler için fotoğrafsız ihraç edin."
            ]
        },
        "classic_ats": {
            "description": "Kurumsal, bankacılık, BT, arka uç, iş analisti ve genel profesyonel başvurular için uygun, güvenli, tek sütunlu ATS uyumlu özgeçmiş şablonu.",
            "best_for": [
                "kurumsal", "bankacılık", "BT", "arka uç", "iş analisti", "ERP", "staj", "başlangıç rolleri"
            ],
            "recommended_for": "Kurumsal, bankacılık, finans, BT ve geleneksel kurumsal iş başvuruları.",
            "not_recommended_for": "Yaratıcı ajanslar veya tasarım odaklı roller.",
            "cautions": "Çok geleneksel düzen; sade gelebilir ancak maksimum ATS uyumluluğu sunar.",
            "ats_notes": [
                "Öngörülebilir ATS ayrıştırması için tek sütunlu yapı kullanır.",
                "Özgeçmiş tarayıcılarını şaşırtabilecek simgelerden, grafiklerden ve tablolardan kaçınır.",
                "Net başlıklar ve standart bölümler kullanır.",
                "İçeriği anahtar kelime dostu bir düzende tutar."
            ]
        },
        "modern_clean": {
            "description": "ATS uyumlu kalırken biraz daha modern boşluklara sahip temiz ve profesyonel tek sütunlu bir CV şablonu.",
            "best_for": [
                "yazılım geliştirici", "iş analisti", "ürün", "BT uzmanı", "kurumsal başvurular", "teknoloji rolleri"
            ],
            "recommended_for": "Teknoloji, ürün ve modern kurumsal başvurular.",
            "not_recommended_for": "Karmaşık çok sütunlu düzenler gerektiren yaratıcı tasarım rolleri.",
            "cautions": "Biraz daha geniş kenar boşlukları; metni düzgün şekilde hizalanmış tutun.",
            "ats_notes": [
                "Temiz boşluklu tek sütunlu bir yapıyı korur.",
                "Simgelerden, grafiklerden ve tablolardan kaçınır.",
                "Tarayıcı uyumluluğu için net başlıklar ve standart bölümler kullanır.",
                "Modern bir sunum sürdürürken anahtar kelime dostu düzeni destekler."
            ]
        },
        "technical_developer": {
            "description": "İş deneyiminden önce teknik becerileri ve projeleri öne çıkaran, geliştirici odaklı ATS uyumlu bir CV şablonu.",
            "best_for": [
                "arka uç geliştirici", "ön uç geliştirici", "full-stack geliştirici", "yazılım mühendisi", "API geliştirici", "başlangıç seviyesi geliştirici", "stajyer geliştirici"
            ],
            "recommended_for": "Yazılım geliştiriciler, başlangıç seviyesindeki mühendisler ve yeni teknik mezunlar.",
            "not_recommended_for": "Teknik olmayan veya yönetici iş yönetimi rolleri.",
            "cautions": "Deneyim projelerin/becerilerin altında yer alır; 10 yıldan fazla deneyimi olan adaylar için ideal olmayabilir.",
            "ats_notes": [
                "Okuma sırasını koruyan tek sütunlu bir yapı kullanır.",
                "ATS doğruluğunu azaltabilecek simgelerden, grafiklerden ve tablolardan kaçınır.",
                "Net teknik başlıklar ve standart özgeçmiş bölümleri kullanır.",
                "Anahtar kelimeleri ve proje kanıtlarını tarayıcıların kolayca okuyabileceği yerlere yerleştirir."
            ]
        },
        "junior_internship": {
            "description": "Öğrenciler, stajyerler, yeni mezunlar ve başlangıç seviyesindeki adaylar için ATS uyumlu bir CV şablonu. Eğitim, teknik yetenekler, projeler ve staj deneyimini öne çıkarır.",
            "best_for": [
                "staj", "yeni mezun", "başlangıç seviyesi geliştirici", "öğrenci", "stajyer"
            ],
            "recommended_for": "Staj başvurusu yapan öğrenciler, yeni mezunlar ve giriş seviyesindeki adaylar.",
            "not_recommended_for": "Kapsamlı iş geçmişine sahip orta veya üst düzey profesyoneller.",
            "cautions": "Eğitim en üstte yer alır; kıdemli profiller bu şablondan kaçınmalıdır.",
            "ats_notes": [
                "Güvenilir ATS ayrıştırması için tek sütunlu yapı kullanır.",
                "Simgelerden, grafiklerden ve tablolardan kaçınır.",
                "Başlangıç seviyesi profillere özel net başlıklar ve standart bölümler kullanır.",
                "Anahtar kelime eşleşmesi için eğitim, yetenekler ve projelere öncelik verir."
            ]
        }
    }
}

def render_template_preview_cards(selected_id: str) -> None:
    is_tr = st.session_state.ui_lang == "tr"

    t_ats_safe = "ATS Uyumlu" if is_tr else "ATS Safe"
    t_one_col = "Tek Sütun" if is_tr else "One-Column"
    t_compact = "Kompakt" if is_tr else "Compact"
    t_photo_opt = "Fotoğraf Opsiyonel" if is_tr else "Photo Optional"
    t_photo_supported = "Fotoğraf: Destekleniyor" if is_tr else "Photo: Supported"
    t_photo_not_supported = "Fotoğraf: Yok" if is_tr else "Photo: No"
    t_recommended = "Önerilen" if is_tr else "Recommended"
    t_technical = "Teknik" if is_tr else "Technical"
    t_visual = "Görsel" if is_tr else "Visual"

    modern_guidance = (
        "Genel kurumsal, ürün, analist, IT ve yeni mezun başvuruları için dengeli şablon."
        if is_tr else
        "Best for general corporate, product, analyst, IT, and new graduate applications."
    )
    compact_guidance = (
        "Backend, yazılım, data/AI ve ATS ağırlıklı teknik başvurular için kompakt şablon."
        if is_tr else
        "Best for backend, software, data/AI, and ATS-heavy technical applications."
    )
    visual_guidance = (
        "Fotoğraflı CV’nin uygun olduğu yerel/kurumsal başvurular için görsel şablon."
        if is_tr else
        "Best for local/corporate applications where a photo CV is acceptable."
    )

    css = """
    <style>
    .mock-cv-page {
        background-color: #ffffff;
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 4px;
        padding: 4px 6px;
        height: 70px;
        position: relative;
        overflow: hidden;
        margin-top: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .mock-line {
        background-color: rgba(128, 128, 128, 0.3);
        height: 3px;
        margin-bottom: 3px;
        border-radius: 1px;
    }
    .mock-line.name {
        background-color: rgba(128, 128, 128, 0.6);
        height: 5px;
        width: 45%;
        margin-bottom: 4px;
    }
    .mock-line.title {
        background-color: rgba(128, 128, 128, 0.4);
        height: 3px;
        width: 30%;
        margin-bottom: 4px;
    }
    .mock-line.contact {
        background-color: rgba(128, 128, 128, 0.25);
        height: 2px;
        width: 65%;
        margin-bottom: 6px;
    }
    .mock-line.section-header {
        background-color: rgba(33, 150, 243, 0.5);
        height: 3px;
        width: 25%;
        margin-top: 4px;
        margin-bottom: 3px;
    }
    .mock-line.bullet {
        background-color: rgba(128, 128, 128, 0.2);
        height: 2px;
        width: 80%;
        margin-left: 6px;
        margin-bottom: 2px;
    }
    .mock-photo-placeholder {
        position: absolute;
        top: 4px;
        right: 4px;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background-color: rgba(128, 128, 128, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 5px;
        color: white;
    }
    .card-badge {
        display: inline-block;
        padding: 1px 4px;
        font-size: 0.65rem;
        font-weight: 500;
        border-radius: 3px;
        margin-right: 3px;
        margin-bottom: 3px;
    }
    .badge-ats { background-color: rgba(46, 125, 50, 0.15); color: #2e7d32; }
    .badge-col { background-color: rgba(21, 101, 192, 0.15); color: #1565c0; }
    .badge-comp { background-color: rgba(239, 108, 0, 0.15); color: #ef6c00; }
    .badge-photo { background-color: rgba(106, 27, 154, 0.15); color: #6a1b9a; }
    .badge-rec { background-color: rgba(197, 160, 89, 0.15); color: #c5a059; }
    .badge-tech { background-color: rgba(0, 150, 136, 0.15); color: #009688; }
    .badge-vis { background-color: rgba(233, 30, 99, 0.15); color: #e91e63; }

    .preview-card-container {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 6px;
        padding: 8px;
        background-color: rgba(128, 128, 128, 0.02);
        transition: all 0.3s ease;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .preview-card-container.selected {
        border: 2px solid #2e7d32;
        background-color: rgba(46, 125, 50, 0.04);
        box-shadow: 0 2px 6px rgba(46, 125, 50, 0.08);
    }
    .preview-card-title {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 2px;
        color: inherit;
    }
    .preview-card-guidance {
        font-size: 0.75rem;
        color: inherit;
        opacity: 0.85;
        margin-bottom: 4px;
        line-height: 1.2;
        min-height: 32px;
    }
    .preview-card-photo-info {
        font-size: 0.7rem;
        font-weight: 600;
        color: inherit;
        opacity: 0.7;
        margin-top: 4px;
        padding-top: 2px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        is_selected = selected_id == "modern_professional"
        sel_class = "selected" if is_selected else ""
        selected_badge = f"<span style='color: #2e7d32; font-weight: bold;'>✓ {'Seçildi' if is_tr else 'Selected'}</span>" if is_selected else ""

        card_html = f"""
        <div class="preview-card-container {sel_class}">
            <div>
                <div class="preview-card-title">Modern Professional {selected_badge}</div>
                <div style="margin-bottom: 3px;">
                    <span class="card-badge badge-ats">{t_ats_safe}</span>
                    <span class="card-badge badge-col">{t_one_col}</span>
                    <span class="card-badge badge-rec">{t_recommended}</span>
                </div>
                <div class="preview-card-guidance">{modern_guidance}</div>
            </div>
            <div>
                <div class="mock-cv-page" style="border-top: 2px solid #1565c0;">
                    <center>
                        <div class="mock-line name" style="width: 45%; margin-left: auto; margin-right: auto; background-color: #1565c0; height: 5px;"></div>
                        <div class="mock-line title" style="width: 25%; margin-left: auto; margin-right: auto; height: 3px;"></div>
                        <div class="mock-line contact" style="width: 65%; margin-left: auto; margin-right: auto; height: 2px;"></div>
                    </center>
                    <div style="border-bottom: 1px solid rgba(128,128,128,0.15); margin-top: 2px; margin-bottom: 2px;"></div>
                    <div class="mock-line section-header" style="background-color: #1565c0; width: 30%;"></div>
                    <div class="mock-line bullet" style="width: 80%;"></div>
                    <div class="mock-line bullet" style="width: 75%;"></div>
                </div>
                <div class="preview-card-photo-info">🚫 {t_photo_not_supported}</div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        btn_lbl = ("✓ Seçildi" if is_tr else "✓ Selected") if is_selected else ("Seç" if is_tr else "Select")
        if st.button(btn_lbl, key="btn_select_modern_professional", disabled=is_selected, use_container_width=True):
            st.session_state.ats_cv_selected_template_id = "modern_professional"
            st.rerun()

    with col2:
        is_selected = selected_id == "compact_technical"
        sel_class = "selected" if is_selected else ""
        selected_badge = f"<span style='color: #2e7d32; font-weight: bold;'>✓ {'Seçildi' if is_tr else 'Selected'}</span>" if is_selected else ""

        card_html = f"""
        <div class="preview-card-container {sel_class}">
            <div>
                <div class="preview-card-title">Compact Technical {selected_badge}</div>
                <div style="margin-bottom: 3px;">
                    <span class="card-badge badge-ats">{t_ats_safe}</span>
                    <span class="card-badge badge-comp">{t_compact}</span>
                    <span class="card-badge badge-tech">{t_technical}</span>
                </div>
                <div class="preview-card-guidance">{compact_guidance}</div>
            </div>
            <div>
                <div class="mock-cv-page" style="border-top: 2px solid #ef6c00;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 2px; border-bottom: 1px solid rgba(128,128,128,0.15); padding-bottom: 1px;">
                        <div class="mock-line name" style="width: 40%; background-color: #ef6c00; height: 5px; margin-bottom: 0;"></div>
                        <div class="mock-line contact" style="width: 40%; height: 2px; margin-bottom: 0;"></div>
                    </div>
                    <div class="mock-line section-header" style="background-color: #ef6c00; width: 25%; margin-top: 1px;"></div>
                    <div style="margin-bottom: 1px; padding: 1px; background-color: rgba(128,128,128,0.05); border-radius: 2px;">
                        <div class="mock-line" style="width: 90%; height: 2px; margin-bottom: 1px;"></div>
                    </div>
                    <div class="mock-line section-header" style="background-color: #ef6c00; width: 25%; margin-top: 1px;"></div>
                    <div class="mock-line bullet" style="margin-left: 4px; width: 85%;"></div>
                </div>
                <div class="preview-card-photo-info">🚫 {t_photo_not_supported}</div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        btn_lbl = ("✓ Seçildi" if is_tr else "✓ Selected") if is_selected else ("Seç" if is_tr else "Select")
        if st.button(btn_lbl, key="btn_select_compact_technical", disabled=is_selected, use_container_width=True):
            st.session_state.ats_cv_selected_template_id = "compact_technical"
            st.rerun()

    with col3:
        is_selected = selected_id == "visual_photo_optional"
        sel_class = "selected" if is_selected else ""
        selected_badge = f"<span style='color: #2e7d32; font-weight: bold;'>✓ {'Seçildi' if is_tr else 'Selected'}</span>" if is_selected else ""

        card_html = f"""
        <div class="preview-card-container {sel_class}">
            <div>
                <div class="preview-card-title">Visual Photo Optional {selected_badge}</div>
                <div style="margin-bottom: 3px;">
                    <span class="card-badge badge-ats">{t_ats_safe}</span>
                    <span class="card-badge badge-photo">{t_photo_opt}</span>
                    <span class="card-badge badge-vis">{t_visual}</span>
                </div>
                <div class="preview-card-guidance">{visual_guidance}</div>
            </div>
            <div>
                <div class="mock-cv-page" style="border-top: 2px solid #6a1b9a;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px; position: relative;">
                        <div style="width: 70%;">
                            <div class="mock-line name" style="width: 75%; background-color: #6a1b9a; height: 5px;"></div>
                            <div class="mock-line title" style="width: 50%; height: 3px;"></div>
                        </div>
                        <div class="mock-photo-placeholder" style="top: 0; right: 0; width: 14px; height: 14px; font-size: 6px; border: 1px solid rgba(128,128,128,0.3); background-color: #f0f0f0;">👤</div>
                    </div>
                    <div style="border-bottom: 1px solid rgba(128,128,128,0.15); margin-top: 1px; margin-bottom: 2px;"></div>
                    <div class="mock-line section-header" style="background-color: #6a1b9a; width: 30%;"></div>
                    <div class="mock-line bullet" style="width: 80%;"></div>
                </div>
                <div class="preview-card-photo-info">📷 {t_photo_supported}</div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        btn_lbl = ("✓ Seçildi" if is_tr else "✓ Selected") if is_selected else ("Seç" if is_tr else "Select")
        if st.button(btn_lbl, key="btn_select_visual_photo_optional", disabled=is_selected, use_container_width=True):
            st.session_state.ats_cv_selected_template_id = "visual_photo_optional"
            st.rerun()


def handle_export_dialog_dismiss():
    st.session_state.show_ats_cv_export_dialog = False


@st.dialog("Export / Download CV", on_dismiss=handle_export_dialog_dismiss)
def show_export_download_dialog(ats_cv: dict, export_template_id: str, export_language: str, selected_template: dict) -> None:
    is_tr = st.session_state.ui_lang == "tr"

    # 1. Export Style
    export_style_label_map = {
        "Standard" if not is_tr else "Standart": "standard",
        "Try to fit into one page" if not is_tr else "Tek sayfaya sığdırmayı dene": "balanced_one_page",
    }
    selected_export_style_label = st.selectbox(
        "Dışa Aktarma Stili" if is_tr else "Export Style",
        list(export_style_label_map.keys()),
        index=0,
        key="ats_cv_export_style_modal"
    )
    selected_export_style = export_style_label_map[selected_export_style_label]
    one_page_export = selected_export_style == "balanced_one_page"

    # 2. DOCX Render Mode
    docx_mode_options = [
        "Programmatic DOCX" if not is_tr else "Programatik DOCX",
        "Template DOCX" if not is_tr else "Şablon DOCX"
    ]
    selected_render_mode_label = st.radio(
        "DOCX Oluşturma Modu" if is_tr else "DOCX Render Mode",
        docx_mode_options,
        index=0,
        horizontal=True,
        key="ats_cv_docx_render_mode_modal"
    )
    docx_render_mode = "template" if "Template" in selected_render_mode_label or "Şablon" in selected_render_mode_label else "programmatic"

    # 3. Photo status
    main_include_photo = st.session_state.get("ats_cv_include_optional_photo", False)
    main_photo_file = st.session_state.get("ats_cv_optional_photo")

    photo_supported = selected_template.get("supports_photo", False)
    photo_ready = False

    if photo_supported:
        if main_include_photo:
            if main_photo_file is not None:
                photo_ready = True
                status_text = "Yes" if not is_tr else "Evet"
                st.success(f"📷 **{'Photo included' if not is_tr else 'Fotoğraf eklendi'}:** {status_text}")
            else:
                st.warning("⚠️ " + ("Include photo is checked, but no photo file was uploaded in settings." if not is_tr else "Fotoğraf ekleme seçildi ancak ayarlarda fotoğraf yüklenmedi."))
        else:
            status_text = "No" if not is_tr else "Hayır"
            st.info(f"📷 **{'Photo included' if not is_tr else 'Fotoğraf eklendi'}:** {status_text}")
    else:
        status_text = "No" if not is_tr else "Hayır"
        st.info(f"📷 **{'Photo included' if not is_tr else 'Fotoğraf eklendi'}:** {status_text} ({'Template does not support photos' if not is_tr else 'Şablon fotoğrafı desteklemiyor'})")

    # 4. Advanced export options expander
    selected_template_id_for_docx = export_template_id
    selected_template_info = {}

    section_options = [
        ("contact", "İletişim" if is_tr else "Contact"),
        ("summary", "Özet" if is_tr else "Summary"),
        ("skills", "Yetenekler" if is_tr else "Skills"),
        ("experience", "Deneyim" if is_tr else "Experience"),
        ("projects", "Projeler" if is_tr else "Projects"),
        ("education", "Eğitim" if is_tr else "Education"),
        ("certifications", "Sertifikalar" if is_tr else "Certifications"),
        ("languages", "Diller" if is_tr else "Languages"),
    ]
    enabled_export_sections = [section_key for section_key, _ in section_options]

    with st.expander("Gelişmiş Dışa Aktarma Seçenekleri" if is_tr else "Advanced Export Options", expanded=False):
        if docx_render_mode == "template":
            st.info("Şablon DOCX deneyseldir ve ATS dostu tutulmuştur. Göndermeden önce formatı kontrol edin." if is_tr else "Template DOCX is experimental and ATS-friendly. Review formatting before sending.")
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
                selected_tpl_disp = st.selectbox(
                    "Şablon DOCX Seçin" if is_tr else "Select DOCX Template",
                    list(tpl_options.keys()),
                    key="ats_cv_docx_template_select_modal"
                )
                selected_template_info = tpl_options[selected_tpl_disp]
                selected_template_id_for_docx = selected_template_info["template_id"]
                st.caption(selected_template_info.get("description", ""))
            else:
                st.warning("No DOCX templates available. Using default.")

        st.markdown(f"**{'Dışa Aktarılacak Bölümler' if is_tr else 'Sections to Export'}**")
        enabled_export_sections = []
        section_cols = st.columns(4)
        for index, (section_key, label) in enumerate(section_options):
            with section_cols[index % 4]:
                if st.checkbox(label, value=True, key=f"ats_cv_export_section_{section_key}_modal"):
                    enabled_export_sections.append(section_key)

        if "contact" not in enabled_export_sections:
            st.warning("İletişim bölümü olmadan çıktı almak önerilmez." if is_tr else "Exporting without contact section is not recommended.")
        if any(section not in enabled_export_sections for section in ["experience", "education", "skills"]):
            st.warning("Kritik bölümler (Deneyim, Eğitim, Yetenekler) eksik." if is_tr else "Critical sections (Experience, Education, Skills) are missing.")

    # Photo support for DOCX/PDF
    photo_supported_for_docx = (
        docx_render_mode == "template"
        and bool(selected_template_info.get("supports_photo"))
    ) or (
        docx_render_mode == "programmatic"
        and bool(selected_template.get("supports_photo"))
    )
    photo_supported_for_pdf = bool(selected_template.get("supports_photo"))

    # 5. Fetch files and render Download buttons
    can_export = bool(enabled_export_sections)
    if can_export:
        with st.spinner("Dosyalar hazırlanıyor..." if is_tr else "Preparing downloads..."):
            try:
                docx_bytes = fetch_ats_cv_export(
                    "export-docx", ats_cv, export_template_id, export_language,
                    one_page_export, enabled_export_sections, selected_export_style,
                    docx_render_mode=docx_render_mode,
                    docx_template_id=selected_template_id_for_docx,
                    include_photo=photo_ready and photo_supported_for_docx,
                    photo_file=main_photo_file if photo_ready and photo_supported_for_docx else None,
                )
                pdf_bytes = fetch_ats_cv_export(
                    "export-pdf", ats_cv, export_template_id, export_language,
                    one_page_export, enabled_export_sections, selected_export_style,
                    include_photo=photo_ready and photo_supported_for_pdf,
                    photo_file=main_photo_file if photo_ready and photo_supported_for_pdf else None,
                )
                txt_bytes = fetch_ats_cv_export(
                    "export-txt", ats_cv, export_template_id, export_language,
                    one_page_export, enabled_export_sections, selected_export_style
                )
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
                docx_bytes, pdf_bytes, txt_bytes = None, None, None
    else:
        docx_bytes, pdf_bytes, txt_bytes = None, None, None

    st.markdown("---")
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        if docx_bytes:
            st.download_button(
                label="DOCX indir" if is_tr else "Download DOCX",
                data=docx_bytes,
                file_name=safe_cv_filename("ats_cv", selected_template_id_for_docx, "docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="ats_cv_dl_docx_modal_btn"
            )
    with dl_col2:
        if pdf_bytes:
            st.download_button(
                label="PDF indir" if is_tr else "Download PDF",
                data=pdf_bytes,
                file_name=safe_cv_filename("ats_cv", export_template_id, "pdf"),
                mime="application/pdf",
                use_container_width=True,
                key="ats_cv_dl_pdf_modal_btn"
            )
    with dl_col3:
        if txt_bytes:
            st.download_button(
                label="TXT indir" if is_tr else "Download TXT",
                data=txt_bytes,
                file_name=safe_cv_filename("ats_cv", export_template_id, "txt"),
                mime="text/plain",
                use_container_width=True,
                key="ats_cv_dl_txt_modal_btn"
            )

    # 6. Short Help text
    st.markdown("")
    help_text = (
        "Tam içerik için Standart, kompakt çıktı için Tek sayfaya sığdırmayı dene seçeneğini kullanın."
        if is_tr else
        "Choose Standard for full content, or Try to fit into one page for a compact export."
    )
    st.caption(help_text)


def translate_score_reason(text: str) -> str:
    if st.session_state.ui_lang != "tr":
        return text
    if not isinstance(text, str):
        return text
    if "The original CV received an estimated score of" in text:
        try:
            score = text.split("of ")[1].split(" because")[0]
        except Exception:
            score = "0"
        return f"Orijinal CV için tahmini skor {score}; çünkü bazı hedef anahtar kelimeler ve iş ilanına özel vurgu eksikti."
    if "The optimized CV received an estimated score of" in text:
        try:
            score = text.split("of ")[1].split(" because")[0]
        except Exception:
            score = "0"
        return f"Optimize edilmiş CV için tahmini skor {score}; çünkü desteklenen anahtar kelimeler ve aktarılabilir deneyimler daha görünür hale getirildi."
    return text

# --- Sidebar UI Language selector ---
ui_lang_choice = st.sidebar.selectbox(
    "Arayüz Dili / UI Language",
    ["Türkçe", "English"],
    index=0 if st.session_state.ui_lang == "tr" else 1,
    key="ui_lang_choice"
)
st.session_state.ui_lang = "tr" if ui_lang_choice == "Türkçe" else "en"

def t(key):
    return TRANSLATIONS[st.session_state.ui_lang].get(key, key)

st.title(t("app_title"))

# --- Sidebar Configuration panel ---
st.sidebar.markdown(f"**{t('sidebar_uploads')}**")

global_cv = st.sidebar.file_uploader(
    t("upload_cv"),
    type=["pdf", "docx"],
    key="global_cv"
)

global_job_desc = st.sidebar.text_area(
    t("job_desc"),
    value=st.session_state.global_job_text,
    height=80,
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
st.sidebar.markdown(f"**{t('nav_title')}**")
page_choice = st.sidebar.radio(
    t("nav_title"),
    menu_options,
    label_visibility="collapsed"
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
    st.markdown("##### " + t("input_status"))
    col1, col2 = st.columns(2)
    with col1:
        if global_cv is not None:
            st.caption(t("using_global_cv").format(name=global_cv.name))
            effective_cv_file = {
                "cv_file": (global_cv.name, global_cv.getvalue(), global_cv.type)
            }
            effective_cv_obj = global_cv
        else:
            st.caption("⚠️ " + t("no_global_cv"))

    with col2:
        if st.session_state.get("global_job_desc_input", "").strip():
            st.caption(t("using_global_job"))
            effective_job_text = st.session_state.global_job_desc_input.strip()
        else:
            st.caption("⚠️ " + t("no_global_job_desc"))

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
            st.info(t("using_override_cv").format(name=override_cv.name))

        override_job = st.text_area(
            t("override_job_label"),
            value="",
            height=120,
            key=f"override_job_{page_id}"
        )
        if override_job.strip():
            effective_job_text = override_job.strip()
            st.info(t("using_override_job"))

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
        st.markdown(f"**{t('docx_supports_photo')}:** {'Yes' if template_info.get('supports_photo') else 'No'}")


def render_quality_report(report: dict, title: str, score_key: str) -> None:
    report = report if isinstance(report, dict) else {}
    if not report or score_key not in report:
        st.warning(t("quality_metadata_missing"))
        return
    score = report.get(score_key)
    issues = report.get("issues", []) if isinstance(report.get("issues"), list) else []
    label = title
    if score is not None:
        label = f"{title} - {score}/100"
    with st.expander(label, expanded=False):
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


def render_quality_report_inline(report: dict, title: str, score_key: str) -> None:
    report = report if isinstance(report, dict) else {}
    if not report or score_key not in report:
        st.warning(t("quality_metadata_missing"))
        return
    score = report.get(score_key)
    issues = report.get("issues", []) if isinstance(report.get("issues"), list) else []
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


def template_short_guidance(template: dict) -> str:
    template_id = str((template or {}).get("id") or "")
    language = st.session_state.ui_lang
    guidance = {
        "modern_professional": {
            "en": "Best for general corporate, product, analyst, IT, and new graduate applications.",
            "tr": "Genel kurumsal, ürün, analist, IT ve yeni mezun başvuruları için dengeli şablon.",
        },
        "compact_technical": {
            "en": "Best for backend, software, data/AI, and ATS-heavy technical applications.",
            "tr": "Backend, yazılım, data/AI ve ATS ağırlıklı teknik başvurular için kompakt şablon.",
        },
        "visual_photo_optional": {
            "en": "Best for local/corporate applications where a photo CV is acceptable.",
            "tr": "Fotoğraflı CV’nin uygun olduğu yerel/kurumsal başvurular için görsel şablon.",
        },
    }
    if template_id in guidance:
        return guidance[template_id].get(language, guidance[template_id]["en"])
    best_for = (template or {}).get("best_for", [])
    if isinstance(best_for, list) and best_for:
        prefix = "Best for" if language == "en" else "En uygun"
        return f"{prefix}: {', '.join(str(item) for item in best_for[:5])}."
    return str((template or {}).get("description") or "")[:180]


def contact_summary_line(locked_values: dict) -> str:
    values = [
        locked_values.get("locked_full_name"),
        locked_values.get("locked_email"),
        locked_values.get("locked_phone"),
        locked_values.get("locked_location"),
    ]
    summary = " • ".join(str(value).strip() for value in values if str(value or "").strip())
    return summary or t("contact_summary_empty")


def render_adaptation_quality_report(report: dict) -> None:
    if not isinstance(report, dict) or not report:
        st.caption(t("adaptation_quality_missing"))
        return
    metric_cols = st.columns(4)
    metric_cols[0].metric(t("adaptation_level"), report.get("adaptation_level") or "-")
    metric_cols[1].metric(t("adaptation_domain"), report.get("detected_domain") or "-")
    metric_cols[2].metric(t("summary_alignment"), report.get("summary_alignment", "-"))
    metric_cols[3].metric(t("skills_alignment"), report.get("skills_alignment", "-"))
    st.write(f"**{t('experience_alignment')}:** {report.get('experience_alignment', '-')}")
    st.write(f"**{t('project_alignment')}:** {report.get('project_alignment', '-')}")
    warnings = report.get("warnings", []) if isinstance(report.get("warnings"), list) else []
    if warnings:
        write_non_empty_list(warnings)
    else:
        st.success(t("looks_clean"))


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
    st.subheader(t("contact"))
    contact_lines = []
    contact_keys_mapping = {
        "full_name": "locked_full_name",
        "email": "locked_email",
        "phone": "locked_phone",
        "location": "locked_location",
        "linkedin": "locked_linkedin",
        "github": "locked_github",
        "portfolio": "locked_portfolio",
        "target_title": "target_title_lbl",
    }
    for key in ["full_name", "target_title", "email", "phone", "location", "linkedin", "github", "portfolio"]:
        value = contact.get(key)
        if value:
            lbl = t(contact_keys_mapping.get(key, key))
            contact_lines.append(f"**{lbl}:** {value}")
    st.markdown("  \n".join(contact_lines) if contact_lines else "-")

    summary_sections = [
        ("professional_summary", "professional_summary"),
        ("career_objective", "career_objective"),
        ("technical_summary", "technical_summary"),
    ]
    for key_lbl, key in summary_sections:
        value = ats_cv.get(key)
        if value:
            st.subheader(t(key_lbl))
            st.write(value)

    st.subheader(t("skills_section"))
    skills = ats_cv.get("skills", {})
    skills_group_mapping = {
        "technical_skills": "Teknik Yetenekler" if st.session_state.ui_lang == "tr" else "Technical Skills",
        "core_skills": "Temel Yetenekler" if st.session_state.ui_lang == "tr" else "Core Skills",
        "soft_skills": "Sosyal Beceriler" if st.session_state.ui_lang == "tr" else "Soft Skills",
        "tools": "Araçlar" if st.session_state.ui_lang == "tr" else "Tools",
        "databases": "Veritabanları" if st.session_state.ui_lang == "tr" else "Databases",
        "cloud": "Bulut Teknolojileri" if st.session_state.ui_lang == "tr" else "Cloud",
    }
    if isinstance(skills, dict):
        for skill_group, items in skills.items():
            if items:
                lbl = skills_group_mapping.get(skill_group, skill_group.replace('_', ' ').title())
                st.markdown(f"**{lbl}**")
                st.write(", ".join(items))
    else:
        st.write("-")

    st.subheader(t("experience_section"))
    for item in ats_cv.get("experience", []):
        role = item.get("role", "")
        company = item.get("company", "")
        dates = " - ".join(filter(None, [item.get("start_date", ""), item.get("end_date", "")]))
        heading = " | ".join(filter(None, [role, company, item.get("location", ""), dates]))
        if heading:
            st.markdown(f"**{heading}**")
        write_non_empty_list(item.get("bullets", []))

    st.subheader(t("projects_section"))
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

    st.subheader(t("education_section"))
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

    st.subheader(t("certifications_section"))
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

    st.subheader(t("languages_section"))
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
    include_photo: bool = False,
    photo_file=None,
) -> bytes | None:
    try:
        data = {
            "ats_cv_json": json.dumps(ats_cv, ensure_ascii=False),
            "template_id": template_id,
            "language": language,
            "one_page": str(one_page).lower(),
            "enabled_sections": json.dumps(enabled_sections) if enabled_sections is not None else "",
            "export_style": export_style,
            "docx_render_mode": docx_render_mode,
            "docx_template_id": docx_template_id,
            "include_photo": str(bool(include_photo)).lower(),
        }
        files = None
        if include_photo and photo_file is not None:
            files = {
                "cv_photo": (
                    photo_file.name,
                    photo_file.getvalue(),
                    photo_file.type or "application/octet-stream",
                )
            }
        response = requests.post(
            f"{API_BASE_URL}/ats-cv/{endpoint}",
            data=data,
            files=files,
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
    /* Sidebar compactness styles */
    section[data-testid="stSidebar"] {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    section[data-testid="stSidebar"] div.stVerticalBlock {
        gap: 0.4rem !important;
    }
    section[data-testid="stSidebar"] .stElementContainer {
        margin-bottom: 0px !important;
        padding-bottom: 2px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        padding: 0.5rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] > div {
        padding: 0px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] div {
        margin-top: 0px !important;
        margin-bottom: 0px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 2px !important;
    }
    .ats-builder-compact-title {
        margin: 0 0 0.25rem 0;
    }
    .ats-builder-compact-note {
        font-size: 0.92rem;
        color: rgba(250, 250, 250, 0.72);
        margin: -0.2rem 0 0.35rem 0;
    }
    .ats-builder-compact-section {
        margin: 0.35rem 0 0.15rem 0;
        font-size: 1rem;
        font-weight: 650;
    }
    .ats-builder-contact-summary {
        font-size: 0.86rem;
        color: rgba(250, 250, 250, 0.68);
        margin: 0.2rem 0 0.1rem 0;
    }
    div[data-testid="stSelectbox"]:not(:has([aria-invalid="true"])) div[data-baseweb="select"] > div,
    div[data-testid="stSelectbox"]:not(:has([aria-invalid="true"])) div[data-baseweb="select"] input,
    div[data-testid="stSelectbox"]:not(:has([aria-invalid="true"])) [aria-invalid="false"] {
        border-color: rgba(128, 132, 149, 0.45) !important;
        box-shadow: none !important;
    }
    div[data-testid="stSelectbox"]:not(:has([aria-invalid="true"])) div[data-baseweb="select"] > div:hover {
        border-color: rgba(160, 166, 184, 0.75) !important;
    }
    div[data-testid="stDownloadButton"] button {
        white-space: nowrap !important;
        min-width: 8.6rem;
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
        f"- {t('db_demo_step_7')}",
    ]))

    st.markdown(f"### {t('db_features')}")
    col_feat1, col_feat2 = st.columns(2)
    with col_feat1:
        st.info(f"**🔍 {t('nav_cv_tools')}**\n\n{t('db_feat_cv_tools')}")
        st.success(f"**💼 {t('nav_job_workspace')}**\n\n{t('db_feat_job_workspace')}")
    with col_feat2:
        st.warning(f"**✉️ {t('nav_application_materials')}**\n\n{t('db_feat_app_materials')}")
        st.info(f"**📄 {t('nav_ats_cv_builder')}**\n\n{t('db_feat_ats_cv_builder')}")

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
    st.markdown(f"### {t('ats_cv_builder')}")
    st.caption(t("ats_cv_builder_next_phase"))
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
        st.markdown(f'<div class="ats-builder-compact-section">{t("main_settings")}</div>', unsafe_allow_html=True)

        # Initialize selected template ID if not present
        if "ats_cv_selected_template_id" not in st.session_state:
            st.session_state.ats_cv_selected_template_id = "modern_professional"

        selected_id = st.session_state.ats_cv_selected_template_id
        is_tr = st.session_state.ui_lang == "tr"

        # 2. Card Selection
        st.markdown(f"**{t('choose_cv_template')}**")
        render_template_preview_cards(selected_id)

        # In case selection changed inside render_template_preview_cards
        selected_id = st.session_state.ats_cv_selected_template_id

        # Resolve selected template
        selected_template = next((t for t in templates if t["id"] == selected_id), None)
        if not selected_template:
            selected_template = next((t for t in templates if t["id"] == "modern_professional"), templates[0])
            selected_id = selected_template.get("id")
            st.session_state.ats_cv_selected_template_id = selected_id

        # Subtle recommendation / help row + Details Expander
        rec_text = ""
        if selected_id == "modern_professional":
            rec_text = "Önerilen varsayılan: Modern Professional" if is_tr else "Recommended default: Modern Professional"
        elif selected_id == "visual_photo_optional":
            rec_text = "Fotoğraflı CV kabul edilen başvurularda kullanın." if is_tr else "Use this when a photo CV is acceptable."
        elif selected_id == "compact_technical":
            rec_text = "Kompakt teknik veya ATS ağırlıklı başvurularda kullanın." if is_tr else "Use this for compact technical or ATS-heavy applications."

        guidance_text = f"**{t('template_guidance')}**: {template_short_guidance(selected_template)}"
        if rec_text:
            guidance_text += f" | 💡 {rec_text}"
        st.caption(guidance_text)

        expander_title = "Şablon Detayları" if is_tr else "Template details"
        with st.expander(expander_title, expanded=False):
            lang = st.session_state.ui_lang
            metadata = TEMPLATE_METADATA_EXT.get(lang, {}).get(selected_id, {})
            t_desc = metadata.get("description", selected_template.get("description", ""))
            t_best_for = metadata.get("best_for", selected_template.get("best_for", []))
            t_ats_notes = metadata.get("ats_notes", selected_template.get("ats_notes", []))
            t_rec_for = metadata.get("recommended_for", "")
            t_not_rec_for = metadata.get("not_recommended_for", "")
            t_cautions = metadata.get("cautions", "")

            st.markdown(f"**{t('template_description')}**")
            st.write(t_desc)

            style_lbl = "Stil" if lang == "tr" else "Style"
            safety_lbl = "ATS Güvenliği" if lang == "tr" else "ATS Safety"
            density_lbl = "Yoğunluk" if lang == "tr" else "Density"
            photo_lbl = "Fotoğraf Desteği" if lang == "tr" else "Photo Support"
            photo_support_val = ("Destekleniyor" if lang == "tr" else "Supported") if selected_template.get("supports_photo") else ("Yok" if lang == "tr" else "No Photo")

            st.caption(
                " | ".join(filter(None, [
                    f"{style_lbl}: {selected_template.get('style_level')}",
                    f"{safety_lbl}: {selected_template.get('ats_safety_level')}",
                    f"{density_lbl}: {selected_template.get('visual_density')}",
                    f"{photo_lbl}: {photo_support_val}",
                ]))
            )

            if t_best_for:
                st.markdown(f"**{t('best_for')}**")
                for item in t_best_for:
                    st.markdown(f"- {item}")

            rec_label = "Önerilen Adaylar / Roller" if lang == "tr" else "Recommended For"
            not_rec_label = "Önerilmeyen Durumlar / Roller" if lang == "tr" else "Not Recommended For"
            cautions_label = "Dikkat Edilmesi Gerekenler" if lang == "tr" else "Cautions"

            if t_rec_for:
                st.markdown(f"**{rec_label}**")
                st.write(t_rec_for)

            if t_not_rec_for:
                st.markdown(f"**{not_rec_label}**")
                st.write(t_not_rec_for)

            if t_cautions:
                st.markdown(f"**{cautions_label}**")
                st.info(t_cautions)

            st.markdown(f"**{t('section_order')}**")
            for index, section in enumerate(selected_template.get("section_order", []), start=1):
                st.markdown(f"{index}. `{section}`")

            if t_ats_notes:
                st.markdown(f"**{t('ats_notes')}**")
                for note in t_ats_notes:
                    st.markdown(f"- {note}")

        # 2.5 Legacy Templates selection (below template details)
        legacy_templates = [t for t in templates if t["id"] not in ["modern_professional", "compact_technical", "visual_photo_optional"]]
        is_legacy_selected = selected_id in [t["id"] for t in legacy_templates]

        legacy_expander_title = "Eski şablonlar" if is_tr else "Legacy templates"
        with st.expander(legacy_expander_title, expanded=is_legacy_selected):
            st.caption(
                "Aşağıdaki eski veya özel kullanım senaryoları için olan şablonları seçebilirsiniz."
                if is_tr else
                "You can select the legacy or specific use-case templates below."
            )
            legacy_names = [t["name"] for t in legacy_templates]
            current_legacy_index = None
            if is_legacy_selected:
                current_legacy_index = next((i for i, t in enumerate(legacy_templates) if t["id"] == selected_id), None)

            def format_legacy_name(name):
                tpl = next((t for t in legacy_templates if t["name"] == name), None)
                if tpl:
                    return f"{tpl['name']} ({tpl['ats_safety_level'].upper()} ATS)"
                return name

            legacy_select_options = ["---"] + legacy_names
            default_index = 0
            if current_legacy_index is not None:
                default_index = current_legacy_index + 1

            legacy_selection = st.selectbox(
                "Şablon Seçin" if is_tr else "Select Template",
                legacy_select_options,
                index=default_index,
                format_func=lambda x: ("Şablon seçilmedi" if is_tr else "No legacy template selected") if x == "---" else format_legacy_name(x),
                key="legacy_template_selectbox"
            )

            if legacy_selection != "---":
                selected_legacy_tpl = next((t for t in legacy_templates if t["name"] == legacy_selection), None)
                if selected_legacy_tpl and selected_legacy_tpl["id"] != selected_id:
                    st.session_state.ats_cv_selected_template_id = selected_legacy_tpl["id"]
                    st.rerun()
            elif is_legacy_selected:
                st.session_state.ats_cv_selected_template_id = "modern_professional"
                st.rerun()

        # 5. Output Language, Adaptation Level in columns
        settings_col1, settings_col2 = st.columns(2, gap="medium")
        with settings_col1:
            ats_cv_language_options = ["Turkish", "English"]
            ats_cv_language = st.selectbox(
                t("cv_output_lang"),
                ats_cv_language_options,
                index=ats_cv_language_options.index(global_language) if global_language in ats_cv_language_options else 0,
                key="ats_cv_output_language"
            )

        with settings_col2:
            adaptation_options = adaptation_level_options()
            selected_adaptation_label = st.selectbox(
                t("adaptation_level"),
                [label for label, _ in adaptation_options],
                index=1,
                key="ats_cv_adaptation_level_label",
                help=t("adaptation_strong_help"),
            )
            selected_adaptation_level = dict(adaptation_options).get(selected_adaptation_label, "balanced")
            st.caption(t("adaptation_strong_help"))

        # 6. Photo controls on a separate line below Language/Adaptation
        ats_cv_photo = None
        include_cv_photo = False
        if selected_template.get("supports_photo"):
            include_cv_photo = st.checkbox(
                t("include_photo_cv"),
                value=False,
                key="ats_cv_include_optional_photo",
            )
            st.caption(t("photo_best_result_note"))
            if include_cv_photo:
                ats_cv_photo = st.file_uploader(
                    t("cv_photo_optional"),
                    type=["png", "jpg", "jpeg"],
                    key="ats_cv_optional_photo",
                )
        else:
            st.caption(t("photo_template_warning"))

        sync_ats_locked_fields_from_uploaded_cv(global_cv)

        if global_cv is not None and st.session_state.get("cv_extraction_failed"):
            st.warning("⚠️ " + t("contact_fields_missing"))

        locked_contact_values = {}
        locked_contact_rows = [
            ("locked_full_name", "locked_email"),
            ("locked_phone", "locked_location"),
            ("locked_linkedin", "locked_github"),
            ("locked_portfolio", None),
        ]

        st.session_state.setdefault(
            "ats_cv_locked_proper_nouns_json",
            json.dumps(st.session_state.get("ats_cv_locked_proper_nouns", ATS_LOCKED_PROPER_NOUNS), ensure_ascii=False, indent=2),
        )
        for left_key, right_key in locked_contact_rows:
            st.session_state.setdefault(f"ats_cv_{left_key}", ATS_LOCKED_CONTACT_DEFAULTS[left_key])
            locked_contact_values[left_key] = st.session_state.get(f"ats_cv_{left_key}", "")
            if right_key:
                st.session_state.setdefault(f"ats_cv_{right_key}", ATS_LOCKED_CONTACT_DEFAULTS[right_key])
                locked_contact_values[right_key] = st.session_state.get(f"ats_cv_{right_key}", "")

        st.markdown(
            f'<div class="ats-builder-contact-summary">{t("locked_contact_fields")}: {contact_summary_line(locked_contact_values)}</div>',
            unsafe_allow_html=True,
        )
        with st.expander(t("locked_fields_protection"), expanded=False):
            st.markdown(f"**{t('locked_contact_fields')}**")
            for left_key, right_key in locked_contact_rows:
                left_col, right_col = st.columns(2)
                with left_col:
                    locked_contact_values[left_key] = st.text_input(
                        t(left_key),
                        key=f"ats_cv_{left_key}",
                    )
                if right_key:
                    with right_col:
                        locked_contact_values[right_key] = st.text_input(
                            t(right_key),
                            key=f"ats_cv_{right_key}",
                        )

            if not all(locked_contact_values.get(key, "").strip() for key in ["locked_full_name", "locked_email", "locked_phone"]):
                st.warning(t("locked_contact_warning"))

            st.markdown(f"**{t('locked_proper_nouns')}**")
            locked_proper_nouns_json = st.text_area(
                t("locked_proper_nouns"),
                key="ats_cv_locked_proper_nouns_json",
                height=160,
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

        # Update cached_proper_nouns so manual edits are not lost when switching pages!
        try:
            parsed_proper_nouns = json.loads(locked_proper_nouns_json)
            if isinstance(parsed_proper_nouns, list):
                st.session_state["cached_proper_nouns"] = parsed_proper_nouns
                st.session_state["cached_proper_nouns_json"] = locked_proper_nouns_json
        except Exception:
            pass

        stored_result = st.session_state.get("ats_cv_builder_result")
        gen_clicked = False
        if stored_result:
            col_gen, col_exp = st.columns([1, 1])
            with col_gen:
                gen_clicked = st.button(t("generate_ats_cv"), use_container_width=True)
            with col_exp:
                if st.button(
                    "Dışa Aktar / İndir" if st.session_state.ui_lang == "tr" else "Export / Download",
                    key="ats_cv_open_export_modal_btn",
                    use_container_width=True
                ):
                    st.session_state.show_ats_cv_export_dialog = True
                    st.rerun()
        else:
            gen_clicked = st.button(t("generate_ats_cv"))

        if gen_clicked:
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
                            st.rerun()
                        else:
                            st.error(f"Error {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(f"{t('status_error')} {str(e)}")

        stored_result = st.session_state.get("ats_cv_builder_result")
        if stored_result:
            # Inject CSS to reduce vertical spacing in result section
            st.markdown("""
            <style>
            .stMetric {
                padding: 4px 8px !important;
            }
            .ats-builder-compact-section {
                margin-top: 8px !important;
                margin-bottom: 4px !important;
            }
            .element-container {
                margin-bottom: 4px !important;
            }
            </style>
            """, unsafe_allow_html=True)
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

            # 1. Score summary metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric(t("ats_score_before"), before_score)
            with col2:
                st.metric(t("ats_score_after"), after_score)
            with col3:
                st.metric(t("score_improvement"), improvement_score)
            with col4:
                q_score = quality_report.get("quality_score") if isinstance(quality_report, dict) else None
                st.metric(t("cv_quality_score"), q_score if q_score is not None else "-")
            with col5:
                s_score = structure_report.get("structure_score") if isinstance(structure_report, dict) else None
                st.metric(t("structure_score"), s_score if s_score is not None else "-")

            contact = ats_cv.get("contact", {})
            col_role, col_title, col_confidence = st.columns(3)
            with col_role:
                st.write(f"**{t('target_role')}**")
                st.write(metadata.get("target_role") or "-")
            with col_title:
                st.write(f"**{t('target_title_lbl')}**")
                st.write(contact.get("target_title") or "-")
            with col_confidence:
                st.write(f"**{t('alignment_confidence')}**")
                st.write(metadata.get("alignment_confidence") or "-")



            if st.session_state.get("show_ats_cv_export_dialog"):
                show_export_download_dialog(ats_cv, export_template_id, export_language, selected_template)

            # 4. Collapsible Preview Section
            preview_title = "Oluşturulan CV Önizlemesi" if st.session_state.ui_lang == "tr" else "Generated CV Preview"
            with st.expander(preview_title, expanded=False):
                render_ats_cv_preview(ats_cv)

            # 5. Grouped reports
            with st.expander(t("quality_and_structure"), expanded=False):
                q_col, s_col = st.columns(2)
                with q_col:
                    render_quality_report_inline(quality_report, t("cv_quality_check"), "quality_score")
                with s_col:
                    render_quality_report_inline(structure_report, t("structure_validation"), "structure_score")

            with st.expander(t("keyword_analysis"), expanded=False):
                st.markdown(f"**{t('used_keywords')}**")
                st.write(", ".join(metadata.get("job_keywords_used", [])) or "-")
                st.markdown(f"**{t('transferable_keywords')}**")
                write_non_empty_list(metadata.get("transferable_keywords_used", []))
                st.markdown(f"**{t('missing_keywords')}**")
                write_non_empty_list(metadata.get("missing_keywords", []))
                st.markdown(f"**{t('risky_keywords_not_added')}**")
                write_non_empty_list(metadata.get("risky_keywords_not_added", []))

            score_explanation = metadata.get("ats_score_explanation", {}) if isinstance(metadata.get("ats_score_explanation"), dict) else {}
            with st.expander(t("ats_explanation_notes"), expanded=False):
                st.caption(t("ats_score_disclaimer"))
                st.markdown(f"**{t('optimization_summary')}**")
                st.write(metadata.get("optimization_summary", ""))
                st.write(f"**{t('before_reason')}:** {translate_score_reason(score_explanation.get('before_reason') or '-')}")
                st.write(f"**{t('after_reason')}:** {translate_score_reason(score_explanation.get('after_reason') or '-')}")
                st.markdown(f"**{t('improvement_reasons')}**")
                write_non_empty_list(score_explanation.get("improvement_reasons", []))
                st.markdown(f"**{t('remaining_gaps')}**")
                write_non_empty_list(score_explanation.get("remaining_gaps", []))
                st.markdown(f"**{t('adaptation_notes')}**")
                write_non_empty_list(metadata.get("adaptation_notes", []))

            with st.expander(t("adaptation_quality"), expanded=False):
                render_adaptation_quality_report(metadata.get("adaptation_quality_report", {}))

            with st.expander(t("advanced_technical_details"), expanded=False):
                current_export_style = st.session_state.get("ats_cv_export_style_modal")
                if current_export_style:
                    is_tr = st.session_state.ui_lang == "tr"
                    export_style_label_map = {
                        "Standard" if not is_tr else "Standart": "standard",
                        "Try to fit into one page" if not is_tr else "Tek sayfaya sığdırmayı dene": "balanced_one_page",
                    }
                    disp_export_style = export_style_label_map.get(current_export_style, "standard")
                else:
                    disp_export_style = "standard"

                current_docx_mode = st.session_state.get("ats_cv_docx_render_mode_modal")
                if current_docx_mode:
                    disp_docx_mode = "template" if "Template" in current_docx_mode or "Şablon" in current_docx_mode else "programmatic"
                else:
                    disp_docx_mode = "programmatic"

                disp_one_page = (disp_export_style == "balanced_one_page")

                section_keys = ["contact", "summary", "skills", "experience", "projects", "education", "certifications", "languages"]
                disp_enabled_sections = []
                for sk in section_keys:
                    chk_val = st.session_state.get(f"ats_cv_export_section_{sk}_modal")
                    if chk_val is None or chk_val:
                        disp_enabled_sections.append(sk)

                st.json({
                    "template_id": export_template_id,
                    "language": export_language,
                    "export_style": disp_export_style,
                    "docx_render_mode": disp_docx_mode,
                    "one_page": disp_one_page,
                    "enabled_sections": disp_enabled_sections,
                    "validation": validation,
                })



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
    st.write(t("job_workspace_desc") if "job_workspace_desc" in TRANSLATIONS[st.session_state.ui_lang] else "Use this workspace to add a job posting, analyze fit, and generate tailored application materials.")

    alerts = api_json("GET", "/job-monitoring/alerts") or []
    sources_payload = api_json("GET", "/job-monitoring/sources", timeout=30) or {}
    source_settings = sources_payload.get("sources", [])
    source_names = [source.get("source_name") for source in source_settings if source.get("source_name")]
    enabled_runnable_sources = [
        source.get("source_name") for source in source_settings
        if source.get("enabled") and source.get("runnable") and source.get("status") == "active"
    ]

    tab_add, tab_jobs, tab_assets, tab_profiles, tab_sources, tab_pipeline = st.tabs([
        t("tab_add_job") if "tab_add_job" in TRANSLATIONS[st.session_state.ui_lang] else "Add Job",
        t("tab_jobs") if "tab_jobs" in TRANSLATIONS[st.session_state.ui_lang] else "Jobs",
        t("tab_assets") if "tab_assets" in TRANSLATIONS[st.session_state.ui_lang] else "Assets",
        t("tab_search_profiles") if "tab_search_profiles" in TRANSLATIONS[st.session_state.ui_lang] else "Mock Search (Advanced)",
        t("tab_sources") if "tab_sources" in TRANSLATIONS[st.session_state.ui_lang] else "Sources (Advanced)",
        t("tab_pipeline") if "tab_pipeline" in TRANSLATIONS[st.session_state.ui_lang] else "Pipeline (Optional)"
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

                    # Optional application notes section
                    st.markdown(f"#### 📅 {t('jm_pipeline_title')}")
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
                        help=t("adaptation_strong_help"),
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
                                        if p_dict.get("export_format", "").lower() == "docx":
                                            st.warning(t("docx_preview_limited"))
                                        content = p_dict.get("content_text")
                                        if not content and p_dict.get("file_path"):
                                            content = "Text content not found, please download the file." if st.session_state.ui_lang == "en" else "Metin içeriği bulunamadı, fiziksel dosyayı indirin."
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

    # --- Tab 4: Advanced Mock Search ---
    with tab_profiles:
        st.subheader("Advanced Mock Search / Gelişmiş Mock Arama")
        st.info(t("jm_sources_phase3a_note"))
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
        st.subheader("Existing Mock Search Profiles / Mevcut Mock Arama Profilleri")
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

    # --- Tab 5: Advanced Sources ---
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

    # --- Tab 6: Optional Pipeline Notes ---
    with tab_pipeline:
        st.subheader(t("jm_pipeline_title"))
        st.caption(t("jm_sources_phase3a_note"))
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
                            if p_dict.get("export_format", "").lower() == "docx":
                                st.warning(t("docx_preview_limited"))
                            content = p_dict.get("content_text")
                            if not content and p_dict.get("file_path"):
                                content = "Text content not found, please download the file." if st.session_state.ui_lang == "en" else "Metin içeriği bulunamadı, fiziksel dosyayı indirin."
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
