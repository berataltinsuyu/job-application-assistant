import json
import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="💼",
    layout="wide"
)

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

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
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
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

# Initialize Session State
if "global_job_text" not in st.session_state:
    st.session_state.global_job_text = ""

# Sidebar Global Inputs
st.sidebar.image("https://img.icons8.com/clouds/200/000000/resume.png", width=90)
st.sidebar.title("AI Job Assistant")

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Global Uploads")

global_cv = st.sidebar.file_uploader(
    "Upload CV (PDF/DOCX)",
    type=["pdf", "docx"],
    key="global_cv"
)

global_job_desc = st.sidebar.text_area(
    "Job Description",
    value=st.session_state.global_job_text,
    height=160,
    key="global_job_desc_input"
)
# Sync to state
st.session_state.global_job_text = global_job_desc

global_language = st.sidebar.selectbox(
    "Output Language",
    ["Turkish", "English"],
    key="global_language"
)

st.sidebar.markdown("---")

# Navigation Menu
page = st.sidebar.radio(
    "Navigate Features",
    [
        "📊 Dashboard",
        "🔗 Job URL Extractor",
        "🔍 CV Analysis",
        "🎯 ATS Score",
        "🔑 Job Keywords",
        "💡 CV Improvement",
        "📝 Tailored CV",
        "✍️ Rewrite CV Section",
        "✉️ Cover Letter",
        "📧 Application Email",
        "🤝 Interview Prep",
        "🎯 Personalized Interview",
        "📜 History"
    ]
)

# Helper function to get files dict for requests
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

# Validations
def validate_inputs(require_cv=True, require_job=True):
    if require_cv and global_cv is None:
        st.warning("⚠️ Please upload your CV in the sidebar.")
        return False
    if require_job and not st.session_state.global_job_text.strip():
        st.warning("⚠️ Please provide a job description in the sidebar (or use Job URL Extractor).")
        return False
    return True

# --- Pages ---

if page == "📊 Dashboard":
    st.markdown('<div class="dashboard-banner"><h1>📊 Assistant Dashboard</h1><p>Analyze matches, scores, and manage application activities in one place.</p></div>', unsafe_allow_html=True)
    
    # Fetch History to populate dashboard stats
    try:
        response = requests.get(f"{API_BASE_URL}/history")
        if response.status_code == 200:
            history_data = response.json()
        else:
            history_data = []
    except Exception:
        history_data = []

    total_history = len(history_data)
    
    # Extract statistics
    latest_ats_score = "N/A"
    latest_match_score = "N/A"
    
    for item in history_data:
        req_type = item.get("request_type")
        res = item.get("result")
        
        if req_type == "ats_score" and latest_ats_score == "N/A" and isinstance(res, dict):
            latest_ats_score = f"{res.get('ats_score', 'N/A')}%"
        elif req_type == "analyze" and latest_match_score == "N/A" and isinstance(res, dict):
            latest_match_score = f"{res.get('match_score', 'N/A')}%"

    # Layout Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><h3 style="margin:0;">Total Operations</h3><h1 style="color:#6366F1;margin:5px 0 0 0;">{total_history}</h1></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3 style="margin:0;">Latest Match Score</h3><h1 style="color:#10B981;margin:5px 0 0 0;">{latest_match_score}</h1></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3 style="margin:0;">Latest ATS Score</h3><h1 style="color:#06B6D4;margin:5px 0 0 0;">{latest_ats_score}</h1></div>', unsafe_allow_html=True)

    st.markdown("### 🚀 Features Overview")
    
    col_feat1, col_feat2 = st.columns(2)
    with col_feat1:
        st.info("**🔍 CV-Job Matcher & ATS scoring**\n\nUpload your CV and paste the job posting to analyze compatibility, keywords and ATS formatting compliance.")
        st.success("**📝 Content Generators**\n\nCreate tailored resumes, rewrite sections, build emails/LinkedIn requests and draft cover letters.")
    with col_feat2:
        st.warning("**🔗 URL Extractor**\n\nPaste URLs of postings to scrape details automatically instead of copying manually.")
        st.help("**🤝 Tailored Interview Coach**\n\nGenerate realistic QA preps matching difficulty and based specifically on your CV weaknesses.")

    st.markdown("### ⏱️ Recent History Highlights")
    if history_data:
        for idx, item in enumerate(history_data[:5]):
            st.markdown(f"**#{item['id']}** - **{item['request_type'].upper()}** | 📅 {item['created_at'].split('T')[0]} | 📂 File: {item.get('cv_filename') or 'None'}")
    else:
        st.info("No operations found in history. Start analyzing your first application using the side menu!")


elif page == "🔗 Job URL Extractor":
    st.header("🔗 Job Description Extractor from URL")
    st.write("Extract detailed job listings automatically from public links (including LinkedIn, tech boards, and general sites).")

    job_url = st.text_input("Enter Job Posting URL:", placeholder="https://...")

    if st.button("Extract Job Details"):
        if not job_url.strip():
            st.warning("Please provide a valid URL.")
        else:
            with st.spinner("Fetching and parsing job page..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/extract-job-description",
                        json={"job_url": job_url}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            st.success("Details extracted successfully!")
                            extracted_text = result.get("extracted_text", "")
                            
                            st.text_area("Extracted Text:", value=extracted_text, height=300)
                            
                            if st.button("Set as Active Job Description"):
                                st.session_state.global_job_text = extracted_text
                                st.success("Job description saved! You can view it on the sidebar now.")
                                st.rerun()
                        else:
                            st.error(result.get("message"))
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")


elif page == "🔍 CV Analysis":
    st.header("🔍 CV Analysis")
    st.write("Compare the active CV against the job description for mapping fit, strengths, and application strategic advice.")

    if validate_inputs():
        if st.button("Analyze Match"):
            with st.spinner("Analyzing CV and Job compatibility..."):
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
                        
                        st.success("Analysis complete!")
                        st.metric("Fit Score", f"{result.get('match_score', 'N/A')}%")
                        
                        st.subheader("Summary")
                        st.write(result.get("summary", ""))

                        st.subheader("Strengths")
                        for item in result.get("strengths", []):
                            st.write(f"✅ {item}")

                        st.subheader("Weaknesses & Skill Gaps")
                        for item in result.get("weaknesses", []):
                            st.write(f"⚠️ {item}")

                        st.subheader("CV Improvements")
                        for item in result.get("cv_improvements", []):
                            st.write(f"💡 {item}")

                        st.subheader("Application Strategy")
                        st.write(result.get("application_strategy", ""))

                        st.subheader("Final Recommendation")
                        st.write(result.get("final_recommendation", ""))
                        
                        # Download Button
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Analysis Report",
                            data=json_data,
                            file_name="cv_analysis.json",
                            mime="application/json"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "🎯 ATS Score":
    st.header("🎯 ATS Compatibility Score")
    st.write("Evaluate your CV format, keywords matching, and compliance warnings with Applicant Tracking Systems.")

    if validate_inputs():
        if st.button("Calculate ATS Score"):
            with st.spinner("Running ATS scanner..."):
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
                        
                        st.success("ATS check done!")
                        st.metric("ATS Score", f"{result.get('ats_score', 0)}%")
                        
                        st.subheader("Matched Keywords")
                        st.write(", ".join(result.get("matched_keywords", [])))
                        
                        st.subheader("Missing Keywords")
                        for kw in result.get("missing_keywords", []):
                            st.markdown(f"- ❌ {kw}")
                            
                        st.subheader("Keyword Recommendations")
                        for rec in result.get("keyword_recommendations", []):
                            st.markdown(f"- 💡 {rec}")
                            
                        st.subheader("Formatting Warnings")
                        for warn in result.get("format_warnings", []):
                            st.markdown(f"- ⚠️ {warn}")
                            
                        st.subheader("Summary")
                        st.write(result.get("summary", ""))
                        
                        # Download button
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON ATS Report",
                            data=json_data,
                            file_name="ats_report.json",
                            mime="application/json"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "🔑 Job Keywords":
    st.header("🔑 Job Keyword Extraction")
    st.write("Extract core technical keywords, must-have skills, soft skills, and summaries from the job description.")

    if validate_inputs(require_cv=False):
        if st.button("Extract Job Keywords"):
            with st.spinner("Processing job description..."):
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
                        
                        st.success("Keywords extracted successfully!")
                        st.subheader(f"Role: {result.get('role_title', 'N/A')} ({result.get('experience_level', 'N/A')})")
                        st.write(result.get("role_summary", ""))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### Must-Have Skills")
                            for skill in result.get("must_have_skills", []):
                                st.write(f"- 🎯 {skill}")
                                
                            st.markdown("### Nice-to-Have Skills")
                            for skill in result.get("nice_to_have_skills", []):
                                st.write(f"- ⭐ {skill}")
                        
                        with col2:
                            st.markdown("### Technical Keywords")
                            st.write(", ".join(result.get("technical_keywords", [])))
                            
                            st.markdown("### Soft Skills")
                            st.write(", ".join(result.get("soft_skills", [])))
                        
                        st.subheader("Responsibilities")
                        for resp in result.get("responsibilities", []):
                            st.write(f"- {resp}")
                            
                        # Download button
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Keyword Report",
                            data=json_data,
                            file_name="job_keywords.json",
                            mime="application/json"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "💡 CV Improvement":
    st.header("💡 CV Improvement Assistant")
    st.write("Suggest specific improvements to CV sections without inventing experience.")

    if validate_inputs():
        if st.button("Generate Improvement Suggestions"):
            with st.spinner("Analyzing CV sections..."):
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
                        
                        st.success("CV improvements suggestions ready!")
                        st.subheader("Overall Feedback")
                        st.write(result.get("overall_feedback", ""))
                        
                        st.subheader("Priority Actions")
                        for act in result.get("priority_actions", []):
                            st.markdown(f"🔥 **{act}**")
                            
                        st.subheader("Missing Sections")
                        for sec in result.get("missing_sections", []):
                            st.markdown(f"- ❌ {sec}")
                            
                        st.subheader("Skills Section Suggestions")
                        for sug in result.get("skills_section_suggestions", []):
                            st.markdown(f"- {sug}")
                            
                        st.subheader("Project Section Suggestions")
                        for sug in result.get("project_section_suggestions", []):
                            st.markdown(f"- {sug}")
                            
                        st.subheader("Experience Section Suggestions")
                        for sug in result.get("experience_section_suggestions", []):
                            st.markdown(f"- {sug}")
                            
                        # Download
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Improvement Report",
                            data=json_data,
                            file_name="cv_improvements.json",
                            mime="application/json"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "📝 Tailored CV":
    st.header("📝 Tailored CV Draft Generator")
    st.write("Rephrase and prioritize your existing CV details to fit the job requirements. (No fake information).")

    if validate_inputs():
        if st.button("Generate Tailored Draft"):
            with st.spinner("Drafting tailored CV layout..."):
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
                        
                        st.success("Draft generated successfully!")
                        st.subheader("Tailored Profile Summary")
                        st.write(result.get("profile_summary", ""))
                        
                        st.subheader("Tailored Skills List")
                        st.write(", ".join(result.get("skills", [])))
                        
                        st.subheader("Tailored Projects Highlight")
                        for prj in result.get("projects", []):
                            st.markdown(f"**{prj.get('name')}**")
                            st.write(prj.get("description"))
                            st.write("---")
                            
                        st.subheader("Tailored Experience Bulletpoints")
                        for bullet in result.get("experience_bullets", []):
                            st.write(f"- {bullet}")
                            
                        st.subheader("Education Section")
                        st.write(result.get("education_section", ""))
                        
                        if result.get("warnings"):
                            st.warning("⚠️ Warnings/Missing Facts: " + ", ".join(result.get("warnings", [])))
                        
                        # Generate txt content
                        txt_cv = f"=== TAILORED CV DRAFT ===\n\n"
                        txt_cv += f"SUMMARY:\n{result.get('profile_summary','')}\n\n"
                        txt_cv += f"SKILLS:\n{', '.join(result.get('skills',[]))}\n\n"
                        txt_cv += f"PROJECTS:\n"
                        for p in result.get('projects',[]):
                            txt_cv += f"- {p.get('name')}: {p.get('description')}\n"
                        txt_cv += f"\nEXPERIENCE BULLETS:\n"
                        for b in result.get('experience_bullets',[]):
                            txt_cv += f"- {b}\n"
                        txt_cv += f"\nEDUCATION:\n{result.get('education_section','')}\n"
                        
                        # Download buttons
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Draft",
                            data=json_data,
                            file_name="tailored_cv.json",
                            mime="application/json"
                        )
                        st.download_button(
                            label="📥 Download Text-Formatted Draft (.txt)",
                            data=txt_cv,
                            file_name="tailored_cv.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "✍️ Rewrite CV Section":
    st.header("✍️ CV Section Rewriter")
    st.write("Rewrite specific parts of your CV with customized tone, keeping details strictly authentic.")

    sec_type = st.selectbox("Select CV section to rewrite:", ["summary", "skills", "projects", "experience"])
    rewrite_tone = st.selectbox("Select tone:", ["professional", "confident", "concise"])

    if validate_inputs():
        if st.button("Rewrite CV Section"):
            with st.spinner("Rewriting section..."):
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
                        
                        st.success("Section rewritten!")
                        st.subheader(f"Rewritten {result.get('section_type').upper()} ({rewrite_tone.title()})")
                        st.text_area("Content:", value=result.get("rewritten_content"), height=250)
                        
                        st.subheader("AI Rationale / Explanation")
                        st.info(result.get("explanation", ""))
                        
                        # Download buttons
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Rewritten Section",
                            data=json_data,
                            file_name="rewritten_section.json",
                            mime="application/json"
                        )
                        st.download_button(
                            label="📥 Download Text Content (.txt)",
                            data=result.get("rewritten_content"),
                            file_name="rewritten_section.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "✉️ Cover Letter":
    st.header("✉️ Cover Letter Generator")
    st.write("Create a customized cover letter matching your experience to the job requirements.")

    cl_tone = st.selectbox("Select Letter Tone:", ["professional", "friendly", "confident", "formal", "short"])

    if validate_inputs():
        if st.button("Generate Cover Letter"):
            with st.spinner("Writing cover letter..."):
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
                        
                        st.success("Cover letter generated!")
                        st.text_area("Generated Cover Letter", value=result, height=350)
                        
                        st.download_button(
                            label="📥 Download Cover Letter (.txt)",
                            data=result,
                            file_name="cover_letter.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "📧 Application Email":
    st.header("📧 Application Email Generator")
    st.write("Generate outreach templates, including cold application emails, follow-ups, and LinkedIn connection notes.")

    comp_name = st.text_input("Company Name (Optional):", placeholder="e.g. Acme Corp")
    pos_title = st.text_input("Position Title (Optional):", placeholder="e.g. Backend Developer")
    email_tone = st.selectbox("Select Tone:", ["professional", "friendly", "concise"])

    if validate_inputs():
        if st.button("Generate Templates"):
            with st.spinner("Drafting emails..."):
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
                        
                        st.success("Email templates generated!")
                        
                        st.subheader(f"Email Subject: {result.get('subject')}")
                        st.text_area("Main Application Email:", value=result.get("email_body"), height=250)
                        
                        st.subheader("Short LinkedIn Message:")
                        st.text_area("LinkedIn Message:", value=result.get("short_linkedin_message"), height=120)
                        
                        st.subheader("Follow-up Email Template:")
                        st.text_area("Follow-up Email:", value=result.get("follow_up_message"), height=180)
                        
                        # Txt templates package
                        outreach_txt = f"=== APPLICATION EMAIL ===\nSubject: {result.get('subject')}\n\n{result.get('email_body')}\n\n"
                        outreach_txt += f"=== LINKEDIN MESSAGE ===\n{result.get('short_linkedin_message')}\n\n"
                        outreach_txt += f"=== FOLLOW-UP EMAIL ===\n{result.get('follow_up_message')}\n"
                        
                        # Download buttons
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Email Templates",
                            data=json_data,
                            file_name="email_templates.json",
                            mime="application/json"
                        )
                        st.download_button(
                            label="📥 Download Outreach Text Pack (.txt)",
                            data=outreach_txt,
                            file_name="outreach_pack.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "🤝 Interview Prep":
    st.header("🤝 General Interview Prep")
    st.write("Generate general role-based technical questions and HR questions from job listing keywords.")

    if validate_inputs(require_cv=False):
        if st.button("Generate Prep Guide"):
            with st.spinner("Generating interview QA..."):
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
                        
                        st.success("Prep questions generated!")
                        
                        st.subheader("Technical Questions")
                        for idx, item in enumerate(result.get("technical_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader("HR / Behavioral Questions")
                        for idx, item in enumerate(result.get("hr_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()

                        st.subheader("Zorlayıcı / Challenging Questions")
                        for idx, item in enumerate(result.get("challenging_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader("Preparation Tips")
                        for tip in result.get("preparation_tips", []):
                            st.write(f"- {tip}")
                            
                        # Download button
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Prep Report",
                            data=json_data,
                            file_name="general_interview_prep.json",
                            mime="application/json"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "🎯 Personalized Interview":
    st.header("🎯 Personalized CV-Based Interview Prep")
    st.write("Generate unique mock interview questions specifically tailored to your CV's weak areas and experience details.")

    prep_diff = st.selectbox("Select Difficulty Level:", ["easy", "medium", "hard"])

    if validate_inputs():
        if st.button("Generate Custom QA"):
            with st.spinner("Analyzing CV alignment and generating questions..."):
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
                        
                        st.success("Personalized prep is ready!")
                        
                        st.subheader("Technical Questions")
                        for idx, item in enumerate(result.get("technical_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader("CV-Specific Questions")
                        for idx, item in enumerate(result.get("cv_based_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()

                        st.subheader("Weak Area & Stress Testing Questions")
                        for idx, item in enumerate(result.get("weak_area_questions", [])):
                            st.markdown(f"**Q{idx+1}: {item.get('question')}**")
                            st.write(f"💡 Hint: {item.get('answer_hint')}")
                            st.divider()
                            
                        st.subheader("Sample Complete Responses")
                        for sa in result.get("sample_answers", []):
                            st.markdown(f"**Q: {sa.get('question')}**")
                            st.write(f"💬 Sample Answer: {sa.get('sample_answer')}")
                            st.divider()

                        st.subheader("Preparation Step-by-Step Plan")
                        for step in result.get("preparation_plan", []):
                            st.write(f"- 📋 {step}")
                            
                        # Download button
                        json_data = json.dumps(result, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download JSON Prep Report",
                            data=json_data,
                            file_name="personalized_interview_prep.json",
                            mime="application/json"
                        )
                    else:
                        st.error(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


elif page == "📜 History":
    st.header("📜 Operation History")
    st.write("Browse, filter, review, and delete records of past evaluations and drafts.")

    # Refresh items
    history_items = []
    
    st.subheader("Filter and Clean History")
    filter_type = st.selectbox(
        "Filter by operation type:",
        ["all", "analyze", "cover_letter", "interview", "ats_score", "job_keywords", "cv_improvement", "tailored_cv", "cv_rewrite", "application_email", "personalized_interview"]
    )
    
    # Refresh/Clear Buttons
    col_a, col_b = st.columns([1, 4])
    with col_a:
        refresh = st.button("Refresh List")
    with col_b:
        confirm_clear = st.checkbox("I want to delete ALL records")
        if confirm_clear:
            if st.button("⚠️ Clear Entire History Now"):
                try:
                    res = requests.delete(f"{API_BASE_URL}/history")
                    if res.status_code == 200:
                        st.success("All history deleted successfully.")
                        st.rerun()
                    else:
                        st.error(res.text)
                except Exception as e:
                    st.error(str(e))

    # Fetch History
    try:
        url = f"{API_BASE_URL}/history"
        if filter_type != "all":
            url += f"?request_type={filter_type}"
            
        response = requests.get(url)
        if response.status_code == 200:
            history_items = response.json()
        else:
            st.error(response.text)
    except Exception as e:
        st.error(f"Failed to fetch history: {str(e)}")

    st.markdown("---")
    
    if not history_items:
        st.info("No records found for this selection.")
    else:
        for item in history_items:
            with st.expander(
                f"ID #{item['id']} - [{item['request_type'].upper()}] - {item['created_at'].split('T')[0]} {item['created_at'].split('T')[1][:5]}"
            ):
                st.write(f"**CV Filename:** {item.get('cv_filename') or 'N/A'}")
                st.write("**Job Description Excerpt:**")
                st.text(item.get("job_text")[:200] + "..." if item.get("job_text") else "N/A")
                
                st.write("**Generated Output:**")
                st.json(item.get("result")) if isinstance(item.get("result"), dict) else st.write(item.get("result"))
                
                # Delete Single Record Button
                if st.button(f"🗑️ Delete Record #{item['id']}", key=f"del_{item['id']}"):
                    try:
                        res = requests.delete(f"{API_BASE_URL}/history/{item['id']}")
                        if res.status_code == 200:
                            st.success(f"Record #{item['id']} deleted.")
                            st.rerun()
                        else:
                            st.error(res.text)
                    except Exception as e:
                        st.error(str(e))