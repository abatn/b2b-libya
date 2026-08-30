"""
Libya B2B Platform - QR-Code Tests
Sprint 2: QR-Code-Generierung und Scan-Tests
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from qr_code import (
    generate_order_qr_code,
    generate_delivery_qr_code,
    parse_qr_code,
    validate_order_qr_code,
    verify_delivery,
    calculate_qr_code_hash
)

# DB setup handled by conftest.py (shared engine + override)
client = TestClient(app)

@pytest.fixture
def sample_order_data():
    return {
        "order_number": "LYB-20260815-123456",
        "total_amount": 450.00,
        "currency": "LYD",
        "delivery_address": "Tripolis, Gergaresch"
    }

# ============================================================
# QR-CODE GENERATION TESTS
# ============================================================

def test_generate_order_qr_code(sample_order_data):
    """QR-Code fuer Bestellung muss generiert werden koennen"""
    qr_base64 = generate_order_qr_code(
        order_number=sample_order_data["order_number"],
        total_amount=sample_order_data["total_amount"],
        currency=sample_order_data["currency"],
        delivery_address=sample_order_data["delivery_address"]
    )
    
    assert qr_base64 is not None
    assert len(qr_base64) > 0
    # Base64 Validierung
    import base64
    decoded = base64.b64decode(qr_base64)
    assert len(decoded) > 0

def test_generate_delivery_qr_code():
    """Lieferungs-QR-Code muss generiert werden koennen"""
    qr_base64 = generate_delivery_qr_code(
        order_number="LYB-20260815-123456",
        delivery_photo_url="delivery_photo.jpg",
        gps_lat=32.8872,
        gps_lon=13.1913
    )
    
    assert qr_base64 is not None
    assert len(qr_base64) > 0

def test_calculate_qr_code_hash():
    """Hash muss einzigartig sein"""
    hash1 = calculate_qr_code_hash("ORDER-001")
    hash2 = calculate_qr_code_hash("ORDER-002")
    
    assert hash1 != hash2
    assert len(hash1) == 16

# ============================================================
# QR-CODE PARSING TESTS
# ============================================================

def test_parse_qr_code():
    """QR-Code-String muss korrekt geparst werden"""
    qr_string = "LIBYA_B2B|order:LYB-001|amount:100.0|currency:LYD"
    parsed = parse_qr_code(qr_string)
    
    assert parsed["platform"] == "LIBYA_B2B"
    assert parsed["order"] == "LYB-001"
    assert parsed["amount"] == "100.0"
    assert parsed["currency"] == "LYD"

def test_validate_order_qr_code_valid():
    """Gueltiger QR-Code muss validiert werden"""
    qr_data = {
        "platform": "LIBYA_B2B",
        "order": "LYB-001",
        "amount": "100.0",
        "currency": "LYD"
    }
    
    assert validate_order_qr_code(qr_data) == True

def test_validate_order_qr_code_invalid_platform():
    """QR-Code mit falscher Platform muss abgelehnt werden"""
    qr_data = {
        "platform": "OTHER_PLATFORM",
        "order": "LYB-001",
        "amount": "100.0",
        "currency": "LYD"
    }
    
    assert validate_order_qr_code(qr_data) == False

def test_validate_order_qr_code_missing_fields():
    """QR-Code ohne Pflichtfelder muss abgelehnt werden"""
    qr_data = {
        "platform": "LIBYA_B2B"
        # Fehlende Felder: order, amount, currency
    }
    
    assert validate_order_qr_code(qr_data) == False

def test_validate_order_qr_code_negative_amount():
    """QR-Code mit negativem Betrag muss abgelehnt werden"""
    qr_data = {
        "platform": "LIBYA_B2B",
        "order": "LYB-001",
        "amount": "-100.0",
        "currency": "LYD"
    }
    
    assert validate_order_qr_code(qr_data) == False

# ============================================================
# QR-CODE VERIFICATION TESTS
# ============================================================

def test_verify_delivery_success():
    """Erfolgreiche Lieferung muss verifiziert werden"""
    qr_data = {
        "order": "LYB-001",
        "photo": "delivery_photo.jpg",
        "lat": "32.8872",
        "lon": "13.1913",
        "delivered_at": "2026-08-15T10:00:00"
    }
    
    result = verify_delivery(
        qr_data=qr_data,
        expected_order="LYB-001"
    )
    
    assert result["verified"] == True
    assert result["order_match"] == True
    assert result["has_photo"] == True
    assert result["has_gps"] == True
    assert result["timestamp_valid"] == True

def test_verify_delivery_wrong_order():
    """Falsche Bestellnummer muss abgelehnt werden"""
    qr_data = {
        "order": "LYB-999",
        "photo": "delivery_photo.jpg",
        "lat": "32.8872",
        "lon": "13.1913",
        "delivered_at": "2026-08-15T10:00:00"
    }
    
    result = verify_delivery(
        qr_data=qr_data,
        expected_order="LYB-001"
    )
    
    assert result["verified"] == False
    assert result["order_match"] == False

def test_verify_delivery_no_photo():
    """Fehlendes Foto muss abgelehnt werden"""
    qr_data = {
        "order": "LYB-001",
        "lat": "32.8872",
        "lon": "13.1913",
        "delivered_at": "2026-08-15T10:00:00"
    }
    
    result = verify_delivery(
        qr_data=qr_data,
        expected_order="LYB-001"
    )
    
    assert result["verified"] == False
    assert result["has_photo"] == False

def test_verify_delivery_no_gps():
    """Fehlendes GPS muss abgelehnt werden"""
    qr_data = {
        "order": "LYB-001",
        "photo": "delivery_photo.jpg",
        "delivered_at": "2026-08-15T10:00:00"
    }
    
    result = verify_delivery(
        qr_data=qr_data,
        expected_order="LYB-001"
    )
    
    assert result["verified"] == False
    assert result["has_gps"] == False

# ============================================================
# API ENDPOINT TESTS
# ============================================================

def test_api_generate_qr(sample_order_data):
    """API QR-Code-Generierung muss funktionieren"""
    response = client.post(
        "/api/qrcode/generate",
        params={
            "order_number": sample_order_data["order_number"],
            "total_amount": sample_order_data["total_amount"],
            "currency": sample_order_data["currency"],
            "delivery_address": sample_order_data["delivery_address"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["order_number"] == sample_order_data["order_number"]
    assert "qr_code_base64" in data
    assert "hash" in data

def test_api_scan_qr():
    """API QR-Code-Scan muss funktionieren"""
    qr_data = "LIBYA_B2B|order:LYB-001|amount:100.0|currency:LYD"
    
    response = client.post(
        "/api/qrcode/scan",
        json={"qr_data": qr_data}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["parsed_data"]["platform"] == "LIBYA_B2B"

def test_api_delivery_verification():
    """API Lieferungsverifikation muss funktionieren"""
    qr_data = "order:LYB-001|photo:delivery.jpg|lat:32.8872|lon:13.1913|delivered_at:2026-08-15T10:00:00"
    
    response = client.post(
        "/api/qrcode/delivery-verification",
        params={
            "order_number": "LYB-001",
            "qr_data": qr_data,
            "photo_url": "delivery.jpg",
            "gps_lat": 32.8872,
            "gps_lon": 13.1913
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "verification" in data
    assert "delivery_qr_base64" in data
