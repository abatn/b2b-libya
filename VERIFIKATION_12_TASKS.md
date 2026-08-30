# Libya B2B: Definitive Verifikation aller 12 Migration-Tasks

**Stand:** 28. August 2026
**Methode:** Code-Audit mit Line-by-Line-Verifikation
**Tests:** 339/339 bestanden (12.34s)

---

## Ergebnis: 5/12 Vollständig, 7/12 Teilweise

| Task | Behauptung | Status | Differenz |
|------|-----------|--------|-----------|
| Bug A | product_count dynamisch | ✅ VOLLSTAENDIG | — |
| Bug B | Badge nur wenn is_verified (Detail) | ✅ VOLLSTAENDIG | — |
| Bug C | Badge nur wenn is_verified (Listing) | ✅ VOLLSTAENDIG | — |
| P1 | 125 Produkte mit Unsplash-Bildern | ⚠️ TEILWEISE | 312 OK, aber Kategorie-weit, nicht per-Produkt |
| P2 | Supplier-Mehrfachkategorien | ⚠️ TEILWEISE | Model+API ja, Seed/UI/Filter nein |
| P3 | Pagination "Load More" | ✅ VOLLSTAENDIG | Client-seitig, 12 pro Seite |
| P4 | Dispute-Messaging | ⚠️ TEILWEISE | Backend ja, Frontend-UI nein |
| P5 | Partial Refund | ⚠️ TEILWEISE | User-Endpoint ja, Admin nein |
| P6 | QR→Escrow Auto-Release | ✅ VOLLSTAENDIG | — |
| P7 | Level-4 Kategorie-Hierarchie | ✅ VOLLSTAENDIG | 3 Kategorien mit Level-4 |
| P8 | FTS5-Virtual-Table | ⚠️ TEILWEISE | Tabelle ja, nur /fts-Endpoint, kein Sync |
| P9 | Supplier-Bewertungsseite | ⚠️ TEILWEISE | Backend ja, Frontend-UI nein |
| P10 | 312 Produkte | ✅ VOLLSTAENDIG | — |
| Tests | 339/339 | ✅ 339 passed | 0 failed |

---

## Detail-Analyse: Die 7 teilweisen Tasks

### P1: Bilder

**Was existiert:**
- `seed_data.py` Zeile 62-83: `CATEGORY_IMAGES` Dictionary mit 20 Unsplash-URLs
- `seed_data.py` Zeile 529: `image_url=CATEGORY_IMAGES.get(p["category"])` — jedes Produkt bekommt ein Kategorie-Bild
- 312 Produkte haben alle ein Bild

**Was fehlt:**
- Bilder sind Kategorie-weit (alle "Cement"-Produkte haben dasselbe Bild)
- Keine per-Produkt-Bild-URLs
- Kein Upload-Frontend für Supplier

**Dateien:** `src/backend/seed_data.py`

---

### P2: Supplier-Mehrfachkategorien

**Was existiert:**
- `models.py` Zeile 147: `categories = Column(Text, nullable=True)` — JSON-Array
- `models.py` Zeile 507: `SupplierCreate` hat `categories: Optional[list[str]]`
- `routes/suppliers.py` Zeile 26-27: Serialisierung bei Create
- `routes/suppliers.py` Zeile 208-209: Serialisierung bei Update
- `routes/suppliers.py` Zeile 99: Deserialisierung in List-Response

**Was fehlt:**
- `seed_data.py` setzt nur `category` (singular), nicht `categories`
- `SupplierResponse` (models.py Zeile 535-561) hat kein `categories`-Feld
- Frontend zeigt keine Mehrfachauswahl
- Filter nutzt nur `Supplier.category` (singular)

**Dateien:** `src/backend/models.py`, `src/backend/routes/suppliers.py`, `src/frontend/templates/suppliers.html`

---

### P4: Dispute-Messaging

**Was existiert:**
- `models.py` Zeile 274-282: `DisputeMessage`-Tabelle (escrow_id, sender_id, sender_type, text)
- `models.py` Zeile 691-702: Pydantic-Schemas `DisputeMessageCreate`, `DisputeMessageResponse`
- `routes/escrow.py` Zeile 224-233: `GET /{escrow_id}/dispute/messages`
- `routes/escrow.py` Zeile 236-264: `POST /{escrow_id}/dispute/messages`

**Was fehlt:**
- `templates/escrow.html` hat KEINE Chat-UI
- Keine Nachrichten-Liste
- Kein Input-Feld für neue Nachrichten
- Keine `loadDisputeMessages()`-Funktion

**Dateien:** `src/frontend/templates/escrow.html`

---

### P5: Partial Refund

**Was existiert:**
- `routes/escrow.py` Zeile 130-135: `refund_escrow(escrow_id, amount: float | None = None)`
- `routes/escrow.py` Zeile 145-150: Partial Refund Logik (wenn amount < escrow.amount)

**Was fehlt:**
- `routes/admin_escrow.py` Zeile 44-87: `resolve_escrow()` hat KEIN `amount`-Parameter
- Admin kann nur vollständig freigeben oder erstatten

**Dateien:** `src/backend/routes/admin_escrow.py`

---

### P8: FTS5

**Was existiert:**
- `config.py` Zeile 63-68: `CREATE VIRTUAL TABLE products_fts USING fts5(...)`
- `config.py` Zeile 70-73: Initiale Befüllung aus products-Tabelle
- `routes/search.py` Zeile 305-378: `/api/search/fts` nutzt FTS5 MATCH mit ILIKE-Fallback

**Was fehlt:**
- Haupt-Suche (`/api/search`, Zeile 77-134) nutzt Python-Fuzzy-Scoring, kein FTS5
- Autocomplete (`/api/search/autocomplete`, Zeile 240-302) nutzt ILIKE, kein FTS5
- Keine Trigger für Sync bei Produkt-Insert/Update/Delete
- FTS5-Index kann stale werden

**Dateien:** `src/backend/config.py`, `src/backend/routes/search.py`

---

### P9: Supplier-Bewertungen

**Was existiert:**
- `models.py` Zeile 285-294: `SupplierReview`-Tabelle (supplier_id, user_id, rating, comment, order_id)
- `models.py` Zeile 705-726: Pydantic-Schemas `SupplierReviewCreate`, `SupplierReviewResponse`
- `routes/suppliers.py` Zeile 374-382: `GET /{supplier_id}/reviews`
- `routes/suppliers.py` Zeile 383-424: `POST /{supplier_id}/reviews` (mit Auth + Duplicate-Check)

**Was fehlt:**
- `templates/supplier_detail.html` Zeile 164-168: Nur aggregate Rating-Anzeige
- KEINE individuelle Bewertungsliste
- Keine `loadReviews()`-Funktion
- Keine Review-Karten (User-Name, Kommentar, Datum)

**Dateien:** `src/frontend/templates/supplier_detail.html`

---

## Vollständige Tasks (5 Stück)

### Bug A: product_count dynamisch
`routes/suppliers.py` Zeile 158-159: `product_count = len(products)` aus Live-Query.

### Bug B: Badge nur wenn is_verified (Detail)
`templates/supplier_detail.html` Zeile 283: `if (s.is_verified) badgesHtml += '...Trade Assurance...'`

### Bug C: Badge nur wenn is_verified (Listing)
`templates/suppliers.html` Zeile 248: `${s.is_verified ? '<span...Trade Assurance...</span>' : ''}`

### P3: Pagination "Load More"
`templates/suppliers.html` Zeile 172: `PAGE_SIZE = 12`, Zeile 144: Load-More-Button.

### P6: QR→Escrow Auto-Release
`routes/qr_routes.py` Zeile 70-92: Nach erfolgreicher QR-Verification → Escrow auto-release.

### P7: Level-4 Kategorie-Hierarchie
`routes/b2b.py` Zeile 235-241 (cement), 263-268 (wires), 346-351 (grains): `sub_sub_subcategories`.

### P10: 312 Produkte
`seed_data.py` PRODUCTS-Liste: 312 Einträge, 20 Kategorien.

---

## Offene Aufgaben für vollständige 100%

| # | Aufgabe | Aufwand | Priorität |
|---|---------|---------|-----------|
| 1 | Dispute-Messaging UI (escrow.html) | 3-4h | HOCH |
| 2 | Supplier-Bewertungsliste (supplier_detail.html) | 2-3h | HOCH |
| 3 | FTS5-Sync-Trigger (config.py) | 2-3h | MITTEL |
| 4 | FTS5 in Haupt-Suche + Autocomplete | 3-4h | MITTEL |
| 5 | Admin Partial Refund (admin_escrow.py) | 1-2h | MITTEL |
| 6 | SupplierResponse categories-Feld (models.py) | 30 Min | NIEDRIG |
| 7 | Seed categories-Feld setzen (seed_data.py) | 30 Min | NIEDRIG |
| 8 | Per-Produkt-Bilder statt Kategorie-Bilder | 3-4h | NIEDRIG |

---

*Erstellt: 28.08.2026 | Definitive Verifikation der Libya B2B Migration*
