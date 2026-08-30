"""
Libya B2B Platform - Product Routes
CRUD for products with image support.
"""

import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import get_db
from models import (
    Product,
    ProductCreate,
    ProductImage,
    ProductResponse,
    ProductVariant,
    ProductVariantCreate,
    ProductVariantResponse,
    User,
)
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("", response_model=ProductResponse)
def create_product(
    product: ProductCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    data = product.model_dump()
    data["seller_id"] = user.id
    db_product = Product(**data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("", response_model=List[ProductResponse])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id and product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this product")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted", "id": product_id}


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    if db_product.seller_id and db_product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this product")
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.post("/{product_id}/images")
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    is_primary: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload an image for a product (saved to static/uploads/products/)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    upload_dir = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "products")
    os.makedirs(upload_dir, exist_ok=True)

    os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"product_{product_id}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    image_url = f"/static/uploads/products/{filename}"

    img = ProductImage(product_id=product_id, image_url=image_url, is_primary=is_primary)
    db.add(img)

    if is_primary or not product.image_url:
        product.image_url = image_url

    db.commit()
    return {"image_url": image_url, "is_primary": is_primary}


# --- Product Variants (Alibaba-style: size/color/material) ---


@router.post("/{product_id}/variants", response_model=ProductVariantResponse)
def create_variant(
    product_id: int,
    variant: ProductVariantCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id and product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_variant = ProductVariant(product_id=product_id, **variant.model_dump())
    db.add(db_variant)
    db.commit()
    db.refresh(db_variant)
    return db_variant


@router.get("/{product_id}/variants", response_model=list[ProductVariantResponse])
def list_variants(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == product_id,
            ProductVariant.is_active,
        )
        .all()
    )


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
def update_variant(
    product_id: int,
    variant_id: int,
    variant: ProductVariantCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id and product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_variant = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
        .first()
    )
    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    for key, value in variant.model_dump().items():
        setattr(db_variant, key, value)
    db.commit()
    db.refresh(db_variant)
    return db_variant


@router.delete("/{product_id}/variants/{variant_id}")
def delete_variant(
    product_id: int,
    variant_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id and product.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_variant = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
        .first()
    )
    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    db_variant.is_active = False
    db.commit()
    return {"message": "Variant deleted"}
