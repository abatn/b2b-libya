"""Tests for Shipping — rates, shipments, tracking, auth."""
from fastapi.testclient import TestClient
from main import app


def _register(client: TestClient, username: str, role: str = "buyer") -> None:
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "pass", "role": role},
    )


def test_calculate_shipping():
    """Shipping cost calculation returns options."""
    c = TestClient(app)
    _register(c, "buyer_ship1")
    r = c.post("/api/shipping/calculate?origin=Tripoli&destination=Misrata&weight_kg=5")
    assert r.status_code == 200
    assert "options" in r.json()


def test_create_shipment():
    """Authenticated user creates a shipment."""
    c = TestClient(app)
    _register(c, "seller_ship1", "seller")
    pr = c.post(
        "/api/products",
        json={"name": "Ship Test", "price": 50.0, "category": "Hardware", "moq": 1},
    )
    pid = pr.json()["id"]
    c.post("/api/cart/add", json={"product_id": pid, "quantity": 2})
    orr = c.post(
        "/api/orders",
        json={
            "total_amount": 100.0,
            "payment_method": "COD",
            "delivery_address": "Tripoli",
            "items": [{"product_id": pid, "quantity": 2, "unit_price": 50.0, "moq": 1}],
        },
    )
    oid = orr.json()["id"]
    r = c.post(
        "/api/shipping",
        json={
            "order_id": oid,
            "carrier": "Aramex",
            "weight_kg": 2.5,
            "origin_city": "Tripoli",
            "destination_city": "Misrata",
            "estimated_days": 3,
        },
    )
    assert r.status_code == 200
    assert r.json()["carrier"] == "Aramex"


def test_get_tracking():
    """Tracking events are loaded (public endpoint)."""
    c = TestClient(app)
    _register(c, "seller_track1", "seller")
    pr = c.post(
        "/api/products",
        json={"name": "Track Test", "price": 50.0, "category": "Hardware", "moq": 1},
    )
    pid = pr.json()["id"]
    c.post("/api/cart/add", json={"product_id": pid, "quantity": 1})
    orr = c.post(
        "/api/orders",
        json={
            "total_amount": 50.0,
            "payment_method": "COD",
            "delivery_address": "Tripoli",
            "items": [{"product_id": pid, "quantity": 1, "unit_price": 50.0, "moq": 1}],
        },
    )
    oid = orr.json()["id"]
    sr = c.post(
        "/api/shipping",
        json={"order_id": oid, "carrier": "local", "status": "pending"},
    )
    sid = sr.json()["id"]
    r = c.get(f"/api/shipping/{sid}/tracking")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_update_shipment_status():
    """Seller updates shipment status — order auto-creates via cart."""
    c = TestClient(app)
    # Register a buyer first (who creates the order)
    _register(c, "buyer_stat1", "buyer")
    pr = c.post(
        "/api/products",
        json={"name": "Stat Test", "price": 50.0, "category": "Hardware", "moq": 1},
    )
    pid = pr.json()["id"]
    c.post("/api/cart/add", json={"product_id": pid, "quantity": 1})
    orr = c.post(
        "/api/orders",
        json={
            "total_amount": 50.0,
            "payment_method": "COD",
            "delivery_address": "Tripoli",
            "items": [{"product_id": pid, "quantity": 1, "unit_price": 50.0, "moq": 1}],
        },
    )
    oid = orr.json()["id"]
    # Create shipment (admin bypasses owner check)
    _register(c, "admin_stat1", "admin")
    sr = c.post(
        "/api/shipping",
        json={"order_id": oid, "carrier": "local", "status": "pending"},
    )
    sid = sr.json()["id"]
    r = c.put(f"/api/shipping/{sid}/status?status=shipped&location=Tripoli")
    assert r.status_code == 200
    tr = c.get(f"/api/shipping/{sid}/tracking")
    assert len(tr.json()) >= 1
