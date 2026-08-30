"""
Libya B2B Platform - Review Routes
5-star rating system with comments.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import get_db
from models import Product, Review, ReviewCreate, ReviewResponse, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
def create_review(
    review: ReviewCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Add a review for a product. rating must be 1-5."""
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    product = db.query(Product).filter(Product.id == review.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_review = Review(
        product_id=review.product_id,
        user_id=user.id,
        rating=review.rating,
        comment=review.comment,
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Update product rating aggregate
    _update_product_rating(review.product_id, db)

    return db_review


@router.get("/product/{product_id}")
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a product with average rating."""
    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    avg = db.query(func.avg(Review.rating)).filter(Review.product_id == product_id).scalar()
    count = db.query(func.count(Review.id)).filter(Review.product_id == product_id).scalar()

    # Rating distribution
    distribution = {}
    for i in range(1, 6):
        distribution[str(i)] = (
            db.query(func.count(Review.id))
            .filter(Review.product_id == product_id, Review.rating == i)
            .scalar()
        )

    return {
        "reviews": [
            {
                "id": r.id,
                "product_id": r.product_id,
                "user_id": r.user_id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ],
        "summary": {
            "average": round(float(avg), 2) if avg else 0.0,
            "count": count or 0,
            "distribution": distribution,
        },
    }


@router.get("/stats")
def get_rating_stats(db: Session = Depends(get_db)):
    """Global rating statistics."""
    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    avg_rating = db.query(func.avg(Review.rating)).scalar()
    return {
        "total_reviews": total_reviews,
        "average_rating": round(float(avg_rating), 2) if avg_rating else 0.0,
    }


def _update_product_rating(product_id: int, db: Session):
    """Recalculate average rating for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return
    avg = db.query(func.avg(Review.rating)).filter(Review.product_id == product_id).scalar()
    count = db.query(func.count(Review.id)).filter(Review.product_id == product_id).scalar()
    # Store rating on supplier if needed — for now just update supplier aggregate
    from models import Supplier

    if product.seller_id:
        supplier = db.query(Supplier).filter(Supplier.id == product.seller_id).first()
        if supplier:
            supplier.rating = round(float(avg), 2) if avg else 0.0
            supplier.rating_count = count or 0
            db.commit()
