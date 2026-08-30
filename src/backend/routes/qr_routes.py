"""
Libya B2B Platform - QR Code Routes
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/qrcode", tags=["qrcode"])


@router.post("/generate")
def generate_qr(order_number: str, total_amount: float, currency: str = "LYD"):
    from qr_code import calculate_qr_code_hash, generate_order_qr_code

    qr_base64 = generate_order_qr_code(
        order_number=order_number, total_amount=total_amount, currency=currency
    )
    return {
        "order_number": order_number,
        "qr_code_base64": qr_base64,
        "hash": calculate_qr_code_hash(order_number),
    }


@router.post("/scan")
def scan_qr(qr_data: str = None, body: dict = None):
    from qr_code import parse_qr_code, validate_order_qr_code

    if body and "qr_data" in body:
        qr_data = body["qr_data"]
    if not qr_data:
        raise HTTPException(status_code=400, detail="qr_data required")

    parsed = parse_qr_code(qr_data)
    is_valid = validate_order_qr_code(parsed) if parsed.get("platform") == "LIBYA_B2B" else False
    return {"parsed_data": parsed, "is_valid": is_valid}


@router.post("/delivery-verification")
def delivery_verification(
    order_number: str,
    qr_data: str,
    photo_url: Optional[str] = None,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
):
    from datetime import datetime, timezone

    from config import SessionLocal
    from models import Escrow, EscrowHistory, Order
    from qr_code import (
        generate_delivery_qr_code,
        parse_qr_code,
        verify_delivery,
    )

    parsed = parse_qr_code(qr_data)
    delivery_qr = generate_delivery_qr_code(
        order_number=order_number,
        delivery_photo_url=photo_url,
        gps_lat=gps_lat,
        gps_lon=gps_lon,
    )
    verification = verify_delivery(qr_data=parsed, expected_order=order_number)

    # Auto-release escrow on successful delivery verification
    escrow_released = False
    if verification.get("is_valid"):
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.order_number == order_number).first()
            if order:
                escrow = (
                    db.query(Escrow)
                    .filter(Escrow.order_id == order.id, Escrow.status == "pending")
                    .first()
                )
                if escrow and escrow.amount > 0:
                    escrow.status = "released"
                    escrow.released_at = datetime.now(timezone.utc)
                    escrow.note = (
                        escrow.note or ""
                    ) + " | Auto-released after QR delivery verification"
                    db.add(
                        EscrowHistory(
                            escrow_id=escrow.id,
                            action="released",
                            old_status="pending",
                            new_status="released",
                            note="Auto-released after QR delivery verification",
                        )
                    )
                    db.commit()
                    escrow_released = True
        finally:
            db.close()

    return {
        "order_number": order_number,
        "verification": verification,
        "delivery_qr_base64": delivery_qr,
        "escrow_released": escrow_released,
    }
