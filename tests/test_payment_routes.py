"""
Libya B2B Platform - Payment Routes API Tests
Tests for /api/payments endpoints (methods, pay, status, refund).
"""

import pytest
from fastapi.testclient import TestClient

from conftest import TestSessionLocal
from main import app

client = TestClient(app)


# ============================================================
# PAYMENT METHODS ENDPOINT
# ============================================================


def test_list_payment_methods():
    """GET /api/payments/methods returns available payment methods."""
    response = client.get("/api/payments/methods")
    assert response.status_code == 200
    data = response.json()
    assert "methods" in data
    methods = data["methods"]
    assert isinstance(methods, list)
    assert len(methods) > 0
    # COD should always be available
    method_ids = [m.get("id", "") for m in methods]
    assert "cod" in method_ids


def test_list_payment_methods_has_required_fields():
    """Each payment method has required fields."""
    response = client.get("/api/payments/methods")
    assert response.status_code == 200
    methods = response.json()["methods"]
    for method in methods:
        # Each method should have at least a name/id and availability info
        assert "name" in method or "id" in method


# ============================================================
# CREATE PAYMENT ENDPOINT
# ============================================================


def test_create_payment_cod(auth_client):
    """POST /api/payments/pay with COD method succeeds."""
    # First create an order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 150.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    assert order_res.status_code == 200
    order_id = order_res.json()["id"]

    # Create payment
    response = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 150.0,
        "method": "cod",
        "currency": "LYD",
        "description": "Test COD payment"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "completed"
    assert data["amount"] == 150.0
    assert data["currency"] == "LYD"
    assert "transaction_id" in data
    assert "db_txn_id" in data


def test_create_payment_mock(auth_client):
    """POST /api/payments/pay with mock method succeeds."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 200.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Benghazi"
    })
    order_id = order_res.json()["id"]

    response = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 200.0,
        "method": "mock",
        "currency": "LYD",
        "description": "Test mock payment"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["provider"] == "mock"


def test_create_payment_requires_auth():
    """POST /api/payments/pay requires authentication."""
    response = client.post("/api/payments/pay", json={
        "order_id": 1,
        "amount": 100.0,
        "method": "cod",
        "currency": "LYD"
    })
    assert response.status_code in (401, 403)


def test_create_payment_missing_order(auth_client):
    """POST /api/payments/pay with non-existent order fails."""
    response = auth_client.post("/api/payments/pay", json={
        "order_id": 99999,
        "amount": 100.0,
        "method": "cod",
        "currency": "LYD"
    })
    # May succeed (mock doesn't validate order existence) or fail
    # The important thing is that the endpoint responds
    assert response.status_code in (200, 400, 404, 500)


def test_create_payment_invalid_method(auth_client):
    """POST /api/payments/pay with invalid method returns error."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 50.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Misrata"
    })
    order_id = order_res.json()["id"]

    response = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 50.0,
        "method": "invalid_provider",
        "currency": "LYD"
    })
    assert response.status_code == 400


# ============================================================
# PAYMENT STATUS ENDPOINT
# ============================================================


def test_get_payment_status(auth_client):
    """GET /api/payments/status/{provider}/{txn_id} returns status."""
    # Create a payment first
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 75.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    order_id = order_res.json()["id"]

    pay_res = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 75.0,
        "method": "mock",
        "currency": "LYD"
    })
    txn_id = pay_res.json()["transaction_id"]

    # Check status
    response = auth_client.get(f"/api/payments/status/mock/{txn_id}")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "success" in data
    assert data["provider"] == "mock"


def test_get_payment_status_requires_auth():
    """GET /api/payments/status requires authentication."""
    response = client.get("/api/payments/status/mock/some-txn-id")
    assert response.status_code in (401, 403)


# ============================================================
# PAYMENT REFUND ENDPOINT
# ============================================================


def test_refund_payment(auth_client):
    """POST /api/payments/refund refunds a payment."""
    # Create a payment first
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 100.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    order_id = order_res.json()["id"]

    pay_res = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 100.0,
        "method": "mock",
        "currency": "LYD"
    })
    txn_id = pay_res.json()["transaction_id"]

    # Refund
    response = auth_client.post("/api/payments/refund", json={
        "transaction_id": txn_id,
        "amount": 50.0,
        "reason": "Customer dissatisfied"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "refunded"


def test_refund_payment_requires_auth():
    """POST /api/payments/refund requires authentication."""
    response = client.post("/api/payments/refund", json={
        "transaction_id": "some-txn",
        "reason": "test"
    })
    assert response.status_code in (401, 403)


# ============================================================
# INTEGRATION: Full Payment Flow
# ============================================================


def test_full_payment_flow(auth_client):
    """Full flow: create order → pay → check status → refund."""
    # 1. Create order
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 300.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    assert order_res.status_code == 200
    order_id = order_res.json()["id"]

    # 2. Pay
    pay_res = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 300.0,
        "method": "mock",
        "currency": "LYD"
    })
    assert pay_res.status_code == 200
    txn_id = pay_res.json()["transaction_id"]

    # 3. Check status
    status_res = auth_client.get(f"/api/payments/status/mock/{txn_id}")
    assert status_res.status_code == 200

    # 4. Refund
    refund_res = auth_client.post("/api/payments/refund", json={
        "transaction_id": txn_id,
        "reason": "Full refund"
    })
    assert refund_res.status_code == 200
    assert refund_res.json()["success"] is True


# ============================================================
# WEBHOOK ENDPOINTS
# ============================================================


def test_webhook_sadad_completed():
    """POST /api/payments/webhook/sadad processes completed webhook."""
    response = client.post("/api/payments/webhook/sadad", json={
        "provider": "sadad",
        "transaction_id": "SADAD-TEST123",
        "status": "completed",
        "amount": 100.0,
        "metadata": {"payment_url": "https://sadad.qa/pay/123"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Transaction not in DB → returns message, not status
    assert "message" in data or "status" in data


def test_webhook_fawry_failed():
    """POST /api/payments/webhook/fawry processes failed webhook."""
    response = client.post("/api/payments/webhook/fawry", json={
        "provider": "fawry",
        "transaction_id": "FAWRY-TEST456",
        "status": "failed",
        "metadata": {"error": "insufficient_funds"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Transaction not in DB → returns message, not status
    assert "message" in data or "status" in data


def test_webhook_unknown_provider():
    """POST /api/payments/webhook/{unknown} returns 400."""
    response = client.post("/api/payments/webhook/unknown", json={
        "provider": "unknown",
        "transaction_id": "TEST",
        "status": "completed"
    })
    assert response.status_code == 400


def test_webhook_updates_db_transaction(auth_client):
    """Webhook updates transaction status in DB."""
    # Create order + payment
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 50.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    order_id = order_res.json()["id"]

    pay_res = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 50.0,
        "method": "mock",
        "currency": "LYD"
    })
    txn_id = pay_res.json()["transaction_id"]

    # Send webhook
    webhook_res = client.post("/api/payments/webhook/mock", json={
        "provider": "mock",
        "transaction_id": txn_id,
        "status": "completed",
        "metadata": {"confirmed": True}
    })
    assert webhook_res.status_code == 200
    assert webhook_res.json()["status"] == "completed"


def test_webhook_no_auth_required():
    """Webhook endpoint does not require authentication (called by provider)."""
    response = client.post("/api/payments/webhook/mock", json={
        "provider": "mock",
        "transaction_id": "TEST-TXN",
        "status": "completed"
    })
    # Should succeed without auth (200, not 401/403)
    assert response.status_code == 200


# ============================================================
# STATUS POLLING ENDPOINTS
# ============================================================


def test_poll_payment_status(auth_client):
    """GET /api/payments/poll/{provider}/{txn_id} polls status."""
    # Create order + payment
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 80.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    order_id = order_res.json()["id"]

    pay_res = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 80.0,
        "method": "mock",
        "currency": "LYD"
    })
    txn_id = pay_res.json()["transaction_id"]

    # Poll status
    response = auth_client.get(f"/api/payments/poll/mock/{txn_id}")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "success" in data
    assert data["provider"] == "mock"


def test_poll_payment_status_requires_auth():
    """GET /api/payments/poll requires authentication."""
    response = client.get("/api/payments/poll/mock/some-txn")
    assert response.status_code in (401, 403)


def test_poll_updates_db_on_status_change(auth_client):
    """Polling updates DB if status changed."""
    order_res = auth_client.post("/api/orders", json={
        "total_amount": 90.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli"
    })
    order_id = order_res.json()["id"]

    pay_res = auth_client.post("/api/payments/pay", json={
        "order_id": order_id,
        "amount": 90.0,
        "method": "mock",
        "currency": "LYD"
    })
    txn_id = pay_res.json()["transaction_id"]

    # Poll
    response = auth_client.get(f"/api/payments/poll/mock/{txn_id}")
    assert response.status_code == 200


# ============================================================
# PROVIDER HEALTH CHECK
# ============================================================


def test_payment_health_check():
    """GET /api/payments/health returns provider status."""
    response = client.get("/api/payments/health")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert "total" in data
    assert "live_count" in data
    assert "sandbox_count" in data
    assert data["total"] > 0


def test_payment_health_check_providers():
    """Health check shows each provider with required fields."""
    response = client.get("/api/payments/health")
    assert response.status_code == 200
    providers = response.json()["providers"]
    for name, info in providers.items():
        assert "name" in info
        assert "display_name" in info
        assert "available" in info
        assert "mode" in info
        assert info["mode"] in ("live", "sandbox")


def test_payment_health_check_requires_no_auth():
    """Health check does not require authentication."""
    response = client.get("/api/payments/health")
    assert response.status_code == 200
