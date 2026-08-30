"""
Shared test configuration — single DB engine, single override.
All test files should NOT create their own engine/override.
"""
import sys
import os
import shutil
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend source to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'backend')
sys.path.insert(0, backend_dir)

# Copy frontend HTML files to backend static/ so FileResponse routes work in tests
frontend_templates = os.path.join(os.path.dirname(__file__), '..', 'src', 'frontend', 'templates')
backend_static = os.path.join(backend_dir, 'static')
os.makedirs(backend_static, exist_ok=True)

for html_file in os.listdir(frontend_templates):
    if html_file.endswith('.html'):
        src = os.path.join(frontend_templates, html_file)
        dst = os.path.join(backend_static, html_file)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

# Also copy index.html and index_ar.html as landing page aliases
landing_src = os.path.join(frontend_templates, 'landing.html')
index_dst = os.path.join(backend_static, 'index.html')
if os.path.exists(landing_src) and not os.path.exists(index_dst):
    shutil.copy2(landing_src, index_dst)

# index_ar.html: same content as landing.html (backend renders raw template)
index_ar_dst = os.path.join(backend_static, 'index_ar.html')
if os.path.exists(landing_src) and not os.path.exists(index_ar_dst):
    shutil.copy2(landing_src, index_ar_dst)

# Copy new JS files from frontend/static to backend/static
frontend_static = os.path.join(os.path.dirname(__file__), '..', 'src', 'frontend', 'static')
if os.path.exists(frontend_static):
    for js_file in os.listdir(frontend_static):
        if js_file.endswith('.js'):
            src = os.path.join(frontend_static, js_file)
            dst = os.path.join(backend_static, js_file)
            shutil.copy2(src, dst)

# Import after path setup
from main import app, Base, get_db

# ============================================================
# SINGLE SHARED TEST DATABASE (In-Memory SQLite)
# ============================================================

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override ONCE — all tests share this
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _setup_test_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    # Clear rate-limit cooldowns between tests (same user IDs are recycled)
    from routes.auth_routes import _send_verification_cooldown
    _send_verification_cooldown.clear()
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


# ============================================================
# AUTHENTICATED CLIENTS (created per-test, after tables exist)
# ============================================================

@pytest.fixture()
def client():
    """Unauthenticated TestClient (for public endpoint tests)."""
    from fastapi.testclient import TestClient as TC
    return TC(app)


@pytest.fixture()
def auth_client():
    """TestClient with a logged-in buyer (session cookie set)."""
    from fastapi.testclient import TestClient as TC
    c = TC(app)
    c.post(
        "/api/auth/register",
        json={"username": "test_user", "password": "pass", "role": "buyer"},
    )
    return c


@pytest.fixture()
def seller_client():
    """TestClient with a logged-in seller."""
    from fastapi.testclient import TestClient as TC
    c = TC(app)
    c.post(
        "/api/auth/register",
        json={"username": "test_seller", "password": "pass", "role": "seller"},
    )
    return c
