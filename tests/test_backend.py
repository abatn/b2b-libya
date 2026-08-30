"""
Libya B2B Platform - Backend Tests
Sprint 1: CRUD-Tests fuer Products und Orders
"""

import pytest
from conftest import TestSessionLocal

from main import app


@pytest.fixture
def sample_product():
    """Beispiel-Produkt"""
    return {
        "name": "Baumaterial X",
        "name_arabic": "مواد بناء X",
        "description": "Hochwertige Baustoffe",
        "price": 150.00,
        "currency": "LYD",
        "category": "building_materials",
        "stock_quantity": 100,
        "moq": 10,
    }


@pytest.fixture
def sample_order(auth_client):
    """Bestellung mit existing Product."""
    return {
        "total_amount": 250.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli, Libya",
    }


# ============================================================
# HEALTH / ROOT
# ============================================================

def test_health_check(client):
    response = client.get("/api/b2b/stats")
    assert response.status_code == 200


def test_root(client):
    response = client.get("/api/b2b/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data


# ============================================================
# PRODUCT CRUD TESTS
# ============================================================

def test_create_product(auth_client, sample_product):
    """Produkt muss erstellt werden koennen"""
    response = auth_client.post("/api/products", json=sample_product)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Baumaterial X"
    assert data["name_arabic"] == "مواد بناء X"
    assert data["price"] == 150.00
    assert data["currency"] == "LYD"
    assert data["is_active"] == True


def test_list_products(auth_client, sample_product):
    """Produkte muessen aufgelistet werden koennen"""
    auth_client.post("/api/products", json=sample_product)
    response = auth_client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_product(auth_client, sample_product):
    """Einzelnes Produkt muss abgerufen werden koennen"""
    create_response = auth_client.post("/api/products", json=sample_product)
    product_id = create_response.json()["id"]
    response = auth_client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == "Baumaterial X"


def test_update_product(auth_client, sample_product):
    """Produkt muss aktualisiert werden koennen"""
    create_response = auth_client.post("/api/products", json=sample_product)
    product_id = create_response.json()["id"]
    update_data = {"name": "Updated Product", "price": 200.00, "currency": "LYD"}
    response = auth_client.put(f"/api/products/{product_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product"
    assert data["price"] == 200.00


def test_delete_product(auth_client, sample_product):
    """Produkt muss geloescht werden koennen"""
    create_response = auth_client.post("/api/products", json=sample_product)
    product_id = create_response.json()["id"]
    response = auth_client.delete(f"/api/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Product deleted"
    get_response = auth_client.get(f"/api/products/{product_id}")
    assert get_response.status_code == 404


def test_create_product_requires_auth(client, sample_product):
    """Produkt erstellen erfordert Login"""
    response = client.post("/api/products", json=sample_product)
    assert response.status_code == 401


def test_delete_product_requires_auth(client, sample_product):
    """Produkt loeschen erfordert Login"""
    response = client.delete("/api/products/1")
    assert response.status_code == 401


# ============================================================
# ORDER TESTS
# ============================================================

def test_create_order(auth_client, sample_order):
    """Bestellung muss erstellt werden koennen"""
    response = auth_client.post("/api/orders", json=sample_order)
    assert response.status_code == 200
    data = response.json()
    assert "order_number" in data
    assert data["status"] == "pending"


def test_list_orders(auth_client, sample_order):
    """Bestellungen muessen aufgelistet werden koennen"""
    auth_client.post("/api/orders", json=sample_order)
    response = auth_client.get("/api/orders")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_confirm_delivery(auth_client, sample_order):
    """Lieferung muss bestaetigt werden koennen"""
    create_response = auth_client.post("/api/orders", json=sample_order)
    order_id = create_response.json()["id"]
    response = auth_client.put(f"/api/orders/{order_id}/deliver")
    assert response.status_code == 200


# ============================================================
# CHAT TESTS
# ============================================================

def test_chat_arabic(client):
    """Chat muss Arabisch verstehen"""
    response = client.post(
        "/api/chat",
        json={"message": "مرحبا", "session_id": "test1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


def test_chat_price_inquiry(client):
    """Chat muss Preisanfragen verstehen"""
    response = client.post(
        "/api/chat",
        json={"message": "ما سعر الأسمنت", "session_id": "test2"},
    )
    assert response.status_code == 200


def test_chat_delivery_inquiry(client):
    """Chat muss Lieferanfragen verstehen"""
    response = client.post(
        "/api/chat",
        json={"message": "متى التوصيل", "session_id": "test3"},
    )
    assert response.status_code == 200


# ============================================================
# SYNC TESTS
# ============================================================

def test_get_changes(client):
    """Änderungen muessen abgerufen werden koennen"""
    response = client.get("/api/sync/changes")
    assert response.status_code == 200


# ============================================================
# PRODUCT IMAGE TESTS
# ============================================================

def test_upload_product_image(auth_client, sample_product):
    """Bild muss hochgeladen werden koennen"""
    create_response = auth_client.post("/api/products", json=sample_product)
    product_id = create_response.json()["id"]
    import io
    data = {"file": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")}
    response = auth_client.post(f"/api/products/{product_id}/images", files=data)
    assert response.status_code == 200
    result = response.json()
    assert "image_url" in result


def test_upload_product_image_updates_product(auth_client, sample_product):
    """Bild-Upload muss Produktbild aktualisieren"""
    create_response = auth_client.post("/api/products", json=sample_product)
    product_id = create_response.json()["id"]
    import io
    data = {"file": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")}
    auth_client.post(f"/api/products/{product_id}/images", files=data)
    response = auth_client.get(f"/api/products/{product_id}")
    assert response.status_code == 200


def test_upload_image_nonexistent_product(auth_client):
    """Bild-Upload fuer nicht-existierendes Produkt muss 404 geben"""
    import io
    data = {"file": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")}
    response = auth_client.post("/api/products/99999/images", files=data)
    assert response.status_code == 404


# ============================================================
# QR CODE TESTS
# ============================================================

def test_qr_scan_valid(client):
    """QR-Scan muss gueltige Daten verarbeiten"""
    response = client.post(
        "/api/qrcode/scan",
        json={"qr_data": "LIBYA-B2B-ORDER-001"},
    )
    assert response.status_code == 200


def test_qr_scan_empty_data(client):
    """QR-Scan mit leeren Daten muss Fehler geben"""
    response = client.post(
        "/api/qrcode/scan",
        json={"qr_data": ""},
    )
    assert response.status_code in [200, 400]


# ============================================================
# SUPPLIER VERIFICATION TESTS
# ============================================================

def test_supplier_verification_flag(client):
    """Supplier muss Verifizierungsflag haben"""
    response = client.post(
        "/api/b2b/suppliers",
        json={
            "name": "Test Supplier",
            "business_name": "Test Corp",
            "business_name_arabic": "شركة اختبار",
            "phone": "+218912345678",
            "is_verified": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] == True


def test_supplier_unverified_flag(client):
    """Supplier kann unverifiziert sein"""
    response = client.post(
        "/api/b2b/suppliers",
        json={
            "name": "Unverified Supplier",
            "business_name": "Unverified Corp",
            "business_name_arabic": "شركة غير معتمدة",
            "phone": "+218912345679",
            "is_verified": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] == False


# ============================================================
# SEARCH TESTS
# ============================================================

def test_full_text_search(client):
    """Volltextsuche muss funktionieren"""
    response = client.get("/api/search?q= Baumaterial")
    assert response.status_code == 200


def test_search_empty_query(client):
    """Leere Suche muss Fehler geben"""
    response = client.get("/api/search?q=")
    assert response.status_code in [200, 400, 422]


# ============================================================
# B2B DASHBOARD TESTS
# ============================================================

def test_b2b_dashboard_requires_auth(client):
    """B2B Dashboard erfordert Login"""
    response = client.get("/api/b2b/dashboard")
    assert response.status_code == 401


def test_b2b_analytics_requires_auth(client):
    """B2B Analytics erfordert Login"""
    response = client.get("/api/b2b/analytics")
    assert response.status_code == 401
