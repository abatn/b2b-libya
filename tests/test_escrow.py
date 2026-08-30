"""
Libya B2B Platform - Escrow Tests
Tests for the escrow payment system.
"""

import pytest
from fastapi.testclient import TestClient

from conftest import TestSessionLocal
from main import app

client = TestClient(app)


# ============================================================
# ESCROW TESTS
# ============================================================


def test_create_escrow(auth_client):
    """Create an escrow transaction for an order."""
    # First create an order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 100.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    order_id = order_res.json()["id"]

    # Create escrow
    response = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 100.0, "note": "Test escrow"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == order_id
    assert data["amount"] == 100.0
    assert data["status"] == "pending"
    assert data["currency"] == "LYD"
    assert data["note"] == "Test escrow"
    assert "id" in data


def test_get_escrow_status(auth_client):
    """Get escrow status by ID."""
    # Create order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 250.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    # Create escrow
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 250.0},
    )
    escrow_id = create_res.json()["id"]

    # Get escrow status
    response = auth_client.get(f"/api/escrow/{escrow_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == escrow_id
    assert data["amount"] == 250.0
    assert data["status"] == "pending"


def test_release_escrow(auth_client):
    """Release escrow funds to supplier (confirm delivery)."""
    # Create order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 500.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    # Create escrow
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 500.0},
    )
    escrow_id = create_res.json()["id"]

    # Release escrow
    response = auth_client.post(f"/api/escrow/{escrow_id}/release")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "released"
    assert data["released_at"] is not None


def test_refund_escrow(auth_client):
    """Refund escrow funds to buyer."""
    # Create order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 75.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    # Create escrow
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 75.0},
    )
    escrow_id = create_res.json()["id"]

    # Refund escrow
    response = auth_client.post(f"/api/escrow/{escrow_id}/refund")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refunded"
    assert data["refunded_at"] is not None


def test_dispute_escrow(auth_client):
    """Open a dispute for an escrow transaction."""
    # Create order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 200.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    # Create escrow
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 200.0, "note": "Dispute test"},
    )
    escrow_id = create_res.json()["id"]

    # Dispute escrow
    response = auth_client.post(f"/api/escrow/{escrow_id}/dispute")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disputed"
    assert data["disputed_at"] is not None


def test_cannot_release_already_released(auth_client):
    """Cannot release an escrow that is already released."""
    # Create order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 100.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    # Create and release
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 100.0},
    )
    escrow_id = create_res.json()["id"]
    auth_client.post(f"/api/escrow/{escrow_id}/release")

    # Try to release again
    response = auth_client.post(f"/api/escrow/{escrow_id}/release")
    assert response.status_code == 400
    assert "Cannot release" in response.json()["detail"]


def test_cannot_refund_already_released(auth_client):
    """Cannot refund an escrow that is already released."""
    # Create order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 100.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    # Create and release
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 100.0},
    )
    escrow_id = create_res.json()["id"]
    auth_client.post(f"/api/escrow/{escrow_id}/release")

    # Try to refund
    response = auth_client.post(f"/api/escrow/{escrow_id}/refund")
    assert response.status_code == 400
    assert "Cannot refund" in response.json()["detail"]


def test_get_nonexistent_escrow(auth_client):
    """Getting a nonexistent escrow returns 404."""
    response = auth_client.get("/api/escrow/99999")
    assert response.status_code == 404


def test_create_escrow_negative_amount(auth_client):
    """Creating escrow with negative amount fails."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 50.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    response = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": -50.0},
    )
    assert response.status_code == 400
    assert "positive" in response.json()["detail"].lower()


def test_create_duplicate_escrow(auth_client):
    """Cannot create duplicate escrow for same order."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 100.0,
        "currency": "LYD",
        "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 100.0},
    )
    response = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 200.0},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


# ============================================================
# SPRINT 3: NEW TESTS
# ============================================================


def test_escrow_history_on_create(auth_client):
    """Creating an escrow writes an entry to escrow_history."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 120.0, "currency": "LYD", "payment_method": "COD",
    })
    order_id = order_res.json()["id"]
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 120.0},
    )
    escrow_id = create_res.json()["id"]

    history_res = auth_client.get(f"/api/escrow/{escrow_id}/history")
    assert history_res.status_code == 200
    entries = history_res.json()
    assert len(entries) >= 1
    assert entries[0]["action"] == "created"
    assert entries[0]["new_status"] == "pending"


def test_escrow_history_on_release(auth_client):
    """Releasing an escrow adds a 'released' entry to history."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 80.0, "currency": "LYD", "payment_method": "COD",
    })
    order_id = order_res.json()["id"]
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 80.0},
    )
    escrow_id = create_res.json()["id"]
    auth_client.post(f"/api/escrow/{escrow_id}/release")

    history_res = auth_client.get(f"/api/escrow/{escrow_id}/history")
    entries = history_res.json()
    assert len(entries) >= 2
    assert entries[-1]["action"] == "released"
    assert entries[-1]["new_status"] == "released"


def test_auto_escrow_on_order_create(auth_client):
    """Non-COD order creation auto-creates an escrow transaction."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 200.0, "currency": "LYD", "payment_method": "escrow",
    })
    assert order_res.status_code == 200
    order_id = order_res.json()["id"]

    # The escrow should have been auto-created — trying again gives 409
    dup_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 200.0},
    )
    assert dup_res.status_code == 409  # already exists = auto-created


def test_no_auto_escrow_for_cod(auth_client):
    """COD orders do NOT auto-create escrow (paid at delivery)."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 100.0, "currency": "LYD", "payment_method": "COD",
    })
    assert order_res.status_code == 200
    order_id = order_res.json()["id"]

    # Manual escrow creation should succeed (no auto-created escrow)
    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 100.0},
    )
    assert create_res.status_code == 200


def test_admin_resolve_dispute(seller_client):
    """Admin can resolve a disputed escrow."""
    from fastapi.testclient import TestClient
    from main import app

    admin = TestClient(app)
    admin.post("/api/auth/register", json={
        "username": "admin_escrow_test", "password": "pass", "role": "admin",
    })

    # Create order + manual escrow as seller
    order_res = seller_client.post("/api/orders", json={
        "total_amount": 300.0, "currency": "LYD", "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    create_res = seller_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 300.0},
    )
    assert create_res.status_code == 200
    escrow_id = create_res.json()["id"]

    # Dispute the escrow as seller
    seller_client.post(f"/api/escrow/{escrow_id}/dispute")

    # Admin resolves it
    resolve_res = admin.post(
        f"/api/admin/escrow/{escrow_id}/resolve",
        json={"resolution": "release", "reason": "Buyer confirmed delivery"},
    )
    assert resolve_res.status_code == 200
    data = resolve_res.json()
    assert data["status"] == "resolved_release"
    assert data["resolution_reason"] == "Buyer confirmed delivery"


def test_admin_cannot_resolve_non_admin(auth_client):
    """Non-admin user cannot resolve escrows."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 50.0, "currency": "LYD", "payment_method": "COD",
    })
    order_id = order_res.json()["id"]

    create_res = auth_client.post(
        "/api/escrow",
        json={"order_id": order_id, "amount": 50.0},
    )
    assert create_res.status_code == 200
    escrow_id = create_res.json()["id"]

    auth_client.post(f"/api/escrow/{escrow_id}/dispute")

    # Non-admin tries to resolve
    resolve_res = auth_client.post(
        f"/api/admin/escrow/{escrow_id}/resolve",
        json={"resolution": "release", "reason": "test"},
    )
    assert resolve_res.status_code == 403
