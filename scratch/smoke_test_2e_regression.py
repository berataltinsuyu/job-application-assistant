import io
import os
import sys
import asyncio
from fpdf import FPDF
from fastapi import UploadFile

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Base, engine
from services.job_application_asset_service import generate_job_tailored_cv
from models import MonitoredJob

# 1. Create DB tables
Base.metadata.create_all(bind=engine)

def create_rich_mock_cv_pdf() -> UploadFile:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    # Contact info block
    pdf.cell(200, 10, text="BERAT ALTINSUYU", ln=1, align="C")
    pdf.cell(200, 10, text="Email: berat.altinsuyu@example.com", ln=1, align="L")
    pdf.cell(200, 10, text="Phone: +90 555 555 55 55", ln=1, align="L")
    pdf.cell(200, 10, text="LinkedIn: https://linkedin.com/in/berataltinsuyu", ln=1, align="L")
    pdf.cell(200, 10, text="GitHub: https://github.com/berataltinsuyu", ln=1, align="L")
    
    # Education block
    pdf.cell(200, 10, text="Education: BS in Computer Engineering, Middle East Technical University", ln=1, align="L")
    
    # Experience block
    pdf.cell(200, 10, text="Experience: Software Engineer at Global Tech Solutions (2020-2025)", ln=1, align="L")
    pdf.cell(200, 10, text="Built high-performance backend APIs using Python and FastAPI", ln=1, align="L")
    
    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    
    file_like = io.BytesIO(pdf_bytes)
    from starlette.datastructures import Headers
    headers = Headers({"content-type": "application/pdf"})
    return UploadFile(filename="rich_mock_cv.pdf", file=file_like, headers=headers)

async def test_cv_regression():
    db = SessionLocal()
    
    # Get or create a monitored job
    job = db.query(MonitoredJob).first()
    if not job:
        print("Creating mock job...")
        job = MonitoredJob(
            source="manual_import",
            source_job_id="test_smoke_2e_regression",
            title="Senior Python Backend Developer",
            company="Global Tech Solutions",
            location="Istanbul / Remote",
            work_model="remote",
            seniority="senior",
            job_type="full_time",
            description="We are looking for a Senior Python Developer with experience in FastAPI and microservices.",
            status="new",
            match_score=85
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
    print(f"Test job ID: {job.id}, Title: {job.title}")

    # Create mock upload CV
    cv_file = create_rich_mock_cv_pdf()
    
    # Test Tailored CV Generation
    print("\nGenerating Tailored CV with dynamic locked fields and proper noun protection...")
    res_cv = await generate_job_tailored_cv(
        db=db,
        job_id=job.id,
        cv_file=cv_file,
        template_id="classic_ats",
        language="English",
        output_format="pdf",
        one_page=False,
        enabled_sections=None
    )
    
    asset = res_cv["asset"]
    ats_cv = asset["structured_json"]
    content_text = asset["content_text"]
    
    print("\nGenerated CV Contact Details:")
    print("Full Name:", ats_cv.get("contact", {}).get("full_name"))
    print("Email:", ats_cv.get("contact", {}).get("email"))
    print("Phone:", ats_cv.get("contact", {}).get("phone"))
    print("LinkedIn:", ats_cv.get("contact", {}).get("linkedin"))
    print("GitHub:", ats_cv.get("contact", {}).get("github"))
    
    print("\nVerifying Name Character-spacing Regression:")
    name = ats_cv.get("contact", {}).get("full_name", "")
    assert "B E R A T" not in name, "Name must not contain character spacing!"
    assert name.strip() == "BERAT ALTINSUYU", f"Name must be exactly BERAT ALTINSUYU, got: {name}"
    print("Name verification passed successfully!")
    
    print("\nVerifying LinkedIn / GitHub Username Preservation:")
    linkedin = ats_cv.get("contact", {}).get("linkedin", "")
    github = ats_cv.get("contact", {}).get("github", "")
    assert "berataltinsuyu" in linkedin, f"LinkedIn must contain username berataltinsuyu, got: {linkedin}"
    assert "berataltinsuyu" in github, f"GitHub must contain username berataltinsuyu, got: {github}"
    print("LinkedIn/GitHub verification passed successfully!")
    
    print("\nVerifying Phone digits structure:")
    phone = ats_cv.get("contact", {}).get("phone", "")
    assert "5 5 5" not in phone, "Phone must not have split/isolated digits"
    print("Phone verification passed successfully!")
    
    print("\nVerifying Proper Nouns (School Name):")
    schools = [edu.get("school", "") for edu in ats_cv.get("education", [])]
    print("Schools in tailored CV:", schools)
    assert any("Middle East Technical University" in s for s in schools), "School name must be preserved!"
    print("School name verification passed successfully!")

    print("\nAll regression checks passed! Phase 2E tailored CV contact behavior is 100% correct.")
    db.close()

if __name__ == "__main__":
    asyncio.run(test_cv_regression())
