# Libya B2B Platform — Project Knowledge

Offline-first AI-powered B2B platform for Libya, based on the Alibaba model.  
Designed for the Libyan market: 100% COD, offline-first, Arabic chatbot, QR tracking.

**Current Version:** v3.1 | **Budget:** Max. 20 EUR/month hosting

---

## Quick Commands

All commands run from `libya_b2b_platform/`:

```bash
make setup          # venv + deps + DB init + seed data
make dev            # FastAPI backend on :8000 (--reload)
make test           # pytest from src/backend context
make lint           # ruff check
make format         # ruff format
make build && make up  # Docker: backend:8000, frontend:3000
```

Single test file:
```bash
cd src/backend && python -m pytest ../tests/test_backend.py -v
```

---

## Architecture

```
libya_b2b_platform/
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── config.py            # DB setup (SQLite), constants
│   │   ├── models.py            # 14 SQLAlchemy + 28 Pydantic models
│   │   ├── chatbot.py           # Arabic intent recognition (20 intents)
│   │   ├── qr_code.py           # QR generation + hash verification
│   │   ├── sync_engine.py       # Delta sync (singleton, Last-Write-Wins)
│   │   ├── errors_ar.py         # Arabic error messages
│   │   ├── routes/              # 15 route modules
│   │   │   ├── auth_routes.py   # 12 endpoints (register, login, 2FA, email verify)
│   │   │   ├── products.py      # 6 endpoints (CRUD + images)
│   │   │   ├── orders.py        # 4 endpoints (create, list, track, deliver)
│   │   │   ├── cart.py          # 5 endpoints (get, add, update, remove, clear)
│   │   │   ├── reviews.py       # 3 endpoints (create, list, stats)
│   │   │   ├── chat.py          # 4 endpoints (chat, history, suggestions, clear)
│   │   │   ├── sync_routes.py   # 6 endpoints (delta, all, stats, changes, pending, clear)
│   │   │   ├── qr_routes.py     # 3 endpoints (generate, scan, delivery-verify)
│   │   │   ├── rfq.py           # 4 endpoints (CRUD for RFQ)
│   │   │   ├── suppliers.py     # 3 endpoints (create, list, detail)
│   │   │   ├── messages.py      # 4 endpoints (conversations + messages)
│   │   │   ├── b2b.py           # 9 endpoints (dashboard, analytics, inventory, categories)
│   │   │   ├── search.py        # 1 endpoint (fuzzy full-text search)
│   │   │   ├── monitoring.py    # 4 endpoints (health, stats, detailed health, root)
│   │   │   └── static_pages.py  # 17 endpoints (HTML fallbacks + Arabic routes)
│   │   ├── services/
│   │   │   ├── email.py         # SMTP email service (stdlib smtplib)
│   │   │   ├── auth.py          # Auth helpers
│   │   │   ├── search.py        # Search service
│   │   │   └── payment.py       # Payment helpers
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   ├── locales/             # Backend i18n (en.json, ar.json)
│   │   ├── static/              # Static files (HTML fallbacks, uploads)
│   │   └── Dockerfile
│   └── frontend/
│       ├── server.py            # Python HTTP server (serves templates)
│       ├── templates/           # 26 HTML templates
│       ├── static/              # JS, CSS, images
│       ├── locales/             # Frontend i18n (en.json, ar.json)
│       └── Dockerfile
├── tests/                       # 218 tests, 7 files
│   ├── conftest.py              # Shared in-memory SQLite
│   ├── test_backend.py          # Core API tests
│   ├── test_register.py         # Registration flow tests
│   ├── test_integration.py      # Integration tests
│   ├── test_sprint8.py          # Sprint 8 tests
│   ├── test_chatbot.py          # Chatbot tests
│   └── test_qr.py               # QR code tests
├── docs/                        # Documentation
├── data/                        # SQLite database storage
├── docker-compose.yml           # Docker setup
├── docker-compose.prod.yml      # Production Docker
├── pyproject.toml               # Ruff config, pytest config, deps
├── Makefile                     # Build/dev commands
└── .env.example                 # Environment variables template
```

---

## Tech Stack

| Component | Technology | License |
|-----------|-----------|---------|
| Backend | Python 3.12+ / FastAPI | MIT |
| Database | SQLite (offline-first) | Public Domain |
| ORM | SQLAlchemy 2.0 | MIT |
| Validation | Pydantic 2.9 | MIT |
| Frontend | Static HTML + JS (Python server) | MIT |
| AI/ML | scikit-learn | BSD-3 |
| QR Codes | qrcode[pil] | MIT |
| Email | stdlib smtplib | — |
| Monitoring | psutil | BSD |
| Testing | pytest + httpx | MIT |
| Linting | ruff | MIT |
| Hosting | OVH VPS (20 EUR/month) | — |

---

## Database Schema (14 Tables)

### Core Tables

| Table | Columns | Description |
|-------|---------|-------------|
| `users` | id, username, email, password_hash, role, business_name, business_name_arabic, phone, is_active, email_verified, email_verification_code, email_verification_code_expires_at, two_factor_secret, two_factor_enabled, created_at | User accounts (buyer/seller/admin) |
| `user_sessions` | id, session_token, user_id, created_at, expires_at | Session management (30-day cookies) |
| `products` | id, name, name_arabic, description, description_arabic, price, currency, category, stock_quantity, moq, seller_id, image_url, is_active, created_at | Product catalog |
| `product_images` | id, product_id, image_url, is_primary, sort_order | Multiple images per product |
| `reviews` | id, product_id, user_id, rating, comment, created_at | 5-star rating system |
| `orders` | id, order_number, buyer_id, seller_id, total_amount, currency, payment_method, status, delivery_address, delivery_photo, delivery_gps_lat, delivery_gps_lon, delivery_timestamp, created_at | COD orders with QR tracking |

### B2B Tables

| Table | Columns | Description |
|-------|---------|-------------|
| `suppliers` | id, user_id, name, name_arabic, description, location, rating, rating_count, is_verified, years_on_platform, product_count, created_at | Supplier profiles |
| `rfqs` | id, buyer_id, product_name, product_name_arabic, quantity, delivery_address, message, status, created_at | Request for Quotation |
| `conversations` | id, buyer_id, supplier_id, last_message_at | Buyer-supplier messaging |
| `messages` | id, conversation_id, sender_type, sender_id, text, is_read, created_at | Message threads |

### System Tables

| Table | Columns | Description |
|-------|---------|-------------|
| `chat_messages` | id, session_id, user_message, bot_response, is_arabic, created_at | Arabic chatbot history |
| `login_history` | id, user_id, ip_address, user_agent, success, created_at | Security audit log |
| `carts` | id, user_id, created_at, updated_at | Shopping carts |
| `cart_items` | id, cart_id, product_id, quantity, added_at | Cart line items |

---

## Pydantic Models (28 Schemas)

### Auth (8)
- `UserCreate` — Registration payload
- `UserLogin` — Login payload (username, password, remember_me)
- `UserResponse` — User data (id, username, email, role, business_name, is_active, created_at)
- `SessionResponse` — Session token + user data
- `EmailVerifyRequest` — 6-digit verification code
- `ProfileUpdateRequest` — Role, business name, phone
- `TwoFASetupResponse` — 2FA secret + QR URL
- `TwoFAVerifyRequest` — 2FA code
- `LoginHistoryResponse` — Login audit entry

### Product (3)
- `ProductCreate` — Create product payload
- `ProductResponse` — Product data
- `ProductRatingSummary` — Average, count, distribution

### Review (3)
- `ReviewCreate` — Create review (product_id, rating 1-5, comment)
- `ReviewResponse` — Review data
- `ProductRatingSummary` — Rating aggregation

### Order (2)
- `OrderCreate` — Create order (amount, currency, payment_method, address)
- `OrderResponse` — Order data

### Chat (2)
- `ChatRequest` — Chat message (session_id, message, is_arabic)
- `ChatResponse` — Bot response

### Supplier (2)
- `SupplierCreate` — Create supplier profile
- `SupplierResponse` — Supplier data

### RFQ (2)
- `RFQCreate` — Request for Quotation
- `RFQResponse` — RFQ data

### Message (3)
- `MessageCreate` — Send message
- `MessageResponse` — Message data
- `ConversationResponse` — Conversation with last message

### Cart (3)
- `CartItemCreate` — Add to cart (product_id, quantity)
- `CartItemResponse` — Cart item with product details
- `CartResponse` — Full cart with total

---

## API Endpoints (73 Unique)

### Authentication (`/api/auth`) — 12 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Register new user, set session cookie |
| POST | `/login` | No | Login, set session cookie |
| POST | `/logout` | Yes | Clear session |
| POST | `/forgot-password` | No | Send password reset email |
| POST | `/reset-password` | No | Reset password with token |
| GET | `/me` | Yes | Get current user info |
| PUT | `/me` | Yes | Update profile (role, company, phone) |
| POST | `/send-verification` | Yes | Send 6-digit email verification code |
| POST | `/verify-email` | Yes | Verify email with 6-digit code |
| GET | `/login-history` | Yes | Get login audit log |
| POST | `/2fa/setup` | Yes | Generate 2FA secret + QR URL |
| POST | `/2fa/verify` | Yes | Verify 2FA code, enable 2FA |

### Products (`/api/products`) — 6 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | No | Create product |
| GET | `` | No | List products (skip, limit) |
| GET | `/{product_id}` | No | Get product by ID |
| PUT | `/{product_id}` | No | Update product |
| DELETE | `/{product_id}` | No | Delete product |
| POST | `/{product_id}/images` | No | Upload product image |

### Orders (`/api/orders`) — 4 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | Yes | Create order (auto-generates LYB-YYYYMMDD-XXXXXX) |
| GET | `` | Yes | List orders |
| GET | `/{order_number}` | No | Get order by number (public tracking) |
| PUT | `/{order_id}/deliver` | Yes | Confirm delivery (photo + GPS) |

### Cart (`/api/cart`) — 5 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `` | Yes | Get cart with items + total |
| POST | `/items` | Yes | Add item to cart (or update quantity) |
| PUT | `/items/{item_id}` | Yes | Update item quantity |
| DELETE | `/items/{item_id}` | Yes | Remove item from cart |
| DELETE | `` | Yes | Clear entire cart |

### Reviews (`/api/reviews`) — 3 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | No | Create review (rating 1-5) |
| GET | `/product/{product_id}` | No | Get reviews + rating summary |
| GET | `/stats` | No | Global rating statistics |

### Chat (`/api/chat`) — 4 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | No | Send message to Arabic chatbot |
| GET | `/{session_id}` | No | Get chat history |
| GET | `/{session_id}/suggestions` | No | Get chat suggestions |
| DELETE | `/{session_id}` | No | Clear chat history |

### Sync (`/api/sync`) — 6 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/delta` | No | Create delta sync entry |
| POST | `/all` | No | Sync all pending entries |
| GET | `/stats` | No | Sync statistics |
| GET | `/changes` | No | Get changes since timestamp |
| GET | `/pending` | No | Get pending sync entries |
| DELETE | `/completed` | No | Clear completed syncs |

### QR Code (`/api/qrcode`) — 3 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/generate` | No | Generate QR code for order |
| POST | `/scan` | No | Scan and validate QR code |
| POST | `/delivery-verification` | No | Verify delivery with QR + photo + GPS |

### B2B — RFQ (`/api/b2b/rfq`) — 4 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | Yes | Create RFQ |
| GET | `` | Yes | List RFQs (filter by status, buyer_id) |
| GET | `/{rfq_id}` | Yes | Get RFQ detail |
| PUT | `/{rfq_id}` | Yes | Update RFQ status |

### B2B — Suppliers (`/api/b2b/suppliers`) — 3 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | No | Create supplier profile |
| GET | `` | No | List suppliers (sort: rating, products, name) |
| GET | `/{supplier_id}` | No | Get supplier detail + products |

### B2B — Messages (`/api/b2b/messages`) — 4 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | Yes | Create conversation |
| GET | `` | Yes | List conversations |
| GET | `/{conversation_id}` | Yes | Get conversation messages |
| POST | `/{conversation_id}` | Yes | Send message in conversation |

### B2B — Dashboard & Analytics (`/api/b2b`) — 9 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/dashboard` | No | B2B dashboard (30-day stats) |
| GET | `/seller/{seller_id}` | Yes | Seller dashboard |
| GET | `/buyer/{buyer_id}` | Yes | Buyer dashboard |
| GET | `/analytics` | No | Category + top product analytics |
| GET | `/inventory` | No | Inventory overview |
| GET | `/bulk-pricing` | No | Bulk pricing tiers (10+, 50+, 100+) |
| GET | `/products` | No | B2B product feed with filters |
| GET | `/categories` | No | 21 categories with product counts |
| GET | `/stats` | No | Platform-wide statistics |

### Search (`/api/search`) — 1 endpoint

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `` | No | Fuzzy full-text search (products + suppliers) |

### Monitoring — 4 endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/` | No | API root info |
| GET | `/api/monitoring/stats` | No | CPU, memory, disk, uptime |
| GET | `/api/monitoring/health-detailed` | No | Detailed system health |

### Static/Arabic Routes — 17 endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/landing` | Landing page (EN) |
| GET | `/ar/landing` | Landing page (AR) |
| GET | `/products` | Products page |
| GET | `/cart` | Cart page |
| GET | `/checkout` | Checkout page |
| GET | `/seller` | Seller dashboard |
| GET | `/buyer` | Buyer dashboard |
| GET | `/tracking` | Order tracking |
| GET | `/ar/cart` | Cart (AR) |
| GET | `/ar/checkout` | Checkout (AR) |
| GET | `/ar/seller` | Seller (AR) |
| GET | `/ar/tracking` | Tracking (AR) |
| GET | `/ar/products` | Products (AR) |
| POST | `/ar/orders` | Create order (AR) |
| POST | `/ar/chat` | Chatbot (AR) |
| GET | `/ar/errors` | Error messages (AR) |
| GET | `/ar/success` | Success messages (AR) |

---

## Frontend Templates (26)

| Template | Route | Description |
|----------|-------|-------------|
| `landing.html` | `/landing` | Homepage with hero, features, stats |
| `products.html` | `/products` | Product catalog with search/filter |
| `cart.html` | `/cart` | Shopping cart |
| `checkout.html` | `/checkout` | COD checkout flow |
| `tracking.html` | `/tracking` | Order tracking with QR |
| `seller.html` | `/seller` | Seller dashboard |
| `buyer.html` | `/buyer` | Buyer dashboard |
| `register.html` | `/register` | 3-step registration |
| `2fa.html` | `/2fa` | Two-factor authentication setup |
| `verify-email.html` | `/verify-email` | Email verification |
| `forgot-password.html` | `/forgot-password` | Password reset |
| `suppliers.html` | `/suppliers` | Supplier directory |
| `supplier_detail.html` | `/suppliers/{id}` | Supplier profile |
| `rfq.html` | `/rfq` | RFQ list |
| `rfq_new.html` | `/rfq/new` | Create RFQ |
| `rfq_detail.html` | `/rfq/{id}` | RFQ detail |
| `messages.html` | `/messages` | Message inbox |
| `conversation.html` | `/conversation/{id}` | Chat conversation |
| `b2b.html` | `/b2b` | B2B dashboard |
| `b2b_products.html` | `/b2b/products` | B2B product feed |
| `about.html` | `/about` | About page |
| `faq.html` | `/faq` | FAQ page |
| `careers.html` | `/careers` | Careers page |
| `privacy.html` | `/privacy` | Privacy policy |
| `terms.html` | `/terms` | Terms of service |
| `cookie.html` | `/cookie` | Cookie policy |

---

## Key Features

### 1. Offline-First Architecture
- **SQLite** for local data storage
- **Delta Sync** — only changed data is transmitted
- **Last-Write-Wins** conflict resolution
- **Checksum validation** for data integrity
- **Automatic retry** (3 attempts per sync entry)

### 2. Arabic AI Chatbot
- 20 intents (greetings, products, orders, delivery, pricing, etc.)
- Language detection (Arabic/English)
- Session-based conversation history
- Context-aware responses

### 3. QR Code Tracking
- Order QR codes with hash verification
- Delivery verification with photo + GPS
- Tamper-proof delivery proof

### 4. COD Payment
- 100% Cash on Delivery (no online payment)
- Order tracking via QR code
- Delivery confirmation with photo + GPS coordinates

### 5. B2B Features
- Supplier directory with ratings
- RFQ (Request for Quotation) system
- Buyer-supplier messaging
- Bulk pricing tiers
- Inventory management

---

## Conventions

### Code Style
- **Linting:** Ruff (line-length: 100, target: Python 3.12)
- **Import sorting:** Ruff isort
- **Formatting:** `ruff format .`

### Patterns
- Arabic-first UI (all endpoints have `/ar/` versions)
- COD payment method as default
- SQLite for offline-first capability
- QR codes for order tracking and delivery verification
- Delta sync for offline data synchronization
- Pydantic models for all API validation
- Session-based auth with httponly cookies

### Naming
- Route files: `{feature}.py` (e.g., `products.py`, `orders.py`)
- Templates: `{feature}.html` (e.g., `products.html`, `cart.html`)
- Tests: `test_{feature}.py` (e.g., `test_backend.py`, `test_register.py`)
- DB tables: plural snake_case (e.g., `users`, `cart_items`)
- API paths: plural kebab-case (e.g., `/api/b2b/rfq`, `/api/cart/items`)

---

## Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./libya_b2b.db

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Offline
OFFLINE_MODE=true
SYNC_INTERVAL=300

# Email (leave empty for console fallback)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_USE_TLS=true
```

---

## Testing

```bash
# Run all tests
make test

# Run specific test file
cd src/backend && python -m pytest ../tests/test_register.py -v

# Run with coverage
make test-coverage
```

### Test Structure
- **conftest.py** — Shared in-memory SQLite engine (DO NOT create own DB)
- **test_backend.py** — Core API tests (auth, products, orders, etc.)
- **test_register.py** — Registration flow (61 tests)
- **test_integration.py** — Integration tests
- **test_sprint8.py** — Sprint 8 features
- **test_chatbot.py** — Chatbot tests
- **test_qr.py** — QR code tests

### Critical Gotchas
- **Test DB is shared** — conftest.py sets up a single in-memory SQLite engine
- **Sync engine is a singleton** — `get_sync_engine()` reuses connections
- **Sync entry IDs need microseconds** — use `%f` format
- **Rate limit cooldown** — cleared between tests via conftest

---

## Deployment

### Docker
```bash
# Build and start
make build && make up

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### OVH VPS
- **Server:** OVH VPS (20 EUR/month)
- **OS:** Ubuntu 22.04
- **Docker:** Docker Compose
- **SSL:** Let's Encrypt (certbot)
- **Domain:** Configurable

### CI/CD
GitHub Actions on push to main/develop:
1. `ruff check` (linting)
2. `pytest tests/ -v` (tests)
3. Docker build test

---

## Phase 2 Roadmap

| Sprint | Feature | Status |
|--------|---------|--------|
| Sprint 1 | Documentation | ✅ Current |
| Sprint 2 | PWA (Offline-Mobile) | ⏳ Planned |
| Sprint 3 | Analytics Dashboard | ⏳ Planned |
| Sprint 4 | Admin Panel Extension | ⏳ Planned |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | Aug 2026 | Initial release |
| v1.5 | Aug 2026 | Sprint 5 (monitoring, sync) |
| v2.0 | Aug 2026 | Sprint 8 (B2B features, cart, reviews) |
| v3.0 | Aug 2026 | Sprint 13 (Phase 1 complete) |
| v3.1 | Aug 2026 | Registration, email verification, 218 tests |
