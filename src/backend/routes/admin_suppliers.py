"""
Libya B2B Platform - Admin Supplier Routes
Admin endpoints for supplier verification and management.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from models import Supplier, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/admin/suppliers", tags=["admin-suppliers"])


def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("")
def list_all_suppliers(
    verified: str = "all",
    category: str = None,
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all suppliers for admin (including unverified)."""
    query = db.query(Supplier)

    if verified == "true":
        query = query.filter(Supplier.is_verified)
    elif verified == "false":
        query = query.filter(Supplier.is_verified == False)  # noqa: E712

    if category:
        query = query.filter(Supplier.category == category)

    suppliers = query.order_by(Supplier.created_at.desc()).offset(skip).limit(limit).all()
    total = query.count()

    return {
        "suppliers": [
            {
                "id": s.id,
                "name": s.name,
                "name_arabic": s.name_arabic,
                "city": s.city,
                "phone": s.phone,
                "email": s.email,
                "category": s.category,
                "is_verified": s.is_verified,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in suppliers
        ],
        "total": total,
    }


@router.post("/{supplier_id}/verify")
def verify_supplier(
    supplier_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Mark a supplier as verified."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.is_verified = True
    supplier.verified_at = datetime.now(timezone.utc)
    supplier.verified_by = admin.id
    db.commit()

    return {"message": f"Supplier '{supplier.name}' verified", "id": supplier.id}


@router.post("/{supplier_id}/unverify")
def unverify_supplier(
    supplier_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Remove verification from a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.is_verified = False
    supplier.verified_at = None
    supplier.verified_by = None
    db.commit()

    return {"message": f"Supplier '{supplier.name}' unverified", "id": supplier.id}


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a supplier (admin only)."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db.delete(supplier)
    db.commit()

    return {"message": f"Supplier '{supplier.name}' deleted", "id": supplier_id}


@router.post("/{supplier_id}/verify/{level}")
def verify_supplier_level(
    supplier_id: int,
    level: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Multi-step verification: Level 0→1→2→3→4. At Level 4, is_verified=True."""
    if level < 0 or level > 4:
        raise HTTPException(status_code=400, detail="Level must be 0-4")
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.verification_level = level
    supplier.verified_by = admin.id
    supplier.verified_at = datetime.now(timezone.utc)
    if level >= 4:
        supplier.is_verified = True
    elif level == 0:
        supplier.is_verified = False
    db.commit()

    level_names = {
        0: "Unverified",
        1: "Identity Verified",
        2: "Business Verified",
        3: "Documents Verified",
        4: "Fully Verified",
    }
    return {
        "message": f"Supplier verified at Level {level}: {level_names.get(level, '?')}",
        "id": supplier.id,
        "verification_level": level,
        "is_verified": supplier.is_verified,
    }


@router.get("/stats")
def admin_supplier_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get supplier statistics for admin dashboard."""
    total = db.query(Supplier).count()
    verified = db.query(Supplier).filter(Supplier.is_verified).count()
    unverified = total - verified

    return {
        "total": total,
        "verified": verified,
        "unverified": unverified,
        "verification_rate": round(verified / total * 100, 1) if total > 0 else 0,
    }
