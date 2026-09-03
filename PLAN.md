# Rebuild Plan: Libya B2B — alsouk-platform Architecture as Reference

> **Status:** Planning only. No code changes.
> **Revert-Stand:** `b0316e3` — docs: rebuild plan (previous PLAN.md)
> **Code-Stand:** `8a84de7` — feat: Libya B2B Platform v6.0 (312 products, 30 suppliers, 357 tests)
> **Reference:** github.com/abatn/alsouk-platform (337 commits, Next.js + Supabase)

---

## Part I: alsouk-platform Principles (Evidence-Based)

### P1 — EINE Runtime (Next.js-Server)

**Prinzip:** Ein Prozess rendert HTML *und* bedient API-Endpoints.

**Beweis:**
- `package.json`: `"scripts": { "dev": "next dev", "build": "next build", "start": "next start" }`
- `app/`-Verzeichnis enthält sowohl Seiten (`page.tsx`) als auch Route-Handler (`api/*/route.ts`)
- Kein separates Backend-Prozess. Ein `npm run dev` startet alles.

**Dateien:** `package.json`, `app/page.tsx`, `app/api/*/route.ts`

---

### P2 — SAME-ORIGIN (Frontend + API unter einer Domain)

**Prinzip:** Browser ruft `/api/*` auf derselben Origin wie die Seite auf. Kein CORS nötig.

**Beweis:**
- `middleware.ts`: `import { updateSession } from "@/lib/supabase/middleware"` — Session-Refresh bei jedem Request
- Keine `CORSMiddleware`-Konfiguration im gesamten Codebase
- `next.config.mjs`: `allowedDevOrigins: ['127.0.0.1']` (nur für Dev, kein Production-CORS)

**Dateien:** `middleware.ts`, `next.config.mjs`

---

### P3 — Supabase als DB + PostgREST-API in einem

**Prinzip:** Kein separates Backend. Supabase liefert Postgres + PostgREST + Auth + Storage.

**Beweis:**
- `lib/supabase/rest.ts`: `fetch(\`${cfg.url}/rest/v1/${path}\`)` — direkter PostgREST-Zugriff
- `lib/supabase/client.ts`: `createBrowserClient(supabaseUrl, supabaseAnonKey)` — Client-seitig nur Anon-Key
- `supabase/schema.sql`: Alles in einer SQL-Datei (companies, stores, products, RLS-Policies)

**Dateien:** `lib/supabase/rest.ts`, `lib/supabase/client.ts`, `lib/supabase/server.ts`, `supabase/schema.sql`

---

### P4 — Auth über Framework-Session + RLS-Policies in der DB

**Prinzip:** Supabase Auth verwaltet Sessions via Cookies. RLS-Policies schützen Datenbankzeilen.

**Beweis:**
- `middleware.ts`: `import { updateSession } from "@/lib/supabase/middleware"` — Session-Refresh
- `lib/supabase/middleware.ts`: `supabase.auth.getUser()` — Session-Validierung
- `supabase/schema.sql`: `create policy "Owners can insert their company" on public.companies for insert with check (owner_id = auth.uid())`
- Admin-Check: `isAdmin()` nutzt Service-Key + PostgREST für `admin_users`-Tabelle

**Dateien:** `middleware.ts`, `lib/supabase/middleware.ts`, `supabase/schema.sql`

---

### P5 — Service-Keys nur serverseitig

**Prinzip:** `SUPABASE_SERVICE_ROLE_KEY` und `AI_API_KEY` werden NIE mit `NEXT_PUBLIC_` prefix公开.

**Beweis:**
- `.env.example`: `SUPABASE_SERVICE_ROLE_KEY=` (ohne NEXT_PUBLIC), Kommentar: "NEVER prefix with NEXT_PUBLIC"
- `lib/supabase/env.ts` unterscheidet `KEY_VARS` (public) von `SERVICE_KEY_VARS` (server-only)
- `lib/supabase/rest.ts` nutzt nur den public Key für Reads

**Dateien:** `.env.example`, `lib/supabase/env.ts`, `lib/supabase/rest.ts`

---

### P6 — Deploy durch einen einzigen Auto-Deploy (Vercel)

**Prinzip:** Push to `main` → Vercel baut + deployed automatisch. Preview-Deployments pro PR.

**Beweis:**
- `PROJECT_STATUS.md`: "main auto-deploys to Vercel"
- Keine Docker-Files, keine docker-compose.yml
- `next.config.mjs`: `images: { unoptimized: true }` (Vercel-Image-Optimierung wird umgangen)

**Dateien:** `PROJECT_STATUS.md`, `next.config.mjs`

---

### P7 — Thin Pages, Heavy Components

**Prinzip:** Seiten in `app/` sind minimal (Metadata + Shell-Wrapper). Feature-Logik lebt in `components/`.

**Beweis:**
- `app/page.tsx`: Rendered `HomepageComposition` in `MarketplaceShell`
- `components/home/*`, `components/directory/*`, `components/marketplace/*`: Feature-Komponenten
- `lib/services/*-service.ts` (server) + `*-client.ts` (browser) — getrennte Datenzugriffsschichten

**Dateien:** `app/page.tsx`, `components/`, `lib/services/`

---

### P8 — i18n via Dictionary + RTL-Logical-Properties

**Prinzip:** Hand-rolled Dictionary (EN/FR/AR), kein Framework. `dir` via React Context + `localStorage`.

**Beweis:**
- `lib/i18n.ts`, `lib/directory-i18n.ts`: Dictionary-Objekte mit EN+FR+AR Keys
- `components/language-provider.tsx`: `LanguageProvider` setzt `dir`-Attribut
- CSS nutzt logische Properties: `start/end` statt `left/right`, `rtl:` Tailwind-Modifier

**Dateien:** `lib/i18n.ts`, `lib/directory-i18n.ts`, `components/language-provider.tsx`

---

## Part II: Libya B2B Current State (Code-Stand 8a84de7)

### Komponenten-Übersicht

| Komponente | Technologie | Status |
|---|---|---|
| **Backend** | FastAPI (Python), 40+ Dateien | 21+ Route-Module, 357 Tests |
| **Frontend** | Python HTTP-Server (`server.py`), 35 HTML-Templates | Jinja-Rendering auf Port 3000 |
| **Datenbank** | SQLite (offline-first) | 52 Pydantic-Modelle, 27 SQLAlchemy-Tables |
| **Auth** | Session-Cookie + bcrypt | `services/auth.py`, `routes/auth_routes.py` |
| **API** | FastAPI auf Port 8000 | CORS: `allow_origins=["*"]` (cross-origin) |
| **Deploy** | Docker Compose (2 Container) | Backend:8000 + Frontend:3000 |
| **Daten** | 312 Produkte, 30 Suppliers | Seed-Data in `seed_data.py` |
| **Tests** | pytest, 357 Tests | `tests/test_backend.py` + 20 weitere Dateien |
| **Offline-First** | SQLite, Sync-Engine | `sync_engine.py` mit Delta-Sync |
| **Budget** | 20 EUR/Monat | Keine Cloud-Dependencies |

---

## Part III: Principle-by-Principle Comparison mit konkreten Beweisen

### P1: EINE Runtime

**alsouk:** Ein `npm run dev` startet alles.

**Libya B2B Lücke:** Zwei separate Prozesse.

| Komponente | Datei | Beweis |
|---|---|---|
| Backend | `src/backend/main.py:21-25` | `app = FastAPI(...)` — eigener Prozess |
| Frontend | `src/frontend/server.py:15-16` | `PORT = 3000`, `BACKEND_URL = "http://localhost:8000"` |
| Docker | `docker-compose.yml:9-64` | Zwei Services: `backend` + `frontend` |

**Was sich ändern muss:** Frontend wird zu FastAPI-Routen degradiert. Ein Prozess.

---

### P2: SAME-ORIGIN

**alsouk:** Keine CORS-Konfiguration, `/api/*` same-origin.

**Libya B2B Lücke:** Cross-Origin mit CORS `*`.

| Komponente | Datei | Beweis |
|---|---|---|
| CORS | `src/backend/main.py:30-36` | `allow_origins=["*"]` — explizit cross-origin |
| Proxy | `src/frontend/server.py:439-469` | `proxy_request()` leitet `/api/*` an Backend weiter |
| Frontend URL | `src/frontend/server.py:16` | `BACKEND_URL = "http://localhost:8000"` |
| JS-Fetches | `src/frontend/static/auth.js:37` | `fetch('/api/auth/register')` — relativ, aber cross-origin durch 2 Prozesse |

**Was sich ändern muss:** Ein Prozess, CORS entfernen, keine Proxy-Logik nötig.

---

### P3: DB + API in einem

**alsouk:** Supabase = Postgres + PostgREST + Auth + Storage.

**Libya B2B Status:** SQLite + FastAPI (akzeptabel für Offline-First).

| Komponente | Datei | Beweis |
|---|---|---|
| DB | `src/backend/config.py` | SQLite-Engine, `init_db()` |
| API | `src/backend/main.py:88` | `register_routes(app)` — FastAPI-Routen |
| Sync | `src/backend/sync_engine.py` | Delta-Sync für Offline-First |

**Was sich ändern muss:** Nichts (Offline-First-Constraint). SQLite + FastAPI bleibt.

---

### P4: Auth via Framework + RLS

**alsouk:** Supabase Auth + RLS-Policies in der DB.

**Libya B2B Status:** Custom Session-Cookie + Dependency Injection.

| Komponente | Datei | Beweis |
|---|---|---|
| Session | `src/backend/routes/auth_routes.py:34` | `SESSION_COOKIE_NAME = "b2b_session"` |
| Login | `src/backend/routes/auth_routes.py:90-100` | `@router.post("/register")` mit Cookie-Setzung |
| Protected Routes | `src/backend/routes/auth_routes.py:43-62` | `get_current_user(request, db)` — Dependency |
| Password | `src/backend/services/auth.py:19-25` | `hash_password()` mit bcrypt |

**Was sich ändern muss:** Auth ist bereits Framework-integriert (FastAPI Dependencies). Kein RLS nötig (SQLite).

---

### P5: Service-Keys serverseitig

**alsouk:** `SUPABASE_SERVICE_ROLE_KEY` ohne `NEXT_PUBLIC_`.

**Libya B2B Status:** Bereits korrekt.

| Komponente | Datei | Beweis |
|---|---|---|
| Env | `src/backend/config.py` | `DATABASE_URL` nur serverseitig |
| Keys | `docker-compose.yml:17` | `DATABASE_URL=sqlite:///./libya_b2b.db` — kein PUBLIC_ |

**Was sich ändern muss:** Nichts. Bereits korrekt implementiert.

---

### P6: Single Auto-Deploy

**alsouk:** Push to main → Vercel deployed.

**Libya B2B Status:** Docker Compose (2 Container).

| Komponente | Datei | Beweis |
|---|---|---|
| Docker | `docker-compose.yml:9-64` | Zwei Services: `backend` + `frontend` |
| Healthcheck | `docker-compose.yml:22-27` | `curl -f http://localhost:8000/health` |
| Network | `docker-compose.yml:86-88` | `libya-b2b-network` Bridge |

**Was sich ändern muss:** Ein Container statt zwei.

---

### P7: Thin Pages, Heavy Components

**alsouk:** `app/page.tsx` minimal, Features in `components/`.

**Libya B2B Status:** Templates mit eingebetteter Logik.

| Komponente | Datei | Beweis |
|---|---|---|
| Templates | `src/frontend/templates/*.html` | 35 Dateien mit Inline-JavaScript |
| JS-Logik | `src/frontend/static/*.js` | 24 Dateien mit API-Logik |
| Render | `src/frontend/server.py:102-177` | `render_template()` — Jinja2-Rendering |

**Was sich ändern muss:** Templates bleiben (Jinja2), aber Logik wird getrennt.

---

### P8: i18n Dictionary + RTL

**alsouk:** Hand-rolled Dictionary, RTL via Context.

**Libya B2B Status:** Bereits implementiert.

| Komponente | Datei | Beweis |
|---|---|---|
| Locales | `src/frontend/locales/en.json`, `ar.json` | Dictionary-Dateien |
| RTL | `src/frontend/server.py:172-175` | `<html lang="ar" dir="rtl">` dynamisch |
| Navigation | `src/frontend/server.py:32-99` | `rewrite_nav_links()` für /ar/ Prefix |

**Was sich ändern muss:** Nichts. Bereits implementiert.

---

## Part IV: Option A vs. Option B

### Option A: FastAPI-Monolith same-origin
- **Ein Service** rendert HTML + dient API
- Code bleibt (FastAPI + server.py)
- SQLite bleibt (offline-first)
- Docker Compose wird zu einem einzigen Container optimiert

### Option B: Echter Nachbau (Next.js + Supabase)
- FastAPI wird verworfen
- Next.js ersetzt server.py
- Supabase ersetzt SQLite
- Vercel ersetzt Docker

### **Empfehlung: Option A**

**Begründung:**

1. **Offline-First:** Supabase erfordert Internet. SQLite funktioniert offline. Das ist ein hartes Constraint für Libyen (instabile Internetverbindung).

2. **Budget 20 EUR/Monat:** Supabase Free-Tier ist begrenzt (500MB DB, 1GB Storage, 50k MAU). Bei 500 Pilot-SMEs mit 312 Produkten + Bildern → schnell überschritten. Vercel Free-Tier: 100GB Bandwidth, aber Build-Limits.

3. **Bestehende Investition:** 357 Tests, 312 Produkte, 30 Suppliers, complete Auth, Sync-Engine, QR-Codes, Chatbot, Payment-Gateway — alles in Python. Verwerfen = Monate an Arbeit.

4. **Libyen-spezifisch:** Kein Vercel in Libyen erreichbar (DNS-Blocking). Kein Supabase-Deployment in Nordafrika. SQLite läuft überall.

5. **Architektur-Prinzipien sind framework-agnostisch:** Same-Origin, eine Runtime, Session-basierte Auth — das sind Konzepte, keine Next.js-spezifischen Features.

---

## Part V: Phasenplan (Option A — FastAPI same-origin)

### Phase 1: Same-Origin Consolidation

**Ziel:** Ein Prozess, ein Port, kein CORS.

**Was sich ändert:**
- `src/backend/main.py` bekommt StaticFiles-Mount + Jinja2-Rendering
- `src/frontend/server.py` wird zu FastAPI-Router degradiert
- CORS-Middleware wird entfernt

**Betroffene Dateien:**
- `src/backend/main.py` — FastAPI rendert HTML + API
- `src/frontend/server.py` — Wird zu FastAPI-Route
- `src/frontend/templates/` — Bleiben als Jinja2-Templates
- `src/frontend/static/` — Werden zu FastAPI-StaticFiles

**Verifikation:**
```bash
# Ein Prozess auf Port 8000
curl -s http://localhost:8000/ | head -5  # HTML
curl -s http://localhost:8000/api/v1/products | head -5  # JSON
# Kein CORS-Header nötig
curl -s -I http://localhost:8000/api/v1/products | grep -i "access-control"
# Erwartung: Kein Output (kein CORS-Header)
```

**Push-Punkt:** `refactor: consolidate to single FastAPI server on :8000`

---

### Phase 2: Session-Based Auth (Framework-Integration)

**Ziel:** Auth via FastAPI-Sessions (Cookie-basiert) + Dependency Injection.

**Was sich ändert:**
- Cookie-Middleware in `main.py` hinzufügen
- `get_current_user` wird zur globalen Dependency
- Alle geschützten Routes bekommen `Depends(get_current_user)`

**Betroffene Dateien:**
- `src/backend/services/auth.py` — Session-Management (bereits vorhanden)
- `src/backend/main.py` — Cookie-Middleware
- `src/backend/routes/` — Dependency `get_current_user` für alle Routes
- `src/backend/models.py` — Session-Model (bereits vorhanden)

**Verifikation:**
```bash
# Login → Set-Cookie
curl -v -X POST http://localhost:8000/api/auth/login \
  -d '{"username":"test","password":"test"}' 2>&1 | grep -i "set-cookie"
# Protected Route → Cookie noetig
curl -s http://localhost:8000/api/orders  # 401
curl -s -b "b2b_session=..." http://localhost:8000/api/orders  # 200
```

**Push-Punkt:** `feat: session-based auth with cookie middleware`

---

### Phase 3: SQLite "RLS" via Dependency Injection

**Ziel:** Row-Level-Security-Äquivalent in SQLite via FastAPI Dependencies.

**Was sich ändert:**
- `get_owner_scope()` Dependency für supplier-spezifische Routen
- Scope-Filter in Queries einbauen
- Owner-Feld in relevanten Tabellen (bereits vorhanden)

**Betroffene Dateien:**
- `src/backend/routes/` — Jede Route bekommt `Depends(get_owner_scope)`
- `src/backend/services/` — Scope-Filter in Queries
- `src/backend/models.py` — Owner-Feld (bereits vorhanden)

**Verifikation:**
```bash
# Supplier A kann nur eigene Produkte sehen
curl -s -b "session=a" http://localhost:8000/api/products?owner=me
# Supplier B sieht nichts von A
curl -s -b "session=b" http://localhost:8000/api/products?owner=a  # 403
```

**Push-Punkt:** `feat: row-level scope via dependency injection`

---

### Phase 4: Frontend-Integration (Jinja2 + Same-Origin)

**Ziel:** Alle API-Calls nutzen relative Pfade (`/api/*`), keine externen URLs.

**Was sich ändert:**
- Templates bleiben unverändert (bereits relative Pfade)
- `BACKEND_URL` wird aus server.py entfernt
- StaticFiles-Mount in main.py

**Betroffene Dateien:**
- `src/frontend/templates/*.html` — Unverändert (bereits relativ)
- `src/frontend/static/*.js` — Unverändert (bereits relativ)
- `src/frontend/server.py` — Wird zu FastAPI-Route

**Verifikation:**
```bash
# HTML-Page lädt JavaScript
curl -s http://localhost:8000/ | grep -o 'src="[^"]*"' | head -5
# JavaScript ruft API auf (same-origin)
curl -s http://localhost:8000/static/auth.js | grep "fetch(" | head -3
# Erwartung: fetch('/api/auth/register') — relativ
```

**Push-Punkt:** `refactor: frontend same-origin API calls`

---

### Phase 5: Docker-Compose Consolidation

**Ziel:** Ein einziger Container statt zwei.

**Was sich ändert:**
- Ein Dockerfile für alles
- docker-compose.yml mit einem Service
- Makefile angepasst

**Betroffene Dateien:**
- `Dockerfile` (neu oder erweitert)
- `docker-compose.prod.yml` — Ein Service statt zwei
- `Makefile` — Commands anpassen

**Verifikation:**
```bash
docker compose up -d
curl -s http://localhost:8000/ | head -3  # HTML
curl -s http://localhost:8000/api/health  # {"status":"ok"}
docker compose ps  # Ein Container
```

**Push-Punkt:** `ops: single-container Docker deployment`

---

### Phase 6: Test-Migration

**Ziel:** 357 Tests laufen gegen Same-Origin-Architektur.

**Was sich ändert:**
- `tests/conftest.py` — Client-Setup anpassen
- Tests laufen gegen Port 8000 statt 3000+8000

**Betroffene Dateien:**
- `tests/conftest.py` — Client-Setup
- `tests/test_backend.py` — URL-Patterns

**Verifikation:**
```bash
cd src/backend && python -m pytest ../tests/ -v
# 357 Tests, alle gruen
```

**Push-Punkt:** `test: all 357 tests pass on same-origin architecture`

---

### Phase 7: Seed-Data & Initial-Deploy

**Ziel:** 312 Produkte, 30 Suppliers, alles auf neue Architektur.

**Was sich ändert:**
- Nichts (Seed-Data bleibt)
- Production-Config angepasst

**Betroffene Dateien:**
- `src/backend/seed_data.py` — Unverändert
- `docker-compose.prod.yml` — Production-Config

**Verifikation:**
```bash
make setup && make dev
curl -s http://localhost:8000/api/products | python -c "import sys,json; print(len(json.load(sys.stdin)))"
# 312
curl -s http://localhost:8000/api/b2b/suppliers | python -c "import sys,json; print(len(json.load(sys.stdin)))"
# 30
```

**Push-Punkt:** `feat: v7.0 — same-origin monolith with 312 products`

---

## Part VI: alsouk-Prinzipien → Libya B2B Umsetzung (Zusammenfassung)

| alsouk-Prinzip | Libya B2B Umsetzung | Risiko |
|---|---|---|
| P1: Eine Runtime | FastAPI rendert HTML + API auf Port 8000 | ✅ Niedrig |
| P2: Same-Origin | Ein Prozess, keine CORS, relative API-URLs | ✅ Niedrig |
| P3: Supabase=DB+API | SQLite + FastAPI (kein externer Service) | ⚠️ Mittel (offline-first kompatibel) |
| P4: Auth=Framework+RLS | FastAPI Session-Cookies + Dependency Injection Scope | ⚠️ Mittel (kein echtes RLS) |
| P5: Service-Keys serverseitig | Bereits so (Environment-Variablen) | ✅ Niedrig |
| P6: Single Auto-Deploy | Docker Compose (ein Container) | ✅ Niedrig |
| P7: Thin Pages, Heavy Components | Jinja2-Templates + FastAPI-Routen | ✅ Niedrig |
| P8: i18n Dictionary+RTL | locales/en.json + ar.json, RTL via CSS | ✅ Niedrig |

---

## Part VII: Bekannte Fallen aus den 4 gescheiterten Tagen

### 1. Cross-Origin-Premature-Optimization

**Fall:** Frontend (localhost:3000) + Backend (localhost:8000) als separate Services konzipiert → CORS-Preflight bei jedem Request, Cookie-Security problems, Session-Verlust.

**Ausschluss:** Phase 1 consolidiert auf EINEN Prozess. Kein CORS nötig. Cookie funktioniert same-origin.

---

### 2. Pages-Source-Verwirrung

**Fall:** HTML-Templates in `server.py` + `main.py` dupliziert. Zwei Quellen für dieselbe Seite → Inkonsistenzen, Wartungschaos.

**Ausschluss:** Phase 4 degradiert `server.py` zur FastAPI-Route. Templates leben nur noch in `templates/`. Eine einzige Quelle.

---

### 3. Deploy-Race-Bedingung

**Fall:** Zwei Container starten parallel → Backend ist noch nicht bereit, Frontend schon → API-Timeouts, Fehler im UI.

**Ausschluss:** Phase 5: Ein Container. `depends_on` + `healthcheck` in Docker Compose. Startsequenz ist deterministisch.

---

### 4. Framework-Blindheit

**Fall:** Next.js/Supabase wurde als "Lösung" gesehen, ohne Offline-First und Budget zu berücksichtigen → Architektur passt nicht zum Kontext.

**Ausschluss:** Option A wurde bewusst gewählt. Architektur-Prinzipien (Same-Origin, Session-Auth) werden übernommen, Framework wird nicht kopiert.

---

### 5. Auth-Verschiebung

**Fall:** "Später machen wir Auth" → API-Endpoints ungeschützt, dann hastig JWT reingeklatscht → Inkonsistente Authorization-Logik.

**Ausschluss:** Phase 2 implementiert Session-Auth VOR der Frontend-Integration. Kein Endpoint bleibt ungeschützt.

---

## Part VIII: Was NICHT geändert wird

| Komponente | Grund |
|---|---|
| **SQLite** | Offline-first Requirement, Budget, Libyen-spezifisch |
| **Bestehende Auth** | Session-Cookie + bcrypt bereits implementiert (357 Tests) |
| **API-Pfade** | `/api/*` Pfade bleiben identisch |
| **357 Tests** | Alle bleiben, werden nur gegen neue Architektur angepasst |
| **Seed-Data** | 312 Produkte, 30 Suppliers bleiben |
| **i18n** | locales/en.json + ar.json bleiben |
| **RTL-Support** | Bereits implementiert |
| **Sync-Engine** | Offline-First bleibt |

---

## Appendix: Quick Commands (nach Umbau)

```bash
make setup          # venv + deps + DB init + seed data
make dev            # FastAPI auf :8000 (HTML + API, kein CORS)
make test           # 357 Tests
make lint           # ruff check
make format         # ruff format
docker compose up   # Ein Container: HTML + API auf :8000
```

---

## Appendix: Code-Beweise (aktuell)

### Fetch-Aufrufe in Templates (99 Stück)
- Alle relativ: `fetch('/api/...')`
- Keine absoluten URLs: `fetch('http://localhost:8000/api/...')`

### Fetch-Aufrufe in Static JS (33 Stück)
- Alle relativ: `fetch('/api/...')`
- Beispiele: `auth.js:37`, `cart.js:9`, `nav.js:101`

### CORS-Konfiguration
- `main.py:30-36`: `allow_origins=["*"]`
- `server.py:462`: `Access-Control-Allow-Origin: *` (im Proxy)

### Docker Services
- `docker-compose.yml:9-34`: Backend (Port 8000)
- `docker-compose.yml:39-64`: Frontend (Port 3000)

### Test-Anzahl
- 357 Test-Funktionen
- 14 Test-Klassen
- 21 Test-Dateien

---

*Erstellt: 2026-09-03 | Basis: Code-Stand 8a84de7 | Referenz: alsouk-platform (337 Commits)*
