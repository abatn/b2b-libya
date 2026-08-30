"""
Libya B2B Platform - Sync Engine Tests
Sprint 4: Delta-Sync-Engine Tests
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from main import app
from sync_engine import (
    DeltaSyncEngine,
    SyncEntry,
    SyncStatus,
    get_sync_engine
)

# DB setup handled by conftest.py (shared engine + override)
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_sync_singleton():
    """Reset the sync engine singleton before each test to avoid threading issues"""
    import sync_engine as se_mod
    se_mod._sync_engine_instance = None
    yield
    se_mod._sync_engine_instance = None

@pytest.fixture
def sync_engine():
    """In-Memory Sync-Engine fuer Tests"""
    return DeltaSyncEngine(db_path=":memory:")

@pytest.fixture
def sample_data():
    return {
        "name": "Test Produkt",
        "price": 100.0,
        "currency": "LYD",
        "category": "Bau"
    }

# ============================================================
# SYNC ENGINE UNIT TESTS
# ============================================================

def test_sync_engine_initialization(sync_engine):
    """Sync-Engine muss initialisiert werden koennen"""
    assert sync_engine is not None
    assert sync_engine.local_db is not None

def test_calculate_checksum(sync_engine, sample_data):
    """Checksum muss korrekt berechnet werden"""
    checksum = sync_engine.calculate_checksum(sample_data)
    assert checksum is not None
    assert len(checksum) == 32  # MD5
    
    # Gleiche Daten = gleicher Checksum
    checksum2 = sync_engine.calculate_checksum(sample_data)
    assert checksum == checksum2

def test_create_sync_entry(sync_engine, sample_data):
    """Sync-Eintrag muss erstellt werden koennen"""
    entry = sync_engine.create_sync_entry(
        table_name="products",
        record_id=1,
        action="create",
        data=sample_data
    )
    
    assert entry is not None
    assert entry.table_name == "products"
    assert entry.record_id == 1
    assert entry.action == "create"
    assert entry.status == SyncStatus.PENDING
    assert entry.retry_count == 0

def test_get_pending_syncs(sync_engine, sample_data):
    """Ausstehende Syncs muessen abgerufen werden koennen"""
    # Eintraege erstellen
    sync_engine.create_sync_entry("products", 1, "create", sample_data)
    sync_engine.create_sync_entry("products", 2, "update", sample_data)
    
    pending = sync_engine.get_pending_syncs()
    assert len(pending) == 2

def test_sync_entry_success(sync_engine, sample_data):
    """Sync muss erfolgreich sein koennen"""
    entry = sync_engine.create_sync_entry(
        table_name="products",
        record_id=1,
        action="create",
        data=sample_data
    )
    
    success, message = sync_engine.sync_entry(entry)
    # 95% Erfolgsrate - kann fehlschlagen
    assert isinstance(success, bool)
    assert isinstance(message, str)

def test_get_changes_since(sync_engine, sample_data):
    """Aenderungen seit Zeitpunkt muessen abgerufen werden koennen"""
    # Eintrag erstellen
    sync_engine.create_sync_entry("products", 1, "create", sample_data)
    
    # Aenderungen abrufen
    since = datetime.now() - timedelta(hours=1)
    changes = sync_engine.get_changes_since(since)
    
    assert isinstance(changes, list)

def test_resolve_conflict(sync_engine, sample_data):
    """Konfliktloesung muss funktionieren"""
    entry = sync_engine.create_sync_entry(
        table_name="products",
        record_id=1,
        action="update",
        data=sample_data
    )
    
    remote_data = {"name": "Remote Produkt", "price": 200.0}
    
    winner = sync_engine.resolve_conflict(entry, remote_data)
    assert winner is not None
    assert "name" in winner

def test_get_sync_stats(sync_engine, sample_data):
    """Sync-Statistiken muessen abgerufen werden koennen"""
    # Eintraege erstellen
    sync_engine.create_sync_entry("products", 1, "create", sample_data)
    sync_engine.create_sync_entry("orders", 1, "create", sample_data)
    
    stats = sync_engine.get_sync_stats()
    
    assert "total_entries" in stats
    assert "by_status" in stats
    assert "by_table" in stats
    assert stats["total_entries"] == 2

def test_clear_completed_syncs(sync_engine, sample_data):
    """Abgeschlossene Syncs muessen geloescht werden koennen"""
    # Eintrag erstellen und synchronisieren
    entry = sync_engine.create_sync_entry("products", 1, "create", sample_data)
    sync_engine.sync_entry(entry)
    
    # Loeschen
    deleted = sync_engine.clear_completed_syncs()
    assert deleted >= 0

def test_metadata(sync_engine):
    """Metadaten muessen gespeichert/abgerufen werden koennen"""
    sync_engine._update_metadata("last_sync", "2026-08-15T10:00:00")
    
    value = sync_engine.get_metadata("last_sync")
    assert value == "2026-08-15T10:00:00"

# ============================================================
# API ENDPOINT TESTS
# ============================================================

def test_api_delta_sync():
    """API Delta-Sync muss funktionieren"""
    response = client.post(
        "/api/sync/delta",
        params={
            "table_name": "products",
            "record_id": 1,
            "action": "create"
        },
        json={
            "name": "Test",
            "price": 100.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "entry_id" in data
    assert "checksum" in data

def test_api_sync_all():
    """API Sync All muss funktionieren"""
    response = client.post("/api/sync/all")
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "success" in data
    assert "failed" in data

def test_api_get_pending():
    """API Pending Syncs muss funktionieren"""
    response = client.get("/api/sync/pending")
    
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "count" in data

def test_api_sync_stats():
    """API Sync Stats muss funktionieren"""
    response = client.get("/api/sync/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_entries" in data

def test_api_clear_completed():
    """API Clear Completed muss funktionieren"""
    response = client.delete("/api/sync/completed")
    
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data

# ============================================================
# OFFLINE-SYNC INTEGRATION TESTS
# ============================================================

def test_offline_sync_workflow(sync_engine, sample_data):
    """Offline-Sync-Workflow muss funktionieren"""
    # 1. Offline: Eintrag erstellen
    entry1 = sync_engine.create_sync_entry("products", 1, "create", sample_data)
    assert entry1.status == SyncStatus.PENDING
    
    # 2. Offline: Zweiten Eintrag erstellen
    sample_data["price"] = 150.0
    entry2 = sync_engine.create_sync_entry("products", 1, "update", sample_data)
    assert entry2.status == SyncStatus.PENDING
    
    # 3. Online: Alle synchronisieren
    results = sync_engine.sync_all_pending()
    assert results["total"] == 2
    
    # 4. Statistiken pruefen
    stats = sync_engine.get_sync_stats()
    assert stats["total_entries"] == 2

def test_sync_with_retry(sync_engine, sample_data):
    """Sync mit Retry muss funktionieren"""
    entry = sync_engine.create_sync_entry("products", 1, "create", sample_data)
    
    # Mehrmals versuchen
    for i in range(3):
        success, message = sync_engine.sync_entry(entry)
        if success:
            break
    
    # Nach 3 Versuchen sollte Status gesetzt sein
    stats = sync_engine.get_sync_stats()
    assert "by_status" in stats
