"""
Libya B2B Platform - Static Pages & Arabic API Routes
Fallback routes for serving HTML pages directly from the backend.
"""

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["static"])

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")


# ============================================================
# Landing pages
# ============================================================


@router.get("/landing")
def landing_page():
    return FileResponse(os.path.join(static_dir, "index.html"), media_type="text/html")


@router.get("/ar/landing")
def landing_page_arabic():
    return FileResponse(os.path.join(static_dir, "index_ar.html"), media_type="text/html")


# ============================================================
# Static pages (backend fallback)
# ============================================================


@router.get("/products")
def products_page():
    return FileResponse(os.path.join(static_dir, "products.html"), media_type="text/html")


@router.get("/cart")
def cart_page():
    return FileResponse(os.path.join(static_dir, "cart.html"), media_type="text/html")


@router.get("/checkout")
def checkout_page():
    return FileResponse(os.path.join(static_dir, "checkout.html"), media_type="text/html")


@router.get("/seller")
def seller_page():
    return FileResponse(os.path.join(static_dir, "seller.html"), media_type="text/html")


@router.get("/ar/cart")
def cart_page_ar():
    return FileResponse(os.path.join(static_dir, "cart.html"), media_type="text/html")


@router.get("/ar/checkout")
def checkout_page_ar():
    return FileResponse(os.path.join(static_dir, "checkout.html"), media_type="text/html")


@router.get("/ar/seller")
def seller_page_ar():
    return FileResponse(os.path.join(static_dir, "seller.html"), media_type="text/html")


# ============================================================
# Tracking & Buyer
# ============================================================


@router.get("/tracking")
def tracking_page():
    return FileResponse(os.path.join(static_dir, "tracking.html"), media_type="text/html")


@router.get("/buyer")
def buyer_page():
    return FileResponse(os.path.join(static_dir, "buyer.html"), media_type="text/html")


@router.get("/ar/tracking")
def tracking_page_ar():
    return FileResponse(os.path.join(static_dir, "tracking.html"), media_type="text/html")


# ============================================================
# Arabic API endpoints
# ============================================================

from datetime import datetime, timezone  # noqa: E402
from typing import List  # noqa: E402

from fastapi import Depends  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from config import get_db  # noqa: E402
from models import (  # noqa: E402
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Order,
    OrderCreate,
    OrderResponse,
    Product,
)


@router.get("/ar/products", response_model=List)
def list_products_arabic(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()


@router.post("/ar/orders", response_model=OrderResponse)
def create_order_arabic(order: OrderCreate, db: Session = Depends(get_db)):
    import random  # noqa: E402
    import string  # noqa: E402

    order_number = (
        f"LYB-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=6))}"
    )
    order_data = order.model_dump(exclude={"items"}, exclude_unset=True)
    db_order = Order(order_number=order_number, **order_data)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.post("/ar/chat", response_model=ChatResponse)
def chat_arabic(request: ChatRequest, db: Session = Depends(get_db)):
    from chatbot import get_chatbot  # noqa: E402

    chatbot_instance = get_chatbot()
    result = chatbot_instance.process_message(
        session_id=request.session_id, message=request.message, is_arabic=True
    )
    db_message = ChatMessage(
        session_id=request.session_id,
        user_message=request.message,
        bot_response=result["response"],
        is_arabic=True,
    )
    db.add(db_message)
    db.commit()
    return ChatResponse(
        session_id=request.session_id,
        response=result["response"],
        is_arabic=True,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/ar/errors")
def get_arabic_errors():
    from errors_ar import get_all_errors  # noqa: E402

    return get_all_errors("ar")


@router.get("/ar/success")
def get_arabic_success():
    from errors_ar import get_all_success  # noqa: E402

    return get_all_success("ar")
