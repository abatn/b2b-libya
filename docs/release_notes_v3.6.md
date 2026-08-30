# Release Notes v3.6 — 27. August 2026

## Summary
Push Notifications (VAPID) vollständig aktiviert. Developer-Guide erstellt. Knowledge-Base aktualisiert.

---

## New Features

### Push Notifications — VAPID aktiviert
- **VAPID-Keys generiert** — Private PEM + Public Key (URL-safe base64)
- **VAPID Public Key Endpoint** — `GET /api/notifications/vapid-public-key`
- **push-notifications.js** — Holt Public Key vom Server statt hardcodiert
- **notifications.py** — Liest Keys aus Dateien → Env-Vars als Fallback
- **pywebpush 2.0.3** + **py-vapid 1.9.1** zu Dependencies hinzugefügt

### Developer Guide
- **docs/developer_guide.md** — Vollständiger Developer-Guide mit:
  - Architecture Overview (Verzeichnisstruktur + Data Flow)
  - API Reference (76 Endpoints, alle Module)
  - Database Schema (19 Tabellen)
  - Payment SDK Architecture
  - PWA / Service Worker
  - Push Notifications (VAPID)
  - Navigation System (3-Layer)
  - i18n / RTL Support
  - Testing (267 Tests)
  - Deployment (Docker + Production Checklist)
  - Conventions + Gotchas

### Knowledge Base
- **knowledge.md** — Von v1.5 auf v3.6 aktualisiert
  - 76 Endpoints (vorher 9)
  - 19 Tabellen (vorher 14)
  - 37 Pydantic Models (vorher 22)
  - 29 Templates (vorher 26)
  - 267 Tests (vorher 218)

---

## Changes

| Datei | Änderung |
|-------|----------|
| `pyproject.toml` | pywebpush==2.0.3 + py-vapid==1.9.1 |
| `src/backend/requirements.txt` | pywebpush + py-vapid |
| `src/backend/routes/notifications.py` | VAPID-Key-Loading + Public-Key-Endpoint |
| `src/frontend/static/push-notifications.js` | Public Key wird vom Server geladen |
| `docker-compose.yml` | env_file entfernt |
| `.gitignore` | vapid_keys/, .env, vapid_*.pem |
| `.env.example` | VAPID-Variablen dokumentiert |
| `knowledge.md` | v1.5 → v3.6 |
| `docs/developer_guide.md` | Neu erstellt |

---

## Stats

| Metric | v3.5 | v3.6 | Change |
|--------|------|------|--------|
| Tests | 267 | 267 | — |
| Templates | 29 | 29 | — |
| API Endpoints | 76 | 76 | — |
| DB Tables | 19 | 19 | — |
| Documentation Files | 5 | 6 | +1 (developer_guide.md) |

---

## Known Limitations
- Echte Payment Provider (SADAD/Fawry/Moamalat) — warten auf API-Keys
- VAPID Private Key — muss in Produktion als Environment Variable gesetzt werden

---

*Released: 27.08.2026 | Version: v3.6*
