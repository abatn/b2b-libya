"""
Libya B2B Platform - Order Routes
Order creation, listing, and delivery confirmation.
"""

import random
import string
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from models import (
    Escrow,
    Order,
    OrderCreate,
    OrderItem,
    OrderResponse,
    Product,
    User,
)
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _generate_order_number():
    return f"LYB-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=6))}"


@router.post("", response_model=OrderResponse)
def create_order(
    order: OrderCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    order_number = _generate_order_number()
    # Exclude items (Pydantic list) — not an Order column
    order_data = order.model_dump(exclude={"items"}, exclude_unset=True)
    db_order = Order(order_number=order_number, **order_data)
    db.add(db_order)
    db.flush()  # get order.id

    # Create line items if provided
    if order.items:
        for item in order.items:
            # Look up product name
            product = db.query(Product).filter(Product.id == item.product_id).first()
            db_item = OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                supplier_id=item.supplier_id,
                product_name=product.name if product else None,
                quantity=item.quantity,
                unit_price=item.unit_price,
                moq=item.moq,
                moq_met=item.quantity >= item.moq,
            )
            db.add(db_item)
        db.flush()

    # Auto-create escrow for non-COD orders (Alibaba Trade Assurance style)
    existing_escrow = db.query(Escrow).filter(Escrow.order_id == db_order.id).first()
    if not existing_escrow and db_order.total_amount > 0 and db_order.payment_method != "COD":
        escrow = Escrow(
            order_id=db_order.id,
            buyer_id=db_order.buyer_id or user.id,
            supplier_id=db_order.seller_id or user.id,
            amount=db_order.total_amount,
            currency=db_order.currency or "LYD",
            status="pending",
            note="Auto-created with order",
        )
        db.add(escrow)
        db.flush()
        from routes.escrow import _log_history

        _log_history(
            db,
            escrow.id,
            "created",
            None,
            "pending",
            performed_by=user.id,
            note="Auto-created with order",
        )

    db.commit()
    db.refresh(db_order)

    # C1: Auto-create pending shipment for the order
    try:
        from models import Shipment

        shipment = Shipment(
            order_id=db_order.id,
            carrier="local",
            status="pending",
            origin_city="Tripoli",
            destination_city=db_order.delivery_address or "Tripoli",
        )
        db.add(shipment)
        db.commit()
    except Exception:
        pass  # Don't fail order creation if shipment fails

    # Notify supplier of new order
    try:
        from routes.notifications import send_order_notification

        if db_order.seller_id:
            send_order_notification(db_order.seller_id, db_order.id, "confirmed")
    except Exception:
        pass

    return db_order


@router.get("", response_model=List[OrderResponse])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Order).offset(skip).limit(limit).all()


@router.get("/{order_number}")
def get_order_by_number(order_number: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": order.id,
        "order_number": order.order_number,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "payment_method": order.payment_method,
        "status": order.status,
        "buyer_id": order.buyer_id,
        "seller_id": order.seller_id,
        "delivery_address": order.delivery_address,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "delivery_timestamp": order.delivery_timestamp.isoformat()
        if order.delivery_timestamp
        else None,
    }


@router.put("/{order_id}/deliver")
def confirm_delivery(
    order_id: int,
    photo_url: Optional[str] = None,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "delivered"
    order.delivery_photo = photo_url
    order.delivery_gps_lat = gps_lat
    order.delivery_gps_lon = gps_lon
    order.delivery_timestamp = datetime.now(timezone.utc)
    db.commit()

    # Send push notification to buyer
    try:
        from routes.notifications import send_order_notification

        if order.buyer_id:
            send_order_notification(order.buyer_id, order.id, "delivered")
    except Exception:
        pass  # Don't fail the delivery if notification fails

    return {"message": "Delivery confirmed", "order_number": order.order_number}


@router.put("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ("pending", "confirmed"):
        raise HTTPException(
            status_code=400, detail=f"Cannot cancel order in '{order.status}' status"
        )
    order.status = "cancelled"
    db.commit()

    # Notify both buyer and supplier
    try:
        from routes.notifications import send_order_notification

        if order.buyer_id:
            send_order_notification(order.buyer_id, order.id, "cancelled")
        if order.seller_id:
            send_order_notification(order.seller_id, order.id, "cancelled")
    except Exception:
        pass

    return {"message": "Order cancelled", "order_number": order.order_number}
