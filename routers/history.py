import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import ApplicationHistory

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


def parse_result(result: str):
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return result


@router.get("")
def get_history(
    request_type: str | None = Query(None, description="Request type to filter by"),
    db: Session = Depends(get_db)
):
    query = db.query(ApplicationHistory)
    if request_type:
        query = query.filter(ApplicationHistory.request_type == request_type)

    history_items = query.order_by(ApplicationHistory.created_at.desc()).all()

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


@router.get("/{history_id}")
def get_history_item(history_id: int, db: Session = Depends(get_db)):
    item = db.query(ApplicationHistory).filter(ApplicationHistory.id == history_id).first()
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Geçmiş kaydı bulunamadı."
        )

    return {
        "id": item.id,
        "request_type": item.request_type,
        "cv_filename": item.cv_filename,
        "result": parse_result(item.result),
        "created_at": item.created_at
    }


@router.delete("")
def clear_all_history(db: Session = Depends(get_db)):
    try:
        db.query(ApplicationHistory).delete()
        db.commit()
        return {"message": "Tüm geçmiş kayıtları başarıyla silindi."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Geçmiş temizlenirken hata oluştu: {str(e)}"
        )


@router.delete("/{history_id}")
def delete_history_item(history_id: int, db: Session = Depends(get_db)):
    item = db.query(ApplicationHistory).filter(ApplicationHistory.id == history_id).first()
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Geçmiş kaydı bulunamadı."
        )

    try:
        db.delete(item)
        db.commit()
        return {"message": f"Kayıt {history_id} başarıyla silindi."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Kayıt silinirken hata oluştu: {str(e)}"
        )