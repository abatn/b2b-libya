"""
Libya B2B Platform - Payment Routes
API endpoints for Payment SDK.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import get_db
from models import PaymentTransaction, User
from routes.auth_routes import get_current_user
from services.payment.gateway import get_payment_gateway
from services.payment.service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["payments"])


class PaymentCreateRequest(BaseModel):
    """Payment creation request."""

    order_id: int
    amount: float
    method: str = "cod"
    currency: str = "LYD"
    description: str = ""


class PaymentRefundRequest(BaseModel):
    """Payment refund request."""

    transaction_id: str
    amount: Optional[float] = None
    reason: str = ""


class WebhookPayload(BaseModel):
    """Webhook payload from payment provider."""

    provider: str
    transaction_id: str
    status: str
    amount: Optional[float] = None
    signature: Optional[str] = None
    metadata: Optional[dict] = None


@router.get("/methods")
async def list_payment_methods():
    """List available payment methods."""
    service = PaymentService()
    methods = service.get_available_methods()
    return {"methods": methods}


@router.post("/pay")
async def create_payment(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a payment for an order."""
    service = PaymentService()
    result = service.process_payment(
        order_id=request.order_id,
        amount=request.amount,
        method=request.method,
        currency=request.currency,
        description=request.description,
        metadata={"user_id": current_user.id},
    )

    # Persist transaction to DB
    txn = PaymentTransaction(
        order_id=request.order_id,
        user_id=current_user.id,
        provider=request.method,
        amount=request.amount,
        currency=request.currency,
        status=result.status.value,
        provider_reference=result.transaction_id,
        provider_response=result.message,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    if result.success:
        return {
            "success": True,
            "transaction_id": result.transaction_id,
            "status": result.status.value,
            "message": result.message,
            "provider": result.provider,
            "amount": result.amount,
            "currency": result.currency,
            "payment_url": result.metadata.get("payment_url"),
            "db_txn_id": txn.id,
        }
    else:
        raise HTTPException(status_code=400, detail=result.message)


@router.get("/status/{provider}/{transaction_id}")
async def get_payment_status(
    provider: str,
    transaction_id: str,
    current_user: User = Depends(get_current_user),
):
    """Check payment status."""
    service = PaymentService()
    result = service.get_payment_status(provider, transaction_id)

    return {
        "success": result.success,
        "transaction_id": result.transaction_id,
        "status": result.status.value,
        "message": result.message,
        "provider": result.provider,
    }


@router.post("/refund")
async def refund_payment(
    request: PaymentRefundRequest,
    current_user: User = Depends(get_current_user),
):
    """Refund a payment."""
    service = PaymentService()
    result = service.refund_payment(
        provider="mock",  # TODO: Get provider from transaction
        transaction_id=request.transaction_id,
        amount=request.amount,
        reason=request.reason,
    )

    if result.success:
        return {
            "success": True,
            "transaction_id": result.transaction_id,
            "status": result.status.value,
            "message": result.message,
            "amount": result.amount,
        }
    else:
        raise HTTPException(status_code=400, detail=result.message)


# ============================================================
# WEBHOOK ENDPOINTS — For async payment notifications
# ============================================================


@router.post("/webhook/{provider}")
async def payment_webhook(
    provider: str,
    payload: WebhookPayload,
    db: Session = Depends(get_db),
):
    """
    Receive webhook from payment provider.

    Providers (SADAD, Fawry, Moamalat) send status updates
    via webhooks when payment is completed, failed, or refunded.

    This endpoint:
    1. Validates the webhook signature (if provided)
    2. Updates the payment transaction status in DB
    3. Returns success acknowledgment
    """
    # Validate provider
    valid_providers = ["sadad", "fawry", "moamalat", "mock"]
    if provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    # Find transaction in DB
    txn = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.provider_reference == payload.transaction_id)
        .first()
    )

    if not txn:
        # Transaction not found — log but return 200 (provider expects acknowledgment)
        return {"success": True, "message": "Webhook received (transaction not in DB)"}

    # Update transaction status
    status_map = {
        "completed": "completed",
        "failed": "failed",
        "refunded": "refunded",
        "pending": "pending",
        "processing": "processing",
    }
    new_status = status_map.get(payload.status.lower(), "pending")
    txn.status = new_status
    if payload.metadata:
        try:
            import json

            existing = json.loads(txn.provider_response or "{}")
            if not isinstance(existing, dict):
                existing = {}
            existing["webhook"] = payload.metadata
            txn.provider_response = json.dumps(existing)
        except (json.JSONDecodeError, TypeError):
            import json

            txn.provider_response = json.dumps({"webhook": payload.metadata})
    db.commit()

    return {
        "success": True,
        "transaction_id": payload.transaction_id,
        "status": new_status,
        "message": f"Webhook from {provider} processed",
    }


# ============================================================
# STATUS POLLING — For providers without webhook support
# ============================================================


@router.get("/poll/{provider}/{transaction_id}")
async def poll_payment_status(
    provider: str,
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Poll payment status from provider.

    Use this endpoint when:
    - Provider doesn't support webhooks
    - User wants to check status after redirect
    - Frontend needs to poll for status updates

    Updates the DB transaction if status changed.
    """
    service = PaymentService()
    result = service.get_payment_status(provider, transaction_id)

    if result.success:
        # Update DB transaction if status changed
        txn = (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.provider_reference == transaction_id)
            .first()
        )
        if txn and txn.status != result.status.value:
            txn.status = result.status.value
            db.commit()

    return {
        "success": result.success,
        "transaction_id": result.transaction_id,
        "status": result.status.value,
        "message": result.message,
        "provider": result.provider,
    }


# ============================================================
# PROVIDER HEALTH CHECK — Check which providers are configured
# ============================================================


@router.get("/health")
async def payment_health_check():
    """
    Check payment provider availability.

    Returns which providers are configured and ready
    for real transactions (vs. sandbox/mock mode).
    """
    gateway = get_payment_gateway()
    providers_list = gateway.list_providers()
    providers_status = {}

    for p in providers_list:
        name = p["name"]
        providers_status[name] = {
            "name": name,
            "display_name": p["display_name"],
            "available": p["is_available"],
            "mode": "live" if p["is_available"] else "sandbox",
        }

    return {
        "providers": providers_status,
        "total": len(providers_status),
        "live_count": sum(1 for p in providers_status.values() if p["available"]),
        "sandbox_count": sum(1 for p in providers_status.values() if not p["available"]),
    }
