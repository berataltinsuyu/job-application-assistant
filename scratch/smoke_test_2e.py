import io
import os
import sys
import asyncio

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpdf import FPDF
from fastapi import UploadFile
from database import SessionLocal, Base, engine
from services.job_application_asset_service import (
    generate_job_tailored_cv,
    generate_job_cover_letter,
    generate_job_application_email,
    list_job_assets,
    get_job_asset
)
from models import MonitoredJob, JobApplicationPipeline

# 1. Create DB tables
Base.metadata.create_all(bind=engine)

def create_mock_cv_pdf() -> UploadFile:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.cell(200, 10, text="John Doe CV", ln=1, align="C")
    pdf.cell(200, 10, text="Email: john.doe@example.com", ln=1, align="L")
    pdf.cell(200, 10, text="Phone: +90 555 555 55 55", ln=1, align="L")
    pdf.cell(200, 10, text="LinkedIn: linkedin.com/in/johndoe", ln=1, align="L")
    pdf.cell(200, 10, text="Experience: Software Engineer at Acme Corp (2020-2025)", ln=1, align="L")
    pdf.cell(200, 10, text="Built backend APIs with Python, Django, and FastAPI", ln=1, align="L")
    
    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    
    file_like = io.BytesIO(pdf_bytes)
    from starlette.datastructures import Headers
    headers = Headers({"content-type": "application/pdf"})
    return UploadFile(filename="john_doe_cv.pdf", file=file_like, headers=headers)

async def test_assets():
    db = SessionLocal()
    
    # Get or create a monitored job
    job = db.query(MonitoredJob).first()
    if not job:
        print("Creating mock job...")
        job = MonitoredJob(
            source="manual_import",
            source_job_id="test_smoke_2e",
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
    cv_file = create_mock_cv_pdf()
    
    # 2. Test Tailored CV Generation
    print("\n2. Testing Tailored CV Generation...")
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
    print("Success! Asset ID:", res_cv["asset"]["id"])
    print("Export format:", res_cv["asset"]["export_format"])
    print("File path:", res_cv["asset"]["file_path"])

    # Reset file pointer for next generator calls
    cv_file.file.seek(0)
    
    # 3. Test Cover Letter Generation
    print("\n3. Testing Cover Letter Generation...")
    res_cover = await generate_job_cover_letter(
        db=db,
        job_id=job.id,
        cv_file=cv_file,
        language="English",
        tone="professional"
    )
    print("Success! Asset ID:", res_cover["asset"]["id"])
    print("File path:", res_cover["asset"]["file_path"])

    # Reset file pointer
    cv_file.file.seek(0)

    # 4. Test Application Email Generation
    print("\n4. Testing Application Email Generation...")
    res_email = await generate_job_application_email(
        db=db,
        job_id=job.id,
        cv_file=cv_file,
        language="English",
        tone="concise"
    )
    print("Success! Asset ID:", res_email["asset"]["id"])
    print("File path:", res_email["asset"]["file_path"])
    
    # 5. Test Listing and Retrieval
    print("\n5. Testing listing and retrieving assets...")
    all_assets = list_job_assets(db, job.id)
    print(f"Found {len(all_assets)} assets in database for job_id={job.id}")
    
    single_asset = get_job_asset(db, res_cv["asset"]["id"])
    print("Retrieved asset title:", single_asset["title"])

    # 6. Verify pipeline materials status updates
    pipeline = db.query(JobApplicationPipeline).filter(JobApplicationPipeline.job_id == job.id).first()
    print("\n6. Verifying pipeline materials status updates...")
    print("Pipeline Materials Status:", pipeline.application_materials_status)
    assert pipeline.application_materials_status == "ready", "Pipeline status should be 'ready' since CV and cover letter/email are generated!"
    print("Assert Passed: status is 'ready'")

    print("\nAll Phase 2E backend service smoke tests passed successfully!")
    db.close()

if __name__ == "__main__":
    asyncio.run(test_assets())
