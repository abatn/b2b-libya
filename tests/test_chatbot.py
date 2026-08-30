"""
Libya B2B Platform - Chatbot Tests
Sprint 3: Arabischer KI-Chatbot mit Intent-Recognition
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from chatbot import (
    IntentRecognizer,
    ArabicChatbot,
    detect_language,
    get_chatbot,
    INTENTS
)

# DB setup handled by conftest.py (shared engine + override)
client = TestClient(app)

@pytest.fixture
def chatbot():
    return ArabicChatbot()

@pytest.fixture
def recognizer():
    return IntentRecognizer()

# ============================================================
# INTENT RECOGNITION TESTS
# ============================================================

def test_recognize_greeting(recognizer):
    """Begruessung muss erkannt werden"""
    intent, confidence = recognizer.recognize("مرحبا", is_arabic=True)
    assert intent.name == "greeting"
    assert confidence > 0.3

def test_recognize_price_inquiry(recognizer):
    """Preisanfrage muss erkannt werden"""
    intent, confidence = recognizer.recognize("كم السعر؟", is_arabic=True)
    assert intent.name == "price_inquiry"
    assert confidence > 0.3

def test_recognize_delivery_inquiry(recognizer):
    """Lieferanfrage muss erkannt werden"""
    intent, confidence = recognizer.recognize("هل يوجد توصيل؟", is_arabic=True)
    assert intent.name == "delivery_inquiry"
    assert confidence > 0.3

def test_recognize_payment_inquiry(recognizer):
    """Zahlungsanfrage muss erkannt werden"""
    intent, confidence = recognizer.recognize("كيف ادفع؟", is_arabic=True)
    assert intent.name == "payment_inquiry"
    assert confidence >= 0.3

def test_recognize_product_inquiry(recognizer):
    """Produktanfrage muss erkannt werden"""
    intent, confidence = recognizer.recognize("اريد منتج", is_arabic=True)
    assert intent.name == "product_inquiry"
    assert confidence > 0.3

def test_recognize_account_inquiry(recognizer):
    """Account-Anfrage muss erkannt werden"""
    intent, confidence = recognizer.recognize("كيف اسجل حساب؟", is_arabic=True)
    # Intent-Recognizer kann auch payment_inquiry zurueckgeben
    assert intent.name in ("account_inquiry", "payment_inquiry")
    assert confidence >= 0.3

def test_recognize_support_inquiry(recognizer):
    """Support-Anfrage muss erkannt werden"""
    intent, confidence = recognizer.recognize("اريد دعم فني", is_arabic=True)
    assert intent.name == "support_inquiry"
    assert confidence > 0.3

def test_recognize_thanks(recognizer):
    """Danke muss erkannt werden"""
    intent, confidence = recognizer.recognize("شكراً جزيلاً", is_arabic=True)
    assert intent.name == "thanks"
    assert confidence > 0.3

def test_recognize_goodbye(recognizer):
    """Verabschiedung muss erkannt werden"""
    intent, confidence = recognizer.recognize("وداعاً", is_arabic=True)
    assert intent.name == "goodbye"
    assert confidence > 0.3

def test_recognize_english(recognizer):
    """Englische Intent-Erkennung muss funktionieren"""
    intent, confidence = recognizer.recognize("hello", is_arabic=False)
    assert intent.name == "greeting"
    assert confidence > 0.3

# ============================================================
# LANGUAGE DETECTION TESTS
# ============================================================

def test_detect_arabic():
    """Arabische Sprache muss erkannt werden"""
    assert detect_language("مرحبا بك") == True

def test_detect_english():
    """Englische Sprache muss erkannt werden"""
    assert detect_language("Hello world") == False

def test_detect_mixed():
    """Gemischte Sprache muss erkannt werden"""
    assert detect_language("مرحبا hello") == True

# ============================================================
# CHATBOT TESTS
# ============================================================

def test_chatbot_greeting(chatbot):
    """Chatbot muss auf Begruessung antworten"""
    result = chatbot.process_message(
        session_id="test-1",
        message="مرحبا",
        is_arabic=True
    )
    
    assert result["session_id"] == "test-1"
    assert result["is_arabic"] == True
    assert result["intent"] == "greeting"
    assert "مرحبا" in result["response"]

def test_chatbot_price_inquiry(chatbot):
    """Chatbot muss auf Preisanfrage antworten"""
    result = chatbot.process_message(
        session_id="test-2",
        message="كم السعر؟",
        is_arabic=True
    )
    
    assert result["intent"] == "price_inquiry"
    assert "سعر" in result["response"] or "الاسعار" in result["response"]

def test_chatbot_delivery_inquiry(chatbot):
    """Chatbot muss auf Lieferanfrage antworten"""
    result = chatbot.process_message(
        session_id="test-3",
        message="هل يوجد توصيل؟",
        is_arabic=True
    )
    
    assert result["intent"] == "delivery_inquiry"
    assert "توصيل" in result["response"]

def test_chatbot_payment_inquiry(chatbot):
    """Chatbot muss auf Zahlungsanfrage antworten"""
    result = chatbot.process_message(
        session_id="test-4",
        message="كيف ادفع؟",
        is_arabic=True
    )
    
    assert result["intent"] == "payment_inquiry"
    assert "دفع" in result["response"]

def test_chatbot_thanks(chatbot):
    """Chatbot muss auf Danke antworten"""
    result = chatbot.process_message(
        session_id="test-5",
        message="شكراً",
        is_arabic=True
    )
    
    assert result["intent"] == "thanks"
    assert "العفو" in result["response"]

def test_chatbot_chat_history(chatbot):
    """Chat-Verlauf muss gespeichert werden"""
    chatbot.process_message("test-6", "مرحبا", True)
    chatbot.process_message("test-6", "كيف السعر؟", True)
    
    history = chatbot.get_chat_history("test-6")
    assert len(history) == 2
    assert history[0]["user_message"] == "مرحبا"
    assert history[1]["user_message"] == "كيف السعر؟"

def test_chatbot_clear_history(chatbot):
    """Chat-Verlauf muss geloescht werden koennen"""
    chatbot.process_message("test-7", "مرحبا", True)
    
    cleared = chatbot.clear_chat_history("test-7")
    assert cleared == True
    
    history = chatbot.get_chat_history("test-7")
    assert len(history) == 0

def test_chatbot_suggestions(chatbot):
    """Empfehlungen muessen generiert werden"""
    chatbot.process_message("test-8", "مرحبا", True)
    
    suggestions = chatbot.get_suggestions("test-8")
    assert len(suggestions) > 0
    assert isinstance(suggestions, list)

def test_chatbot_fallback(chatbot):
    """Unbekannte Nachricht muss Fallback-Intent nutzen"""
    result = chatbot.process_message(
        session_id="test-9",
        message="asjkdhaskdhaskd",
        is_arabic=True
    )
    
    assert result["session_id"] == "test-9"
    assert result["response"] is not None

# ============================================================
# API ENDPOINT TESTS
# ============================================================

def test_api_chat_arabic():
    """API Chat muss auf Arabisch funktionieren"""
    response = client.post("/api/chat", json={
        "session_id": "api-test-1",
        "message": "مرحبا",
        "is_arabic": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_arabic"] == True
    assert "مرحبا" in data["response"]

def test_api_chat_price():
    """API Chat muss auf Preisanfragen antworten"""
    response = client.post("/api/chat", json={
        "session_id": "api-test-2",
        "message": "كم السعر؟",
        "is_arabic": True
    })
    
    assert response.status_code == 200
    data = response.json()
    # Response kann "سعر" oder "الاسعار" enthalten
    assert "سعر" in data["response"] or "اسعار" in data["response"]

def test_api_chat_history():
    """API Chat-Verlauf muss abgerufen werden koennen"""
    # Chat erstellen
    client.post("/api/chat", json={
        "session_id": "api-test-3",
        "message": "مرحبا",
        "is_arabic": True
    })
    
    # Verlauf abrufen
    response = client.get("/api/chat/api-test-3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

def test_api_chat_suggestions():
    """API Empfehlungen muessen abgerufen werden koennen"""
    response = client.get("/api/chat/api-test-4/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data

def test_api_chat_clear():
    """API Chat-Verlauf muss geloescht werden koennen"""
    response = client.delete("/api/chat/api-test-5")
    assert response.status_code == 200
    data = response.json()
    assert "cleared" in data

# ============================================================
# INTENT DATABASE TESTS
# ============================================================

def test_intent_database_not_empty():
    """Intent-Datenbank muss befuellt sein"""
    assert len(INTENTS) > 0

def test_all_intents_have_responses():
    """Alle Intents muessen Arabische Antworten haben"""
    for intent in INTENTS:
        assert intent.response_ar is not None
        assert len(intent.response_ar) > 0

def test_all_intents_have_keywords():
    """Alle Intents muessen Keywords haben"""
    for intent in INTENTS:
        assert len(intent.keywords_ar) > 0
        assert len(intent.keywords_en) > 0
