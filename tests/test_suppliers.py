"""Tests for supplier import, admin verification, and extended fields."""

import io
import json
import csv

from fastapi.testclient import TestClient
from main import app, Base, get_db


# ── Helper ──────────────────────────────────────────────────────────────────


def _create_supplier(client, name="Test Supplier", **kwargs):
    data = {"name": name, **kwargs}
    return client.post("/api/b2b/suppliers", json=data)


# ── Supplier CRUD with new fields ───────────────────────────────────────────


def test_create_supplier_with_new_fields(client):
    resp = _create_supplier(
        client,
        name="AlSahl Group",
        name_arabic="السهل جروب",
        phone="+218-91-2159527",
        email="info@alsahl.ly",
        website="alsahlgroup.com",
        category="Building Materials",
        city="Tripoli",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "AlSahl Group"
    assert data["name_arabic"] == "السهل جروب"
    assert data["phone"] == "+218-91-2159527"
    assert data["email"] == "info@alsahl.ly"
    assert data["website"] == "alsahlgroup.com"
    assert data["category"] == "Building Materials"
    assert data["city"] == "Tripoli"


def test_supplier_list_with_category_filter(client):
    _create_supplier(client, name="Supplier A", category="Electrical")
    _create_supplier(client, name="Supplier B", category="Building Materials")
    _create_supplier(client, name="Supplier C", category="Electrical")

    resp = client.get("/api/b2b/suppliers?category=Electrical")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(s["category"] == "Electrical" for s in data["suppliers"])


def test_supplier_list_with_city_filter(client):
    _create_supplier(client, name="Tripoli Co", city="Tripoli")
    _create_supplier(client, name="Benghazi Co", city="Benghazi")

    resp = client.get("/api/b2b/suppliers?city=Tripoli")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_supplier_list_with_search(client):
    _create_supplier(client, name="AlSahl Building Materials")
    _create_supplier(client, name="Libya Tools")

    resp = client.get("/api/b2b/suppliers?search=AlSahl")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["suppliers"][0]["name"] == "AlSahl Building Materials"


def test_supplier_list_verified_only(client):
    _create_supplier(client, name="Verified Co", is_verified=True)
    _create_supplier(client, name="Unverified Co", is_verified=False)

    resp = client.get("/api/b2b/suppliers?verified_only=true")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# ── Supplier categories/cities endpoints ────────────────────────────────────


def test_supplier_categories(client):
    _create_supplier(client, name="A", category="Electrical")
    _create_supplier(client, name="B", category="Building Materials")
    _create_supplier(client, name="C", category="Electrical")

    resp = client.get("/api/b2b/suppliers/categories")
    assert resp.status_code == 200
    cats = resp.json()["categories"]
    assert "Electrical" in cats
    assert "Building Materials" in cats


def test_supplier_cities(client):
    _create_supplier(client, name="A", city="Tripoli")
    _create_supplier(client, name="B", city="Benghazi")

    resp = client.get("/api/b2b/suppliers/cities")
    assert resp.status_code == 200
    cities = resp.json()["cities"]
    assert "Tripoli" in cities
    assert "Benghazi" in cities


def test_supplier_stats(client):
    _create_supplier(client, name="A", is_verified=True)
    _create_supplier(client, name="B", is_verified=False)

    resp = client.get("/api/b2b/suppliers/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_suppliers"] == 2
    assert data["verified_suppliers"] == 1
    assert data["unverified_suppliers"] == 1


# ── Update supplier ─────────────────────────────────────────────────────────


def test_update_supplier(client):
    resp = _create_supplier(client, name="Old Name")
    sid = resp.json()["id"]

    resp = client.put(f"/api/b2b/suppliers/{sid}", json={"name": "New Name", "phone": "+218-91-0000000"})
    assert resp.status_code == 200

    resp = client.get(f"/api/b2b/suppliers/{sid}")
    assert resp.json()["name"] == "New Name"
    assert resp.json()["phone"] == "+218-91-0000000"


# ── CSV Import ──────────────────────────────────────────────────────────────


def test_csv_import(client):
    csv_content = "name,name_arabic,city,phone,category\n"
    csv_content += "AlSahl,السهل,Tripoli,+218-91-0000000,Building Materials\n"
    csv_content += "Libya Tools,ليبيا تولز,Benghazi,+218-92-0000000,Hardware\n"
    csv_content += "Northfields,نورث فيلدز,Tripoli,,Electrical\n"

    file = io.BytesIO(csv_content.encode("utf-8"))
    resp = client.post(
        "/api/b2b/suppliers/import",
        files={"file": ("suppliers.csv", file, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 3
    assert data["skipped"] == 0


def test_csv_import_with_empty_names(client):
    csv_content = "name,city\n"
    csv_content += "Valid Supplier,Tripoli\n"
    csv_content += ",Benghazi\n"
    csv_content += "Another Supplier,Misrata\n"

    file = io.BytesIO(csv_content.encode("utf-8"))
    resp = client.post(
        "/api/b2b/suppliers/import",
        files={"file": ("suppliers.csv", file, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 1


def test_csv_import_rejects_non_csv(client):
    file = io.BytesIO(b"not a csv")
    resp = client.post(
        "/api/b2b/suppliers/import",
        files={"file": ("data.txt", file, "text/plain")},
    )
    assert resp.status_code == 400


def test_csv_import_case_insensitive_headers(client):
    csv_content = "Name,City,Phone\n"
    csv_content += "Test Company,Tripoli,+218-91-0000000\n"

    file = io.BytesIO(csv_content.encode("utf-8"))
    resp = client.post(
        "/api/b2b/suppliers/import",
        files={"file": ("suppliers.csv", file, "text/csv")},
    )
    assert resp.status_code == 200
    assert resp.json()["imported"] == 1


def test_json_import(client):
    suppliers = [
        {"name": "Company A", "city": "Tripoli", "category": "Electrical"},
        {"name": "Company B", "city": "Benghazi", "category": "Hardware"},
    ]
    resp = client.post("/api/b2b/suppliers/import/json", json=suppliers)
    assert resp.status_code == 200
    assert resp.json()["imported"] == 2


# ── Admin Verification ──────────────────────────────────────────────────────


def _make_auth_client(role="buyer"):
    c = TestClient(app)
    c.post(
        "/api/auth/register",
        json={"username": f"test_{role}_user", "password": "pass", "role": role},
    )
    return c


def test_admin_verify_supplier():
    auth_client = _make_auth_client("admin")
    # Create supplier
    resp = _create_supplier(auth_client, name="Verify Me")
    sid = resp.json()["id"]

    # Verify
    resp = auth_client.post(f"/api/admin/suppliers/{sid}/verify")
    assert resp.status_code == 200

    # Check
    resp = auth_client.get(f"/api/b2b/suppliers/{sid}")
    assert resp.json()["is_verified"] is True


def test_admin_unverify_supplier():
    auth_client = _make_auth_client("admin")
    resp = _create_supplier(auth_client, name="Unverify Me", is_verified=True)
    sid = resp.json()["id"]

    resp = auth_client.post(f"/api/admin/suppliers/{sid}/unverify")
    assert resp.status_code == 200

    resp = auth_client.get(f"/api/b2b/suppliers/{sid}")
    assert resp.json()["is_verified"] is False


def test_admin_delete_supplier():
    auth_client = _make_auth_client("admin")
    resp = _create_supplier(auth_client, name="Delete Me")
    sid = resp.json()["id"]

    resp = auth_client.delete(f"/api/admin/suppliers/{sid}")
    assert resp.status_code == 200

    resp = auth_client.get(f"/api/b2b/suppliers/{sid}")
    assert resp.status_code == 404


def test_admin_list_all_suppliers():
    auth_client = _make_auth_client("admin")
    _create_supplier(auth_client, name="Verified", is_verified=True)
    _create_supplier(auth_client, name="Unverified", is_verified=False)

    resp = auth_client.get("/api/admin/suppliers")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    resp = auth_client.get("/api/admin/suppliers?verified=false")
    assert resp.json()["total"] == 1


def test_admin_supplier_stats():
    auth_client = _make_auth_client("admin")
    _create_supplier(auth_client, name="A", is_verified=True)
    _create_supplier(auth_client, name="B", is_verified=False)

    resp = auth_client.get("/api/admin/suppliers/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["verified"] == 1
    assert data["verification_rate"] == 50.0


def test_non_admin_cannot_verify(client):
    buyer_client = _make_auth_client("buyer")
    resp = _create_supplier(buyer_client, name="Test")
    sid = resp.json()["id"]

    resp = buyer_client.post(f"/api/admin/suppliers/{sid}/verify")
    assert resp.status_code == 403


# ── Supplier Detail with new fields ─────────────────────────────────────────


def test_supplier_detail_includes_new_fields(client):
    resp = _create_supplier(
        client,
        name="Detail Test",
        phone="+218-91-1234567",
        email="test@example.com",
        website="test.ly",
        category="IT Equipment",
        city="Tripoli",
    )
    sid = resp.json()["id"]

    resp = client.get(f"/api/b2b/suppliers/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] == "+218-91-1234567"
    assert data["email"] == "test@example.com"
    assert data["website"] == "test.ly"
    assert data["category"] == "IT Equipment"
    assert data["city"] == "Tripoli"


# ── Supplier Logo Tests ─────────────────────────────────────────────────────


def test_supplier_logo_url_stored(client):
    """Supplier logo_url is stored and returned in API response."""
    resp = _create_supplier(
        client,
        name="Logo Test Supplier",
        logo_url="https://example.com/logo.png",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["logo_url"] == "https://example.com/logo.png"


def test_supplier_logo_url_in_list(client):
    """Supplier logo_url appears in supplier list endpoint."""
    _create_supplier(
        client,
        name="List Logo Supplier",
        logo_url="/static/logos/test.svg",
    )
    resp = client.get("/api/b2b/suppliers")
    assert resp.status_code == 200
    data = resp.json()
    suppliers = data.get("suppliers", data) if isinstance(data, dict) else data
    logo_supplier = [s for s in suppliers if s["name"] == "List Logo Supplier"]
    assert len(logo_supplier) == 1
    assert logo_supplier[0]["logo_url"] == "/static/logos/test.svg"


def test_supplier_logo_none_by_default(client):
    """Supplier without logo_url returns null."""
    resp = _create_supplier(client, name="No Logo Supplier")
    assert resp.status_code == 200
    assert resp.json()["logo_url"] is None


def test_seed_data_has_all_supplier_logos():
    """All 30 suppliers in seed_data have a logo_url entry."""
    from seed_data import SUPPLIER_LOGOS
    assert len(SUPPLIER_LOGOS) == 30
    for name, url in SUPPLIER_LOGOS.items():
        assert url, f"Supplier '{name}' has empty logo_url"
        assert len(url) > 5, f"Supplier '{name}' logo_url too short: {url}"


def test_seed_data_no_facebook_cdn_logos():
    """No supplier logos use Facebook CDN (which blocks hotlinking)."""
    from seed_data import SUPPLIER_LOGOS
    fb_domains = ["fbcdn.net", "facebook.com"]
    for name, url in SUPPLIER_LOGOS.items():
        for domain in fb_domains:
            assert domain not in url, (
                f"Supplier '{name}' uses Facebook CDN: {url[:80]}"
            )


def test_seed_data_svg_logos_are_local_files():
    """SVG logos for Facebook-blocked companies use local /static/logos/ paths."""
    from seed_data import SUPPLIER_LOGOS
    fb_companies = [
        "Al-Hawari Food Stuff",
        "Libya Automotive",
        "El Meselati Furniture",
        "TechnoFarm International",
        "Green Libya",
        "Alliance Mechanical Equipment",
        "Al Moheit Computer Services",
    ]
    for name in fb_companies:
        url = SUPPLIER_LOGOS.get(name, "")
        assert url.startswith("/static/logos/"), (
            f"Supplier '{name}' should use local SVG, got: {url[:60]}"
        )
        assert url.endswith(".svg"), (
            f"Supplier '{name}' should be SVG, got: {url}"
        )
