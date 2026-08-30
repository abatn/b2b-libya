"""
Libya B2B Platform - Supplier Routes
Extended with CSV import, admin verification, category filter.
"""

import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import get_db
from models import Product, Supplier, SupplierCreate, SupplierResponse, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/b2b/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierResponse)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    data = supplier.model_dump()
    # Serialize categories list to JSON string
    if data.get("categories"):
        data["categories"] = json.dumps(data["categories"])
    db_supplier = Supplier(**data)
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@router.get("")
def list_suppliers(
    sort_by: Optional[str] = "rating",
    category: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    verified_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Supplier)

    if category:
        cats = [c.strip() for c in category.split(",") if c.strip()]
        if len(cats) == 1:
            query = query.filter(Supplier.category == cats[0])
        elif len(cats) > 1:
            query = query.filter(Supplier.category.in_(cats))
    if city:
        query = query.filter(Supplier.city == city)
    if verified_only:
        query = query.filter(Supplier.is_verified)
    if search:
        query = query.filter(
            Supplier.name.ilike(f"%{search}%")
            | Supplier.name_arabic.ilike(f"%{search}%")
            | Supplier.description.ilike(f"%{search}%")
        )

    if sort_by == "products":
        query = query.order_by(Supplier.product_count.desc())
    elif sort_by == "name":
        query = query.order_by(Supplier.name.asc())
    else:
        query = query.order_by(Supplier.rating.desc())

    suppliers = query.offset(skip).limit(limit).all()
    total = query.count()

    # Build product count map (dynamic, not from stale product_count field)
    supplier_ids = [s.id for s in suppliers]
    user_ids = [s.user_id for s in suppliers if s.user_id]
    product_counts = {}
    if supplier_ids or user_ids:
        # Count products where seller_id matches supplier.id OR supplier.user_id
        from sqlalchemy import or_  # noqa: E402

        prod_query = db.query(Product.seller_id).filter(
            Product.is_active,
            or_(Product.seller_id.in_(supplier_ids), Product.seller_id.in_(user_ids)),
        )
        for row in prod_query.all():
            sid = row[0]
            product_counts[sid] = product_counts.get(sid, 0) + 1

    return {
        "suppliers": [
            {
                "id": s.id,
                "name": s.name,
                "name_arabic": s.name_arabic,
                "description": s.description,
                "location": s.location,
                "city": s.city,
                "phone": s.phone,
                "email": s.email,
                "website": s.website,
                "category": s.category,
                "categories": json.loads(s.categories) if s.categories else [],
                "logo_url": s.logo_url,
                "rating": s.rating,
                "rating_count": s.rating_count,
                "is_verified": s.is_verified,
                "years_on_platform": s.years_on_platform,
                "product_count": product_counts.get(s.id, 0) + product_counts.get(s.user_id, 0)
                if s.user_id
                else product_counts.get(s.id, 0),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in suppliers
        ],
        "total": total,
    }


@router.get("/categories")
def list_supplier_categories(db: Session = Depends(get_db)):
    """Get all unique categories from suppliers."""
    rows = db.query(Supplier.category).filter(Supplier.category.isnot(None)).distinct().all()
    categories = sorted([r[0] for r in rows if r[0]])
    return {"categories": categories}


@router.get("/cities")
def list_supplier_cities(db: Session = Depends(get_db)):
    """Get all unique cities from suppliers."""
    rows = db.query(Supplier.city).filter(Supplier.city.isnot(None)).distinct().all()
    cities = sorted([r[0] for r in rows if r[0]])
    return {"cities": cities}


@router.get("/stats")
def supplier_stats(db: Session = Depends(get_db)):
    """Get supplier statistics."""
    total = db.query(Supplier).count()
    verified = db.query(Supplier).filter(Supplier.is_verified).count()
    categories = (
        db.query(Supplier.category).filter(Supplier.category.isnot(None)).distinct().count()
    )
    cities = db.query(Supplier.city).filter(Supplier.city.isnot(None)).distinct().count()
    return {
        "total_suppliers": total,
        "verified_suppliers": verified,
        "unverified_suppliers": total - verified,
        "categories": categories,
        "cities": cities,
    }


@router.get("/{supplier_id}")
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Query products by user_id (if linked) or by supplier_id
    seller_id = supplier.user_id if supplier.user_id else supplier_id
    products = db.query(Product).filter(Product.seller_id == seller_id, Product.is_active).all()

    # Dynamic product count (not stale DB field)
    product_count = len(products)

    return {
        "id": supplier.id,
        "name": supplier.name,
        "name_arabic": supplier.name_arabic,
        "description": supplier.description,
        "location": supplier.location,
        "city": supplier.city,
        "phone": supplier.phone,
        "email": supplier.email,
        "website": supplier.website,
        "category": supplier.category,
        "categories": json.loads(supplier.categories) if supplier.categories else [],
        "logo_url": supplier.logo_url,
        "user_id": supplier.user_id,
        "rating": supplier.rating,
        "rating_count": supplier.rating_count,
        "is_verified": supplier.is_verified,
        "years_on_platform": supplier.years_on_platform,
        "product_count": product_count,
        "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "name_arabic": p.name_arabic,
                "price": p.price,
                "currency": p.currency,
                "category": p.category,
                "stock_quantity": p.stock_quantity,
                "image_url": p.image_url,
            }
            for p in products
        ],
    }


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for key, value in supplier_data.model_dump(exclude_unset=True).items():
        if key == "categories" and value is not None:
            value = json.dumps(value)
        setattr(supplier, key, value)

    db.commit()
    db.refresh(supplier)
    return {"message": "Supplier updated", "id": supplier.id}


@router.post("/{supplier_id}/logo")
async def upload_supplier_logo(
    supplier_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a logo image for a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File must be JPEG, PNG, WebP, or GIF")

    # Save file
    import os  # noqa: E402

    upload_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "static", "uploads", "logos"
    )
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"supplier_{supplier_id}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    supplier.logo_url = f"/static/uploads/logos/{filename}"
    db.commit()

    return {"message": "Logo uploaded", "logo_url": supplier.logo_url}


@router.get("/{supplier_id}/badges")
def get_supplier_badges(supplier_id: int, db: Session = Depends(get_db)):
    """Get all badges for a supplier based on their profile."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    badges = []

    # Verified badge
    if supplier.is_verified:
        badges.append({"type": "verified", "label": "Verified Supplier", "color": "green"})

    # Gold badge (4+ years, 4+ rating, verified)
    if supplier.years_on_platform >= 4 and supplier.rating >= 4.0 and supplier.is_verified:
        badges.append({"type": "gold", "label": "Gold Supplier", "color": "gold"})
    # Silver badge (2+ years, 3.5+ rating, verified)
    elif supplier.years_on_platform >= 2 and supplier.rating >= 3.5 and supplier.is_verified:
        badges.append({"type": "silver", "label": "Silver Supplier", "color": "silver"})

    # Trade Assurance (only for verified suppliers)
    if supplier.is_verified:
        badges.append({"type": "trade", "label": "Trade Assurance", "color": "orange"})

    # Years badge
    if supplier.years_on_platform >= 3:
        badges.append(
            {"type": "years", "label": f"{supplier.years_on_platform}+ Years", "color": "blue"}
        )

    # Top Supplier (rating >= 4.5)
    if supplier.rating >= 4.5 and supplier.rating_count >= 10:
        badges.append({"type": "top", "label": "Top Supplier", "color": "orange"})

    # New Supplier (less than 1 year)
    if supplier.years_on_platform <= 1:
        badges.append({"type": "new", "label": "New Supplier", "color": "purple"})

    return {"badges": badges}


# ── CSV Import ──────────────────────────────────────────────────────────────


@router.post("/import")
async def import_suppliers_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import suppliers from CSV file.
    Expected columns: name, name_arabic, description, city,
    phone, email, website, category, location
    Minimum required: name
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv file")

    content = await file.read()
    text = content.decode("utf-8-sig")  # Handle BOM
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        name = (row.get("name") or row.get("Name") or row.get("company") or "").strip()
        if not name:
            skipped += 1
            continue

        try:
            supplier_data = {
                "name": name,
                "name_arabic": (row.get("name_arabic") or row.get("Name Arabic") or "").strip()
                or None,
                "description": (row.get("description") or row.get("Description") or "").strip()
                or None,
                "city": (row.get("city") or row.get("City") or "").strip() or None,
                "phone": (row.get("phone") or row.get("Phone") or row.get("tel") or "").strip()
                or None,
                "email": (row.get("email") or row.get("Email") or "").strip() or None,
                "website": (
                    row.get("website") or row.get("Website") or row.get("url") or ""
                ).strip()
                or None,
                "category": (row.get("category") or row.get("Category") or "").strip() or None,
                "location": (row.get("location") or row.get("Location") or "").strip() or None,
            }

            db_supplier = Supplier(**supplier_data)
            db.add(db_supplier)
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
            skipped += 1

    db.commit()

    return {
        "message": f"Import complete: {imported} imported, {skipped} skipped",
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10],
    }


@router.post("/import/json")
def import_suppliers_json(
    suppliers: list[SupplierCreate],
    db: Session = Depends(get_db),
):
    """Import suppliers from JSON array (for programmatic import)."""
    imported = 0
    for s in suppliers:
        try:
            db_supplier = Supplier(**s.model_dump())
            db.add(db_supplier)
            imported += 1
        except Exception:
            pass

    db.commit()
    return {"message": f"Imported {imported} suppliers", "imported": imported}


# ============================================================
# SUPPLIER REVIEWS
# ============================================================

from models import SupplierReview, SupplierReviewCreate, SupplierReviewResponse  # noqa: E402


@router.get("/{supplier_id}/reviews", response_model=list[SupplierReviewResponse])
def get_supplier_reviews(supplier_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a supplier."""
    reviews = (
        db.query(SupplierReview)
        .filter(SupplierReview.supplier_id == supplier_id)
        .order_by(SupplierReview.created_at.desc())
        .all()
    )
    return reviews


@router.post("/{supplier_id}/reviews", response_model=SupplierReviewResponse)
def create_supplier_review(
    supplier_id: int,
    review: SupplierReviewCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a review for a supplier."""
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    # Check if user already reviewed this supplier
    existing = (
        db.query(SupplierReview)
        .filter(
            SupplierReview.supplier_id == supplier_id,
            SupplierReview.user_id == user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already reviewed this supplier")

    db_review = SupplierReview(
        supplier_id=supplier_id,
        user_id=user.id,
        rating=review.rating,
        comment=review.comment,
        order_id=review.order_id,
    )
    db.add(db_review)

    # Update supplier rating (average)
    all_reviews = db.query(SupplierReview).filter(SupplierReview.supplier_id == supplier_id).all()
    total = sum(r.rating for r in all_reviews) + review.rating
    count = len(all_reviews) + 1
    supplier.rating = round(total / count, 1)
    supplier.rating_count = count

    db.commit()
    db.refresh(db_review)
    return db_review
