from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class ApplicationHistory(Base):
    __tablename__ = "application_history"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String(50), nullable=False)
    cv_filename = Column(String(255), nullable=True)
    job_text = Column(Text, nullable=True)
    result = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)