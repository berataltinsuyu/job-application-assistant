# Job Application Assistant - Advanced Product Features Implementation Prompt

You are working on an existing Python project called `job-application-assistant`.

The current project already has:

- FastAPI backend
- Streamlit frontend
- SQLite database with SQLAlchemy
- Gemini API integration
- PDF/DOCX CV upload and text extraction
- `/analyze` endpoint
- `/cover-letter` endpoint
- `/interview-prep` endpoint
- `/history` endpoint
- Streamlit tabs for CV Analysis, Cover Letter, Interview Prep, and History

Do not rewrite the whole project from scratch. Extend the existing structure cleanly.

Current project structure is approximately:

```txt
job-application-assistant/
│
├── main.py
├── database.py
├── models.py
├── schemas.py
├── streamlit_app.py
├── requirements.txt
├── README.md
│
├── routers/
│   ├── analyze.py
│   ├── cover_letter.py
│   ├── interview.py
│   └── history.py
│
└── services/
    ├── file_parser_service.py
    └── llm_service.py
```

The project uses Gemini with this model:

```python
GEMINI_MODEL = "gemini-2.5-flash-lite"
```

Do not remove existing working features.

---

## Goal

Turn this project from a basic MVP into a more complete AI job application assistant.

Add the following advanced features:

1. Job description extraction from URL
2. ATS compatibility score
3. Job keyword extraction
4. CV improvement assistant
5. Tailored CV draft generator
6. CV section rewriter
7. Application email generator
8. Personalized interview preparation
9. Downloadable outputs in Streamlit
10. Improved history management
11. Improved Streamlit UI

---

## 1. Job Description Extraction from URL

Add a new backend endpoint:

```txt
POST /extract-job-description
```

Input:

```txt
job_url: str
```

Expected behavior:

- Try to fetch the job posting page.
- Extract readable job description text from the page.
- Return extracted text.
- If extraction fails, return a clear error message asking the user to paste the job description manually.
- LinkedIn job URLs should be supported on a best-effort basis.
- LinkedIn may block scraping or require login. In that case, do not crash. Return a helpful fallback message.

Recommended libraries:

```txt
requests
beautifulsoup4
trafilatura
```

Create a new service:

```txt
services/job_description_service.py
```

Functions:

```python
def extract_job_description_from_url(job_url: str) -> dict:
    ...
```

Return format:

```json
{
  "success": true,
  "source_url": "https://...",
  "extracted_text": "...",
  "message": "Job description extracted successfully."
}
```

If failed:

```json
{
  "success": false,
  "source_url": "https://...",
  "extracted_text": "",
  "message": "Could not extract job description from this URL. Please paste the job description manually."
}
```

Create router:

```txt
routers/job_description.py
```

Add it to `main.py`.

Important:

- Do not use Selenium.
- Keep it simple.
- Use normal HTTP extraction.
- Handle LinkedIn limitations gracefully.

---

## 2. ATS Compatibility Score

Add endpoint:

```txt
POST /ats-score
```

Input:

```txt
cv_file: PDF/DOCX
job_text: str
language: Turkish / English
```

Output JSON:

```json
{
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
}
```

Add to:

```txt
routers/ats.py
services/llm_service.py
```

In `llm_service.py`, add:

```python
def generate_ats_score(cv_text: str, job_text: str, language: str) -> dict:
    ...

def build_ats_prompt(cv_text: str, job_text: str, language: str) -> str:
    ...
```

Store result in history with:

```txt
request_type = "ats_score"
```

---

## 3. Job Keyword Extraction

Add endpoint:

```txt
POST /job-keywords
```

Input:

```txt
job_text: str
language: Turkish / English
```

Output JSON:

```json
{
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
}
```

Add router:

```txt
routers/job_keywords.py
```

Add service functions to `llm_service.py`:

```python
def extract_job_keywords(job_text: str, language: str) -> dict:
    ...

def build_job_keywords_prompt(job_text: str, language: str) -> str:
    ...
```

Store in history:

```txt
request_type = "job_keywords"
```

---

## 4. CV Improvement Assistant

Add endpoint:

```txt
POST /cv-improvement
```

Input:

```txt
cv_file: PDF/DOCX
job_text: str
language: Turkish / English
```

Output JSON:

```json
{
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
}
```

Add router:

```txt
routers/cv_improvement.py
```

Add service functions:

```python
def generate_cv_improvement(cv_text: str, job_text: str, language: str) -> dict:
    ...

def build_cv_improvement_prompt(cv_text: str, job_text: str, language: str) -> str:
    ...
```

Store in history:

```txt
request_type = "cv_improvement"
```

Important:

- Do not invent fake experience.
- Only suggest improvements based on existing CV content.
- Clearly mention missing skills as recommendations, not as existing experience.

---

## 5. Tailored CV Draft Generator

Add endpoint:

```txt
POST /tailored-cv
```

Input:

```txt
cv_file: PDF/DOCX
job_text: str
language: Turkish / English
```

Output JSON:

```json
{
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
    {
      "name": "Job Application Assistant",
      "description": "Built an AI-powered application that analyzes uploaded CV files against job descriptions and generates match analysis, cover letters and interview questions."
    }
  ],
  "experience_bullets": [
    "Developed strong communication and problem-solving skills in a fast-paced customer-facing environment."
  ],
  "education_section": "Computer Engineering student...",
  "warnings": [
    "This draft is based only on the uploaded CV. Review before use."
  ]
}
```

Add router:

```txt
routers/tailored_cv.py
```

Add service functions:

```python
def generate_tailored_cv(cv_text: str, job_text: str, language: str) -> dict:
    ...

def build_tailored_cv_prompt(cv_text: str, job_text: str, language: str) -> str:
    ...
```

Store in history:

```txt
request_type = "tailored_cv"
```

Important prompt rules:

- Do not create fake experience.
- Do not invent companies, dates, certificates, or projects.
- Rephrase and prioritize existing CV content according to the job description.
- Mention missing information in warnings.

---

## 6. CV Section Rewriter

Add endpoint:

```txt
POST /rewrite-cv-section
```

Input:

```txt
cv_file: PDF/DOCX
job_text: str
section_type: summary / skills / projects / experience
language: Turkish / English
tone: professional / confident / concise
```

Output JSON:

```json
{
  "section_type": "projects",
  "rewritten_content": "...",
  "explanation": "This version highlights FastAPI, REST APIs and AI integration because they match the job description."
}
```

Add router:

```txt
routers/cv_rewrite.py
```

Add service functions:

```python
def rewrite_cv_section(cv_text: str, job_text: str, section_type: str, language: str, tone: str) -> dict:
    ...

def build_cv_rewrite_prompt(cv_text: str, job_text: str, section_type: str, language: str, tone: str) -> str:
    ...
```

Store in history:

```txt
request_type = "cv_rewrite"
```

---

## 7. Application Email Generator

Add endpoint:

```txt
POST /application-email
```

Input:

```txt
cv_file: PDF/DOCX
job_text: str
language: Turkish / English
tone: professional / friendly / concise
company_name: optional str
position_title: optional str
```

Output JSON:

```json
{
  "subject": "Application for Junior Python Developer Intern Position",
  "email_body": "Dear Hiring Manager,...",
  "short_linkedin_message": "Hello, I am interested in the Junior Python Developer Intern position...",
  "follow_up_message": "Hello, I wanted to kindly follow up on my application..."
}
```

Add router:

```txt
routers/application_email.py
```

Add service functions:

```python
def generate_application_email(cv_text: str, job_text: str, language: str, tone: str, company_name: str | None, position_title: str | None) -> dict:
    ...

def build_application_email_prompt(...) -> str:
    ...
```

Store in history:

```txt
request_type = "application_email"
```

---

## 8. Personalized Interview Preparation

Current `/interview-prep` uses only job_text.

Add a stronger endpoint:

```txt
POST /personalized-interview-prep
```

Input:

```txt
cv_file: PDF/DOCX
job_text: str
language: Turkish / English
difficulty: easy / medium / hard
```

Output JSON:

```json
{
  "technical_questions": [
    {
      "question": "...",
      "answer_hint": "..."
    }
  ],
  "cv_based_questions": [
    {
      "question": "Tell me about your Job Application Assistant project.",
      "answer_hint": "Explain FastAPI, Streamlit, Gemini API and file upload."
    }
  ],
  "weak_area_questions": [
    {
      "question": "You have limited Docker experience. How would you handle deployment?",
      "answer_hint": "Be honest and explain your learning plan."
    }
  ],
  "hr_questions": [],
  "sample_answers": [
    {
      "question": "...",
      "sample_answer": "..."
    }
  ],
  "preparation_plan": [
    "Review Python basics.",
    "Prepare your project explanations."
  ]
}
```

Add router:

```txt
routers/personalized_interview.py
```

Add service functions:

```python
def generate_personalized_interview(cv_text: str, job_text: str, language: str, difficulty: str) -> dict:
    ...

def build_personalized_interview_prompt(...) -> str:
    ...
```

Store in history:

```txt
request_type = "personalized_interview"
```

---

## 9. Downloadable Outputs in Streamlit

Add download buttons to Streamlit results.

For each generated result:

- Analysis report download as `.json`
- ATS report download as `.json`
- Cover letter download as `.txt`
- Interview prep download as `.json`
- Tailored CV draft download as `.json` and `.txt`
- Application email download as `.txt`

Use:

```python
st.download_button(...)
```

No need to generate PDF yet.

PDF export can be a future improvement.

---

## 10. Improved History Management

Enhance history endpoints.

Current:

```txt
GET /history
```

Add:

```txt
GET /history/{history_id}
DELETE /history/{history_id}
DELETE /history
GET /history?request_type=analyze
```

Update `routers/history.py`.

Expected behavior:

- List all history
- Filter by request_type
- Get single record
- Delete single record
- Clear all history

Do not break existing `/history`.

---

## 11. Improved Streamlit UI

Redesign `streamlit_app.py`.

Use sidebar navigation instead of too many tabs if needed.

Suggested pages:

```txt
Dashboard
Job URL Extractor
CV Analysis
ATS Score
Job Keywords
CV Improvement
Tailored CV
Rewrite CV Section
Cover Letter
Application Email
Interview Prep
Personalized Interview
History
```

Dashboard should show:

- Total history count
- Latest analysis
- Latest ATS score
- Recent history
- Feature overview

Add user-friendly validations:

- Show warning if CV is missing
- Show warning if job text is missing
- Show fallback if URL extraction fails
- Show Gemini error messages clearly

Keep UI simple but clean.

---

## 12. Important Engineering Rules

Follow these rules:

1. Do not remove existing working functionality.
2. Keep routers small and clean.
3. Keep Gemini calls inside `services/llm_service.py`.
4. Keep file parsing inside `services/file_parser_service.py`.
5. Keep URL extraction inside `services/job_description_service.py`.
6. Use `json.loads` for structured Gemini outputs.
7. Use existing `clean_json_response` helper.
8. Store JSON results in DB using:

```python
json.dumps(result, ensure_ascii=False)
```

9. Return JSON objects to frontend, not JSON strings.
10. Use clear `HTTPException` errors.
11. Do not invent fake CV experience in prompts.
12. Add all new routers to `main.py`.
13. Update `requirements.txt`.
14. Update README with new features briefly.

---

## 13. Suggested New Files

Create these files:

```txt
routers/ats.py
routers/job_description.py
routers/job_keywords.py
routers/cv_improvement.py
routers/tailored_cv.py
routers/cv_rewrite.py
routers/application_email.py
routers/personalized_interview.py

services/job_description_service.py
```

Update these files:

```txt
main.py
services/llm_service.py
routers/history.py
streamlit_app.py
requirements.txt
README.md
```

---

## 14. New Dependencies

Install if missing:

```bash
pip install beautifulsoup4 trafilatura
```

Then update:

```bash
pip freeze > requirements.txt
```

If `trafilatura` causes installation issues, fall back to only `requests + beautifulsoup4`.

---

## 15. Final Expected Product

After implementation, the app should support:

- Upload CV
- Paste job description
- Extract job description from public job posting URL
- Analyze CV-job match
- Calculate ATS compatibility score
- Extract job keywords
- Suggest CV improvements
- Generate a tailored CV draft
- Rewrite selected CV sections
- Generate Turkish/English cover letters
- Generate application emails and LinkedIn messages
- Generate general and personalized interview questions
- Save all outputs to history
- View, filter and delete history
- Download generated outputs from Streamlit

Make the implementation robust and readable.

If a feature is too large, implement it step-by-step but keep the project runnable after each change.

---

## Implementation Order

Implement in this order:

1. Backend endpoint files and service functions
2. Add routers to `main.py`
3. Test all new endpoints in Swagger
4. Redesign Streamlit UI
5. Add download buttons
6. Improve history management
7. Update README
8. Update requirements.txt

Important final note:

For LinkedIn job URLs, do not promise perfect extraction. Implement best-effort extraction. If LinkedIn blocks the request, show a fallback message and allow the user to paste the job description manually.
