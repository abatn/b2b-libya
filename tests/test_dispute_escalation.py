"""Tests for Dispute Escalation — 4-level escalation with auth."""
from fastapi.testclient import TestClient
from main import app


def _register(c: TestClient, username: str, role: str = "buyer") -> int:
    r = c.post(
        "/api/auth/register",
        json={"username": username, "password": "pass", "role": role},
    )
    if r.status_code == 200:
        me = c.get("/api/auth/me").json()
        return me.get("id", 0)
    return 0


def _create_disputed_escrow(c: TestClient, buyer: str, seller: str) -> int:
    """Create order + escrow + dispute → return escrow_id."""
    buyer_id = _register(c, buyer, "buyer")
    seller_id = _register(c, seller, "seller")

    # Create product + COD order (no auto-escrow)
    pr = c.post(
        "/api/products",
        json={"name": "Disp Prod", "price": 100.0, "category": "Test", "moq": 1},
    )
    pid = pr.json()["id"]
    c.post("/api/cart/add", json={"product_id": pid, "quantity": 1})
    orr = c.post(
        "/api/orders",
        json={
            "total_amount": 100.0,
            "payment_method": "COD",
            "delivery_address": "Tripoli",
            "items": [{"product_id": pid, "quantity": 1, "unit_price": 100.0, "moq": 1}],
        },
    )
    oid = orr.json()["id"]

    # Create escrow manually
    c.post("/api/auth/login", json={"username": buyer, "password": "pass"})
    er = c.post(
        "/api/escrow",
        json={"order_id": oid, "buyer_id": buyer_id, "supplier_id": seller_id, "amount": 100.0},
    )
    eid = er.json()["id"]

    # Dispute it
    c.post(f"/api/escrow/{eid}/dispute?reason=quality&description=Bad+product")
    return eid


def test_escalate_dispute():
    """Buyer escalates dispute → 200."""
    c = TestClient(app)
    eid = _create_disputed_escrow(c, "buyer_e1", "seller_e1")
    r = c.post(f"/api/escrow/{eid}/escalate", json={"description": "Need mediation"})
    assert r.status_code == 200
    body = r.json()
    assert "level" in body


def test_escalate_not_authorized():
    """Unrelated user tries to escalate → 403."""
    c = TestClient(app)
    eid = _create_disputed_escrow(c, "buyer_e2", "seller_e2")
    _register(c, "stranger_e2")
    r = c.post(f"/api/escrow/{eid}/escalate", json={"description": "Hack"})
    assert r.status_code == 403


def test_resolve_escalation_admin():
    """Admin resolves escalation → 200."""
    c = TestClient(app)
    eid = _create_disputed_escrow(c, "buyer_e3", "seller_e3")
    er = c.post(f"/api/escrow/{eid}/escalate", json={})
    esc_id = er.json()["id"]
    _register(c, "admin_e3", "admin")
    r = c.put(
        f"/api/escrow/{eid}/escalations/{esc_id}/resolve",
        json={"resolution": "Resolved by admin"},
    )
    assert r.status_code == 200


def test_resolve_escalation_non_admin():
    """Non-admin tries to resolve → 403."""
    c = TestClient(app)
    eid = _create_disputed_escrow(c, "buyer_e4", "seller_e4")
    er = c.post(f"/api/escrow/{eid}/escalate", json={})
    esc_id = er.json()["id"]
    # buyer (not admin) tries to resolve
    r = c.put(
        f"/api/escrow/{eid}/escalations/{esc_id}/resolve",
        json={"resolution": "I decide"},
    )
    assert r.status_code == 403
