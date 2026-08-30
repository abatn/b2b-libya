"""
Libya B2B Platform - Cart Tests
Sprint 11: Server-side cart management.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def product(auth_client):
    """Create a test product and return its id."""
    resp = auth_client.post(
        "/api/products",
        json={
            "name": "Cart Test Product",
            "price": 25.0,
            "currency": "LYD",
            "category": "hardware",
            "stock_quantity": 100,
        },
    )
    return resp.json()["id"]


# ============================================================
# CART CRUD TESTS
# ============================================================

def test_get_empty_cart(auth_client):
    """Empty cart returns empty list."""
    resp = auth_client.get("/api/cart")
    assert resp.status_code == 200
    # Cart returns a CartResponse object with items list
    data = resp.json()
    assert "items" in data
    assert data["items"] == []


def test_add_to_cart(auth_client, product):
    """Add item to cart."""
    resp = auth_client.post(
        "/api/cart/items",
        json={"product_id": product, "quantity": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == product
    assert data["quantity"] == 3


def test_add_nonexistent_product(auth_client):
    """Adding nonexistent product returns 404."""
    resp = auth_client.post(
        "/api/cart/items",
        json={"product_id": 99999, "quantity": 1},
    )
    assert resp.status_code == 404


def test_add_duplicate_item(auth_client, product):
    """Adding same product again updates quantity."""
    auth_client.post(
        "/api/cart/items",
        json={"product_id": product, "quantity": 2},
    )
    resp = auth_client.post(
        "/api/cart/items",
        json={"product_id": product, "quantity": 3},
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 5


def test_cart_total(auth_client, product):
    """Cart returns correct total."""
    auth_client.post(
        "/api/cart/items",
        json={"product_id": product, "quantity": 4},
    )
    resp = auth_client.get("/api/cart")
    data = resp.json()
    assert len(data["items"]) >= 1
    assert data["total"] > 0


def test_update_cart_item(auth_client, product):
    """Update cart item quantity."""
    add_resp = auth_client.post(
        "/api/cart/items",
        json={"product_id": product, "quantity": 2},
    )
    item_id = add_resp.json()["id"]
    resp = auth_client.put(f"/api/cart/items/{item_id}", params={"quantity": 10})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Cart updated"


def test_remove_from_cart(auth_client, product):
    """Remove item from cart."""
    add_resp = auth_client.post(
        "/api/cart/items",
        json={"product_id": product, "quantity": 1},
    )
    item_id = add_resp.json()["id"]
    resp = auth_client.delete(f"/api/cart/items/{item_id}")
    assert resp.status_code == 200
    # Verify empty
    cart_resp = auth_client.get("/api/cart")
    assert cart_resp.json()["items"] == []


def test_clear_cart(auth_client, product):
    """Clear entire cart."""
    auth_client.post(
        "/api/cart/items",
        json={"product_id": product, "quantity": 5},
    )
    resp = auth_client.delete("/api/cart")
    assert resp.status_code == 200
    # Verify empty
    cart_resp = auth_client.get("/api/cart")
    assert cart_resp.json()["items"] == []
