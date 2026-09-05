# Agent-Prompt: Alsouk-Platform aufbauen (nach Libya B2B Muster)

Kopiere diesen Prompt komplett und sende ihn an einen Agenten, der das Projekt `github.com/abatn/alsouk-platform` als separates Repo aufbaut.

---

```
Du bist ein Implementierungs-Agent und baust die Alsouk-Platform als separates Projekt
von Grund auf auf. Das Architektur-Muster nimmst du aus dem Libya B2B Projekt
(github.com/abatn/b2b-libya, Stand: b2b-libya.onrender.com läuft), dessen _PLAN.md
die 8 alsouk-Prinzipien definiert. Du baust ein identisches Muster, aber mit alsouk-spezifischen
Inhalten (B2B-Messe/Exhibition-Plattform für Tunesien/Nordafrika).

## HARD RULES (nicht verletzen)

1. EIN Repository: github.com/abatn/alsouk-platform (NEU, kein Fork von b2b-libya)
2. EIN Prozess: FastAPI auf Port 8000, served HTML + API + Static (same-origin)
3. Kein CORS, kein cross-origin, kein API_BASE im Frontend
4. Session-Cookie auth (bcrypt + secrets.token_hex), same-origin
5. SQLite als DB (Fallback: PostgreSQL via DATABASE_URL)
6. Server-gerenderte HTML via Jinja2Templates (kein React, kein Next.js)
7. render.yaml + Dockerfile im Root für Render-Deploy
8. CI: pytest + ruff check + ruff format --check → alles grün
9. Kein Plan ohne Gates — jeder Block bricht ab wenn pytest/ruff rot ist

## ARCHITEKTUR (exakt wie Libya B2B)

### Dateistruktur
```
alsouk-platform/
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI App-Factory, mount /static, include_router
│   │   ├── config.py            # SQLite/PostgreSQL Engine, init_db()
│   │   ├── models.py            # SQLAlchemy ORM (Alles was alsouk braucht)
│   │   ├── seed_data.py         # Seed-Daten (Kategorien, Exhibitions, Companies)
│   │   ├── services/
│   │   │   └── auth.py          # bcrypt + session token
│   │   ├── routes/
│   │   │   ├── __init__.py      # Reihenfolge: static VOR monitoring
│   │   │   ├── auth_routes.py   # Login/Logout/Me
│   │   │   ├── static_pages.py  # HTML-Routen via Jinja2Templates
│   │   │   ├── monitoring.py    # /health
│   │   │   ├── exhibitions.py   # REST: /api/exhibitions
│   │   │   ├── companies.py     # REST: /api/companies
│   │   │   ├── categories.py    # REST: /api/categories
│   │   │   ├── rfqs.py          # REST: /api/rfqs
│   │   │   └── admin.py         # REST: /api/admin/*
│   │   ├── requirements.txt
│   │   └── locales/             # i18n (en.json, ar.json)
│   └── frontend/
│       ├── static/              # JS + CSS (nav.js, auth.js, cart.js, config.js gelöscht)
│       └── templates/           # Jinja2 HTML-Templates
│           ├── base.html        # Layout mit {{content}} block
│           ├── nav.html         # Navigation (<!-- NAV_JS_INCLUDE --> im <head>)
│           ├── landing.html
│           ├── exhibitions.html
│           ├── exhibition_detail.html
│           ├── companies.html
│           ├── company_detail.html
│           ├── categories.html
│           ├── rfqs.html
│           ├── rfq_new.html
│           ├── rfq_detail.html
│           ├── login.html
│           ├── register.html
│           ├── admin/
│           │   ├── dashboard.html
│           │   ├── exhibitions.html
│           │   ├── companies.html
│           │   └── rfqs.html
│           └── ar/              # Arabische Templates (RTL)
├── tests/
│   ├── conftest.py             # Shared in-memory SQLite
│   ├── test_backend.py
│   └── test_api.py
├── Dockerfile                   # WORKDIR /app/src/backend, uvicorn
├── render.yaml                  # Single service, healthCheckPath /health
├── docker-compose.yml           # Ein Service (lokale Dev)
├── .github/workflows/
│   └── ci.yml                   # lint → test → docker → deploy
├── .gitignore
├── requirements.txt             # Alias für src/backend/requirements.txt
├── README.md
└── pytest.ini
```

### Block 1: Ein FastAPI-Prozess (HTML + API + Static same-origin)

**Ziel:** `main.py` mounted static aus `../frontend/static`, `routes/static_pages.py`
rendert 10+ HTML-Templates via Jinja2Templates. Alle fetch()-Calls relativ `/api/...`.

**Schritte:**
1. `main.py`: App-Factory, StaticFiles mount auf `/static` (NICHT templates), include_router für alle routes
2. `routes/static_pages.py`: Jinja2Templates mit `from_string()` oder `TemplateResponse`
3. `routes/__init__.py`: static_router VOR monitoring_router (sonst fängt `/` der monitoring_router ab)
4. `services/auth.py`: Session-Cookie (b2b_session), bcrypt, secrets.token_hex
5. `routes/auth_routes.py`: Login → Cookie, Logout → Cookie löschen, Me → User aus Cookie
6. `routes/monitoring.py`: `/health` mit DB-Typ dynamisch

**Gate:**
```bash
cd alsouk-platform && python -m pytest tests/ -q   # Muss: passed
ruff check src/backend/                             # Muss: All checks passed
ruff format --check src/backend/                    # Muss: 0 would be reformatted

# Seiten-Schleife
for route in / /exhibitions /companies /categories /login /register /rfqs; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$route)
  echo "$route → $STATUS"
done
# Muss: 200 für alle

# Static-Files
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/static/nav.js
# Muss: 200
```

### Block 2: Deploy auf Render

**Ziel:** Ein Dockerfile, ein Service, `/health` erreichbar, HTML-Seiten live.

**Dockerfile (Root):**
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY src/backend/requirements.txt ./src/backend/requirements.txt
RUN pip install --no-cache-dir -r src/backend/requirements.txt
COPY src/ ./src/
WORKDIR /app/src/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**render.yaml:**
```yaml
services:
  - type: web
    name: alsouk-platform
    env: docker
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        value: sqlite:///./alsouk.db
```

**Gate:**
```bash
# Nach Deploy:
curl -s https://alsouk-platform.onrender.com/health | python3 -m json.tool
# Muss: {"status":"healthy", "database":"sqlite", ...}

curl -s https://alsouk-platform.onrender.com/ | grep "<title>"
# Muss: HTML-Titel (nicht JSON, nicht 404)

curl -s https://alsouk-platform.onrender.com/api/exhibitions | head -c 200
# Muss: JSON-Array
```

### Block 3: Seed-Daten + Auth verifizieren

**Seed (idempotent):**
- Kategorien: Electronics, Agriculture, Textiles, Construction, Food & Beverage, Machinery
- Exhibitions: 6 Beispiele (Tripoli Tech Expo, Tunis Agri Fair, etc.)
- Companies: 10 Beispiele mit Kategorien-Zuordnung
- Users: admin/alsouk123 (admin), tester/alsouk123 (user)

**Auth-Flow (same-origin):**
```bash
# Login
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"alsouk123"}'
# Muss: 200 + Set-Cookie: b2b_session=...

# API mit Cookie
curl -b cookies.txt http://localhost:8000/api/rfqs
# Muss: 200 + JSON

# Ohne Cookie
curl http://localhost:8000/api/rfqs
# Muss: 401
```

### Block 4: i18n + RTL

- `/ar/` Versionen aller Seiten
- `lang="ar"` + `dir="rtl"` im HTML
- Sprach-Switcher in nav.html (EN ↔ AR)
- Locale-JSONs: `locales/en.json`, `locales/ar.json`

**Gate:**
```bash
curl -s https://alsouk-platform.onrender.com/ar/ | grep 'dir="rtl"'
# Muss: 1 Treffer

curl -s https://alsouk-platform.onrender.com/ar/ | grep "<title>"
# Muss: Arabischer Titel
```

## ALSOUK-SPEZIFISCHE INHALTE

### Domain-Wissen
- B2B-Messe/Exhibition-Plattform für Tunesien + Nordafrika
- Exhibitions (Messen), Companies (Aussteller), Categories (Produktkategorien)
- RFQs (Request for Quotation), Admin-Dashboard
- Arabisch + Englisch (RTL)

### API-Endpunkte
```
GET    /health
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
GET    /api/exhibitions
GET    /api/exhibitions/{slug}
GET    /api/companies
GET    /api/companies/{slug}
GET    /api/categories
GET    /api/categories/{slug}
GET    /api/rfqs
POST   /api/rfqs
GET    /api/rfqs/{id}
GET    /api/admin/exhibitions
POST   /api/admin/exhibitions
GET    /api/admin/companies
GET    /api/admin/rfqs
```

### HTML-Seiten
```
/                     → Landing (Hero, Featured Exhibitions, Categories)
/exhibitions          → Exhibition-Liste mit Filter
/exhibitions/{slug}   → Exhibition-Detail (Booths, Companies)
/companies            → Company-Directory mit Kategorien
/companies/{slug}     → Company-Profil (Produkte, RFQs)
/categories           → Kategorie-Übersicht
/categories/{slug}    → Kategorie mit Companies
/rfqs                 → RFQ-Liste (eingeloggt)
/rfqs/new             → Neues RFQ erstellen
/rfqs/{id}            → RFQ-Detail + Antworten
/login                → Login-Modal (wie Libya B2B)
/register             → Registrierung
/admin/*              → Admin-Dashboard
/ar/*                 → Arabische Versionen
```

## VERIFIKATION (nach jedem Block)

```bash
# 1. Tests
python -m pytest tests/ -q                  # passed
ruff check src/backend/                     # All checks passed
ruff format --check src/backend/            # 0 would be reformatted

# 2. Live
curl -s https://alsouk-platform.onrender.com/health
curl -s https://alsouk-platform.onrender.com/ | grep "<title>"
curl -s https://alsouk-platform.onrender.com/api/exhibitions | head -c 100
curl -s https://alsouk-platform.onrender.com/ar/ | grep 'dir="rtl"'

# 3. Auth
curl -c c.txt -X POST .../api/auth/login -d '{"username":"admin","password":"alsouk123"}'
curl -b c.txt .../api/rfqs                  # 200
curl .../api/rfqs                            # 401
```

## VERBOTE

- Kein React, kein Next.js, kein Vue — nur FastAPI + Jinja2Templates
- Kein `window.API_BASE`, kein `config.js`, kein cross-origin
- Kein CORS — alles same-origin
- Keine Passwörter/Secrets in Code oder Git
- Kein `/api/v1` — nur `/api/*`
- Kein neuer Block ohne grünen Gate des vorherigen
```

---

*Erstellt: 2026-09-05 | Basierend auf: _PLAN.md + b2b-libya.onrender.com Live-Zustand*
