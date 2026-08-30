"""
Libya B2B Platform - Sprint 8 Integrationstests
Testet den vollen B2B-Workflow: Produkte -> Warenkorb -> Checkout -> Monitoring
"""

import pytest


@pytest.fixture
def sample_product():
    return {
        "name": "Sprint8 Product",
        "name_arabic": "منتج سبرينت 8",
        "description": "Test product for Sprint 8",
        "price": 100.00,
        "currency": "LYD",
        "category": "hardware",
        "stock_quantity": 50,
        "moq": 5,
    }


# ============================================================
# PRODUCT CRUD TESTS
# ============================================================

def test_create_product(auth_client, sample_product):
    """Produkt muss erstellt werden koennen"""
    response = auth_client.post("/api/products", json=sample_product)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sprint8 Product"


def test_list_products(auth_client, sample_product):
    """Produkte muessen aufgelistet werden koennen"""
    auth_client.post("/api/products", json=sample_product)
    response = auth_client.get("/api/products")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_product(auth_client, sample_product):
    """Einzelnes Produkt muss abgerufen werden koennen"""
    create_resp = auth_client.post("/api/products", json=sample_product)
    product_id = create_resp.json()["id"]
    response = auth_client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id


def test_delete_product(auth_client, sample_product):
    """Produkt muss geloescht werden koennen"""
    create_resp = auth_client.post("/api/products", json=sample_product)
    product_id = create_resp.json()["id"]
    response = auth_client.delete(f"/api/products/{product_id}")
    assert response.status_code == 200
    get_resp = auth_client.get(f"/api/products/{product_id}")
    assert get_resp.status_code == 404


def test_update_product(auth_client, sample_product):
    """Produkt muss aktualisiert werden koennen"""
    create_resp = auth_client.post("/api/products", json=sample_product)
    product_id = create_resp.json()["id"]
    update_data = {"name": "Updated Sprint8", "price": 150.00, "currency": "LYD"}
    response = auth_client.put(f"/api/products/{product_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Sprint8"


# ============================================================
# ORDER + DELIVERY WORKFLOW
# ============================================================

def test_full_order_workflow(auth_client, sample_product):
    """Full workflow: Create product -> order -> confirm delivery"""
    prod_resp = auth_client.post("/api/products", json=sample_product)
    product_id = prod_resp.json()["id"]

    order_data = {
        "total_amount": 300.0,
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

    confirm_resp = auth_client.put(f"/api/orders/{order_id}/deliver")
    assert confirm_resp.status_code == 200


# ============================================================
# RFQ WORKFLOW
# ============================================================

def test_rfq_workflow(auth_client, sample_product):
    """RFQ: Create -> View -> Update status"""
    rfq_data = {
        "product_name": "Bulk Cement",
        "product_name_arabic": "اسمنت بالجملة",
        "quantity": 100,
        "unit": "bags",
        "delivery_address": "Tripoli",
        "notes": "Need within 2 weeks",
    }
    create_resp = auth_client.post("/api/b2b/rfq", json=rfq_data)
    assert create_resp.status_code == 200
    rfq_id = create_resp.json()["id"]

    view_resp = auth_client.get(f"/api/b2b/rfq/{rfq_id}")
    assert view_resp.status_code == 200

    update_resp = auth_client.put(f"/api/b2b/rfq/{rfq_id}", params={"status": "quoted"})
    assert update_resp.status_code == 200


# ============================================================
# MESSAGES WORKFLOW
# ============================================================

def test_messaging_workflow(auth_client):
    """Create conversation -> send message -> view"""
    conv_resp = auth_client.post(
        "/api/b2b/messages",
        params={"buyer_id": 1, "supplier_id": 1},
    )
    assert conv_resp.status_code == 200
    conv_id = conv_resp.json()["id"]

    msg_resp = auth_client.post(
        f"/api/b2b/messages/{conv_id}",
        json={"sender_type": "buyer", "text": "Hello supplier!"},
    )
    assert msg_resp.status_code == 200

    get_resp = auth_client.get(f"/api/b2b/messages/{conv_id}")
    assert get_resp.status_code == 200


# ============================================================
# ESCROW WORKFLOW
# ============================================================

def test_escrow_workflow(auth_client, sample_product):
    """Create product -> order -> escrow -> release"""
    prod_resp = auth_client.post("/api/products", json=sample_product)
    product_id = prod_resp.json()["id"]

    order_data = {
        "total_amount": 200.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Tripoli",
    }
    order_resp = auth_client.post("/api/orders", json=order_data)
    order_id = order_resp.json()["id"]

    escrow_data = {
        "order_id": order_id,
        "amount": 200.00,
        "note": "Test escrow",
    }
    escrow_resp = auth_client.post("/api/escrow", json=escrow_data)
    assert escrow_resp.status_code == 200
    escrow_id = escrow_resp.json()["id"]

    release_resp = auth_client.post(f"/api/escrow/{escrow_id}/release")
    assert release_resp.status_code == 200
    assert release_resp.json()["status"] == "released"


# ============================================================
# B2B DASHBOARD
# ============================================================

def test_b2b_dashboard(auth_client, sample_product):
    """B2B Dashboard muss Daten anzeigen"""
    auth_client.post("/api/products", json=sample_product)
    response = auth_client.get("/api/b2b/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "total_revenue" in data


def test_b2b_analytics(auth_client, sample_product):
    """B2B Analytics muss Daten anzeigen"""
    auth_client.post("/api/products", json=sample_product)
    response = auth_client.get("/api/b2b/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data


def test_b2b_products(auth_client, sample_product):
    """B2B Products muss gefilterte Liste liefern"""
    auth_client.post("/api/products", json=sample_product)
    response = auth_client.get("/api/b2b/products?category=hardware")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


def test_b2b_categories(client):
    """B2B Categories muss alle Kategorien liefern"""
    response = client.get("/api/b2b/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) >= 20


def test_b2b_stats(client):
    """B2B Stats muss Plattform-Statistiken liefern"""
    response = client.get("/api/b2b/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_products" in data


def test_b2b_bulk_pricing(auth_client, sample_product):
    """B2B Bulk Pricing muss Mengenrabatte anzeigen"""
    auth_client.post("/api/products", json=sample_product)
    response = auth_client.get("/api/b2b/bulk-pricing")
    assert response.status_code == 200


def test_b2b_inventory(auth_client, sample_product):
    """B2B Inventory muss Lagerbestand anzeigen"""
    auth_client.post("/api/products", json=sample_product)
    response = auth_client.get("/api/b2b/inventory")
    assert response.status_code == 200


# ============================================================
# FULL B2B WORKFLOW (end-to-end)
# ============================================================

def test_full_b2b_workflow(auth_client, sample_product):
    """Voller B2B-Workflow: Supplier -> Product -> Buyer -> Order -> Delivery -> Review"""
    prod_resp = auth_client.post("/api/products", json=sample_product)
    product_id = prod_resp.json()["id"]

    order_data = {
        "total_amount": 500.0,
        "currency": "LYD",
        "payment_method": "COD",
        "delivery_address": "Benghazi, Libya",
    }
    order_resp = auth_client.post("/api/orders", json=order_data)
    assert order_resp.status_code == 200
    order_id = order_resp.json()["id"]

    confirm_resp = auth_client.put(f"/api/orders/{order_id}/deliver")
    assert confirm_resp.status_code == 200

    review_data = {
        "product_id": product_id,
        "rating": 5,
        "comment": "Excellent product!",
    }
    review_resp = auth_client.post("/api/reviews", json=review_data)
    assert review_resp.status_code == 200

    dashboard_resp = auth_client.get("/api/b2b/dashboard")
    assert dashboard_resp.status_code == 200
    assert dashboard_resp.json()["total_orders"] >= 1
