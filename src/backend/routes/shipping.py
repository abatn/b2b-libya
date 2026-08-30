"""
Libya B2B Platform - Shipping Routes
Carrier integration, rate calculation, shipment tracking.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from models import (
    Order,
    Shipment,
    ShipmentCreate,
    ShipmentEvent,
    ShipmentEventResponse,
    ShipmentResponse,
    ShippingRate,
    ShippingRateResponse,
    User,
)
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/shipping", tags=["shipping"])


# ── Shipping Rates ────────────────────────────────────────────


@router.get("/rates", response_model=list[ShippingRateResponse])
def get_shipping_rates(
    origin: str = "Tripoli",
    destination: str = "Tripoli",
    db: Session = Depends(get_db),
):
    """Get available shipping rates between two cities."""
    rates = (
        db.query(ShippingRate)
        .filter(
            ShippingRate.origin_city == origin,
            ShippingRate.destination_city == destination,
            ShippingRate.is_active,
        )
        .all()
    )
    return rates


@router.post("/calculate")
def calculate_shipping(
    origin: str = "Tripoli",
    destination: str = "Tripoli",
    weight_kg: float = 1.0,
    db: Session = Depends(get_db),
):
    """Calculate shipping cost for a given route and weight."""
    rates = (
        db.query(ShippingRate)
        .filter(
            ShippingRate.origin_city == origin,
            ShippingRate.destination_city == destination,
            ShippingRate.is_active,
        )
        .all()
    )
    if not rates:
        # Fallback: flat rate
        return {
            "options": [
                {
                    "carrier": "local",
                    "cost": 15.0,
                    "currency": "LYD",
                    "estimated_days": 3,
                }
            ]
        }

    options = []
    for rate in rates:
        cost = max(rate.base_cost + (weight_kg * rate.cost_per_kg), rate.min_cost)
        options.append(
            {
                "carrier": rate.carrier,
                "cost": round(cost, 2),
                "currency": "LYD",
                "estimated_days": rate.estimated_days,
            }
        )
    return {"options": options}


# ── Shipments ─────────────────────────────────────────────────


@router.post("", response_model=ShipmentResponse)
def create_shipment(
    data: ShipmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a shipment for an order (seller/supplier action)."""
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db_shipment = Shipment(
        order_id=data.order_id,
        carrier=data.carrier,
        tracking_number=data.tracking_number,
        weight_kg=data.weight_kg,
        shipping_cost=data.shipping_cost,
        currency=data.currency,
        origin_city=data.origin_city,
        destination_city=data.destination_city,
        estimated_days=data.estimated_days,
        status="pending",
    )
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment


@router.get("/order/{order_id}", response_model=list[ShipmentResponse])
def get_order_shipments(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all shipments for an order (auth required)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Only buyer or seller of the order can see shipments
    if user.id not in (order.buyer_id, order.seller_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(Shipment).filter(Shipment.order_id == order_id).all()


@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(
    shipment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get shipment details (auth required)."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    order = db.query(Order).filter(Order.id == shipment.order_id).first()
    if order and user.id not in (order.buyer_id, order.seller_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return shipment


@router.get("/{shipment_id}/tracking", response_model=list[ShipmentEventResponse])
def get_tracking(shipment_id: int, db: Session = Depends(get_db)):
    """Get tracking events for a shipment."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return (
        db.query(ShipmentEvent)
        .filter(ShipmentEvent.shipment_id == shipment_id)
        .order_by(ShipmentEvent.event_time.desc())
        .all()
    )


@router.put("/{shipment_id}/status")
def update_shipment_status(
    shipment_id: int,
    status: str,
    location: str | None = None,
    description: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update shipment status (seller/supplier action)."""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    # C3: Only the seller of the order can update shipment status
    order = db.query(Order).filter(Order.id == shipment.order_id).first()
    if order and order.seller_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this shipment")

    valid_statuses = [
        "pending",
        "shipped",
        "in_transit",
        "out_for_delivery",
        "delivered",
        "returned",
    ]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid_statuses}")

    shipment.status = status
    shipment.updated_at = datetime.now(timezone.utc)

    if status == "shipped":
        shipment.shipped_at = datetime.now(timezone.utc)
    elif status == "delivered":
        shipment.delivered_at = datetime.now(timezone.utc)

    # Add tracking event
    event = ShipmentEvent(
        shipment_id=shipment_id,
        status=status,
        location=location,
        description=description or f"Status updated to {status}",
    )
    db.add(event)
    db.commit()
    return {"message": f"Shipment updated to {status}"}
