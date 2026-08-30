"""
Tests for Phase 1: Server-side Cart & Checkout
MOQ validation, line items, supplier mapping.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def _register_and_login(username, password="pass", role="buyer"):
    """Register user and return authenticated client."""
    c = TestClient(app)
    c.post("/api/auth/register", json={"username": username, "password": password, "role": role})
    return c


def _create_product(authed_client, name="Test Product", price=10.0, moq=5, category="Test"):
    """Create a product and return its ID."""
    resp = authed_client.post("/api/products", json={
        "name": name, "price": price, "moq": moq, "category": category,
        "stock_quantity": 100, "seller_id": None,
    })
    assert resp.status_code == 200
    return resp.json()["id"]


# ============================================================
# CART TESTS
# ============================================================

def test_add_to_cart_success():
    """Adding a product to cart should work."""
    c = _register_and_login("cart_user1")
    pid = _create_product(c, "Cement 50kg", 45.0, moq=1)
    resp = c.post("/api/cart/items", json={"product_id": pid, "quantity": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == pid
    assert data["quantity"] == 5
    assert data["moq"] == 1
    assert data["moq_met"] is True


def test_add_to_cart_moq_violation():
    """Adding fewer items than MOQ should return 400."""
    c = _register_and_login("cart_user2")
    pid = _create_product(c, "Steel Bar", 320.0, moq=10)
    resp = c.post("/api/cart/items", json={"product_id": pid, "quantity": 3})
    assert resp.status_code == 400
    assert "Minimum order quantity" in resp.json()["detail"]


def test_add_to_cart_product_not_found():
    """Adding a non-existent product should return 404."""
    c = _register_and_login("cart_user3")
    resp = c.post("/api/cart/items", json={"product_id": 99999, "quantity": 1})
    assert resp.status_code == 404


def test_get_cart_empty():
    """Empty cart should return 0 items."""
    c = _register_and_login("cart_user4")
    resp = c.get("/api/cart")
    assert resp.status_code == 200
    data = resp.json()
    assert data["item_count"] == 0
    assert data["total"] == 0.0


def test_get_cart_with_items():
    """Cart should show items with supplier info."""
    c = _register_and_login("cart_user5")
    pid = _create_product(c, "Solar Panel", 850.0, moq=1)
    c.post("/api/cart/items", json={"product_id": pid, "quantity": 2})
    resp = c.get("/api/cart")
    assert resp.status_code == 200
    data = resp.json()
    assert data["item_count"] == 1
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["product_price"] == 850.0


def test_update_cart_item():
    """Updating cart item quantity should work."""
    c = _register_and_login("cart_user6")
    pid = _create_product(c, "Generator", 12000.0, moq=1)
    add_resp = c.post("/api/cart/items", json={"product_id": pid, "quantity": 1})
    item_id = add_resp.json()["id"]
    resp = c.put(f"/api/cart/items/{item_id}?quantity=3")
    assert resp.status_code == 200


def test_remove_cart_item():
    """Removing a cart item should work."""
    c = _register_and_login("cart_user7")
    pid = _create_product(c, "LED Light", 95.0, moq=1)
    add_resp = c.post("/api/cart/items", json={"product_id": pid, "quantity": 2})
    item_id = add_resp.json()["id"]
    resp = c.delete(f"/api/cart/items/{item_id}")
    assert resp.status_code == 200
    # Cart should be empty
    cart_resp = c.get("/api/cart")
    assert cart_resp.json()["item_count"] == 0


def test_clear_cart():
    """Clearing cart should remove all items."""
    c = _register_and_login("cart_user8")
    pid = _create_product(c, "Drill", 185.0, moq=1)
    c.post("/api/cart/items", json={"product_id": pid, "quantity": 3})
    resp = c.delete("/api/cart")
    assert resp.status_code == 200
    cart_resp = c.get("/api/cart")
    assert cart_resp.json()["item_count"] == 0


def test_multi_supplier_cart():
    """Cart should handle products from different suppliers."""
    buyer = _register_and_login("multi_cart_buyer")
    seller1 = _register_and_login("multi_cart_s1", role="seller")
    seller2 = _register_and_login("multi_cart_s2", role="seller")

    pid1 = _create_product(seller1, "Cement", 45.0, moq=1)
    pid2 = _create_product(seller2, "Sand", 35.0, moq=1)

    buyer.post("/api/cart/items", json={"product_id": pid1, "quantity": 10, "supplier_id": seller1.post("/api/auth/me").json().get("id")})
    buyer.post("/api/cart/items", json={"product_id": pid2, "quantity": 5, "supplier_id": seller2.post("/api/auth/me").json().get("id")})

    cart = buyer.get("/api/cart").json()
    assert cart["item_count"] == 2
    total = sum(item["product_price"] * item["quantity"] for item in cart["items"])
    assert total == 45 * 10 + 35 * 5


# ============================================================
# ORDER WITH LINE ITEMS TESTS
# ============================================================

def test_order_with_line_items():
    """Order creation should accept and store line items."""
    buyer = _register_and_login("order_buyer1")
    seller = _register_and_login("order_seller1", role="seller")

    pid = _create_product(seller, "Wiring Cable", 320.0, moq=5)
    seller_id = seller.post("/api/auth/me").json().get("id")

    resp = buyer.post("/api/orders", json={
        "total_amount": 640.0,
        "payment_method": "COD",
        "delivery_address": "Tripoli, Main St",
        "items": [{
            "product_id": pid,
            "supplier_id": seller_id,
            "quantity": 2,
            "unit_price": 320.0,
            "moq": 5,
        }],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_number"].startswith("LYB-")
    assert data["total_amount"] == 640.0


def test_order_without_line_items():
    """Order without items should still work (backward compat)."""
    buyer = _register_and_login("order_buyer2")
    resp = buyer.post("/api/orders", json={
        "total_amount": 100.0,
        "payment_method": "COD",
    })
    assert resp.status_code == 200
    assert resp.json()["order_number"].startswith("LYB-")


def test_order_arabic_with_line_items():
    """Arabic order endpoint should also handle line items."""
    buyer = _register_and_login("ar_order_buyer")
    resp = buyer.post("/ar/orders", json={
        "total_amount": 200.0,
        "payment_method": "COD",
        "items": [],
    })
    assert resp.status_code == 200


# ============================================================
# MOQ EDGE CASES
# ============================================================

def test_moq_exactly_met():
    """Quantity exactly at MOQ should succeed."""
    c = _register_and_login("moq_exact")
    pid = _create_product(c, "Paint", 25.0, moq=10)
    resp = c.post("/api/cart/items", json={"product_id": pid, "quantity": 10})
    assert resp.status_code == 200
    assert resp.json()["moq_met"] is True


def test_moq_one():
    """MOQ of 1 should always succeed."""
    c = _register_and_login("moq_one")
    pid = _create_product(c, "Single Item", 50.0, moq=1)
    resp = c.post("/api/cart/items", json={"product_id": pid, "quantity": 1})
    assert resp.status_code == 200
    assert resp.json()["moq_met"] is True


def test_cart_requires_auth():
    """Cart endpoints should require authentication."""
    resp = TestClient(app).get("/api/cart")
    assert resp.status_code in (401, 403)
