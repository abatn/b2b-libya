"""
Libya B2B Platform - Integrationstests
Sprint 5: Vollstaendige Workflow-Tests
Projektversion: v1.5
"""

import pytest


@pytest.fixture
def sample_product():
    return {
        "name": "Integration Test Product",
        "name_arabic": "منتج اختبار التكامل",
        "description": "Full workflow test",
        "price": 75.00,
        "currency": "LYD",
        "category": "building_materials",
        "stock_quantity": 200,
        "moq": 5,
    }


# ============================================================
# FULL WORKFLOW TESTS
# ============================================================

def test_full_product_lifecycle(auth_client, sample_product):
    """Create -> Read -> Update -> Delete"""
    create_resp = auth_client.post("/api/products", json=sample_product)
    assert create_resp.status_code == 200
    product_id = create_resp.json()["id"]

    get_resp = auth_client.get(f"/api/products/{product_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Integration Test Product"

    update_resp = auth_client.put(
        f"/api/products/{product_id}",
        json={"name": "Updated Product", "price": 99.0, "currency": "LYD"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Product"

    delete_resp = auth_client.delete(f"/api/products/{product_id}")
    assert delete_resp.status_code == 200

    get_resp2 = auth_client.get(f"/api/products/{product_id}")
    assert get_resp2.status_code == 404


def test_full_order_workflow(auth_client):
    """Create order -> Track -> Confirm delivery"""
    order_data = {
        "total_amount": 500.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli, Libya",
    }
    order_resp = auth_client.post("/api/orders", json=order_data)
    assert order_resp.status_code == 200
    order = order_resp.json()
    order_id = order["id"]
    order_number = order["order_number"]

    track_resp = auth_client.get(f"/api/orders/{order_number}")
    assert track_resp.status_code == 200
    assert track_resp.json()["status"] == "pending"

    confirm_resp = auth_client.put(f"/api/orders/{order_id}/deliver")
    assert confirm_resp.status_code == 200
    assert "message" in confirm_resp.json()


def test_full_chat_workflow(client):
    """Send message -> Get reply -> Check history"""
    session_id = "integration_test_session"

    resp1 = client.post(
        "/api/chat",
        json={"message": "مرحبا", "session_id": session_id},
    )
    assert resp1.status_code == 200
    data = resp1.json()
    assert "response" in data

    resp2 = client.post(
        "/api/chat",
        json={"message": "ما سعر الأسمنت", "session_id": session_id},
    )
    assert resp2.status_code == 200

    hist_resp = client.get(f"/api/chat/{session_id}")
    assert hist_resp.status_code == 200


def test_full_b2b_workflow(auth_client, sample_product):
    """Full B2B: Product -> Order -> Delivery -> Review -> Dashboard"""
    prod_resp = auth_client.post("/api/products", json=sample_product)
    product_id = prod_resp.json()["id"]

    order_data = {
        "total_amount": 375.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Benghazi",
    }
    order_resp = auth_client.post("/api/orders", json=order_data)
    order_id = order_resp.json()["id"]

    confirm_resp = auth_client.put(f"/api/orders/{order_id}/deliver")
    assert confirm_resp.status_code == 200

    review_resp = auth_client.post(
        "/api/reviews",
        json={"product_id": product_id, "rating": 5, "comment": "Great!"},
    )
    assert review_resp.status_code == 200

    dash_resp = auth_client.get("/api/b2b/dashboard")
    assert dash_resp.status_code == 200
    assert dash_resp.json()["total_orders"] >= 1


def test_rfq_to_order_flow(auth_client):
    """RFQ -> Quote"""
    rfq_resp = auth_client.post(
        "/api/b2b/rfq",
        json={
            "product_name": "Steel Rebar",
            "product_name_arabic": "حديد تسليح",
            "quantity": 500,
            "unit": "tons",
            "delivery_address": "Misrata",
            "notes": "Urgent",
        },
    )
    assert rfq_resp.status_code == 200
    rfq_id = rfq_resp.json()["id"]

    view_resp = auth_client.get(f"/api/b2b/rfq/{rfq_id}")
    assert view_resp.status_code == 200

    update_resp = auth_client.put(
        f"/api/b2b/rfq/{rfq_id}", params={"status": "quoted"}
    )
    assert update_resp.status_code == 200


def test_search_and_filter_flow(client, auth_client, sample_product):
    """Create product -> Search -> Filter"""
    auth_client.post("/api/products", json=sample_product)
    search_resp = client.get("/api/search?q=Integration")
    assert search_resp.status_code == 200
