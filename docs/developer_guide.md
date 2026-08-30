# Libya B2B Platform — Developer Guide

**Version:** v3.6  
**Last Updated:** 27. August 2026  
**Python:** 3.12 | **Framework:** FastAPI | **DB:** SQLite | **Tests:** 267

---

## 1. Architecture Overview

```
libya_b2b_platform/
├── src/
│   ├── backend/                    # FastAPI API Server (Port 8000)
│   │   ├── main.py                 # App entrypoint, CORS, startup
│   │   ├── config.py               # Database engine, session factory
│   │   ├── models.py               # SQLAlchemy ORM + Pydantic schemas (19 tables, 37 schemas)
│   │   ├── chatbot.py              # Arabic intent recognition (20 intents)
│   │   ├── sync_engine.py          # Delta-sync engine (singleton)
│   │   ├── qr_code.py              # QR generation + verification
│   │   ├── routes/                 # 20 route modules, 76 endpoints
│   │   │   ├── auth_routes.py      # Register, login, 2FA, email-verify
│   │   │   ├── products.py         # CRUD, images, search
│   │   │   ├── orders.py           # Create, track, deliver, cancel
│   │   │   ├── cart.py             # Server-side cart management
│   │   │   ├── escrow.py           # Escrow create/release/refund/dispute
│   │   │   ├── admin_escrow.py     # Admin resolve endpoint
│   │   │   ├── payment_routes.py   # Payment SDK integration
│   │   │   ├── notifications.py    # Push subscriptions + in-app notifications
│   │   │   ├── b2b.py              # B2B dashboard, analytics, categories
│   │   │   ├── messages.py         # Buyer-Supplier messaging
│   │   │   ├── rfq.py              # Request for Quotation
│   │   │   ├── reviews.py          # Product reviews
│   │   │   ├── suppliers.py        # Supplier profiles
│   │   │   ├── search.py           # Advanced search
│   │   │   ├── chat.py             # Arabic chatbot
│   │   │   ├── qr_routes.py       # QR code endpoints
│   │   │   ├── sync_routes.py     # Offline sync
│   │   │   ├── monitoring.py      # Health checks, stats
│   │   │   └── static_pages.py    # Landing, products, cart pages
│   │   ├── services/
│   │   │   ├── auth.py             # Session management
│   │   │   ├── email.py            # SMTP email sending
│   │   │   ├── search.py           # Search logic
│   │   │   └── payment/            # Payment SDK (Provider-Abstraktion)
│   │   │       ├── base.py         # Abstract PaymentProvider
│   │   │       ├── gateway.py      # PaymentGateway (provider registry)
│   │   │       ├── service.py      # PaymentService (high-level API)
│   │   │       ├── mock_provider.py
│   │   │       ├── sadad_provider.py
│   │   │       ├── fawry_provider.py
│   │   │       └── moamalat_provider.py
│   │   ├── locales/                # Backend i18n (en.json, ar.json)
│   │   ├── static/                 # PWA icons (icon-192.png, icon-512.png)
│   │   └── vapid_private.pem       # VAPID key (gitignored)
│   │
│   └── frontend/                   # Python HTTP Server (Port 3000)
│       ├── server.py               # Template rendering, i18n, static files
│       ├── templates/              # 29 HTML templates
│       │   ├── nav.html            # Shared 3-Layer Navigation (Alibaba-konform)
│       │   ├── landing.html        # Hero + Categories + Products
│       │   ├── buyer.html          # Buyer Dashboard
│       │   ├── seller.html         # Seller Dashboard
│       │   ├── escrow.html         # Escrow Management
│       │   ├── escrow_admin.html   # Admin Escrow Panel
│       │   ├── register.html       # 3-Step Registration
│       │   ├── cart.html           # Shopping Cart + Checkout
│       │   └── ...                 # 21 more templates
│       ├── static/
│       │   ├── nav.css             # Shared navigation CSS
│       │   ├── nav.js              # Shared navigation JS (auth-aware, role-based)
│       │   ├── auth.js             # Auth logic (login, register, session)
│       │   ├── cart.js             # Cart operations
│       │   ├── push-notifications.js  # Push subscription + badge
│       │   ├── sw.js               # Service Worker (offline-first)
│       │   ├── sw-register.js      # SW registration + online/offline status
│       │   ├── manifest.json       # PWA manifest
│       │   ├── toast.js            # Toast notifications
│       │   ├── tabs.js             # Tab switching
│       │   └── chatbot-widget.js   # Chat widget
│       └── locales/                # Frontend i18n (en.json, ar.json)
│
├── tests/                          # 267 tests across 12 files
│   ├── conftest.py                 # Shared in-memory SQLite fixture
│   ├── test_backend.py             # Core API tests
│   ├── test_cart.py                # Cart + Checkout tests
│   ├── test_escrow.py              # Escrow tests
│   ├── test_payment_sdk.py         # Payment SDK tests
│   ├── test_register.py            # Registration tests
│   ├── test_chatbot.py             # Chatbot tests
│   ├── test_qr_code.py             # QR code tests
│   ├── test_sync_engine.py         # Sync engine tests
│   ├── test_sprint8.py             # Sprint 8 tests
│   ├── test_integration.py         # Integration tests
│   └── test_arabic.py              # Arabic localization tests
│
├── docs/                           # Documentation
│   ├── developer_guide.md          # THIS FILE
│   ├── user_guide.md               # User guide (EN)
│   ├── user_guide_ar.md            # User guide (AR)
│   ├── admin_guide.md              # Admin guide
│   └── release_notes_v3.1.md       # Release notes
│
├── knowledge.md                    # Project knowledge base
├── REKAP_PROJEKTSTATUS.md          # Sprint status
├── .loop.md                        # Loop status
├── pyproject.toml                  # Dependencies + ruff config
├── docker-compose.yml              # Docker setup
└── Makefile                        # Quick commands
```

### Data Flow

```
Frontend (:3000) ──→ Backend API (:8000) ──→ SQLite (libya_b2b.db)
       │                     │
       │                     ├──→ Payment Gateway (Mock/SADAD/Fawry/Moamalat)
       │                     ├──→ Push Notifications (VAPID + pywebpush)
       │                     ├──→ Email (SMTP)
       │                     └──→ QR Code Generation
       │
       ├──→ Service Worker (sw.js) ──→ Cache (Offline-First)
       └──→ IndexedDB (Offline Queue)
```

---

## 2. Quick Start

```bash
# Setup
cd libya_b2b_platform
make setup          # venv + deps + DB init + seed data

# Development
make dev            # Backend on :8000 (--reload)
# Frontend starts separately on :3000

# Docker
make build && make up   # Backend: :8000, Frontend: :3000

# Tests
make test           # pytest from src/backend context
python3 -m pytest tests/ -v   # All 267 tests

# Linting
make lint           # ruff check
make format         # ruff format
```

---

## 3. API Reference (76 Endpoints)

### Auth (routes/auth_routes.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | 3-step registration |
| POST | `/api/auth/login` | No | Login with username+password |
| POST | `/api/auth/logout` | Yes | Logout (invalidate session) |
| GET | `/api/auth/me` | Yes | Get current user |
| PUT | `/api/auth/me` | Yes | Update profile |
| POST | `/api/auth/send-verification` | No | Send 6-digit email code |
| POST | `/api/auth/verify-email` | No | Verify email with code |
| POST | `/api/auth/2fa/setup` | Yes | Generate 2FA secret |
| POST | `/api/auth/2fa/verify` | Yes | Verify 2FA code |
| POST | `/api/auth/forgot-password` | No | Send password reset |
| POST | `/api/auth/reset-password` | No | Reset with token |
| GET | `/api/auth/login-history` | Yes | Login history |

### Products (routes/products.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/products` | No | List products (with filters) |
| POST | `/api/products` | Seller | Create product |
| GET | `/api/products/{id}` | No | Get product detail |
| PUT | `/api/products/{id}` | Seller | Update product |
| DELETE | `/api/products/{id}` | Seller | Delete product |
| POST | `/api/products/{id}/images` | Seller | Upload product images |

### Orders (routes/orders.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/orders` | Yes | List user's orders |
| POST | `/api/orders` | Yes | Create order |
| GET | `/api/orders/{number}` | Yes | Get order detail |
| POST | `/api/orders/{id}/deliver` | Seller | Confirm delivery |
| POST | `/api/orders/{id}/cancel` | Yes | Cancel order |

### Cart (routes/cart.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/cart` | Yes | Get cart |
| POST | `/api/cart/items` | Yes | Add item |
| PUT | `/api/cart/items/{id}` | Yes | Update quantity |
| DELETE | `/api/cart/items/{id}` | Yes | Remove item |

### Escrow (routes/escrow.py + admin_escrow.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/escrow` | Yes | Create escrow |
| GET | `/api/escrow/{id}` | Yes | Get escrow status |
| POST | `/api/escrow/{id}/release` | Yes | Release funds |
| POST | `/api/escrow/{id}/refund` | Yes | Refund buyer |
| POST | `/api/escrow/{id}/dispute` | Yes | Open dispute |
| GET | `/api/escrow/{id}/history` | Yes | Audit trail |
| POST | `/api/admin/escrow/{id}/resolve` | Admin | Admin resolve |

### Payment (routes/payment_routes.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/payment/pay` | Yes | Process payment |
| GET | `/api/payment/status/{provider}/{id}` | Yes | Check status |
| POST | `/api/payment/refund` | Yes | Refund payment |
| GET | `/api/payment/methods` | No | List payment methods |

### Notifications (routes/notifications.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/notifications/vapid-public-key` | No | Get VAPID public key |
| POST | `/api/notifications/subscribe` | Yes | Subscribe to push |
| DELETE | `/api/notifications/subscribe` | Yes | Unsubscribe |
| GET | `/api/notifications` | Yes | List notifications |
| GET | `/api/notifications/unread-count` | Yes | Unread count |
| POST | `/api/notifications/{id}/read` | Yes | Mark as read |
| POST | `/api/notifications/read-all` | Yes | Mark all read |

### B2B (routes/b2b.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/b2b/dashboard` | Yes | B2B dashboard stats |
| GET | `/api/b2b/analytics` | Yes | Sales analytics |
| GET | `/api/b2b/categories` | No | List categories (21) |
| GET | `/api/b2b/bulk-pricing/{id}` | No | Bulk pricing tiers |

### Messages (routes/messages.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/messages` | Yes | List conversations |
| POST | `/api/messages` | Yes | Send message |
| GET | `/api/messages/{id}` | Yes | Get conversation |

### RFQ (routes/rfq.py)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/rfq` | Yes | List RFQs |
| POST | `/api/rfq` | Yes | Create RFQ |
| GET | `/api/rfq/{id}` | Yes | Get RFQ detail |

### Other Endpoints

| Module | Endpoints | Description |
|--------|-----------|-------------|
| Reviews | 3 | Create, list, summary per product |
| Suppliers | 3 | List, get, verify |
| Search | 2 | Advanced search, suggestions |
| Chat | 2 | Arabic chatbot, suggestions |
| QR | 2 | Generate, verify |
| Sync | 2 | Delta sync, changes |
| Monitoring | 2 | Health, stats |

---

## 4. Database Schema (19 Tables)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `users` | User accounts | id, username, email, role, email_verified, two_factor_enabled |
| `user_sessions` | Session tokens | session_token, user_id, expires_at |
| `products` | Product catalog | name, price, category, stock_quantity, moq, seller_id |
| `product_images` | Product images | product_id, image_url, is_primary |
| `reviews` | Product reviews | product_id, user_id, rating (1-5) |
| `orders` | Order tracking | order_number, buyer_id, seller_id, status, payment_method |
| `carts` | Shopping carts | user_id |
| `cart_items` | Cart items | cart_id, product_id, quantity |
| `suppliers` | Supplier profiles | user_id, name, is_verified, rating |
| `rfqs` | Request for Quotation | buyer_id, product_name, quantity, status |
| `conversations` | Message threads | buyer_id, supplier_id |
| `messages` | Chat messages | conversation_id, sender_type, text |
| `chat_messages` | Chatbot history | session_id, user_message, bot_response |
| `escrow_transactions` | Escrow payments | order_id, amount, status |
| `escrow_history` | Escrow audit trail | escrow_id, action, old/new_status |
| `payment_transactions` | Payment log | order_id, provider, amount, status |
| `push_subscriptions` | Push endpoints | user_id, endpoint, p256dh, auth |
| `notifications` | In-app notifications | user_id, type, title, is_read |
| `login_history` | Login audit | user_id, ip_address, success |

### Pydantic Schemas (37 total)

Each table has at least: `XxxCreate` (input), `XxxResponse` (output).  
Some have additional: `XxxUpdate`, `XxxSummary`.

---

## 5. Payment SDK Architecture

```
PaymentService (service.py)
    └── PaymentGateway (gateway.py)
            ├── MockProvider   (mock_provider.py)    ← Dev/Test
            ├── SadadProvider  (sadad_provider.py)   ← Placeholders
            ├── FawryProvider  (fawry_provider.py)   ← Placeholders
            └── MoamalatProvider (moamalat_provider.py) ← Placeholders
```

**Adding a new provider:**
1. Create `new_provider.py` extending `PaymentProvider` (base.py)
2. Implement: `create_payment()`, `verify_payment()`, `refund_payment()`
3. Register in `gateway.py`: `gateway.register('new', NewProvider())`
4. Set env vars: `NEW_API_KEY=...`, `NEW_MERCHANT_ID=...`

---

## 6. PWA / Service Worker

### Caching Strategy

| Resource | Strategy | Rationale |
|----------|----------|-----------|
| Static assets (CSS, JS, images) | Cache-First | Fast, reliable |
| API calls | Network-First | Fresh data, fallback to cache |
| HTML pages | Stale-While-Revalidate | Fast + fresh |

### Files

| File | Purpose |
|------|---------|
| `sw.js` | Service Worker (install, fetch, push handlers) |
| `sw-register.js` | Registration, update detection, online/offline status |
| `manifest.json` | PWA manifest (name, icons, theme) |
| `push-notifications.js` | Push subscription, badge, in-app UI |

---

## 7. Push Notifications (VAPID)

### Architecture

```
Browser → GET /api/notifications/vapid-public-key → Public Key
Browser → subscribe(Public Key) → Subscription
Browser → POST /api/notifications/subscribe → Server stores
Server → Order status change → webpush(Private Key + Subscription)
```

### VAPID Key Management

| File | Location | Purpose |
|------|----------|---------|
| `vapid_private.pem` | `src/backend/` (gitignored) | Signs push messages |
| `vapid_public_key.txt` | `src/backend/` (gitignored) | Sent to browser |
| `.env.example` | Project root | Documents env vars |

**Regenerate keys:**
```bash
./venv/bin/python -c "
from py_vapid import Vapid
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import base64
v = Vapid(); v.generate_keys()
pub = v.public_key.public_bytes(encoding=Encoding.X962, format=PublicFormat.UncompressedPoint)
print('PUBLIC:', base64.urlsafe_b64encode(pub).rstrip(b'=').decode())
open('vapid_keys/vapid_private.pem', 'wb').write(v.private_pem())
"
```

---

## 8. Navigation System (3-Layer, Alibaba-konform)

### Layer Structure

| Layer | Height | Background | Content |
|-------|--------|------------|---------|
| Layer 1 (nav-top) | 56px | White | Logo, Search, Cart, Messages, Avatar |
| Layer 2 (nav-main) | 32px | Dark (#111827) | My Account, Help, Language toggle |
| Layer 3 (nav-categories) | Auto | White | Products, Suppliers, RFQ, 21 Category Tabs + Flyout |

### Shared Component

All 29 templates use the shared navigation via includes:
```html
<!-- NAV_CSS_INCLUDE -->  → nav.css
<!-- NAV_INCLUDE -->      → nav.html
<!-- NAV_JS_INCLUDE -->   → nav.js
```

### Auth-Aware Behavior

- **Not logged in:** Register + Sign In buttons visible
- **Buyer logged in:** My Account dropdown (Orders, Cart, RFQ, Track, Escrow, Logout)
- **Seller logged in:** My Account dropdown (Products, Orders, Analytics, Messages, Logout)

---

## 9. i18n / RTL Support

### Files

| File | Purpose |
|------|---------|
| `src/frontend/locales/en.json` | English translations |
| `src/frontend/locales/ar.json` | Arabic translations |
| `src/backend/locales/en.json` | Backend English |
| `src/backend/locales/ar.json` | Backend Arabic |

### Template Usage

```html
{{nav.home}}           → "Home" (EN) / "الرئيسية" (AR)
{{meta_description.xxx}} → SEO meta description
{{escrow.xxx}}         → Escrow-specific labels
```

### RTL Handling

- `server.py` sets `dir="rtl"` for `/ar/` routes
- `nav.css` has RTL-specific overrides
- Arabic-first: all endpoints have `/ar/` route versions

---

## 10. SEO (Search Engine Optimization)

### On-Page SEO (29 Templates)

| Component | Status | Location |
|-----------|--------|----------|
| `<title>` | ✅ 28/29 | `<head>` in each template |
| `<meta description>` | ✅ 28/29 | `<head>` in each template |
| `<h1>` | ✅ 28/29 | One per page |
| Open Graph (og:*) | ✅ 29/29 | `nav.html` (shared) |
| Twitter Card | ✅ 29/29 | `nav.html` (shared) |
| Canonical URL | ✅ 29/29 | `nav.html` (shared) |
| Alt-Texte | ✅ 0 missing | All `<img>` tags |

### How SEO Variables Work

`nav.html` (shared by all 29 templates) contains:
```html
<link rel="canonical" href="{{canonical_url}}">
<meta property="og:title" content="{{title}}">
<meta property="og:description" content="{{meta_description}}">
<meta property="og:image" content="/static/icons/icon-512.png">
<meta property="og:url" content="{{canonical_url}}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Libya B2B">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{title}}">
<meta name="twitter:description" content="{{meta_description}}">
```

`server.py` injects these variables per template:
- `{{title}}` ← from `locales/{lang}.json` → `{template_name}.title`
- `{{meta_description}}` ← from `locales/{lang}.json` → `{template_name}.meta_description`
- `{{canonical_url}}` ← computed from template name + language

### Technical SEO

| File | Purpose | Location |
|------|---------|----------|
| `robots.txt` | Crawl rules | `static/robots.txt` |
| `sitemap.xml` | 24 URLs | `static/sitemap.xml` |
| JSON-LD Organization | Structured data | `landing.html` |
| JSON-LD BreadcrumbList | Navigation schema | 7 main pages |

### Adding SEO to a New Template

1. Add `title` and `meta_description` to `locales/en.json` and `locales/ar.json`:
   ```json
   "new_page": {
     "title": "Page Title | Libya B2B",
     "meta_description": "Description for search engines (150-160 chars)"
   }
   ```
2. Add `<h1>` tag in the template HTML
3. OG tags and Canonical are automatic via `nav.html`

### Updating sitemap.xml

When adding new pages, add URLs to `src/frontend/static/sitemap.xml`:
```xml
<url>
  <loc>http://localhost:3000/new-page</loc>
  <lastmod>2026-08-27</lastmod>
  <changefreq>weekly</changefreq>
  <priority>0.8</priority>
</url>
```

---

## 11. Testing

### Running Tests

```bash
# All tests
python3 -m pytest tests/ -v

# Single file
python3 -m pytest tests/test_escrow.py -v

# With coverage
python3 -m pytest tests/ --cov=src/backend --cov-report=term-missing

# Quick check (no output)
python3 -m pytest tests/ -q --tb=no
```

### Test Database

- **In-memory SQLite** — configured in `tests/conftest.py`
- **Shared engine** — all tests use the same DB
- **Never create your own engine** — use the `db` fixture from conftest

### Key Test Files

| File | Tests | Coverage |
|------|-------|----------|
| test_backend.py | ~80 | Core CRUD, auth, products, orders |
| test_cart.py | ~25 | Cart operations, checkout |
| test_escrow.py | ~16 | Escrow lifecycle, admin resolve |
| test_payment_sdk.py | ~33 | Payment providers, gateway |
| test_register.py | ~15 | 3-step registration flow |
| test_chatbot.py | ~10 | Arabic intent recognition |
| test_qr_code.py | ~8 | QR generation, verification |
| test_sync_engine.py | ~10 | Offline delta-sync |
| test_sprint8.py | ~20 | Sprint 8 features |
| test_integration.py | ~15 | End-to-end flows |
| test_arabic.py | ~10 | Arabic localization |

---

## 12. Deployment

### Docker Compose

```yaml
services:
  backend:    # FastAPI on :8000
  frontend:   # Static server on :3000
  monitor:    # Health check monitor
```

### Commands

```bash
docker compose up -d --build      # Build + start all
docker compose logs -f backend    # Watch backend logs
docker compose ps                 # Status
docker compose down               # Stop all
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./libya_b2b.db` | Database connection |
| `DEBUG` | `true` | Debug mode |
| `SMTP_HOST` | (empty = console) | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USERNAME` | | SMTP auth |
| `SMTP_PASSWORD` | | SMTP auth |
| `SMTP_FROM` | | Sender email |
| `VAPID_PRIVATE_KEY` | (from file) | VAPID signing key |
| `VAPID_PUBLIC_KEY` | (from file) | VAPID public key |

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure SMTP for email verification
- [ ] Generate VAPID keys for push notifications
- [ ] Set up SSL/TLS (reverse proxy with nginx/caddy)
- [ ] Configure CORS for production domain
- [ ] Set up SQLite backup cron job
- [ ] Monitor with `/api/monitoring/stats`

---

## 13. Conventions

### Code Style

- **Ruff** for linting (line-length: 100, target: py312)
- **Imports:** stdlib → third-party → local (isort)
- **Naming:** snake_case for functions/variables, PascalCase for classes

### API Design

- All endpoints under `/api/` prefix
- Arabic-first: every endpoint has an `/ar/` route version
- Pydantic models for all request/response validation
- COD (Cash on Delivery) is the default payment method

### Git Workflow

- Branch: `main` (production), `develop` (staging)
- CI: `ruff check` → `pytest tests/ -v` → Docker build test
- Commit messages: imperative mood, concise

### Critical Gotchas

1. **Test DB is shared** — never create your own engine in tests
2. **Sync engine is a singleton** — `get_sync_engine()` reuses connections
3. **Sync entry IDs need microseconds** — use `%f` format
4. **`server.py` renders templates** — `main.py` serves raw HTML as fallback
5. **SQLite only** — offline-first requirement. No PostgreSQL/Redis
6. **No paid dependencies** — budget is 20 EUR/month
7. **PEM keys in .env** — Docker `.env` parser can't handle `/` in PEM. Use file-based loading

---

*Generated: 27.08.2026 | Libya B2B Platform v3.6*
