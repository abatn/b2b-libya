# Phase 3: Escrow-Lösung — Dokumentation

**Stand:** 25. August 2026
**Version:** v3.2
**Status:** Implementiert (manuell) + Erweiterungsplan

---

## 1. Aktueller Ist-Zustand

### Was implementiert ist

| Komponente | Status | Details |
|------------|--------|---------|
| **Escrow-Datenbank-Modell** | ✅ | `escrow_transactions` Tabelle mit 12 Feldern |
| **5 API-Endpoints** | ✅ | create, get, release, refund, dispute |
| **Frontend-Template** | ✅ | escrow.html mit Create/Lookup/Details/Actions |
| **10 Tests** | ✅ | test_escrow.py (create, get, release, refund, dispute, edge cases) |
| **i18n (EN/AR)** | ✅ | 16 Keys in en.json + ar.json |
| **Router-Registrierung** | ✅ | In routes/__init__.py eingebunden |

### Datenbank-Schema

```python
class Escrow(Base):
    __tablename__ = "escrow_transactions"
    id              = Column(Integer, primary_key=True)
    order_id        = Column(Integer, ForeignKey("orders.id"))
    buyer_id        = Column(Integer, ForeignKey("users.id"))
    supplier_id     = Column(Integer, ForeignKey("users.id"))
    amount          = Column(Float)
    currency        = Column(String(3), default="LYD")
    status          = Column(String(50), default="pending")  # pending|released|refunded|disputed
    note            = Column(String(500))
    created_at      = Column(DateTime)
    released_at     = Column(DateTime, nullable=True)
    refunded_at     = Column(DateTime, nullable=True)
    disputed_at     = Column(DateTime, nullable=True)
```

### API-Endpoints

| Methode | Endpoint | Funktion | Auth |
|---------|----------|----------|------|
| `POST` | `/api/escrow` | Escrow erstellen | ✅ |
| `GET` | `/api/escrow/{id}` | Status abrufen | ✅ |
| `POST` | `/api/escrow/{id}/release` | Geld freigeben | ✅ |
| `POST` | `/api/escrow/{id}/refund` | Geld zurückgeben | ✅ |
| `POST` | `/api/escrow/{id}/dispute` | Dispute eröffnen | ✅ |

### Frontend (escrow.html)

- ✅ Escrow erstellen (Order-ID + Betrag + Notiz)
- ✅ Escrow nachschlagen (Lookup)
- ✅ Status-Anzeige (pending/released/refunded/disputed) mit Farbcodes
- ✅ Buttons: Release / Refund / Dispute
- ✅ Transaktionshistorie (Client-seitig)
- ✅ Toast-Benachrichtigungen

### Tests (test_escrow.py — 10 Tests)

| Test | Beschreibung |
|------|-------------|
| `test_create_escrow` | Escrow für Bestellung erstellen |
| `test_get_escrow_status` | Status abrufen |
| `test_release_escrow` | Geld an Supplier freigeben |
| `test_refund_escrow` | Geld an Buyer zurückgeben |
| `test_dispute_escrow` | Dispute eröffnen |
| `test_cannot_release_already_released` | Doppelte Freigabe verhindern |
| `test_cannot_refund_already_released` | Rückerstattung nach Freigabe verhindern |
| `test_get_nonexistent_escrow` | 404 für nicht-existierendes Escrow |
| `test_create_escrow_negative_amount` | Negativer Betrag abgelehnt |
| `test_create_duplicate_escrow` | Duplikat pro Order abgelehnt |

---

## 2. Fehlende Features (Lückenanalyse)

### Lücke 1: Escrow-Tests in test_backend.py

**Status:** ❌ Nicht vorhanden
**Grund:** Alle Escrow-Tests sind in `test_airtable.py` (10 Tests). In `test_backend.py` gibt es keine Escrow-Tests.
**Empfehlung:** OK — separate test-Datei ist sauberer. Kein Handlungsbedarf.

### Lücke 2: Automatische Zahlung

**Status:** ❌ Nicht implementiert
**Grund:** Libyen hat kein Bank-System für API-Integrationen. Alle Zahlungen sind manuell (COD, E-Wallet-App, Bar).
**Lösung:** Manuelles Escrow-System (wie implementiert). Buyer bestätigt Zahlung → Supplier liefert → Buyer bestätigt Lieferung → Geld freigegeben.
**Keine Änderung nötig** — das ist die korrekte Architektur für den libyschen Markt.

### Lücke 3: Timeout/Auto-Release

**Status:** ❌ Nicht implementiert
**Grund:** Kein automatisches Freigeben nach X Tagen.
**Auswirkung:** Wenn Buyer nicht bestätigt, bleibt Escrow "pending" für immer.
**Lösung (Sprint 3):**
- Admin kann Escrow manuell freigeben
- Optional: Cron-Job prüft Escrow älter als 30 Tage → Status "expired"
- Keine automatische Zahlung (manueller Prozess)

### Lücke 4: Admin-Dispute-Resolution

**Status:** ❌ Kein Admin-Panel für Disputes
**Grund:** Kein Admin-Endpoint für Escrow-Resolution.
**Lösung (Sprint 3):**
- `POST /api/admin/escrow/{id}/resolve` (Admin only)
- `GET /api/admin/escrow/disputes` (Liste aller offenen Disputes)
- Admin-Template mit Escrow-Übersicht

### Lücke 5: Escrow in Order-Flow

**Status:** ❌ Kein Auto-Escrow bei Bestellung
**Grund:** Escrow muss manuell erstellt werden (separater Schritt).
**Lösung (Sprint 3):**
- Option A: Auto-Escrow bei Bestellung (wenn payment_method="escrow")
- Option B: Buyer klickt "Escrow erstellen" nach Bestellung
- Empfehlung: Option B (manuell, passend zum libyschen Markt)

---

## 3. Implementierungsplan (Sprint 3)

### Sprint 3: Escrow-Vervollständigung

| # | Task | Aufwand | Priorität |
|---|------|---------|-----------|
| 1 | Admin-Escrow-Resolution (API + UI) | 4h | 🔴 Hoch |
| 2 | Auto-Expire nach 30 Tagen (Cron/Endpoint) | 2h | 🟡 Mittel |
| 3 | Escrow im Order-Flow (Buyer-Button) | 2h | 🟡 Mittel |
| 4 | Escrow-Historie (DB-seitig, nicht Client) | 2h | 🟡 Mittel |
| 5 | Tests für neue Endpoints | 2h | 🔴 Hoch |
| **Gesamt** | | **12h** | |

### Detail: Admin-Escrow-Resolution

**Neue Endpoints:**

```python
# routes/admin_escrow.py
@router.get("/admin/escrow/disputes")     # Liste offener Disputes
@router.post("/admin/escrow/{id}/resolve") # Admin löst Dispute auf
@router.post("/admin/escrow/{id}/force-release") # Admin erzwingt Freigabe
```

**Admin-Template:**
- Liste aller Escrow-Transaktionen
- Filter: pending / disputed / released / refunded
- Buttons: Force Release / Refund / Mark Resolved

### Detail: Auto-Expire

**Option A (Cron-Job):**
```python
# Im Startup-Event
@app.on_event("startup")
async def start_escrow_expiry_checker():
    # Prüfe alle 24h: Escrow "pending" älter als 30 Tage → "expired"
```

**Option B (Lazy Check):**
```python
# Bei GET /api/escrow/{id}: Prüfe ob älter als 30 Tage
if escrow.status == "pending" and (now - escrow.created_at).days > 30:
    escrow.status = "expired"
```

Empfehlung: Option B (einfacher, kein Background-Thread).

### Detail: Escrow im Order-Flow

**In checkout.html / buyer.html:**
```html
<button onclick="createEscrowForOrder(orderId, amount)">
    🔒 Escrow erstellen
</button>
```

**Neuer Endpoint:**
```python
@router.post("/api/escrow/from-order/{order_id}")
# Erstellt automatisch Escrow basierend auf Order-Daten
```

---

## 4. Gesamtübersicht Phase 3

### Was ist fertig

| Feature | Status | Tests |
|---------|--------|-------|
| Escrow-Datenbank | ✅ | — |
| 5 Escrow-Endpoints | ✅ | 10 Tests |
| Escrow-Frontend | ✅ | — |
| Escrow-i18n | ✅ | — |
| Router-Registrierung | ✅ | — |

### Was fehlt

| Feature | Aufwand | Priorität |
|---------|---------|-----------|
| Admin-Dispute-Resolution | 4h | 🔴 |
| Auto-Expire (30 Tage) | 2h | 🟡 |
| Escrow im Order-Flow | 2h | 🟡 |
| DB-seitige Historie | 2h | 🟡 |
| Tests für neue Endpoints | 2h | 🔴 |
| **Gesamt** | **12h** | |

### Empfohlene Reihenfolge

```
Sprint 3, Tag 1: Admin-Escrow-Resolution (API + UI)
Sprint 3, Tag 2: Auto-Expire + DB-Historie
Sprint 3, Tag 3: Escrow im Order-Flow + Tests
```

---

## 5. Technische Details

### Status-Flow

```
pending → released    (Buyer bestätigt Lieferung)
pending → refunded    (Buyer bietet Rückerstattung an)
pending → disputed    (Konflikt zwischen Buyer/Supplier)
pending → expired     (30 Tage ohne Aktion)
disputed → released   (Admin entscheidet für Supplier)
disputed → refunded   (Admin entscheidet für Buyer)
```

### Sicherheit

- Nur authentifizierte User können Escrow erstellen/verwalten
- Release/Refund nur durch Buyer (nicht Supplier)
- Admin-Endpoints erfordern Admin-Rolle
- Keine automatische Zahlung (manueller Prozess)

### Kompatibilität

- **COD:** Escrow optional (Buyer kann Escrow erstellen oder direkt bar zahlen)
- **Offline:** Escrow-Status wird lokal gespeichert, bei nächster Synchronisation übertragen
- **RTL:** Volle Arabische Unterstützung in escrow.html

---

## 6. Test-Übersicht

### Aktuelle Tests (10)

```
test_create_escrow                    ✅
test_get_escrow_status                ✅
test_release_escrow                   ✅
test_refund_escrow                    ✅
test_dispute_escrow                   ✅
test_cannot_release_already_released  ✅
test_cannot_refund_already_released   ✅
test_get_nonexistent_escrow           ✅
test_create_escrow_negative_amount    ✅
test_create_duplicate_escrow          ✅
```

### Geplante Tests (+6)

```
test_admin_resolve_dispute            ⏳
test_admin_force_release              ⏳
test_escrow_auto_expire               ⏳
test_escrow_from_order                ⏳
test_escrow_history_db                ⏳
test_unauthorized_escrow_access       ⏳
```

**Gesamt nach Sprint 3:** 228 + 6 = 234 Tests

---

*Erstellt: 25.08.2026 | Nächste Aktualisierung: Nach Sprint 3*
