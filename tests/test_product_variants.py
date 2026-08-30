"""Tests for Product Variants — CRUD + Owner-Check Security."""
from fastapi.testclient import TestClient
from main import app


def _register(client: TestClient, username: str, role: str = "seller") -> None:
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "pass", "role": role},
    )


def _create_product(client: TestClient) -> int:
    r = client.post(
        "/api/products",
        json={"name": "Test Product", "price": 10.0, "category": "Hardware"},
    )
    assert r.status_code == 200
    return r.json()["id"]


def test_create_variant():
    """Seller creates a variant for own product → 200."""
    c = TestClient(app)
    _register(c, "seller_v1")
    pid = _create_product(c)
    r = c.post(
        f"/api/products/{pid}/variants",
        json={"name": "Red / XL", "price": 12.0, "stock_quantity": 50, "moq": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Red / XL"
    assert data["price"] == 12.0
    assert data["product_id"] == pid


def test_create_variant_wrong_owner():
    """Seller creates variant for another seller's product → 403."""
    c1 = TestClient(app)
    _register(c1, "owner_v1")
    pid = _create_product(c1)

    c2 = TestClient(app)
    _register(c2, "intruder_v1")
    r = c2.post(
        f"/api/products/{pid}/variants",
        json={"name": "Fake Variant", "price": 5.0},
    )
    assert r.status_code == 403


def test_list_variants():
    """Variants are listed correctly."""
    c = TestClient(app)
    _register(c, "seller_v2")
    pid = _create_product(c)
    c.post(f"/api/products/{pid}/variants", json={"name": "A", "price": 10.0})
    c.post(f"/api/products/{pid}/variants", json={"name": "B", "price": 15.0})
    r = c.get(f"/api/products/{pid}/variants")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_variant():
    """Variant update with owner-check."""
    c = TestClient(app)
    _register(c, "seller_v3")
    pid = _create_product(c)
    vr = c.post(
        f"/api/products/{pid}/variants",
        json={"name": "Original", "price": 10.0},
    )
    vid = vr.json()["id"]
    r = c.put(
        f"/api/products/{pid}/variants/{vid}",
        json={"name": "Updated", "price": 20.0, "stock_quantity": 100},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"
    assert r.json()["price"] == 20.0
