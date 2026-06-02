from fastapi import FastAPI

from routers import analyze, cover_letter, interview, history
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


@app.get("/")
def root():
    return {
        "message": "Job Application Assistant API çalışıyor."
    }