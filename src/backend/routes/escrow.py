"""Libya B2B Platform - Escrow Routes
Manual escrow system for B2B transactions.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from models import (
    DisputeMessage,
    DisputeMessageCreate,
    DisputeMessageResponse,
    EscalationResponse,
    Escrow,
    EscrowCreate,
    EscrowHistory,
    EscrowHistoryResponse,
    EscrowResponse,
    Order,
    User,
)
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/escrow", tags=["escrow"])


# ── helpers ───────────────────────────────────────────────


def _log_history(
    db: Session,
    escrow_id: int,
    action: str,
    old_status: str | None,
    new_status: str,
    performed_by: int | None = None,
    note: str | None = None,
):
    """Write one row into escrow_history."""
    entry = EscrowHistory(
        escrow_id=escrow_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        performed_by=performed_by,
        note=note,
    )
    db.add(entry)


# ── public endpoints ──────────────────────────────────────


@router.post("", response_model=EscrowResponse)
def create_escrow(
    data: EscrowCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Create an escrow transaction for an order."""
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if escrow already exists for this order
    existing = db.query(Escrow).filter(Escrow.order_id == data.order_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Escrow already exists for this order")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    escrow = Escrow(
        order_id=data.order_id,
        buyer_id=order.buyer_id or user.id,
        supplier_id=order.seller_id or user.id,
        amount=data.amount,
        currency=order.currency,
        status="pending",
        note=data.note,
    )
    db.add(escrow)
    db.flush()  # get escrow.id before logging
    _log_history(db, escrow.id, "created", None, "pending", performed_by=user.id, note=data.note)
    db.commit()
    db.refresh(escrow)
    return escrow


@router.get("/{escrow_id}", response_model=EscrowResponse)
def get_escrow(
    escrow_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get escrow status by ID."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    return escrow


@router.get("/{escrow_id}/history", response_model=list[EscrowHistoryResponse])
def get_escrow_history(
    escrow_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get audit trail for an escrow transaction."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    return (
        db.query(EscrowHistory)
        .filter(EscrowHistory.escrow_id == escrow_id)
        .order_by(EscrowHistory.created_at)
        .all()
    )


@router.post("/{escrow_id}/release", response_model=EscrowResponse)
def release_escrow(
    escrow_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Release escrow funds to supplier (confirm delivery)."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")

    if escrow.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Cannot release escrow in '{escrow.status}' status"
        )

    old = escrow.status
    escrow.status = "released"
    escrow.released_at = datetime.now(timezone.utc)
    _log_history(db, escrow_id, "released", old, "released", performed_by=user.id)
    db.commit()
    db.refresh(escrow)
    return escrow


@router.post("/{escrow_id}/refund", response_model=EscrowResponse)
def refund_escrow(
    escrow_id: int,
    amount: float | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Refund escrow funds to buyer. Partial refund if amount specified."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")

    if escrow.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Cannot refund escrow in '{escrow.status}' status"
        )

    old = escrow.status
    if amount is not None and amount < escrow.amount:
        # Partial refund
        escrow.amount = escrow.amount - amount
        escrow.status = "pending"  # Keep pending for remainder
        note = f"Partial refund: {amount} {escrow.currency} refunded, {escrow.amount} remaining"
        _log_history(
            db, escrow_id, "partial_refunded", old, "pending", performed_by=user.id, note=note
        )
    else:
        # Full refund
        escrow.status = "refunded"
        escrow.refunded_at = datetime.now(timezone.utc)
        _log_history(db, escrow_id, "refunded", old, "refunded", performed_by=user.id)

    db.commit()
    db.refresh(escrow)
    return escrow


@router.post("/{escrow_id}/dispute", response_model=EscrowResponse)
def dispute_escrow(
    escrow_id: int,
    reason: str = "quality",
    description: str = "",
    evidence: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Open a dispute for an escrow transaction with reason and evidence."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")

    if escrow.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Cannot dispute escrow in '{escrow.status}' status"
        )

    valid_reasons = ["quality", "damage", "wrong_item", "not_delivered"]
    if reason not in valid_reasons:
        raise HTTPException(
            status_code=400, detail=f"Invalid reason. Must be one of: {valid_reasons}"
        )

    old = escrow.status
    escrow.status = "disputed"
    escrow.disputed_at = datetime.now(timezone.utc)
    escrow.dispute_reason = reason
    escrow.dispute_description = description
    escrow.dispute_evidence = evidence  # JSON array of image URLs
    _log_history(
        db,
        escrow_id,
        "disputed",
        old,
        "disputed",
        performed_by=user.id,
        note=f"Reason: {reason} | {description[:100]}",
    )
    db.commit()
    db.refresh(escrow)
    return escrow


# ── auto-expire (called from startup) ────────────────────


def check_expired_escrows():
    """Release escrows pending > 30 days (Alibaba-style auto-release)."""
    from config import SessionLocal

    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        expired = (
            db.query(Escrow).filter(Escrow.status == "pending", Escrow.created_at < cutoff).all()
        )
        for escrow in expired:
            old = escrow.status
            escrow.status = "released"
            escrow.released_at = datetime.now(timezone.utc)
            escrow.note = (escrow.note or "") + " | Auto-released after 30 days"
            _log_history(
                db, escrow.id, "auto_expired", old, "released", note="Auto-released after 30 days"
            )
        if expired:
            db.commit()
        return len(expired)
    finally:
        db.close()


@router.get("/{escrow_id}/dispute/messages", response_model=list[DisputeMessageResponse])
def get_dispute_messages(escrow_id: int, db: Session = Depends(get_db)):
    """Get all messages for a dispute."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    messages = (
        db.query(DisputeMessage)
        .filter(DisputeMessage.escrow_id == escrow_id)
        .order_by(DisputeMessage.created_at.asc())
        .all()
    )
    return messages


@router.post("/{escrow_id}/dispute/messages", response_model=DisputeMessageResponse)
def send_dispute_message(
    escrow_id: int,
    msg: DisputeMessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message in a dispute."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    if escrow.status not in ("disputed", "pending"):
        raise HTTPException(status_code=400, detail="Dispute not active")
    # Determine sender type
    sender_type = "admin"
    if user.id == escrow.buyer_id:
        sender_type = "buyer"
    elif user.id == escrow.supplier_id:
        sender_type = "supplier"
    message = DisputeMessage(
        escrow_id=escrow_id,
        sender_id=user.id,
        sender_type=sender_type,
        text=msg.text,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


# ── Multi-Level Dispute Escalation ────────────────────────────

ESCALATION_LEVELS = {
    1: "direct_negotiation",
    2: "mediation",
    3: "third_party_inspection",
    4: "arbitration",
}

ESCALATION_DEADLINES = {
    1: timedelta(days=7),
    2: timedelta(days=14),
    3: timedelta(days=21),
    4: timedelta(days=30),
}


@router.post("/{escrow_id}/escalate", response_model=EscalationResponse)
def escalate_dispute(
    escrow_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Escalate a dispute to the next level (Alibaba-style)."""
    from models import DisputeEscalation

    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    if escrow.status != "disputed":
        raise HTTPException(status_code=400, detail="Escrow is not in dispute")
    # A3: Only buyer or supplier of this escrow can escalate
    if user.id not in (escrow.buyer_id, escrow.supplier_id):
        raise HTTPException(status_code=403, detail="Not authorized to escalate this dispute")

    current_level = escrow.escalation_level or 0
    next_level = current_level + 1
    if next_level > 4:
        raise HTTPException(
            status_code=400, detail="Already at maximum escalation level (arbitration)"
        )

    level_name = ESCALATION_LEVELS[next_level]
    deadline = datetime.now(timezone.utc) + ESCALATION_DEADLINES[next_level]

    escalation = DisputeEscalation(
        escrow_id=escrow_id,
        level=next_level,
        level_name=level_name,
        initiated_by=user.id,
        status="active",
        description=data.get("description", f"Escalated to level {next_level}: {level_name}"),
        deadline=deadline,
    )
    db.add(escalation)

    escrow.escalation_level = next_level
    escrow.escalation_deadline = deadline
    escrow.last_escalated_at = datetime.now(timezone.utc)

    # Record in history
    history = EscrowHistory(
        escrow_id=escrow_id,
        action="escalated",
        old_status=escrow.status,
        new_status="disputed",
        performed_by=user.id,
        note=f"Escalated to level {next_level}: {level_name}",
    )
    db.add(history)
    db.commit()
    db.refresh(escalation)
    return escalation


@router.get("/{escrow_id}/escalations")
def get_escalations(escrow_id: int, db: Session = Depends(get_db)):
    """Get all escalation steps for a dispute."""
    from models import DisputeEscalation

    return (
        db.query(DisputeEscalation)
        .filter(DisputeEscalation.escrow_id == escrow_id)
        .order_by(DisputeEscalation.level)
        .all()
    )


@router.put("/{escrow_id}/escalations/{escalation_id}/resolve")
def resolve_escalation(
    escrow_id: int,
    escalation_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resolve an escalation step (admin action)."""
    # A2: Only admins can resolve escalations
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required to resolve escalations")
    from models import DisputeEscalation

    escalation = (
        db.query(DisputeEscalation)
        .filter(
            DisputeEscalation.id == escalation_id,
            DisputeEscalation.escrow_id == escrow_id,
        )
        .first()
    )
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if escalation.status != "active":
        raise HTTPException(status_code=400, detail="Escalation already resolved")

    escalation.status = "resolved"
    escalation.resolution = data.get("resolution", "Resolved")
    escalation.resolved_by = user.id
    escalation.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Level {escalation.level} escalation resolved"}
