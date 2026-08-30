"""
Libya B2B Platform — Admin Escrow Resolution
Admin-only endpoints for resolving disputed escrows.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from models import Escrow, EscrowResolveRequest, EscrowResponse, User
from routes.auth_routes import get_current_user
from routes.escrow import _log_history

router = APIRouter(prefix="/api/admin/escrow", tags=["admin-escrow"])


def _require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/disputes", response_model=list[EscrowResponse])
def list_disputes(
    status: str = "disputed",
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """List escrow transactions filtered by status (default: disputed)."""
    return (
        db.query(Escrow)
        .filter(Escrow.status == status)
        .order_by(Escrow.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/{escrow_id}/resolve", response_model=EscrowResponse)
def resolve_escrow(
    escrow_id: int,
    data: EscrowResolveRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Admin resolves a disputed escrow (release or refund)."""
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")

    if escrow.status not in ("disputed", "pending"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resolve escrow in '{escrow.status}' status",
        )

    if data.resolution not in ("release", "refund"):
        raise HTTPException(
            status_code=400,
            detail="Resolution must be 'release' or 'refund'",
        )

    old = escrow.status
    new_status = "resolved_release" if data.resolution == "release" else "resolved_refund"

    escrow.status = new_status
    escrow.resolved_at = datetime.now(timezone.utc)
    escrow.resolved_by = admin.id
    escrow.resolution_reason = data.reason

    if data.resolution == "release":
        escrow.released_at = datetime.now(timezone.utc)
    else:
        if data.amount is not None and data.amount < escrow.amount:
            # Partial refund
            escrow.amount = escrow.amount - data.amount
            escrow.status = "pending"  # Keep pending for remainder
            new_status = "partial_refund"
        else:
            escrow.refunded_at = datetime.now(timezone.utc)

    _log_history(
        db,
        escrow_id,
        "resolved",
        old,
        new_status,
        performed_by=admin.id,
        note=data.reason,
    )
    db.commit()
    db.refresh(escrow)
    return escrow
