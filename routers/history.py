import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


@router.get("")
def get_history(db: Session = Depends(get_db)):
    history_items = (
        db.query(ApplicationHistory)
        .order_by(ApplicationHistory.created_at.desc())
        .all()
    )

    response = []

    for item in history_items:
        response.append({
            "id": item.id,
            "request_type": item.request_type,
            "cv_filename": item.cv_filename,
            "result": parse_result(item.result),
            "created_at": item.created_at
        })

    return response


def parse_result(result: str):
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return result