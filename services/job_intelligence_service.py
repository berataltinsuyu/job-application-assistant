import json
import os
import re
from services.llm_service import client, GEMINI_MODEL

# Supported Job Families
VALID_JOB_FAMILIES = {
    "software_backend",
    "frontend",
    "fullstack",
    "ai_ml_llm",
    "data_analytics",
    "business_analyst",
    "product_project",
    "fintech_payment",
    "risk_fraud_compliance",
    "cybersecurity",
    "devops_cloud",
    "corporate_applications",
    "sales_operations",
    "general",
}

# Supported Seniorities
VALID_SENIORITIES = {
    "internship",
    "entry_level",
    "junior",
    "mid",
    "senior",
    "lead_manager",
    "unknown",
}

# Recommendations
VALID_RECOMMENDATIONS = {
    "strong_apply",
    "apply",
    "apply_with_tailored_cv",
    "low_match",
    "not_recommended",
}


def detect_job_family_from_text(title: str, description: str) -> str:
    title_norm = _normalize(title)
    desc_norm = _normalize(description)

    family_keywords = {
        "ai_ml_llm": [
            "ai", "ml", "machine learning", "deep learning", "nlp", "llm",
            "genai", "generative ai", "computer vision", "artificial intelligence",
            "pytorch", "tensorflow", "transformer", "openai", "mlops", "langchain", "rag"
        ],
        "cybersecurity": [
            "cybersecurity", "security", "infosec", "penetration", "soc", "siem",
            "firewall", "cryptography", "threat", "vulnerability", "malware", "cyber"
        ],
        "devops_cloud": [
            "devops", "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "k8s",
            "terraform", "ci/cd", "jenkins", "ansible", "pipelines", "sysadmin",
            "infrastructure", "sre", "platform engineer"
        ],
        "data_analytics": [
            "data analyst", "data analytics", "data science", "data scientist",
            "data engineer", "bi developer", "powerbi", "tableau", "spark", "hadoop",
            "etl", "data warehouse", "pandas", "numpy", "tableau", "sql developer"
        ],
        "fintech_payment": [
            "fintech", "payment", "transaction", "banking", "ledger", "credit card",
            "pos", "gateway", "remittance", "acquiring", "billing", "swift", "open banking"
        ],
        "risk_fraud_compliance": [
            "risk", "fraud", "compliance", "aml", "kyc", "audit", "regulatory",
            "sanction", "chargeback", "compliance specialist"
        ],
        "business_analyst": [
            "business analyst", "systems analyst", "business analysis", "requirements",
            "product owner", "scrum master", "jira", "agile", "flowchart", "use case"
        ],
        "product_project": [
            "product manager", "project manager", "product management", "project management",
            "roadmap", "scrum", "agile", "pmp", "gantt"
        ],
        "software_backend": [
            "backend", "java", "python", "go", "golang", "c#", "net", "spring boot",
            "django", "fastapi", "nodejs", "express", "sql", "postgresql", "mysql",
            "mongodb", "redis", "microservices", "api", "rest api", "developer", "engineer"
        ],
        "frontend": [
            "frontend", "react", "angular", "vue", "javascript", "typescript", "html",
            "css", "sass", "webpack", "npm", "ui/ux", "web design", "interface", "css3", "html5"
        ],
        "fullstack": [
            "fullstack", "full-stack", "mern", "mean", "django + react", "spring + angular"
        ],
        "corporate_applications": [
            "sap", "salesforce", "crm", "erp", "dynamics", "sharepoint", "netsuite", "oracle apps"
        ],
        "sales_operations": [
            "sales operations", "sales ops", "crm admin", "hubspot", "sales support"
        ],
    }

    scores = {}
    for family, kw_list in family_keywords.items():
        score = 0
        for kw in kw_list:
            pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
            if re.search(pattern, title_norm):
                score += 5
            if re.search(pattern, desc_norm):
                score += 1
        scores[family] = score

    max_family = max(scores, key=scores.get)
    if scores[max_family] > 0:
        return max_family
    return "general"


def detect_seniority_from_text(title: str, description: str) -> str:
    title_norm = _normalize(title)
    desc_norm = _normalize(description)

    seniority_keywords = {
        "internship": ["intern", "internship", "staj", "stajyer"],
        "entry_level": ["entry level", "entry-level", "new grad", "graduate", "assistant", "entry"],
        "junior": ["junior", "jr", "associate"],
        "mid": ["mid", "mid-level", "intermediate", "experienced"],
        "senior": ["senior", "sr", "lead developer", "lead engineer"],
        "lead_manager": ["lead", "principal", "manager", "director", "head", "architect", "yönetici", "lider", "managing"]
    }

    scores = {k: 0 for k in seniority_keywords}
    for level, kw_list in seniority_keywords.items():
        for kw in kw_list:
            pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
            if re.search(pattern, title_norm):
                scores[level] += 5
            if re.search(pattern, desc_norm):
                scores[level] += 1

    # Check year patterns in description
    years_senior = re.findall(r"\b([5-9]|1[0-5])\+?\s*(?:years?|yıl)\b", desc_norm)
    if years_senior:
        scores["senior"] += len(years_senior) * 3

    years_junior = re.findall(r"\b(1|2|3)\+?\s*(?:years?|yıl)\b", desc_norm)
    if years_junior:
        scores["junior"] += len(years_junior) * 2

    max_level = max(scores, key=scores.get)
    if scores[max_level] > 0:
        return max_level
    return "unknown"


def generate_job_intelligence(job: dict, alert_profile: dict | None = None) -> dict:
    # Check environment flag for LLM enhancement
    use_llm = os.getenv("JOB_INTELLIGENCE_USE_LLM", "false").lower() == "true"
    if use_llm:
        try:
            return _generate_job_intelligence_with_llm(job, alert_profile)
        except Exception:
            # Fallback to deterministic logic if LLM fails
            pass

    return _generate_job_intelligence_deterministically(job, alert_profile)


def _generate_job_intelligence_deterministically(job: dict, alert_profile: dict | None = None) -> dict:
    title = job.get("title") or "Untitled Job"
    company = job.get("company") or "N/A"
    description = job.get("description") or ""
    score = job.get("match_score", 0)

    job_family = detect_job_family_from_text(title, description)
    seniority = detect_seniority_from_text(title, description)

    # 1. Role Summary
    role_summary = (
        f"This is a {seniority.replace('_', ' ')} level {job_family.replace('_', ' ')} position "
        f"as a {title} at {company}. The role involves collaborating on technical and operational "
        f"tasks as outlined in the description. Key responsibilities include working with the team "
        f"to deliver high-quality outcomes in line with requirements."
    )

    # 2. Match Reason
    if alert_profile:
        profile_name = alert_profile.get("name") or "Selected Profile"
        match_reason = (
            f"This job matches your alert profile '{profile_name}' with a score of {score}/100. "
            f"Matches were identified in role keywords and structural requirements (like location "
            f"or seniority) according to the configured alert profile parameters."
        )
    else:
        match_reason = (
            f"No alert profile was selected. The analysis is based on the job title '{title}' "
            f"and company '{company}'. The role matches general {job_family.replace('_', ' ')} requirements."
        )

    # 3. Candidate Strengths
    strengths = []
    if alert_profile and job.get("matched_keywords"):
        matched_kws = job.get("matched_keywords") or []
        # Filter out fields like "location" etc if present
        kws = [kw for kw in matched_kws if not kw.startswith(("location:", "seniority:", "job_type:", "work_model:"))]
        if kws:
            strengths.append(f"Strong overlap on core keywords: {', '.join(kws[:5])}.")
    strengths.append(f"Detected job category aligns with {job_family.replace('_', ' ')} domain.")
    if job.get("location"):
        strengths.append(f"Matches location criteria ({job.get('location')}).")
    if job.get("work_model"):
        strengths.append(f"Matches work model ({job.get('work_model')}).")

    # 4. Candidate Gaps & Missing Keywords
    gaps = []
    missing_kws = []
    if alert_profile:
        missing_kws = job.get("missing_keywords") or []
        # Separate actual keywords from filter indicators
        missing_actual = [kw for kw in missing_kws if ":" not in kw]
        if missing_actual:
            gaps.append(f"Missing core technical keywords: {', '.join(missing_actual[:5])}.")
            missing_kws = missing_actual
        
        # Check seniority mismatch
        expected_seniority = _normalize(alert_profile.get("seniority") or "")
        detected_seniority = _normalize(seniority)
        if expected_seniority and expected_seniority != "unknown" and expected_seniority not in detected_seniority:
            gaps.append(f"Seniority mismatch (Expected '{alert_profile.get('seniority')}', Detected '{seniority.replace('_', ' ')}').")
    else:
        gaps.append("No alert profile keywords mapped; verify requirements in description.")
        # Infer some common terms in that family not present in title
        desc_words = set(re.findall(r"\b\w+\b", _normalize(description)))
        family_defaults = {
            "software_backend": ["sql", "api", "database", "git", "rest"],
            "frontend": ["html", "css", "javascript", "react", "typescript"],
            "ai_ml_llm": ["python", "pytorch", "llm", "ai", "model"],
            "data_analytics": ["sql", "excel", "python", "reporting", "dashboard"],
            "devops_cloud": ["docker", "kubernetes", "aws", "cloud", "pipelines"]
        }
        defaults = family_defaults.get(job_family, ["documentation", "communication"])
        missing_kws = [word for word in defaults if word not in desc_words]

    # 5. Suggested CV Focus
    cv_focus_map = {
        "software_backend": "Emphasize backend architecture, API design, database schemas, and performance tuning.",
        "frontend": "Focus on responsive UI design, component reusability, state management, and modern JS/TS frameworks.",
        "fullstack": "Highlight end-to-end feature ownership, integrating frontend components with backend APIs, and database interactions.",
        "ai_ml_llm": "Highlight model development, data preprocessing pipelines, LLM integration/fine-tuning, and evaluation metrics.",
        "data_analytics": "Emphasize data cleaning, dashboard creation, SQL queries, statistical analysis, and business insight delivery.",
        "business_analyst": "Focus on requirement gathering, documentation, process mapping, agile methodologies, and stakeholder communication.",
        "product_project": "Highlight roadmap planning, lifecycle management, scrum facilitation, and cross-functional coordination.",
        "fintech_payment": "Emphasize transaction security, ledger systems, payment gateway integration, and financial compliance.",
        "risk_fraud_compliance": "Highlight fraud detection algorithms, regulatory compliance audits, and risk assessment models.",
        "cybersecurity": "Emphasize security audits, threat modeling, vulnerability assessments, and incident response planning.",
        "devops_cloud": "Focus on infrastructure as code, CI/CD pipelines, containerization, and cloud resource management.",
        "corporate_applications": "Highlight ERP/CRM configuration, custom business flows, and corporate tool integration.",
        "sales_operations": "Focus on sales pipeline optimization, CRM management, and operational reporting.",
    }
    suggested_cv_focus = cv_focus_map.get(job_family, "Emphasize core technical skills, teamwork, documentation, and process improvement.")

    # 6. Suggested Project Focus
    project_focus_map = {
        "software_backend": "backend/API projects",
        "frontend": "frontend/UI projects",
        "fullstack": "fullstack projects",
        "ai_ml_llm": "AI/LLM projects",
        "data_analytics": "data/reporting projects",
        "business_analyst": "business analysis/process projects",
        "product_project": "product/project management projects",
        "fintech_payment": "fintech/payment projects",
        "risk_fraud_compliance": "risk/compliance projects",
        "cybersecurity": "cybersecurity/security projects",
        "devops_cloud": "DevOps/cloud projects",
        "corporate_applications": "corporate application integrations",
        "sales_operations": "sales operations metrics dashboards",
    }
    suggested_project_focus = f"Highlight {project_focus_map.get(job_family, 'general software engineering or operational improvement')} projects."

    # 7. Suggested Skill Focus
    skill_focus_map = {
        "software_backend": "REST APIs, database queries (SQL/NoSQL), system architecture, testing",
        "frontend": "HTML/CSS, JavaScript/TypeScript, UI frameworks, responsive design",
        "fullstack": "Both frontend and backend languages, database integration, WebSockets",
        "ai_ml_llm": "Python, PyTorch/TensorFlow, LLM APIs, data validation, prompt engineering",
        "data_analytics": "SQL, Python/R, BI tools, Excel, data visualization, reporting",
        "business_analyst": "Requirements gathering, UML, user stories, agile metrics, Jira",
        "product_project": "Agile/Scrum, product roadmap, stakeholder mapping, KPI definition",
        "fintech_payment": "Payment integration, PCI-DSS compliance, accounting principles",
        "risk_fraud_compliance": "Risk assessment, fraud detection, KYC/AML guidelines, auditing",
        "cybersecurity": "Network security, cryptography, penetration testing, SIEM tools",
        "devops_cloud": "Docker, Kubernetes, AWS/Azure/GCP, CI/CD pipelines, bash scripting",
        "corporate_applications": "CRM customization, ERP systems, integration APIs",
        "sales_operations": "Salesforce/HubSpot, sales dashboards, pipeline metrics",
    }
    suggested_skill_focus = skill_focus_map.get(job_family, "Problem solving, git, technical writing, agile cooperation")

    # 8. Application Recommendation
    if score >= 75:
        recommendation = "strong_apply"
    elif score >= 60:
        recommendation = "apply"
    elif score >= 40:
        recommendation = "apply_with_tailored_cv"
    elif score >= 20:
        recommendation = "low_match"
    else:
        recommendation = "not_recommended"

    # 9. Risk Notes
    risk_notes = []
    if seniority in ("senior", "lead_manager"):
        risk_notes.append("Do not claim senior-level leadership or architectural ownership unless supported by direct team experience in your history.")
    if job_family == "ai_ml_llm":
        risk_notes.append("Do not claim production MLOps ownership or direct LLM fine-tuning experience unless supported by actual projects in your portfolio.")
    if job_family == "cybersecurity":
        risk_notes.append("Do not claim direct security auditing or compliance ownership unless supported by verified credentials or direct past experience.")
    if job_family in ("fintech_payment", "risk_fraud_compliance"):
        risk_notes.append("Do not claim payment compliance (e.g. PCI-DSS) or fraud check ownership unless supported by past work.")
    risk_notes.append("Review the required tools list in the description and ensure you do not list technologies you cannot discuss in detail during interviews.")

    # 10. Interview Focus Areas
    interview_focus_map = {
        "software_backend": ["Backend architecture and system design", "Database query optimization and indexing", "REST API design and HTTP status codes", "Concurrency and thread safety"],
        "frontend": ["UI performance optimization", "Responsive web layout design", "State management in modern frameworks", "Component communication patterns"],
        "fullstack": ["End-to-end data flow configuration", "API integration and security", "Database schema definition", "Frontend styling and responsive UI"],
        "ai_ml_llm": ["Model training and evaluation metrics", "Data preprocessing and vector embeddings", "LLM prompt engineering and API usage", "Deep learning architectures"],
        "data_analytics": ["SQL query writing (joins, window functions)", "ETL pipeline steps and data cleansing", "Data modeling and reporting best practices", "Statistical analysis concepts"],
        "business_analyst": ["Requirement gathering techniques", "Documenting clear user stories and acceptance criteria", "Agile methodologies (Scrum/Kanban)", "Process flowcharting and mapping"],
        "product_project": ["Roadmap planning and feature prioritization", "Scrum metrics and agile lifecycle", "Risk management and resource scheduling", "Stakeholder communication"],
        "fintech_payment": ["Transaction lifecycle and gateway operations", "Ledger consistency and audits", "Payment security protocols"],
        "risk_fraud_compliance": ["KYC/AML regulation basics", "Fraud prevention patterns", "Auditing and compliance reports"],
        "cybersecurity": ["Security threat modeling", "Vulnerability scanning and patching", "Incident response planning"],
        "devops_cloud": ["CI/CD pipelines and build automation", "Infrastructure as Code (Terraform)", "Container orchestration (Kubernetes)", "Cloud security and monitoring"],
        "corporate_applications": ["ERP/CRM customization logic", "Third-party APIs integration", "Data migration strategies"],
        "sales_operations": ["Sales pipeline stages optimization", "Sales CRM administration", "Sales metrics analysis"],
    }
    interview_focus_areas = interview_focus_map.get(job_family, ["Core problem-solving paradigms", "Teamwork and agile communication", "Code quality and review best practices"])

    return {
        "job_family": job_family,
        "seniority_assessment": seniority,
        "role_summary": role_summary,
        "match_reason": match_reason,
        "candidate_strengths": strengths,
        "candidate_gaps": gaps,
        "missing_keywords": missing_kws,
        "suggested_cv_focus": suggested_cv_focus,
        "suggested_project_focus": suggested_project_focus,
        "suggested_skill_focus": suggested_skill_focus,
        "application_recommendation": recommendation,
        "risk_notes": risk_notes,
        "interview_focus_areas": interview_focus_areas,
    }


def _generate_job_intelligence_with_llm(job: dict, alert_profile: dict | None = None) -> dict:
    # Construct LLM prompt requesting structured JSON output
    prompt = (
        "You are an expert AI recruiting and job matching system. Analyze the following job details "
        "and alert profile, and return a clean JSON object containing job intelligence analysis. "
        "You must output exactly a JSON object (no markdown wrapping, no trailing text, just JSON) "
        "matching the schema below.\n\n"
        "SCHEMA JSON structure:\n"
        "{\n"
        '  "job_family": "one of: software_backend, frontend, fullstack, ai_ml_llm, data_analytics, business_analyst, product_project, fintech_payment, risk_fraud_compliance, cybersecurity, devops_cloud, corporate_applications, sales_operations, general",\n'
        '  "seniority_assessment": "one of: internship, entry_level, junior, mid, senior, lead_manager, unknown",\n'
        '  "role_summary": "Short 2-4 sentence summary of the role.",\n'
        '  "match_reason": "Practical explanation of how this job aligns with the alert profile (or general fit if no profile provided).",\n'
        '  "candidate_strengths": ["list of strings representing strengths based on keywords/filters"],\n'
        '  "candidate_gaps": ["list of strings representing gap points based on missing keywords/filters"],\n'
        '  "missing_keywords": ["list of key terms missing from description/alert overlap"],\n'
        '  "suggested_cv_focus": "What to emphasize in the CV for this specific job.",\n'
        '  "suggested_project_focus": "What categories of projects to focus on.",\n'
        '  "suggested_skill_focus": "Skills to highlight.",\n'
        '  "application_recommendation": "one of: strong_apply, apply, apply_with_tailored_cv, low_match, not_recommended",\n'
        '  "risk_notes": ["warnings about claiming experiences that may not be supported"],\n'
        '  "interview_focus_areas": ["topics/questions likely to be asked in interview"]\n'
        "}\n\n"
        f"JOB TITLE: {job.get('title')}\n"
        f"COMPANY: {job.get('company')}\n"
        f"LOCATION: {job.get('location')}\n"
        f"WORK MODEL: {job.get('work_model')}\n"
        f"SENIORITY: {job.get('seniority')}\n"
        f"JOB TYPE: {job.get('job_type')}\n"
        f"MATCH SCORE: {job.get('match_score', 0)}/100\n"
        f"MATCHED KEYWORDS: {job.get('matched_keywords', [])}\n"
        f"MISSING KEYWORDS: {job.get('missing_keywords', [])}\n"
        f"JOB DESCRIPTION:\n{job.get('description')}\n\n"
    )
    if alert_profile:
        prompt += (
            f"ALERT PROFILE CRITERIA:\n"
            f"Keywords: {alert_profile.get('keywords', [])}\n"
            f"Location: {alert_profile.get('location')}\n"
            f"Seniority: {alert_profile.get('seniority')}\n"
            f"Job Type: {alert_profile.get('job_type')}\n"
            f"Work Model: {alert_profile.get('work_model')}\n"
            f"Excluded Keywords: {alert_profile.get('excluded_keywords', [])}\n"
        )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    
    text = response.text or ""
    # Parse JSON
    # Strip potential markdown fences if returned
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    parsed = json.loads(text.strip())
    
    # Validate critical fields
    if parsed.get("job_family") not in VALID_JOB_FAMILIES:
        parsed["job_family"] = "general"
    if parsed.get("seniority_assessment") not in VALID_SENIORITIES:
        parsed["seniority_assessment"] = "unknown"
    if parsed.get("application_recommendation") not in VALID_RECOMMENDATIONS:
        parsed["application_recommendation"] = "apply"
        
    return parsed


def _normalize(value: str) -> str:
    cleaned = str(value or "").strip()
    turkish_mapped = cleaned.replace("İ", "i").replace("I", "ı")
    return re.sub(r"\s+", " ", turkish_mapped.lower()).strip()


def _clean_text(value) -> str:
    return str(value or "").strip()
