def analyze_cv_for_job(cv_text: str, job_text: str) -> str:
    return f"""
CV ve iş ilanı başarıyla alındı.

CV metin uzunluğu: {len(cv_text)} karakter
İş ilanı uzunluğu: {len(job_text)} karakter

Bu aşamada gerçek LLM entegrasyonu henüz eklenmedi.
Bir sonraki adımda burada yapay zeka analizi üretilecek.

Planlanan analiz başlıkları:
- Genel uyum skoru
- Güçlü yönler
- Eksik yetkinlikler
- CV iyileştirme önerileri
- İş ilanına özel başvuru stratejisi
"""


def generate_cover_letter(cv_text: str, job_text: str, tone: str) -> str:
    return f"""
Kapak yazısı oluşturma isteği başarıyla alındı.

CV metin uzunluğu: {len(cv_text)} karakter
İş ilanı uzunluğu: {len(job_text)} karakter
Ton: {tone}

Bu aşamada gerçek LLM entegrasyonu henüz eklenmedi.
"""


def generate_interview_questions(job_text: str) -> str:
    return f"""
Mülakat hazırlık isteği başarıyla alındı.

İş ilanı uzunluğu: {len(job_text)} karakter

Bu aşamada gerçek LLM entegrasyonu henüz eklenmedi.

Planlanan çıktı:
- Teknik sorular
- HR soruları
- Zorlayıcı sorular
- Cevaplama ipuçları
"""