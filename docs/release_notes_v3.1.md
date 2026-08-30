# Release Notes — Libya B2B Platform v3.1

**Release Date:** 24. August 2026  
**Sprint:** Phase 2, Sprint 1 (Documentation)  
**Status:** Stable

---

## New Features

### 3-Step Registration Flow
- **Step 1:** Email + Password + Confirm Password with strength meter
- **Step 2:** 6-digit email verification code (sent via SMTP, 10-min expiry)
- **Step 3:** Role selection (Buyer/Seller) + Company Name (EN/AR) + Phone + Country + Terms checkbox

### Email Verification System
- `POST /api/auth/send-verification` — Sends 6-digit code via SMTP
- `POST /api/auth/verify-email` — Validates code with expiry check
- Rate limiting: 60-second cooldown between resend requests
- Console fallback when SMTP is not configured (dev mode)

### Profile Update Endpoint
- `PUT /api/auth/me` — Update role, business name, phone after registration

### Arabic-First Registration
- Full RTL support in registration form
- Arabic labels, placeholders, and error messages
- Country selector with Libyan phone prefix

---

## Bug Fixes

### Double `/ar/` Prefix
- **Affected templates:** `register.html`, `2fa.html`, `verify-email.html`
- **Issue:** Language switcher had hardcoded `/ar/` in href, causing `/ar/ar/register`
- **Fix:** Changed lang-btn hrefs to English paths (e.g., `/register` instead of `/ar/register`)

---

## Changes

### Authentication
- Login modal "Register" button now navigates to `/register` (no inline modal)
- Role selector removed from login modal
- Session duration: 30 days (remember_me) or 7 days (standard)

### Email Service
- New `services/email.py` module using stdlib `smtplib` (no paid dependencies)
- HTML + plain text email templates for verification codes
- Password reset emails (console fallback in dev)

### Rate Limiting
- `send-verification`: 60-second cooldown per user
- Cooldown state cleared between test runs

### Testing
- Test count: 138 → 218 (+80 tests)
- New test file: `tests/test_register.py` (61 tests)
- Updated verification tests to read codes from DB (not response)

---

## Technical Details

### Database Changes
- Added `email_verification_code_expires_at` column to `users` table
- Auto-migration via `init_db()` (SQLite ALTER TABLE)

### API Changes
- `POST /api/auth/send-verification` — No longer returns `code` in response (security)
- `POST /api/auth/verify-email` — Now checks code expiry
- New: `PUT /api/auth/me` — Profile update

### Dependencies
- No new external dependencies added
- All changes use stdlib (`smtplib`, `secrets`, `hashlib`)

---

## Stats

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Tests | 138 | 218 | +80 |
| Templates | 22 | 26 | +4 |
| API Endpoints | ~20 | 85 | +65 |
| DB Tables | 12 | 14 | +2 |
| Pydantic Models | ~15 | 28 | +13 |

---

## Upgrade Guide

### From v3.0 to v3.1

1. **Pull latest code:**
   ```bash
   git pull origin main
   ```

2. **Rebuild Docker containers:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. **Database migration** (automatic):
   - `email_verification_code_expires_at` column added on startup
   - No manual migration needed

4. **Environment variables** (optional):
   ```bash
   # Add to .env for email verification
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your@email.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM=your@email.com
   ```
   Leave empty for console fallback (dev mode).

5. **Verify:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:3000/register
   ```

---

## Known Issues

- Email verification codes are stored in plaintext in the database (acceptable for pilot)
- 2FA uses simplified HMAC-based TOTP (not RFC 6238 compliant)
- Password reset tokens are not persisted (demo mode)

---

## Next Steps (Phase 2, Sprint 2)

- PWA (Progressive Web App) for offline-mobile support
- Service Worker for static asset caching
- Background sync for pending orders
- Offline queue for POST requests
