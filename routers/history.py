from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory
from schemas import HistoryResponse

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


@router.get("", response_model=list[HistoryResponse])
def get_history(db: Session = Depends(get_db)):
    history_items = (
        db.query(ApplicationHistory)
        .order_by(ApplicationHistory.created_at.desc())
        .all()
    )

    return history_items