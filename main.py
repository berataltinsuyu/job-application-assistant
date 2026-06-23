from fastapi import FastAPI

from routers import (
    analyze,
    cover_letter,
    interview,
    history,
    job_description,
    ats,
    job_keywords,
    cv_improvement,
    tailored_cv,
    cv_rewrite,
    application_email,
    personalized_interview,
    job_recommendations,
    ats_cv_builder
)
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Application Assistant API",
    description="CV dosyası ve iş ilanı analizi yapan yapay zeka destekli başvuru asistanı.",
    version="1.0.0"
)

app.include_router(analyze.router)
app.include_router(cover_letter.router)
app.include_router(interview.router)
app.include_router(history.router)
app.include_router(job_description.router)
app.include_router(ats.router)
app.include_router(job_keywords.router)
app.include_router(cv_improvement.router)
app.include_router(tailored_cv.router)
app.include_router(cv_rewrite.router)
app.include_router(application_email.router)
app.include_router(personalized_interview.router)
app.include_router(job_recommendations.router)
app.include_router(ats_cv_builder.router, prefix="/ats-cv", tags=["ATS CV Builder"])


@app.get("/")
def root():
    return {
        "message": "Job Application Assistant API çalışıyor."
    }
