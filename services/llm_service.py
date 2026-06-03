import json
import os

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import errors

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash-lite"

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_cv_for_job(cv_text: str, job_text: str) -> dict:
    prompt = build_analysis_prompt(
        cv_text=cv_text,
        job_text=job_text
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        raw_result = response.text

        cleaned_result = clean_json_response(raw_result)
        parsed_result = json.loads(cleaned_result)

        return parsed_result

    except errors.ServerError:
        raise HTTPException(
            status_code=503,
            detail="Gemini modeli şu anda yoğun veya geçici olarak kullanılamıyor. Lütfen biraz sonra tekrar deneyin."
        )

    except errors.ClientError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Gemini isteği geçersiz. Model adı, API key veya istek formatı hatalı olabilir. Detay: {str(error)}"
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Gemini cevap verdi fakat geçerli JSON formatında cevap üretmedi."
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Yapay zeka analizi sırasında beklenmeyen bir hata oluştu: {str(error)}"
        )


def generate_cover_letter(
    cv_text: str,
    job_text: str,
    tone: str,
    language: str
) -> str:
    prompt = build_cover_letter_prompt(
        cv_text=cv_text,
        job_text=job_text,
        tone=tone,
        language=language
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        return response.text.strip()

    except errors.ServerError:
        raise HTTPException(
            status_code=503,
            detail="Gemini modeli şu anda yoğun veya geçici olarak kullanılamıyor. Lütfen biraz sonra tekrar deneyin."
        )

    except errors.ClientError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Gemini isteği geçersiz. Model adı, API key veya istek formatı hatalı olabilir. Detay: {str(error)}"
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Kapak yazısı oluşturulurken beklenmeyen bir hata oluştu: {str(error)}"
        )


def generate_interview_questions(job_text: str) -> str:
    return f"""
Mülakat hazırlık isteği başarıyla alındı.

İş ilanı uzunluğu: {len(job_text)} karakter

Bu endpoint Gemini entegrasyonuna daha sonra bağlanacak.
"""


def build_analysis_prompt(cv_text: str, job_text: str) -> str:
    return f"""
Aşağıdaki CV metnini ve iş ilanını analiz et.

CV METNİ:
{cv_text}

İŞ İLANI:
{job_text}

Lütfen sonucu Türkçe üret.

Analiz başlıkları:
1. Genel uyum skoru 0-100 arasında olsun.
2. Güçlü yönleri listele.
3. Eksik veya zayıf kalan yetkinlikleri listele.
4. CV'de öne çıkarılması gereken alanları belirt.
5. Bu ilana başvururken nasıl bir strateji izlenmeli açıkla.
6. Kısa ve net öneriler ver.

Sadece geçerli JSON döndür.
JSON dışında açıklama, markdown, kod bloğu veya ek metin yazma.

JSON formatı şu şekilde olsun:

{{
  "match_score": 85,
  "summary": "Kısa genel değerlendirme",
  "strengths": ["Güçlü yön 1", "Güçlü yön 2"],
  "weaknesses": ["Eksik yön 1", "Eksik yön 2"],
  "cv_improvements": ["CV önerisi 1", "CV önerisi 2"],
  "application_strategy": "Başvuru stratejisi",
  "final_recommendation": "Genel sonuç"
}}
"""


def build_cover_letter_prompt(
    cv_text: str,
    job_text: str,
    tone: str,
    language: str
) -> str:
    return f"""
Aşağıdaki CV metnine ve iş ilanına göre bir kapak yazısı oluştur.

CV METNİ:
{cv_text}

İŞ İLANI:
{job_text}

YAZI TONU:
{tone}

YAZI DİLİ:
{language}

Kapak yazısı kuralları:
1. Kapak yazısını mutlaka belirtilen dilde yaz: {language}.
2. Profesyonel ve doğal bir dil kullan.
3. Çok uzun olmasın, 3-5 paragraf arası olsun.
4. CV'deki güçlü yönleri iş ilanındaki beklentilerle ilişkilendir.
5. Adayın bu pozisyona neden uygun olduğunu açıkla.
6. Abartılı, gerçek dışı veya CV'de olmayan deneyimler ekleme.
7. Eğer dil Turkish ise "Sayın Yetkili" ile başla.
8. Eğer dil English ise "Dear Hiring Manager," ile başla.
9. Son paragrafta görüşme isteğini kibarca belirt.
10. Sadece kapak yazısını döndür, ekstra açıklama yazma.
"""


def clean_json_response(text: str) -> str:
    cleaned_text = text.strip()

    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text.replace("```json", "", 1)

    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text.replace("```", "", 1)

    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]

    return cleaned_text.strip()