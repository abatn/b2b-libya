"""
Libya B2B Platform - App Factory (v6.0)
Modular backend. 21+ files, Alibaba-model.
"""

import os
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from config import API_VERSION, APP_DESCRIPTION, APP_TITLE, APP_VERSION, Base, get_db, init_db
from routes import register_routes

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

# Performance: GZip compression (reduces response size ~70%)
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SIMPLE IN-MEMORY API CACHE
# ============================================================
_api_cache: dict[str, tuple[float, object]] = {}
CACHE_TTL = 30  # seconds


def cached_get(key: str, fetch_fn, ttl: int = CACHE_TTL):
    """Return cached result or fetch fresh data."""
    now = time.time()
    if key in _api_cache and now - _api_cache[key][0] < ttl:
        return _api_cache[key][1]
    data = fetch_fn()
    _api_cache[key] = (now, data)
    return data


def invalidate_cache(prefix: str = ""):
    """Invalidate cache entries matching a prefix."""
    global _api_cache
    if prefix:
        _api_cache = {k: v for k, v in _api_cache.items() if not k.startswith(prefix)}
    else:
        _api_cache.clear()


# ============================================================
# API VERSIONING MIDDLEWARE
# ============================================================
@app.middleware("http")
async def api_version_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    path = request.url.path
    # Static assets: cache 1 day
    if path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    # API responses: no cache + version header
    elif path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["X-API-Version"] = API_VERSION
        response.headers["X-Platform-Version"] = APP_VERSION
    return response


# Mount static files from frontend (the real assets live there)
frontend_static = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
if os.path.exists(frontend_static):
    app.mount("/static", StaticFiles(directory=frontend_static), name="static")

# Register all route modules
register_routes(app)


@app.on_event("startup")
def startup():
    init_db()
    # Auto-expire escrows pending > 30 days (Alibaba Trade Assurance style)
    from routes.escrow import check_expired_escrows

    count = check_expired_escrows()
    if count:
        print(f"[escrow] Auto-released {count} expired escrow(s)")


# Re-export for test compatibility
# (conftest.py does: from main import app, Base, get_db)
__all__ = ["app", "Base", "get_db"]
