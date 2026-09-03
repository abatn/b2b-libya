# Libya B2B — Umbau-Analyse nach alsouk-platform Prinzipien

**Stand:** Revert 8a84de7  
**Datum:** 2026-09-03  
**Status:** Analyse (read-only)  
**Ziel:** Ein-Prozess-Architektur per FastAPI mit same-origin

---

## 1. ALSOUK-PRINZIPIEN (als Referenz)

| # | Prinzip | Datei:Zeile (Beweis) | Beschreibung |
|---|---------|----------------------|--------------|
| 1 | **Single Runtime** | `package.json:18` → `"next": "16.2.6"` | Ein Node.js-Prozess: SSR + API + Static |
| 2 | **Same-Origin** | `PROJECT_STATUS.md:57` → `fetch('/api/...')` | Frontend + API auf derselben Domain |
| 3 | **DB+API-in-eins** | `lib/supabase/rest.ts:25-39` → PostgREST fetch | Supabase = DB + REST API |
| 4 | **Framework-Auth** | `middleware.ts:1-8` → `updateSession` | Auth im Framework-Middleware |
| 5 | **Server-Keys** | `.env.example:19` → `NEVER prefix NEXT_PUBLIC_` | Secrets nur server-side |
| 6 | **Single-Auto-Deploy** | `HANDOFF.md:39` → `git push → Vercel auto-deploys` | Push-to-Deploy |

---

## 2. LIBYA B2B — IST-ZUSTAND (Revert 8a84de7)

### 2.1 Routen-Analyse

| Komponente | Datei | Dekoratoren | Befehl |
|------------|-------|-------------|--------|
| Frontend | `server.py` | **0** (Python HTTP, kein FastAPI) | `grep -c "@app\." server.py` → `0` |
| Backend | `main.py` | **2** (App-Factory) | `grep -c "@app\." main.py` → `2` |
| Legacy | `main_old.py` | **27** (Monolith, kann weg) | `grep -c "@app\." main_old.py` → `27` |
| **Routes/** | 22 Dateien | **142** Endpunkte | `grep -rE "^@app\." routes/ \| wc -l` → `142` |

### 2.2 Auth-Implementierung

| Datei | Inhalt | Befehl |
|-------|--------|--------|
| `services/auth.py:1-41` | `hash_password()` (bcrypt), `verify_password()` (auto-detect), `generate_session_token()` (secrets.token_hex) | `head -41 services/auth.py` |
| `models.py` | `user_sessions` Tabelle mit `session_token`, `session_id` | `grep -n "user_sessions\|session_token" models.py` |
| Kein JWT | Session-basiert, kein JWT | `grep -rn "JWT\|jwt" --include="*.py"` → `0` |

### 2.3 Frontend-API-Aufrufe

| Metrik | Wert | Befehl |
|--------|------|--------|
| `fetch()` Aufrufe | **132** | `grep -r "fetch(" --include="*.html" --include="*.js" \| wc -l` |
| `XMLHttpRequest` / `axios` | **0** | `grep -r "XMLHttpRequest\|axios" --include="*.html" --include="*.js" \| wc -l` |

### 2.4 Pytest-Ergebnis

```
====================== 357 passed, 35 warnings in 53.80s =======================
```

**357 Tests bestanden**, 20 Test-Dateien, 5.371 Zeilen Testcode.

### 2.5 Docker-Setup

| Datei | Inhalt |
|-------|--------|
| `src/backend/Dockerfile` | Python 3.12-slim, FastAPI |
| `src/frontend/Dockerfile` | Python 3.12-slim, HTTP-Server |
| `docker-compose.yml:88` | 2 Services + Monitor, `libya-b2b-network` |

### 2.6 Datenbank

- **SQLite** (Offline-First Pflicht)
- `SQLITE_URL = sqlite:///./libya_b2b.db`
- SQLAlchemy ORM: `models.py` (33K, 27 Tabellen)
- FTS5 Full-Text-Search
- `sync_engine.py`: Delta-Sync mit lokaler SQLite

---

## 3. LÜCKEN-ANALYSE (pro alsouk-Prinzip)

| Prinzip | Libya B2B Status | Lücke | Befehl-Beweis |
|---------|------------------|-------|---------------|
| **1. Single Runtime** | 2 Prozesse: Frontend `:3000` + Backend `:8000` | Muss zu **1 FastAPI-Prozess** zusammengeführt werden | `docker-compose ps` → 2 Services |
| **2. Same-Origin** | Cross-Origin: `localhost:3000` → `localhost:8000` | Muss **same-origin** werden (ein Port) | `grep "localhost:8000" static/*.js templates/*.html` |
| **3. DB+API-in-eins** | ✅ Gegeben: FastAPI + SQLite | Kein Umbau nötig (bleibt SQLite) | `grep "sqlite" config.py` |
| **4. Framework-Auth** | Session-Auth in `services/auth.py` | Muss in **FastAPI-Middleware** migriert | `head -41 services/auth.py` |
| **5. Server-Keys** | ✅ Gegeben: `.env`-basiert | Kein Umbau nötig | `cat .env 2>/dev/null \|\| echo "no .env"` |
| **6. Single-Auto-Deploy** | 2 Dockerfiles + Compose | Muss zu **1 Docker-Service** vereinfacht werden | `ls src/*/Dockerfile` |

---

## 4. AUSFÜHRUNGS-BLÖCKE

### BLOCK 1: Ein FastAPI-Prozess Port 8000 mit HTML+API+Static same-origin

**Ziel:** `server.py` (Frontend) + `main.py` (Backend) → **ein** FastAPI-Prozess auf Port 8000

#### Schritte

1. **FastAPI mount static in `main.py`**
   - `app.mount("/static", StaticFiles(directory="src/backend/static"), name="static")`
   - ⚠️ **NUR `/static` mounten** — Templates werden AUSSCHLIESSLICH via `Jinja2Templates` gerendert, NICHT als statische Dateien ausgeliefert (sonst rohe `{{Variablen}}`)

2. **Routen aus `server.py` nach `src/backend/routes/static_pages.py` migrieren**
   - 34 HTML-Routen werden zu FastAPI-Endpunkten
   - `Jinja2Templates` für Template-Rendering
   - `from fastapi.templating import Jinja2Templates`

3. **Frontend-Fetch-Aufrufe anpassen**
   - 132 `fetch("/api/...")` Aufrufe bleiben gleich (same-origin!)
   - Keine CORS-Konfiguration nötig

4. **`server.py` löschen** (nach erfolgreicher Migration)

5. **pytest-357 Gate**
   ```bash
   cd libya_b2b_platform && python -m pytest tests/ -v
   # Muss: 357 passed
   ```

6. **Seiten-Schleifen-Verifikation**
   ```bash
   # Alle Routen curl → 200
   for route in / /products /suppliers /cart /login /register; do
     curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$route
   done
   # Muss: 200 für alle
   
   # Unaufgelöste Variablen → 0
   grep -r "{{.*}}" src/backend/templates/*.html | grep -v "{%.*%}" | wc -l
   # Muss: 0
   ```

#### Deliverables
- [ ] `main.py` mounted static (NICHT templates)
- [ ] `routes/static_pages.py` enthält 34 HTML-Routen mit Jinja2Templates
- [ ] `server.py` gelöscht
- [ ] pytest: 357 passed
- [ ] curl: alle Routen 200
- [ ] grep: 0 unaufgelöste Variablen

---

### BLOCK 2: Deploy EINES Docker-Service auf Render mit /health + Browser-Beweis

**Ziel:** Ein Dockerfile, ein Service, ein Port (8000), Render-Deployment

#### Schritte

1. **Root-Dockerfile erstellen** (bewährtes Muster für src/backend)
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app/src/backend
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
   **Begründung:** `requirements.txt` liegt in `src/backend/` (nicht am Root), `src/` und `src/backend/` haben KEIN `__init__.py`, daher muss `WORKDIR` direkt in `src/backend/` sein, damit `uvicorn main:app` funktioniert.

2. **`render.yaml` erstellen**
   ```yaml
   services:
     - type: web
       name: libya-b2b
       env: docker
       dockerfilePath: ./Dockerfile
       healthCheckPath: /health
       envVars:
         - key: DATABASE_URL
           value: sqlite:///./libya_b2b.db
   ```

3. **`/health` bestätigen** — existiert bereits in `src/backend/routes/monitoring.py:8-16`
   ```bash
   curl -s http://localhost:8000/health | python -m json.tool
   # Muss: {"status":"healthy","version":"2.0.0","database":"sqlite","offline_capable":true}
   curl -sI http://localhost:8000/health | grep -i x-api-version
   # Muss: X-API-Version: 1.0
   ```
   ⚠️ **NICHT neu anlegen** — bestehenden Endpoint verwenden.

4. **Alte Dockerfiles beibehalten** (lokale Dev + CI-Docker-Build-Test)
   - `src/backend/Dockerfile` → bleibt (lokale Entwicklung)
   - `src/frontend/Dockerfile` → bleibt (lokale Entwicklung)
   - `docker-compose.yml` → bleibt (lokale Dev + CI), aber auf **EINEN Service** reduziert

5. **pytest-357 Gate**
   ```bash
   cd libya_b2b_platform && python -m pytest tests/ -v
   # Muss: 357 passed
   ```

6. **Browser-Beweis: "Produkte sichtbar am selben Tag"**
   ```bash
   # Nach Deploy:
   curl -s https://libya-b2b.onrender.com/ | grep -o "<title>.*</title>"
   # Muss: <title>Libya B2B</title> oder ähnlich
   
   curl -s https://libya-b2b.onrender.com/health
   # Muss: {"status":"healthy","version":"2.0.0",...}
   ```

#### Deliverables
- [ ] Root-Dockerfile mit `WORKDIR /app/src/backend`
- [ ] `render.yaml` konfiguriert
- [ ] `/health` antwortet mit `X-API-Version` Header
- [ ] Alte Dockerfiles + Compose bleiben (Dev/CI)
- [ ] pytest: 357 passed
- [ ] Render-Deploy: HTTPS erreichbar
- [ ] `/health` → 200
- [ ] HTML-Seiten → 200

---

### BLOCK 3: Bestehende Session-Auth same-origin verifizieren + Seed-Check 312/30

**Ziel:** Auth funktioniert same-origin, Seed-Daten korrekt

#### Schritte

1. **Session-Auth in FastAPI-Middleware verifizieren**
   - Prüfe ob `services/auth.py` mit FastAPI kompatibel ist
   - Session-Cookie wird bei `/api/*` Aufrufen mitgesendet
   - Browser: Login → Cookie → API-Aufruf → 200

2. **Same-Origin Auth-Flow testen**
   ```bash
   # Login via same-origin (echte Seed-Credentials aus seed_data.py)
   curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@libya-b2b.ly","password":"admin123"}'
   
   # API-Aufruf mit Cookie
   curl -b cookies.txt http://localhost:8000/api/products
   # Muss: 200 + JSON
   ```

3. **Seed-Check: 312 Produkte + 30 Lieferanten** (Top-Level-Imports im Backend-Kontext)
   ```bash
   cd src/backend && python -c "
   from config import get_db
   from models import Product, Supplier
   db = next(get_db())
   products = db.query(Product).count()
   suppliers = db.query(Supplier).count()
   print(f'Products: {products}, Suppliers: {suppliers}')
   assert products >= 312, f'Expected >=312, got {products}'
   assert suppliers >= 30, f'Expected >=30, got {suppliers}'
   "
   # Muss: Products: 312, Suppliers: 30
   ```

4. **pytest-357 Gate**
   ```bash
   cd libya_b2b_platform && python -m pytest tests/ -v
   # Muss: 357 passed
   ```

5. **Seiten-Schleifen-Verifikation (final)**
   ```bash
   # Alle 142 API-Endpunkte
   for route in /api/auth/login /api/products /api/suppliers /api/cart /api/orders; do
     curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$route
   done
   # Muss: 401 (nicht eingeloggt) oder 200
   
   # HTML-Seiten
   for route in / /products /suppliers /cart /login; do
     curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$route
   done
   # Muss: 200 für alle
   ```

#### Deliverables
- [ ] Session-Auth funktioniert same-origin
- [ ] Login → Cookie → API → 200
- [ ] Seed: 312+ Produkte, 30+ Lieferanten
- [ ] pytest: 357 passed
- [ ] Alle HTML-Routen: 200
- [ ] Alle API-Routen: 401/200 (auth-dependent)

---

## 5. ZUSAMMENFASSUNG

| Block | Beschreibung | Gate | Ergebnis |
|-------|-------------|------|----------|
| **1** | Ein FastAPI-Prozess, same-origin | pytest 357 | Port 3000 eliminiert |
| **2** | Ein Docker-Service, Render-Deploy | pytest 357 | HTTPS live |
| **3** | Auth + Seed verifiziert | pytest 357 | Produktionsbereit |

**RLS/Owner-Scope:** Deferred (nach Phase 3, nicht in diesem Plan)  
**API-Pfade:** Unverändert `/api/*` (NICHT `/api/v1`)  
**SQLite:** bleibt (Offline-First Pflicht)  
**main_old.py:** Wird in Block 1 gelöscht

---

## 6. RISIKEN

| Risiko | Impact | Mindermassnahme |
|--------|--------|-----------------|
| Template-Migration fehlerhaft | Pages kaputt | 357 Tests + curl-Verifikation |
| Auth-Cookie same-origin Bug | Login unmöglich | Block 3 explizit testen |
| Render-Deploy dauert >10min | Verzögerung | `/health` als Frühindikator |
| **SQLite auf Render Free Tier** | **Datenverlust bei jedem Redeploy** | Render Free Tier hat KEINEN persistenten Disk → `init_db()` + Seed beim Startup (implizit im Deploy-Step) |

---

## 7. COMMIT-REFERENZ

```
Revert: 8a84de7
Plan: PLAN.md (dieses Dokument)
Änderungen: Nur Analyse, keine Implementierung
```

---

*Erstellt von Analyse-Agent | 2026-09-03*  
*Korrigiert: 5 verifizierte Fehler (docker paths, template mount, invented details, sqlite ephemerality)*
