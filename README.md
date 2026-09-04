# Libya B2B Platform - KI-gestuetzte B2B-Plattform

**Projektversion:** v7.0 (Same-Origin Monolith)  
**Stand:** 4. September 2026  
**Budget:** Max. 20 EUR/Monat Hosting (Render Free Tier + Supabase Free Tier = 0 EUR)  
**Technologie:** 100% Open-Source, CPU-basiert

---

## Beschreibung

Offline-first KI-B2B-Plattform fuer Libyen, basierend auf dem Alibaba-Modell. Die Plattform adressiert die spezifischen Herausforderungen des libyschen Marktes:

- **100% COD** (Cash on Delivery) mit digitalem Tracking
- **Offline-First** fuer 77,4% Stromzugang (World Bank 2024)
- **Arabischer KI-Chatbot** fuer 6,1 Mio. Internetnutzer
- **QR-Code-Tracking** fuer Transparenz trotz Barzahlung

---

## Architektur (alsouk-Prinzip)

EIN FastAPI-Prozess serves ALLES same-origin: server-gerenderte HTML-Seiten (Jinja2),
API unter `/api/*` und Static-Assets. Kein CORS, kein API_BASE, kein separates Frontend.

- **Produktion:** https://b2b-libya.onrender.com (Render, Docker, Auto-Deploy von main)
- **DB:** PostgreSQL via `DATABASE_URL` (Supabase Pooler) — Fallback SQLite ohne Env-Var
- **Auth:** Session-Cookie (`b2b_session`, HttpOnly, Secure auf https, SameSite=Lax)
- **CI:** GitHub Actions — lint → test (357) → Docker-Build + Health/Page/API-Smoke

## Quick Start

### Backend starten

```bash
cd src/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API-Dokumentation: http://localhost:8000/docs

### Tests ausfuehren

```bash
pytest tests/ -v
```

### Docker starten

```bash
docker compose up -d
```

---

## Technologie-Stack

| Komponente | Technologie | Lizenz |
|------------|-------------|--------|
| Frontend+Backend | FastAPI (Jinja2-Rendering, same-origin) | MIT |
| DB | PostgreSQL (Supabase) / SQLite (lokal) | PostgreSQL / Public Domain |
| KI: ML | scikit-learn | BSD-3 |
| KI: NLP | bert-base-arabic | Apache 2.0 |
| KI: CV | OpenCV + MobileNet | Apache 2.0 |
| Hosting | Render (Docker) | Free Tier |

---

## Projektstruktur

```
libya_b2b_platform/
├── src/
│   ├── backend/
│   │   ├── main.py               # FastAPI: HTML + API + Static (ein Prozess)
│   │   ├── config.py             # DB-Setup (PostgreSQL via DATABASE_URL, SQLite-Fallback)
│   │   ├── routes/
│   │   │   ├── static_pages.py   # 34 HTML-Routen (Jinja2, EN + /ar/)
│   │   │   └── ...               # API-Routen (21 Module)
│   │   ├── services/             # auth, payment, search, email
│   │   ├── seed_data.py          # 30 Suppliers + 312 Products (idempotent)
│   │   └── requirements.txt
│   └── frontend/
│       ├── templates/            # Jinja2-Templates (Quelle für static_pages.py)
│       ├── static/               # JS/CSS (via /static/ gemounted)
│       └── locales/              # en.json, ar.json
├── tests/                        # 357 Tests (18 Dateien)
├── Dockerfile                    # Root-Dockerfile (Render + CI)
├── docker-compose.yml            # Lokaler Single-Service
├── render.yaml                   # Render-Blueprint (Single Service)
└── .github/workflows/ci.yml      # CI: lint → test → docker
```

---

## API-Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | Health Check |
| `/api/products` | GET/POST | Produkte auflisten/erstellen |
| `/api/products/{id}` | GET/PUT/DELETE | Produkt verwalten |
| `/api/orders` | GET/POST | Bestellungen (COD) |
| `/api/orders/{id}/deliver` | PUT | Lieferung bestaetigen |
| `/api/chat` | POST | KI-Chatbot (Arabisch) |
| `/api/sync/changes` | GET | Delta-Sync |

---

## Lizenz

MIT License - Siehe LICENSE Datei
