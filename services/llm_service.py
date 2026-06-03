import json
import os

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import errors

load_dotenv()

GEMINI_MODEL = "gemini-3.1-flash-lite"

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


def generate_interview_questions(job_text: str, language: str) -> dict:
    prompt = build_interview_prompt(
        job_text=job_text,
        language=language
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
            detail=f"Mülakat hazırlığı oluşturulurken beklenmeyen bir hata oluştu: {str(error)}"
        )


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


def build_interview_prompt(job_text: str, language: str) -> str:
    return f"""
Aşağıdaki iş ilanına göre mülakat hazırlık soruları üret.

İŞ İLANI:
{job_text}

CEVAP DİLİ:
{language}

Kurallar:
1. Soruları ve ipuçlarını belirtilen dilde üret: {language}.
2. Junior / intern seviyesine uygun sorular hazırla.
3. Teknik sorular, insan kaynakları soruları ve zorlayıcı sorular ayrı listelensin.
4. Her soru için kısa cevap ipucu ekle.
5. Çok uzun açıklama yapma.
6. Sadece geçerli JSON döndür.
7. JSON dışında açıklama, markdown veya kod bloğu yazma.

JSON formatı şu şekilde olsun:

{{
  "technical_questions": [
    {{
      "question": "Teknik soru 1",
      "answer_hint": "Kısa cevap ipucu"
    }},
    {{
      "question": "Teknik soru 2",
      "answer_hint": "Kısa cevap ipucu"
    }}
  ],
  "hr_questions": [
    {{
      "question": "HR soru 1",
      "answer_hint": "Kısa cevap ipucu"
    }},
    {{
      "question": "HR soru 2",
      "answer_hint": "Kısa cevap ipucu"
    }}
  ],
  "challenging_questions": [
    {{
      "question": "Zorlayıcı soru 1",
      "answer_hint": "Kısa cevap ipucu"
    }},
    {{
      "question": "Zorlayıcı soru 2",
      "answer_hint": "Kısa cevap ipucu"
    }}
  ],
  "preparation_tips": [
    "Hazırlık önerisi 1",
    "Hazırlık önerisi 2"
  ]
}}
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


def generate_ats_score(cv_text: str, job_text: str, language: str) -> dict:
    prompt = build_ats_prompt(cv_text, job_text, language)
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
            detail=f"ATS analizi sırasında beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_ats_prompt(cv_text: str, job_text: str, language: str) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    return f"""
Analyze the following CV and Job Description to calculate the ATS (Applicant Tracking System) compatibility score.

CV CONTENT:
{cv_text}

JOB DESCRIPTION:
{job_text}

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "ats_score": 78,
  "matched_keywords": ["Python", "FastAPI", "SQL", "Git"],
  "missing_keywords": ["Docker", "PostgreSQL", "CI/CD"],
  "keyword_recommendations": [
    "Add FastAPI project details more clearly.",
    "Mention SQL experience in project descriptions."
  ],
  "format_warnings": [
    "Use standard section headings.",
    "Avoid excessive tables or images."
  ],
  "summary": "The CV is generally ATS-friendly but some important keywords are missing."
}}
"""


def extract_job_keywords(job_text: str, language: str) -> dict:
    prompt = build_job_keywords_prompt(job_text, language)
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
            detail=f"Anahtar kelime analizi sırasında beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_job_keywords_prompt(job_text: str, language: str) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    return f"""
Analyze the following Job Description to extract roles, skills, keywords and summaries.

JOB DESCRIPTION:
{job_text}

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "role_title": "Junior Python Developer Intern",
  "experience_level": "Intern / Junior",
  "technical_keywords": ["Python", "FastAPI", "SQL", "REST API", "Git"],
  "soft_skills": ["communication", "teamwork", "problem solving"],
  "must_have_skills": ["Python", "Git", "SQL"],
  "nice_to_have_skills": ["Docker", "SQLAlchemy", "AI APIs"],
  "responsibilities": [
    "Support backend development",
    "Test API endpoints"
  ],
  "role_summary": "This role focuses on Python backend development and AI-powered applications."
}}
"""


def generate_cv_improvement(cv_text: str, job_text: str, language: str) -> dict:
    prompt = build_cv_improvement_prompt(cv_text, job_text, language)
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
            detail=f"CV iyileştirme analizi sırasında beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_cv_improvement_prompt(cv_text: str, job_text: str, language: str) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    return f"""
Analyze the following CV against the Job Description to suggest improvements.
CRITICAL: Do not invent fake experience or skills. Only suggest improvements based on existing CV content or mention missing information clearly as suggestions, not as existing experience.

CV CONTENT:
{cv_text}

JOB DESCRIPTION:
{job_text}

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "overall_feedback": "The CV is suitable for junior backend roles but project descriptions should be more specific.",
  "skills_section_suggestions": [
    "Add Python, FastAPI, SQLAlchemy and Gemini API clearly."
  ],
  "project_section_suggestions": [
    "Mention file upload, LLM integration and Streamlit UI in the Job Application Assistant project."
  ],
  "experience_section_suggestions": [
    "Describe part-time work experience with transferable skills such as communication, responsibility and problem solving."
  ],
  "missing_sections": [
    "Technical Projects",
    "GitHub Link",
    "AI Projects"
  ],
  "priority_actions": [
    "Add a technical projects section.",
    "Rewrite project descriptions with technologies used."
  ]
}}
"""


def generate_tailored_cv(cv_text: str, job_text: str, language: str) -> dict:
    prompt = build_tailored_cv_prompt(cv_text, job_text, language)
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
            detail=f"CV uyarlama taslağı oluşturulurken beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_tailored_cv_prompt(cv_text: str, job_text: str, language: str) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    return f"""
You are an expert CV writer. Create a tailored CV draft by rephrasing and prioritizing existing CV content according to the provided job description.
CRITICAL:
1. Do not invent any fake experience, companies, dates, certifications, or projects.
2. Only rephrase and emphasize existing CV facts matching the job requirements.
3. Mention any missing required skills/experiences in the warnings section, not in the CV text itself.

CV CONTENT:
{cv_text}

JOB DESCRIPTION:
{job_text}

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "profile_summary": "Junior software developer with experience in Python, FastAPI, REST APIs and AI-powered application development...",
  "skills": [
    "Python",
    "FastAPI",
    "REST APIs",
    "SQL",
    "Git",
    "Gemini API",
    "Streamlit"
  ],
  "projects": [
    {{
      "name": "Job Application Assistant",
      "description": "Built an AI-powered application that analyzes uploaded CV files against job descriptions and generates match analysis, cover letters and interview questions."
    }}
  ],
  "experience_bullets": [
    "Developed strong communication and problem-solving skills in a fast-paced customer-facing environment."
  ],
  "education_section": "Computer Engineering student...",
  "warnings": [
    "This draft is based only on the uploaded CV. Review before use."
  ]
}}
"""


def rewrite_cv_section(cv_text: str, job_text: str, section_type: str, language: str, tone: str) -> dict:
    prompt = build_cv_rewrite_prompt(cv_text, job_text, section_type, language, tone)
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
            detail=f"Bölüm yeniden yazılırken beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_cv_rewrite_prompt(cv_text: str, job_text: str, section_type: str, language: str, tone: str) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    return f"""
Rewrite the specific section of the CV to match the Job Description requirements.
CRITICAL: Do not invent fake details. Focus only on rephrasing and framing existing details matching the requested tone: {tone}.

CV CONTENT:
{cv_text}

JOB DESCRIPTION:
{job_text}

SECTION TYPE TO REWRITE: {section_type} (options: summary / skills / projects / experience)
TONE: {tone} (options: professional / confident / concise)

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "section_type": "{section_type}",
  "rewritten_content": "...",
  "explanation": "This version highlights FastAPI, REST APIs and AI integration because they match the job description."
}}
"""


def generate_application_email(
    cv_text: str,
    job_text: str,
    language: str,
    tone: str,
    company_name: str | None,
    position_title: str | None
) -> dict:
    prompt = build_application_email_prompt(cv_text, job_text, language, tone, company_name, position_title)
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
            detail=f"E-posta oluşturulurken beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_application_email_prompt(
    cv_text: str,
    job_text: str,
    language: str,
    tone: str,
    company_name: str | None,
    position_title: str | None
) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    company_str = company_name if company_name else "[Company]"
    position_str = position_title if position_title else "[Position]"
    
    return f"""
Draft a cold application email, a short LinkedIn message, and a follow-up email based on the candidate's CV and the job description.
Company Name: {company_str}
Position Title: {position_str}
Tone: {tone} (options: professional / friendly / concise)

CV CONTENT:
{cv_text}

JOB DESCRIPTION:
{job_text}

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "subject": "Application for {position_str} Position",
  "email_body": "Dear Hiring Manager,...",
  "short_linkedin_message": "Hello, I am interested in the {position_str} position...",
  "follow_up_message": "Hello, I wanted to kindly follow up on my application..."
}}
"""


def generate_personalized_interview(
    cv_text: str,
    job_text: str,
    language: str,
    difficulty: str
) -> dict:
    prompt = build_personalized_interview_prompt(cv_text, job_text, language, difficulty)
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
            detail=f"Mülakat hazırlığı oluşturulurken beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_personalized_interview_prompt(
    cv_text: str,
    job_text: str,
    language: str,
    difficulty: str
) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    return f"""
Analyze the candidate's CV and the job description to generate custom, personalized interview prep material.
Difficulty Level: {difficulty} (easy / medium / hard)

CV CONTENT:
{cv_text}

JOB DESCRIPTION:
{job_text}

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "technical_questions": [
    {{
      "question": "General technical question based on requirements...",
      "answer_hint": "Hint on what answer works..."
    }}
  ],
  "cv_based_questions": [
    {{
      "question": "Tell me about your Job Application Assistant project.",
      "answer_hint": "Explain FastAPI, Streamlit, Gemini API and file upload."
    }}
  ],
  "weak_area_questions": [
    {{
      "question": "You have limited Docker experience. How would you handle deployment?",
      "answer_hint": "Be honest and explain your learning plan."
    }}
  ],
  "hr_questions": [
    {{
      "question": "Why do you want to join our company?",
      "answer_hint": "Connect company values with your goals."
    }}
  ],
  "sample_answers": [
    {{
      "question": "Question text...",
      "sample_answer": "Complete sample answer text..."
    }}
  ],
  "preparation_plan": [
    "Review Python basics.",
    "Prepare your project explanations."
  ]
}}
"""