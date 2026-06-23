import json
import os

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import errors

from services.ats_cv_schema import get_empty_ats_cv_schema

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


def generate_ats_cv_json(
    cv_text: str,
    job_description: str,
    template: dict,
    language: str
) -> dict:
    prompt = build_ats_cv_generation_prompt(
        cv_text=cv_text,
        job_description=job_description,
        template=template,
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
            detail="Gemini cevap verdi fakat geçerli ATS CV JSON formatında cevap üretmedi."
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"ATS CV oluşturulurken beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_ats_cv_generation_prompt(
    cv_text: str,
    job_description: str,
    template: dict,
    language: str
) -> str:
    output_language = "Turkish" if language.lower() == "turkish" else "English"
    template_json = json.dumps(template, ensure_ascii=False, indent=2)
    schema_json = json.dumps(get_empty_ats_cv_schema(), ensure_ascii=False, indent=2)

    return f"""
You are an expert ATS CV writer and resume parser.

Your task:
Generate a job-specific, ATS-optimized structured CV JSON by rewriting and organizing ONLY the truthful information supported by the user's existing CV.

CV CONTENT:
{cv_text}

JOB DESCRIPTION:
{job_description}

SELECTED ATS TEMPLATE:
{template_json}

OUTPUT LANGUAGE:
{output_language}

Language consistency rules:
1. Output every generated field in the selected language: {output_language}.
2. Do not mix languages anywhere in the JSON values.
3. If OUTPUT LANGUAGE is Turkish, generate professional Turkish CV content for contact.target_title, summaries, skills where natural, experience bullets, project descriptions, education details, certification descriptions, language levels, ats_metadata.optimization_summary, and ats_metadata.adaptation_notes.
4. If OUTPUT LANGUAGE is English, generate professional English CV content for every generated field.
5. Do not leave rewritten CV content in the source CV language when the selected output language is different.
6. The example phrases in this prompt illustrate meaning only. Translate or adapt them into {output_language} before using similar wording.

Target title alignment rules:
1. contact.target_title must be generated from the target job family and ats_metadata.target_role, not copied blindly from the original CV.
2. contact.target_title must align with ats_metadata.target_role and the job description.
3. If the original CV title belongs to a different role family, adapt contact.target_title to the target job family.
4. Keep the title realistic for the candidate's seniority. Do not use senior, lead, principal, manager, head, director, or architect titles unless clearly supported by the CV.
5. For junior, intern, student, or early-career candidates, use a junior-level target title.
6. If the job is fraud, risk, payment operations, or fintech operations, use a title such as "Junior Payment Systems & Risk Operations Specialist", "Junior Fraud/Risk Operations Analyst", "Junior Payment Operations Analyst", or "Junior Fintech Operations Analyst".
7. If the job is backend or software, use a title such as "Junior Backend Developer", "Junior .NET Developer", or "Junior Software Developer".
8. If the job is business analyst or IT corporate applications, use a title such as "Junior IT Business Analyst", "Junior Corporate Applications Specialist", or "Junior IT Analyst".
9. If the job is data or reporting, use a title such as "Junior Data Analyst", "Junior Reporting Analyst", or "Junior Business Data Analyst".

Balanced job alignment rules:
1. Tailor the CV enough to be useful for the job, while keeping every claim honest and defensible in an interview.
2. You may reframe existing experience toward the target job.
3. You may emphasize transferable skills.
4. You may use job-related terminology when it is supported by the CV context or is a reasonable truthful extension of the candidate's existing work.
5. You may add reasonable domain-aligned wording based on existing experience.
6. You may convert technical work into business, operations, validation, documentation, analysis, support, process, or collaboration impact language when implied by the CV.
7. You may highlight exposure, support, collaboration, validation, documentation, analysis, and process understanding when these are implied by the CV.
8. Do not simply copy the original CV. Improve wording, order, and emphasis for the job description.
9. Strengthen bullets using the job description's language when the claim remains truthful and interview-defensible.
10. Adapt project bullets to emphasize relevance to the target job.
11. Emphasize relevant tools, databases, reporting, APIs, integrations, testing, troubleshooting, documentation, and process work when supported by the CV.

Hard limits:
1. Do not invent companies, roles, dates, education, certifications, links, or projects.
2. Do not claim direct ownership of responsibilities not present in the CV.
3. Do not claim expert-level skills unless the CV clearly supports that level.
4. Do not add regulated or high-responsibility domain claims as direct experience unless clearly present.
5. Do not present interest, exposure, transferable alignment, or general context as direct hands-on ownership.
6. Put important job keywords that cannot be supported or defensibly adapted from the CV into ats_metadata.missing_keywords.
7. If a field cannot be supported from the CV, leave it empty, use an empty list, or omit the unsupported detail inside that field.
8. Do not claim direct fraud detection, AML investigation, compliance ownership, audit responsibility, risk parameter management, chargeback fraud investigation, regulatory reporting, or risk strategy ownership unless the original CV clearly supports it.

Acceptable adaptation examples:
- "Supported payment systems application development and operational process analysis."
- "Performed SQL-based data validation and backend data checks."
- "Contributed to API testing, issue investigation, and technical documentation."
- "Gained exposure to payment systems workflows in a banking environment."
- "Applied analytical problem-solving in technical and operational contexts."
- "Collaborated with technical teams to understand payment system business requirements."
- "Developed RESTful APIs supporting business workflows."
- "Worked on data integrity, validation, and system integration logic."
- "Supported reliable backend operations through testing and debugging."
- "Developed strong communication, problem-solving, and customer-oriented operational skills."
- "Worked in a fast-paced environment requiring process adherence and teamwork."

Risky phrasing to avoid unless explicitly supported by the CV:
- "Led fraud detection operations."
- "Managed AML investigations."
- "Owned regulatory compliance processes."
- "Performed risk scoring for financial transactions."
- "Handled audit and legal compliance reporting."
- "Designed fraud risk parameters."
- "Managed chargeback fraud investigations."
- "Led risk management strategy."
- "Owned regulatory reporting."

Preferred wording for partially related experience:
- supported
- contributed to
- gained exposure to
- assisted with
- collaborated on
- performed validation for
- helped analyze
- documented
- tested
- monitored
- investigated technical issues
- supported process understanding
- contributed to operational reliability

Role family adaptation:
1. If the job is software/backend, emphasize development, APIs, databases, backend stack, testing, integrations, and projects.
2. If the job is business analyst or IT corporate applications, emphasize requirement analysis, documentation, process analysis, stakeholder communication, testing, system integration, and workflow understanding.
3. If the job is fraud/risk/payment operations, emphasize payment systems exposure, SQL/data analysis, reporting, issue investigation, operational process understanding, documentation, and cross-functional collaboration. Use transferable wording when direct fraud/risk experience is missing.
4. If the job is data/reporting, emphasize SQL, data validation, reporting, analytics, dashboards, documentation, and process improvement.

Optimization rules:
1. Rewrite bullets professionally and concisely.
2. Prioritize supported or defensibly adapted keywords from the job description.
3. Keep wording ATS-friendly and keyword-readable.
4. Avoid tables, icons, graphics, columns, decorative formatting, and non-standard section labels.
5. Use the selected template section_order as the intended display order.
6. Keep standard headings and clear section names.
7. Preserve dates, roles, schools, companies, and links only when present in the CV.

ATS scoring:
1. Estimate ats_metadata.ats_score_before from the original CV against the job description.
2. Estimate ats_metadata.ats_score_after from the optimized JSON CV against the job description.
3. The after score must reflect truthful optimization only. Do not increase the score by claiming unsupported experience.
4. Include a clear ats_metadata.optimization_summary.
5. Include ats_metadata.target_role and ats_metadata.target_company if detected from the job description.
6. Include ats_metadata.job_keywords_used with keywords directly supported by the CV.
7. Include ats_metadata.transferable_keywords_used with job keywords indirectly supported through related experience or transferable alignment.
8. Include ats_metadata.missing_keywords with important job keywords not supported by the CV and not defensibly adaptable.
9. Include ats_metadata.risky_keywords_not_added with job keywords or claims that would be dishonest to add as direct experience.
10. Include ats_metadata.alignment_confidence with exactly one value: "high", "medium", or "low".
   - "high": job requirements strongly match the CV.
   - "medium": job requirements partly match through transferable skills.
   - "low": the job requires many direct skills not present in the CV.
11. Include ats_metadata.adaptation_notes as a short list explaining what was adapted and why.

For a fraud/risk/payment operations role, metadata may look like this when supported by the CV:
- job_keywords_used: ["Payment Systems", "SQL", "Data Analysis", "Reporting", "Documentation"]
- transferable_keywords_used: ["Risk Operations", "Issue Investigation", "Operational Follow-up", "Process Analysis"]
- missing_keywords: ["Fraud team experience", "AML investigations", "Compliance license", "Risk parameter management"]
- risky_keywords_not_added: ["Direct fraud detection ownership", "AML investigation ownership", "Regulatory compliance ownership"]
- adaptation_notes: [
  "Payment systems internship experience was reframed toward fintech operations and risk support.",
  "SQL and API testing experience were emphasized as transferable skills for reporting, validation, and issue investigation.",
  "Fraud/compliance ownership was not claimed because it was not directly supported by the CV."
]

Return valid JSON only.
Do not include explanations, markdown, code fences, comments, or any text outside the JSON object.
The JSON object must match this exact top-level shape:

{schema_json}
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


def extract_cv_profile(cv_text: str, language: str) -> dict:
    prompt = build_cv_profile_prompt(cv_text, language)
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
            detail=f"CV profil çıkarımı sırasında beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_cv_profile_prompt(cv_text: str, language: str) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    return f"""
Analyze the following CV content to extract the candidate profile and relevant search keywords.
CRITICAL RULES:
1. Do not invent any fake experience, skills, or history. Only use the facts clearly present in the uploaded CV.
2. If a skill is not clearly in the CV, do not list it as an existing skill.
3. Suggest 3 to 5 realistic search queries based on the CV profile. They should include target roles, location (if inferred/applicable), and relevant technology keywords.

CV CONTENT:
{cv_text}

{lang_instruction}

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "target_roles": [
    "Junior Python Developer",
    "Backend Developer Intern",
    "AI Developer Intern"
  ],
  "technical_skills": [
    "Python",
    "FastAPI",
    "SQL",
    "Git",
    "Streamlit",
    "Gemini API"
  ],
  "soft_skills": [
    "communication",
    "problem solving",
    "teamwork"
  ],
  "experience_level": "Intern / Junior",
  "preferred_job_types": [
    "Internship",
    "Junior",
    "Remote",
    "Hybrid"
  ],
  "suggested_search_queries": [
    "Junior Python Developer",
    "Backend Developer Intern Python",
    "AI Developer Intern FastAPI"
  ],
  "profile_summary": "Short candidate profile summary."
}}
"""


def rank_jobs_for_cv(cv_text: str, jobs: list[dict], language: str) -> dict:
    prompt = build_rank_jobs_prompt(cv_text, jobs, language)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        raw_result = response.text
        cleaned_result = clean_json_response(raw_result)
        parsed_result = json.loads(cleaned_result)
        
        # Ensure we map and preserve URL and source from the original jobs
        ranked = parsed_result.get("ranked_jobs", [])
        updated_ranked = []
        for r_job in ranked:
            # Match back to the original jobs
            original_match = None
            for o_job in jobs:
                if (o_job.get("title", "").lower() == r_job.get("title", "").lower() and 
                    o_job.get("company", "").lower() == r_job.get("company", "").lower()):
                    original_match = o_job
                    break
            
            # Fallback if title/company mismatch: match by title similarity or just key match
            if not original_match:
                for o_job in jobs:
                    if o_job.get("title", "").lower() == r_job.get("title", "").lower():
                        original_match = o_job
                        break
            
            url = ""
            source = "SerpAPI Google Jobs"
            posted_date = ""
            if original_match:
                url = original_match.get("url", "")
                source = original_match.get("source", "SerpAPI Google Jobs")
                posted_date = original_match.get("posted_date", "")
            else:
                url = r_job.get("url", "")
            
            r_job["url"] = url
            r_job["source"] = source
            r_job["posted_date"] = posted_date
            updated_ranked.append(r_job)
            
        parsed_result["ranked_jobs"] = updated_ranked
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
            detail=f"İş ilanları sıralanırken beklenmeyen bir hata oluştu: {str(error)}"
        )


def build_rank_jobs_prompt(cv_text: str, jobs: list[dict], language: str) -> str:
    lang_instruction = "Lütfen sonucu Türkçe üret." if language.lower() == "turkish" else "Please generate the output in English."
    
    simplified_jobs = []
    for idx, job in enumerate(jobs):
        simplified_jobs.append({
            "index": idx,
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "description": job.get("description", "")
        })
    jobs_json_str = json.dumps(simplified_jobs, ensure_ascii=False)

    return f"""
Analyze the candidate's CV and the list of job postings to rank them according to CV compatibility.

CV CONTENT:
{cv_text}

JOB POSTINGS LIST:
{jobs_json_str}

{lang_instruction}

CRITICAL RULES:
1. Preserve the original job details (like title, company, location).
2. For each job, calculate a match_score between 0 and 100.
3. Determine "matched_skills" (skills present in CV that the job requires), "missing_skills" (skills the job requires but not clearly in the CV).
4. Provide a "why_good_match" justification and an "application_tip" tailored to the candidate's projects/skills.
5. If the job description is very short or vague, mention in the "why_good_match" or general summary that the ranking may be approximate.
6. Sort the resulting "ranked_jobs" by "match_score" in descending order.

Ensure the output is a valid JSON. Do not include any explanations, markdown, or code block markers. Just return the JSON object matching this schema:

{{
  "ranked_jobs": [
    {{
      "title": "Junior AI Backend Developer Intern",
      "company": "Demo AI",
      "location": "Remote",
      "match_score": 86,
      "matched_skills": ["Python", "FastAPI", "SQL", "AI APIs"],
      "missing_skills": ["Docker"],
      "why_good_match": "This role matches the candidate's backend and AI project experience.",
      "application_tip": "Highlight AI Document Assistant and Job Application Assistant projects."
    }}
  ],
  "summary": "Short overall recommendation."
}}
"""
