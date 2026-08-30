"""
Libya B2B Platform - RFQ Routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from models import RFQ, RFQCreate, RFQResponse, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/b2b/rfq", tags=["rfq"])


@router.post("", response_model=RFQResponse)
def create_rfq(
    rfq: RFQCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    db_rfq = RFQ(**rfq.model_dump())
    db.add(db_rfq)
    db.commit()
    db.refresh(db_rfq)
    return db_rfq


@router.get("")
def list_rfqs(
    status: Optional[str] = None,
    buyer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(RFQ)
    if status and status != "all":
        query = query.filter(RFQ.status == status)
    if buyer_id:
        query = query.filter(RFQ.buyer_id == buyer_id)
    query = query.order_by(RFQ.created_at.desc())
    rfqs = query.offset(skip).limit(limit).all()
    total = query.count()

    return {
        "rfqs": [
            {
                "id": r.id,
                "buyer_id": r.buyer_id,
                "product_name": r.product_name,
                "product_name_arabic": r.product_name_arabic,
                "quantity": r.quantity,
                "delivery_address": r.delivery_address,
                "message": r.message,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rfqs
        ],
        "total": total,
    }


@router.get("/{rfq_id}")
def get_rfq(rfq_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return {
        "id": rfq.id,
        "buyer_id": rfq.buyer_id,
        "product_name": rfq.product_name,
        "product_name_arabic": rfq.product_name_arabic,
        "quantity": rfq.quantity,
        "delivery_address": rfq.delivery_address,
        "message": rfq.message,
        "status": rfq.status,
        "created_at": rfq.created_at.isoformat() if rfq.created_at else None,
    }


@router.put("/{rfq_id}")
def update_rfq_status(
    rfq_id: int, status: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    rfq.status = status
    db.commit()
    return {"id": rfq.id, "status": rfq.status}
