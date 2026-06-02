from datetime import datetime

from pydantic import BaseModel


class HistoryResponse(BaseModel):
    id: int
    request_type: str
    cv_filename: str | None
    result: str
    created_at: datetime

    class Config:
        from_attributes = True