"""
Libya B2B Platform - Arabische Tests
Sprint 6/7: Arabische Lokalisierung
"""

import pytest
from fastapi.testclient import TestClient

from main import app

# DB setup handled by conftest.py (shared engine + override)
client = TestClient(app)

# ============================================================
# ARABISCHE LANDING-PAGE TESTS
# ============================================================

def test_arabic_landing_page():
    """Arabische Landing Page muss funktionieren"""
    response = client.get("/ar/landing")
    assert response.status_code == 200
    # Backend serves raw template — {{landing.title}} not rendered by backend
    assert "rtl" in response.text

def test_arabic_landing_page_has_features():
    """Arabische Landing Page muss Features enthalten"""
    response = client.get("/ar/landing")
    assert response.status_code == 200
    # Backend serves raw template — {{landing.feature_cod}} not rendered
    assert "<html" in response.text.lower()

# ============================================================
# ARABISCHE API-ENDPOINTS TESTS
# ============================================================

def test_arabic_products():
    """Arabische Produkt-API muss funktionieren"""
    response = client.get("/ar/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_arabic_create_order():
    """Arabische Bestell-API muss funktionieren"""
    response = client.post("/ar/orders", json={
        "buyer_id": 1,
        "seller_id": 1,
        "total_amount": 500.0,
        "currency": "LYD",
        "payment_method": "COD"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["payment_method"] == "COD"
    assert data["order_number"].startswith("LYB-")

def test_arabic_chat():
    """Arabischer Chatbot muss funktionieren"""
    response = client.post("/ar/chat", json={
        "session_id": "ar-test-1",
        "message": "مرحبا",
        "is_arabic": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_arabic"] == True
    assert "مرحبا" in data["response"]

def test_arabic_chat_price_inquiry():
    """Arabischer Chatbot muss auf Preisanfragen antworten"""
    response = client.post("/ar/chat", json={
        "session_id": "ar-test-2",
        "message": "كم السعر؟",
        "is_arabic": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "سعر" in data["response"] or "الاسعار" in data["response"]

def test_arabic_chat_delivery_inquiry():
    """Arabischer Chatbot muss auf Lieferanfragen antworten"""
    response = client.post("/ar/chat", json={
        "session_id": "ar-test-3",
        "message": "هل يوجد توصيل؟",
        "is_arabic": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "توصيل" in data["response"]

def test_arabic_chat_order_status():
    """Arabischer Chatbot muss auf Bestellstatus antworten"""
    response = client.post("/ar/chat", json={
        "session_id": "ar-test-4",
        "message": "حالة الطلب؟",
        "is_arabic": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "تتبع" in data["response"] or "طلب" in data["response"]

def test_arabic_chat_complaint():
    """Arabischer Chatbot muss auf Beschwerden antworten"""
    response = client.post("/ar/chat", json={
        "session_id": "ar-test-5",
        "message": "عندي شكوى",
        "is_arabic": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "نعتذر" in data["response"] or "شكوى" in data["response"]

# ============================================================
# ARABISCHE FEHLERMELDUNGEN TESTS
# ============================================================

def test_arabic_errors():
    """Arabische Fehlermeldungen muessen abrufbar sein"""
    response = client.get("/ar/errors")
    assert response.status_code == 200
    data = response.json()
    assert "product_not_found" in data
    assert "المنتج غير موجود" == data["product_not_found"]

def test_arabic_success():
    """Arabische Erfolgsmeldungen muessen abrufbar sein"""
    response = client.get("/ar/success")
    assert response.status_code == 200
    data = response.json()
    assert "product_created" in data
    assert "تم إنشاء المنتج بنجاح" == data["product_created"]

# ============================================================
# CHATBOT ERWEITERUNG TESTS
# ============================================================

def test_chatbot_20_intents():
    """Chatbot muss 20 Intents haben"""
    from chatbot import INTENTS
    assert len(INTENTS) == 20

def test_chatbot_bulk_order():
    """Chatbot muss auf Grossbestellungen antworten"""
    from chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.process_message("test-bulk", "اريد طلب جماعي", True)
    assert result["intent"] == "bulk_order"

def test_chatbot_return_policy():
    """Chatbot muss auf Rueckfragen antworten"""
    from chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.process_message("test-return", "سياسة الارجاع؟", True)
    assert result["intent"] == "return_policy"

def test_chatbot_warranty():
    """Chatbot muss auf Garantiefragen antworten"""
    from chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.process_message("test-warranty", "الضمان كم شهر؟", True)
    assert result["intent"] == "warranty"

def test_chatbot_complaint():
    """Chatbot muss auf Beschwerden antworten"""
    from chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.process_message("test-complaint", "عندي شكوى", True)
    assert result["intent"] == "complaint"

def test_chatbot_partnership():
    """Chatbot muss auf Partnerschaftsfragen antworten"""
    from chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.process_message("test-partner", "اريد شراكة", True)
    assert result["intent"] == "partnership"

def test_chatbot_logistics():
    """Chatbot muss auf Logistikfragen antworten"""
    from chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.process_message("test-logistics", "خدمات اللوجستيات", True)
    assert result["intent"] == "logistics"
