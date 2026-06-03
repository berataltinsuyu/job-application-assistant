from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HistoryResponse(BaseModel):
    id: int
    request_type: str
    cv_filename: str | None
    result: Any
    created_at: datetime

    class Config:
        from_attributes = True