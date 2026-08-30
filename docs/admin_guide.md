# Libya B2B Platform — Admin Guide

**Version:** v3.1 | **Last Updated:** 24 August 2026

---

## Table of Contents

1. [Dashboard Overview](#1-dashboard-overview)
2. [User Management](#2-user-management)
3. [Product Management](#3-product-management)
4. [Order Management](#4-order-management)
5. [System Monitoring](#5-system-monitoring)
6. [Database Management](#6-database-management)
7. [Deployment](#7-deployment)
8. [Security](#8-security)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Dashboard Overview

### Accessing the Admin Dashboard
- **URL:** `/admin` (if admin panel is implemented)
- **API:** `GET /api/monitoring/stats` (system stats)
- **API:** `GET /api/monitoring/health-detailed` (detailed health)

### System Health
Check system health at any time:
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "sqlite",
  "offline_capable": true
}
```

### Key Metrics
Monitor these metrics regularly:
- **Uptime:** How long the server has been running
- **CPU Usage:** Should stay below 80%
- **Memory Usage:** Should stay below 80%
- **Disk Usage:** Should stay below 90%
- **Active Processes:** Number of running processes

---

## 2. User Management

### User Roles
| Role | Permissions |
|------|------------|
| `buyer` | Browse products, place orders, create RFQ, message suppliers |
| `seller` | Manage products, view orders, respond to RFQ, message buyers |
| `admin` | Full access to all endpoints |

### Viewing Users
```sql
-- Connect to SQLite database
sqlite3 libya_b2b.db

-- List all users
SELECT id, username, email, role, is_active, email_verified, created_at FROM users;

-- Count users by role
SELECT role, COUNT(*) FROM users GROUP BY role;

-- Find inactive users
SELECT id, username, email FROM users WHERE is_active = 0;

-- Find unverified emails
SELECT id, username, email FROM users WHERE email_verified = 0;
```

### User Security
```sql
-- Check 2FA status
SELECT id, username, two_factor_enabled FROM users WHERE two_factor_enabled = 1;

-- View login history (last 24 hours)
SELECT u.username, lh.ip_address, lh.success, lh.created_at 
FROM login_history lh 
JOIN users u ON lh.user_id = u.id 
WHERE lh.created_at > datetime('now', '-1 day')
ORDER BY lh.created_at DESC;

-- Failed login attempts
SELECT u.username, lh.ip_address, lh.created_at 
FROM login_history lh 
JOIN users u ON lh.user_id = u.id 
WHERE lh.success = 0 
ORDER BY lh.created_at DESC;
```

### Disabling a User
```sql
-- Deactivate a user
UPDATE users SET is_active = 0 WHERE id = <user_id>;

-- Reactivate a user
UPDATE users SET is_active = 1 WHERE id = <user_id>;
```

---

## 3. Product Management

### Viewing Products
```sql
-- List all products
SELECT id, name, name_arabic, price, category, stock_quantity, is_active FROM products;

-- Products by category
SELECT category, COUNT(*) as count FROM products GROUP BY category;

-- Low stock products (< 10 units)
SELECT id, name, stock_quantity FROM products WHERE stock_quantity < 10 AND is_active = 1;

-- Products without images
SELECT id, name FROM products WHERE image_url IS NULL;
```

### Adding Products via API
```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cement Bag",
    "name_arabic": "كيس أسمنت",
    "description": "Portland cement, 50kg bag",
    "description_arabic": "أسمنت بورتلاند، كيس 50 كجم",
    "price": 25.00,
    "currency": "LYD",
    "category": "building_materials",
    "stock_quantity": 1000,
    "moq": 10
  }'
```

### Product Categories
The platform supports 21 categories:

| ID | English | Arabic |
|----|---------|--------|
| building_materials | Building Materials | مواد بناء |
| electrical | Electrical | كهرباء |
| hardware | Hardware | أدوات |
| office_supplies | Office Supplies | مستلزمات مكتبية |
| machinery | Machinery | آلات |
| textiles | Textiles | منسوجات |
| packaging | Packaging | تغليف |
| chemicals | Chemicals | كيميائيات |
| automotive | Automotive | سيارات |
| agriculture | Agriculture | زراعة |
| food_beverage | Food & Beverage | أطعمة ومشروبات |
| furniture | Furniture | أثاث |
| safety | Safety Equipment | معدات السلامة |
| plumbing | Plumbing | سباكة |
| painting | Painting | طلاء |
| cleaning | Cleaning | تنظيف |
| medical | Medical Supplies | مستلزمات طبية |
| lighting | Lighting | إنارة |
| it_equipment | IT Equipment | معدات تقنية |
| security | Security | أمان |
| others | Others | أخرى |

---

## 4. Order Management

### Order Statuses
| Status | Description |
|--------|-------------|
| `pending` | Order placed, awaiting processing |
| `processing` | Order is being prepared |
| `shipped` | Order is on the way |
| `delivered` | Order has been delivered (confirmed with photo + GPS) |

### Viewing Orders
```sql
-- All orders
SELECT id, order_number, buyer_id, seller_id, total_amount, status, created_at 
FROM orders ORDER BY created_at DESC;

-- Orders by status
SELECT status, COUNT(*) FROM orders GROUP BY status;

-- Revenue in last 30 days
SELECT SUM(total_amount) as revenue_30d 
FROM orders 
WHERE created_at > datetime('now', '-30 days');

-- Pending orders
SELECT id, order_number, total_amount, created_at 
FROM orders WHERE status = 'pending';
```

### Order Number Format
Orders use the format: `LYB-YYYYMMDD-XXXXXX`
- `LYB` — Libya
- `YYYYMMDD` — Date
- `XXXXXX` — 6-digit random number

### Delivery Confirmation
```bash
# Confirm delivery with photo and GPS
curl -X PUT "http://localhost:8000/api/orders/1/deliver?photo_url=/photos/delivery.jpg&gps_lat=32.9022&gps_lon=13.1800" \
  -H "Cookie: b2b_session=<token>"
```

---

## 5. System Monitoring

### Quick Health Check
```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/api/monitoring/health-detailed

# System stats
curl http://localhost:8000/api/monitoring/stats
```

### Monitoring Stats Response
```json
{
  "uptime": "24h 30m",
  "uptime_seconds": 88200,
  "requests_total": 12345,
  "cpu_usage_percent": 45.2,
  "memory_usage_percent": 62.8,
  "memory_used_mb": 512.5,
  "disk_usage_percent": 35.0,
  "active_processes": 156,
  "timestamp": "2026-08-24T12:00:00Z",
  "version": "2.0.0"
}
```

### Log Files
```bash
# Docker logs
docker logs libya-b2b-backend --tail 100

# Follow logs
docker logs libya-b2b-backend -f

# Log locations (Docker)
/var/lib/docker/containers/<container-id>/<container-id>-json.log
```

### Sync Monitoring
```bash
# Check sync status
curl http://localhost:8000/api/sync/stats

# View pending syncs
curl http://localhost:8000/api/sync/pending

# View recent changes
curl http://localhost:8000/api/sync/changes?since=2026-08-24T00:00:00
```

---

## 6. Database Management

### Database Location
- **Development:** `libya_b2b_backend/libya_b2b.db`
- **Docker:** `/app/libya_b2b.db` (inside container)
- **Production:** `/data/libya_b2b.db` (mounted volume)

### Backup
```bash
# Simple backup
cp libya_b2b.db backup_$(date +%Y%m%d_%H%M%S).db

# Docker backup
docker exec libya-b2b-backend cp /app/libya_b2b.db /app/backup_$(date +%Y%m%d).db

# Automated backup (add to cron)
0 2 * * * cp /path/to/libya_b2b.db /backups/libya_b2b_$(date +\%Y\%m\%d).db
```

### Restore
```bash
# Stop the server first
docker-compose down

# Restore from backup
cp backup_20260824_120000.db libya_b2b.db

# Restart
docker-compose up -d
```

### Schema Management
The database schema is managed automatically:
```python
# config.py - init_db() creates tables + adds missing columns
from config import init_db
init_db()
```

**Important:** SQLite doesn't support `ALTER TABLE DROP COLUMN`. To remove a column:
1. Create a new table without the column
2. Copy data from old table
3. Drop old table
4. Rename new table

### Database Size
```bash
# Check database size
ls -lh libya_b2b.db

# SQLite analysis
sqlite3 libya_b2b.db "PRAGMA page_count; PRAGMA page_size; PRAGMA freelist_count;"
```

---

## 7. Deployment

### Docker Setup
```bash
# Build and start
make build && make up

# Or manually
docker-compose up -d --build

# Stop
docker-compose down

# Restart
docker-compose restart
```

### Production Deployment
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### OVH VPS Setup
1. **Server:** OVH VPS (20 EUR/month)
2. **OS:** Ubuntu 22.04 LTS
3. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```
4. **Clone repository:**
   ```bash
   git clone <repo-url>
   cd libya_b2b_platform
   ```
5. **Start services:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

### SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Environment Variables
Create `.env` file:
```bash
# Database
DATABASE_URL=sqlite:///./libya_b2b.db

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# CORS (production)
CORS_ORIGINS=["https://your-domain.com"]

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your@email.com
```

---

## 8. Security

### Session Management
- **Cookie:** `b2b_session` (httponly, samesite=lax)
- **Duration:** 30 days (remember_me) or 7 days (standard)
- **Storage:** `user_sessions` table

### Password Security
- **Hashing:** SHA-256 (acceptable for pilot, consider bcrypt for production)
- **Storage:** `password_hash` column in `users` table

### Two-Factor Authentication (2FA)
- **Setup:** `POST /api/auth/2fa/setup` (generates secret + QR URL)
- **Verify:** `POST /api/auth/2fa/verify` (validates code, enables 2FA)
- **Algorithm:** HMAC-based TOTP (simplified, not RFC 6238 compliant)

### Email Verification
- **Code:** 6-digit random number
- **Expiry:** 10 minutes
- **Rate limiting:** 60-second cooldown between sends
- **Storage:** `email_verification_code` + `email_verification_code_expires_at`

### Rate Limiting
- **send-verification:** 60-second cooldown per user
- **Storage:** In-memory dictionary (resets on server restart)

### Security Checklist
- [ ] Change default passwords
- [ ] Enable 2FA for admin accounts
- [ ] Set `DEBUG=false` in production
- [ ] Configure CORS properly
- [ ] Enable HTTPS (SSL certificate)
- [ ] Regular database backups
- [ ] Monitor login history for suspicious activity
- [ ] Update dependencies regularly

---

## 9. Troubleshooting

### Common Issues

#### Server won't start
```bash
# Check if port is in use
lsof -i:8000

# Kill existing process
fuser -k 8000/tcp

# Check Docker status
docker ps
docker-compose logs backend
```

#### Database locked
```bash
# Check for concurrent access
sqlite3 libya_b2b.db "PRAGMA journal_mode;"

# If locked, restart the server
docker-compose restart backend
```

#### Email not sending
```bash
# Check SMTP configuration
cat .env | grep SMTP

# Test with console fallback (leave SMTP_HOST empty)
SMTP_HOST= docker-compose up backend
# Check logs for verification code
docker logs libya-b2b-backend | grep "Verification code"
```

#### Sync not working
```bash
# Check sync status
curl http://localhost:8000/api/sync/stats

# View pending syncs
curl http://localhost:8000/api/sync/pending

# Force sync all
curl -X POST http://localhost:8000/api/sync/all
```

#### High memory usage
```bash
# Check memory
curl http://localhost:8000/api/monitoring/stats

# Restart server
docker-compose restart backend

# Check for memory leaks
docker stats libya-b2b-backend
```

### Log Analysis
```bash
# Error logs
docker logs libya-b2b-backend 2>&1 | grep -i error

# Access logs
docker logs libya-b2b-backend 2>&1 | grep "HTTP"

# Slow requests
docker logs libya-b2b-backend 2>&1 | grep "duration"
```

### Performance Tuning
- **SQLite:** Enable WAL mode for better concurrency
  ```sql
  PRAGMA journal_mode=WAL;
  ```
- **Connection pooling:** SQLAlchemy handles this automatically
- **Caching:** Consider Redis for session storage (requires additional budget)

---

## Quick Reference

### API Endpoints for Admin
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/monitoring/stats` | GET | System stats |
| `/api/monitoring/health-detailed` | GET | Detailed health |
| `/api/sync/stats` | GET | Sync statistics |
| `/api/sync/pending` | GET | Pending syncs |
| `/api/b2b/stats` | GET | Platform statistics |
| `/api/b2b/analytics` | GET | Analytics data |

### Docker Commands
| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start services |
| `docker-compose down` | Stop services |
| `docker-compose restart` | Restart services |
| `docker-compose logs -f` | Follow logs |
| `docker-compose ps` | List services |
| `docker-compose exec backend bash` | Shell into backend |

### Database Commands
| Command | Description |
|---------|-------------|
| `sqlite3 libya_b2b.db` | Open database |
| `.tables` | List tables |
| `.schema users` | Show table schema |
| `SELECT COUNT(*) FROM users;` | Count users |
| `.quit` | Exit SQLite |
