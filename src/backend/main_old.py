"""
Libya B2B Platform - Backend
Offline-first KI-B2B-Plattform fuer Libyen
Projektversion: v1.0
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ============================================================
# DATABASE SETUP (SQLite - Offline-first)
# ============================================================

SQLITE_URL = os.getenv("DATABASE_URL", "sqlite:///./libya_b2b.db")

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================
# DATABASE MODELS
# ============================================================


class Product(Base):
    """Produkt-Modell fuer B2B-Marktplatz"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    name_arabic = Column(String(255), nullable=True)  # Arabischer Name
    description = Column(String(1000), nullable=True)
    description_arabic = Column(String(1000), nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="LYD")
    category = Column(String(100), nullable=True)
    stock_quantity = Column(Integer, default=0)
    seller_id = Column(Integer, nullable=True)
    qr_code = Column(String(500), nullable=True)  # QR-Code fuer Tracking
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    """Bestellungs-Modell mit COD-Tracking"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    buyer_id = Column(Integer, nullable=True)
    seller_id = Column(Integer, nullable=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="LYD")
    payment_method = Column(String(50), default="COD")  # Cash on Delivery
    status = Column(String(50), default="pending")  # pending, confirmed, delivered, cancelled
    delivery_address = Column(String(500), nullable=True)
    qr_code = Column(String(500), nullable=True)
    delivery_photo = Column(String(500), nullable=True)  # Foto-Verification
    delivery_gps_lat = Column(Float, nullable=True)
    delivery_gps_lon = Column(Float, nullable=True)
    delivery_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """Chat-Nachrichten fuer KI-Chatbot"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False)
    user_message = Column(String(2000), nullable=False)
    bot_response = Column(String(2000), nullable=False)
    is_arabic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SyncLog(Base):
    """Sync-Protokoll fuer Delta-Sync"""

    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # create, update, delete
    synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================


class ProductCreate(BaseModel):
    name: str
    name_arabic: Optional[str] = None
    description: Optional[str] = None
    description_arabic: Optional[str] = None
    price: float
    currency: str = "LYD"
    category: Optional[str] = None
    stock_quantity: int = 0
    seller_id: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    name_arabic: Optional[str]
    price: float
    currency: str
    category: Optional[str]
    stock_quantity: int
    qr_code: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    buyer_id: Optional[int] = None
    seller_id: Optional[int] = None
    total_amount: float
    currency: str = "LYD"
    payment_method: str = "COD"
    delivery_address: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    total_amount: float
    currency: str
    payment_method: str
    status: str
    qr_code: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: str
    message: str
    is_arabic: bool = True


class ChatResponse(BaseModel):
    session_id: str
    response: str
    is_arabic: bool
    created_at: datetime


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Libya B2B Platform API",
    description="Offline-first KI-B2B-Plattform fuer Libyen - Projekt v1.0",
    version="1.0.0",
)

# CORS fuer React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# DATABASE DEPENDENCY
# ============================================================


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# STARTUP EVENT - Tables erstellen
# ============================================================


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


# ============================================================
# PRODUCT ENDPOINTS (CRUD)
# ============================================================


@app.post("/api/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db=__import__("fastapi").Depends(get_db)):
    """Neues Produkt erstellen"""
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    # Sync-Log erstellen
    sync_log = SyncLog(table_name="products", record_id=db_product.id, action="create")
    db.add(sync_log)
    db.commit()

    return db_product


@app.get("/api/products", response_model=List[ProductResponse])
def list_products(skip: int = 0, limit: int = 100, db=__import__("fastapi").Depends(get_db)):
    """Alle Produkte auflisten"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db=next(get_db())):
    """Einzelnes Produkt abrufen"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    return product


@app.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate, db=next(get_db())):
    """Produkt aktualisieren"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")

    for key, value in product.model_dump().items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)

    # Sync-Log
    sync_log = SyncLog(table_name="products", record_id=product_id, action="update")
    db.add(sync_log)
    db.commit()

    return db_product


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db=next(get_db())):
    """Produkt loeschen"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")

    db.delete(db_product)
    db.commit()

    # Sync-Log
    sync_log = SyncLog(table_name="products", record_id=product_id, action="delete")
    db.add(sync_log)
    db.commit()

    return {"message": "Produkt geloescht"}


# ============================================================
# ORDER ENDPOINTS (COD-Tracking)
# ============================================================


@app.post("/api/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db=next(get_db())):
    """Bestellung erstellen (COD)"""
    import random
    import string

    # Einzigartige Bestellnummer generieren
    order_number = (
        f"LYB-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=6))}"
    )

    db_order = Order(
        order_number=order_number,
        buyer_id=order.buyer_id,
        seller_id=order.seller_id,
        total_amount=order.total_amount,
        currency=order.currency,
        payment_method=order.payment_method,
        delivery_address=order.delivery_address,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    return db_order


@app.get("/api/orders", response_model=List[OrderResponse])
def list_orders(skip: int = 0, limit: int = 100, db=next(get_db())):
    """Alle Bestellungen auflisten"""
    orders = db.query(Order).offset(skip).limit(limit).all()
    return orders


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db=next(get_db())):
    """Einzelne Bestellung abrufen"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
    return order


@app.put("/api/orders/{order_id}/deliver")
def confirm_delivery(
    order_id: int,
    photo_url: Optional[str] = None,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
    db=next(get_db()),
):
    """Lieferung bestaetigen (Foto-Verification + GPS)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")

    order.status = "delivered"
    order.delivery_photo = photo_url
    order.delivery_gps_lat = gps_lat
    order.delivery_gps_lon = gps_lon
    order.delivery_timestamp = datetime.utcnow()

    db.commit()

    return {"message": "Lieferung bestaetigt", "order_number": order.order_number}


# ============================================================
# CHATBOT ENDPOINTS (Arabisch)
# ============================================================


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db=next(get_db())):
    """KI-Chatbot mit Intent-Recognition (Sprint 3)"""

    from chatbot import detect_language, get_chatbot

    # Chatbot-Instanz
    chatbot = get_chatbot()

    # Sprache erkennen falls nicht angegeben
    is_arabic = (
        request.is_arabic if request.is_arabic is not None else detect_language(request.message)
    )

    # Nachricht verarbeiten
    result = chatbot.process_message(
        session_id=request.session_id, message=request.message, is_arabic=is_arabic
    )

    # Nachricht in DB speichern (offline-kompatibel)
    db_message = ChatMessage(
        session_id=request.session_id,
        user_message=request.message,
        bot_response=result["response"],
        is_arabic=is_arabic,
    )
    db.add(db_message)
    db.commit()

    return ChatResponse(
        session_id=request.session_id,
        response=result["response"],
        is_arabic=is_arabic,
        created_at=datetime.utcnow(),
    )


@app.get("/api/chat/{session_id}")
def get_chat_history(session_id: str, db=next(get_db())):
    """Chat-Verlauf abrufen"""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )

    return [
        {
            "user_message": msg.user_message,
            "bot_response": msg.bot_response,
            "created_at": msg.created_at,
        }
        for msg in messages
    ]


@app.get("/api/chat/{session_id}/suggestions")
def get_chat_suggestions(session_id: str):
    """Naechste Handlungsempfehlungen"""
    from chatbot import get_chatbot

    chatbot = get_chatbot()
    suggestions = chatbot.get_suggestions(session_id)

    return {"session_id": session_id, "suggestions": suggestions}


@app.delete("/api/chat/{session_id}")
def clear_chat_history(session_id: str):
    """Chat-Verlauf loeschen"""
    from chatbot import get_chatbot

    chatbot = get_chatbot()
    cleared = chatbot.clear_chat_history(session_id)

    return {
        "session_id": session_id,
        "cleared": cleared,
        "message": "Chat-Verlauf geloescht" if cleared else "Kein Verlauf gefunden",
    }


# ============================================================
# SYNC ENDPOINTS (Delta-Sync Engine - Sprint 4)
# ============================================================

from sync_engine import get_sync_engine


@app.get("/api/sync/changes")
def get_changes(since: Optional[str] = None, db=next(get_db())):
    """Aenderungen seit letztem Sync abrufen"""
    query = db.query(SyncLog).filter(not SyncLog.synced)

    if since:
        since_datetime = datetime.fromisoformat(since)
        query = query.filter(SyncLog.created_at > since_datetime)

    changes = query.all()

    return {
        "changes": [
            {
                "table": log.table_name,
                "record_id": log.record_id,
                "action": log.action,
                "timestamp": log.created_at.isoformat(),
            }
            for log in changes
        ],
        "count": len(changes),
    }


@app.post("/api/sync/confirm")
def confirm_sync(log_ids: List[int], db=next(get_db())):
    """Sync-Bestaetigung"""
    db.query(SyncLog).filter(SyncLog.id.in_(log_ids)).update(
        {SyncLog.synced: True}, synchronize_session=False
    )
    db.commit()

    return {"message": f"{len(log_ids)} Syncs bestaetigt"}


@app.post("/api/sync/delta")
def delta_sync(table_name: str, record_id: int, action: str, data: Dict[str, Any]):
    """Delta-Sync: Einzelnen Datensatz synchronisieren"""
    engine = get_sync_engine()

    entry = engine.create_sync_entry(
        table_name=table_name, record_id=record_id, action=action, data=data
    )

    return {
        "entry_id": entry.id,
        "status": entry.status.value,
        "checksum": entry.checksum,
        "timestamp": entry.timestamp,
    }


@app.post("/api/sync/all")
def sync_all_pending():
    """Alle ausstehenden Syncs synchronisieren"""
    engine = get_sync_engine()
    results = engine.sync_all_pending()

    return results


@app.get("/api/sync/pending")
def get_pending_syncs():
    """Ausstehende Syncs abrufen"""
    engine = get_sync_engine()
    pending = engine.get_pending_syncs()

    return {
        "pending": [
            {
                "id": entry.id,
                "table": entry.table_name,
                "record_id": entry.record_id,
                "action": entry.action,
                "timestamp": entry.timestamp,
                "retry_count": entry.retry_count,
            }
            for entry in pending
        ],
        "count": len(pending),
    }


@app.get("/api/sync/stats")
def get_sync_stats():
    """Sync-Statistiken abrufen"""
    engine = get_sync_engine()
    stats = engine.get_sync_stats()

    return stats


@app.delete("/api/sync/completed")
def clear_completed_syncs():
    """Abgeschlossene Syncs loeschen"""
    engine = get_sync_engine()
    deleted = engine.clear_completed_syncs()

    return {"deleted": deleted, "message": f"{deleted} abgeschlossene Syncs geloescht"}


# ============================================================
# HEALTH CHECK
# ============================================================


@app.get("/health")
def health_check():
    """Health Check fuer Monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "sqlite",
        "offline_capable": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
def root():
    """API Root"""
    return {
        "name": "Libya B2B Platform API",
        "version": "1.4.0",
        "description": "Offline-first KI-B2B-Plattform fuer Libyen - Sprint 4: Delta-Sync",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# QR-CODE ENDPOINTS (Sprint 2)
# ============================================================

from qr_code import (
    calculate_qr_code_hash,
    generate_delivery_qr_code,
    generate_order_qr_code,
    parse_qr_code,
    validate_order_qr_code,
    verify_delivery,
)


@app.post("/api/qrcode/generate")
def generate_qr(
    order_number: str,
    total_amount: float,
    currency: str = "LYD",
    delivery_address: Optional[str] = None,
):
    """QR-Code fuer Bestellung generieren"""
    qr_base64 = generate_order_qr_code(
        order_number=order_number,
        total_amount=total_amount,
        currency=currency,
        delivery_address=delivery_address,
    )

    return {
        "order_number": order_number,
        "qr_code_base64": qr_base64,
        "hash": calculate_qr_code_hash(order_number),
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.post("/api/qrcode/scan")
def scan_qr(qr_data: str):
    """QR-Code scannen und parsen"""
    parsed = parse_qr_code(qr_data)

    is_valid = False
    if parsed.get("platform") == "LIBYA_B2B":
        is_valid = validate_order_qr_code(parsed)

    return {
        "parsed_data": parsed,
        "is_valid": is_valid,
        "scanned_at": datetime.utcnow().isoformat(),
    }


@app.post("/api/qrcode/delivery-verification")
def delivery_verification(
    order_number: str,
    qr_data: str,
    photo_url: Optional[str] = None,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
):
    """Lieferung via QR-Code verifizieren"""

    parsed = parse_qr_code(qr_data)

    # QR-Code fuer Lieferung generieren
    delivery_qr = generate_delivery_qr_code(
        order_number=order_number, delivery_photo_url=photo_url, gps_lat=gps_lat, gps_lon=gps_lon
    )

    # Verifikation durchfuehren
    verification = verify_delivery(qr_data=parsed, expected_order=order_number)

    return {
        "order_number": order_number,
        "verification": verification,
        "delivery_qr_base64": delivery_qr,
        "verified_at": datetime.utcnow().isoformat(),
    }


@app.get("/api/qrcode/download/{order_number}")
def download_qr(order_number: str, total_amount: float):
    """QR-Code als Download"""
    from fastapi.responses import Response

    qr_bytes = generate_order_qr_code(order_number=order_number, total_amount=total_amount)

    # Base64 zurueck zu Bytes
    import base64

    img_bytes = base64.b64decode(qr_bytes)

    return Response(
        content=img_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=qr_{order_number}.png"},
    )
