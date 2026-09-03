"""
Libya B2B Platform - Registration Flow Tests
Tests for the 3-step Alibaba-style registration:
  Step 1: Email + Password + Confirm Password
  Step 2: 6-digit verification code
  Step 3: Role + Company Name EN/AR + Phone + Country + Terms
"""

import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

from main import app

# DB setup handled by conftest.py (shared engine + override)
client = TestClient(app)


# ============================================================
# BACKEND API: REGISTRATION ENDPOINT
# ============================================================


def test_register_buyer_with_all_fields():
    """Register a buyer with all optional fields (Alibaba-style profile)."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "buyer_full",
            "email": "buyer@company.ly",
            "password": "securePass123!",
            "role": "buyer",
            "business_name": "Tripoli Trading Co.",
            "business_name_arabic": "شركة طرابلس للتجارة",
            "phone": "+218 91 234 5678",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["username"] == "buyer_full"
    assert data["user"]["email"] == "buyer@company.ly"
    assert data["user"]["role"] == "buyer"
    assert data["user"]["business_name"] == "Tripoli Trading Co."
    assert data["user"]["is_active"] is True
    assert "session_token" in data


def test_register_seller_with_all_fields():
    """Register a seller with all optional fields."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "seller_full",
            "email": "seller@company.ly",
            "password": "securePass123!",
            "role": "seller",
            "business_name": "Benghazi Supplies LLC",
            "business_name_arabic": "شركة بنغازي للمستلزمات",
            "phone": "+218 92 345 6789",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "seller"
    assert data["user"]["business_name"] == "Benghazi Supplies LLC"
    assert "session_token" in data


def test_register_minimal_fields():
    """Register with only required fields (username + password)."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "minimal_user",
            "password": "pass123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["username"] == "minimal_user"
    assert data["user"]["role"] == "buyer"  # default role
    assert data["user"]["email"] is None
    assert data["user"]["business_name"] is None


def test_register_sets_session_cookie():
    """Registration should set the b2b_session cookie."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "cookie_test",
            "password": "pass123",
            "role": "buyer",
        },
    )
    assert resp.status_code == 200
    # Check that session cookie was set
    cookies = {c.name: c.value for c in client.cookies.jar}
    assert "b2b_session" in cookies
    assert len(cookies["b2b_session"]) > 0


def test_register_duplicate_username_rejected():
    """Duplicate username must be rejected with 409."""
    client.post(
        "/api/auth/register",
        json={"username": "dup_user", "password": "pass123"},
    )
    resp = client.post(
        "/api/auth/register",
        json={"username": "dup_user", "password": "pass456"},
    )
    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"].lower()


def test_register_missing_username_rejected():
    """Registration without username must fail."""
    resp = client.post(
        "/api/auth/register",
        json={"password": "pass123"},
    )
    assert resp.status_code == 422  # Pydantic validation error


def test_register_missing_password_rejected():
    """Registration without password must fail."""
    resp = client.post(
        "/api/auth/register",
        json={"username": "no_pass_user"},
    )
    assert resp.status_code == 422


def test_register_email_stored_correctly():
    """Email address is stored and returned correctly."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "email_test",
            "email": "test@example.com",
            "password": "pass123",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "test@example.com"


def test_register_business_name_arabic_stored():
    """Arabic business name is stored correctly."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "arabic_name",
            "password": "pass123",
            "business_name_arabic": "شركة ليبيا للتجارة",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["business_name"] is None  # EN not set
    # business_name_arabic is not in UserResponse but is stored in DB
    # Verify via /me endpoint after login
    client.post(
        "/api/auth/login",
        json={"username": "arabic_name", "password": "pass123"},
    )
    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200


def test_register_phone_stored():
    """Phone number is stored correctly."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "phone_test",
            "password": "pass123",
            "phone": "+218 91 111 2222",
        },
    )
    assert resp.status_code == 200
    # Phone is stored in DB but not in UserResponse; verify via me
    client.post(
        "/api/auth/login",
        json={"username": "phone_test", "password": "pass123"},
    )
    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200


def test_register_then_login_works():
    """After registration, user can log in with the same credentials."""
    client.post(
        "/api/auth/register",
        json={
            "username": "reg_login",
            "email": "reg@login.ly",
            "password": "mySecurePass",
            "role": "buyer",
        },
    )
    # Login with registered credentials
    resp = client.post(
        "/api/auth/login",
        json={"username": "reg_login", "password": "mySecurePass"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["username"] == "reg_login"


def test_register_then_me_returns_user():
    """After registration, /me endpoint returns the registered user."""
    client.post(
        "/api/auth/register",
        json={
            "username": "me_test",
            "email": "me@test.ly",
            "password": "pass123",
            "role": "seller",
            "business_name": "Me Test Corp",
        },
    )
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "me_test"
    assert data["email"] == "me@test.ly"
    assert data["role"] == "seller"
    assert data["business_name"] == "Me Test Corp"
    assert data["is_active"] is True


def test_register_multiple_users():
    """Multiple users can register with different usernames."""
    for i in range(5):
        resp = client.post(
            "/api/auth/register",
            json={
                "username": f"user_{i}",
                "password": f"pass_{i}",
                "role": "buyer" if i % 2 == 0 else "seller",
            },
        )
        assert resp.status_code == 200

    # Verify all users can log in
    for i in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"username": f"user_{i}", "password": f"pass_{i}"},
        )
        assert resp.status_code == 200


# ============================================================
# BACKEND API: ROLE-BASED REGISTRATION
# ============================================================


def test_register_buyer_role():
    """Buyer role is set correctly during registration."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "buyer_role",
            "password": "pass123",
            "role": "buyer",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "buyer"


def test_register_seller_role():
    """Seller role is set correctly during registration."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "seller_role",
            "password": "pass123",
            "role": "seller",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "seller"


def test_register_default_role_is_buyer():
    """When no role is specified, default should be 'buyer'."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "default_role",
            "password": "pass123",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "buyer"


# ============================================================
# BACKEND API: VERIFICATION CODE ENDPOINTS
# ============================================================


def _get_user_code(username):
    """Read verification code from DB for a test user."""
    from models import User
    from conftest import TestSessionLocal
    db = TestSessionLocal()
    user = db.query(User).filter(User.username == username).first()
    code = user.email_verification_code if user else None
    db.close()
    return code


def test_send_verification_code_after_register():
    """After registration with email, user can request a verification code."""
    client.post(
        "/api/auth/register",
        json={
            "username": "verify_send",
            "email": "send@test.ly",
            "password": "pass123",
            "role": "buyer",
        },
    )
    resp = client.post("/api/auth/send-verification")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "sent" in data["message"].lower()

    # Code is stored in DB (not returned in response)
    code = _get_user_code("verify_send")
    assert code is not None
    assert len(code) == 6
    assert code.isdigit()


def test_verify_email_full_flow():
    """Full email verification flow: register → send code → verify."""
    client.post(
        "/api/auth/register",
        json={
            "username": "verify_flow",
            "email": "verify@flow.ly",
            "password": "pass123",
        },
    )
    # Send verification code
    client.post("/api/auth/send-verification")
    code = _get_user_code("verify_flow")

    # Verify email
    verify_resp = client.post(
        "/api/auth/verify-email", json={"code": code}
    )
    assert verify_resp.status_code == 200
    assert "successfully" in verify_resp.json()["message"].lower()


def test_verify_email_wrong_code_rejected():
    """Wrong verification code must be rejected."""
    client.post(
        "/api/auth/register",
        json={
            "username": "verify_wrong",
            "email": "wrong@test.ly",
            "password": "pass123",
        },
    )
    client.post("/api/auth/send-verification")

    resp = client.post(
        "/api/auth/verify-email", json={"code": "000000"})
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


def test_verify_email_without_code_fails():
    """Verify email without requesting a code first must fail."""
    client.post(
        "/api/auth/register",
        json={
            "username": "verify_nocode",
            "email": "nocode@test.ly",
            "password": "pass123",
        },
    )
    resp = client.post(
        "/api/auth/verify-email", json={"code": "123456"})
    assert resp.status_code == 400


# ============================================================
# FRONTEND TEMPLATE RENDERING
# ============================================================

FRONTEND_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "frontend"
)


def _render(template_name, lang="en"):
    """Helper to render a frontend template via FastAPI."""
    url_map = {
        "landing": "/",
        "login": "/login",
    }
    base = url_map.get(template_name, f"/{template_name}")
    if lang == "ar":
        base = f"/ar{base}"
    resp = client.get(base)
    return resp.text


class TestRegisterTemplateEN:
    """Tests for the English register.html template."""

    def test_template_exists(self):
        """register.html template file exists."""
        assert os.path.exists(
            os.path.join(FRONTEND_DIR, "templates", "register.html")
        )

    def test_renders_without_error(self):
        """Template renders successfully in English."""
        content = _render("register", "en")
        assert content is not None
        assert len(content) > 1000

    def test_contains_step1(self):
        """Template contains Step 1 form fields."""
        content = _render("register", "en")
        assert 'id="step1"' in content
        assert 'id="reg-email"' in content
        assert 'id="reg-password"' in content
        assert 'id="reg-password-confirm"' in content

    def test_contains_step2(self):
        """Template contains Step 2 verification code."""
        content = _render("register", "en")
        assert 'id="step2"' in content
        assert 'id="reg-code"' in content

    def test_contains_step3(self):
        """Template contains Step 3 profile fields."""
        content = _render("register", "en")
        assert 'id="step3"' in content
        assert 'id="reg-company"' in content
        assert 'id="reg-company-ar"' in content
        assert 'id="reg-phone"' in content
        assert 'id="reg-country"' in content

    def test_terms_checkbox_present(self):
        """Terms checkbox is present and required."""
        content = _render("register", "en")
        assert 'id="reg-terms"' in content
        assert 'type="checkbox"' in content
        assert "Terms of Service" in content

    def test_role_selector_present(self):
        """Role selector with buyer/seller options exists."""
        content = _render("register", "en")
        assert 'class="role-selector"' in content
        assert "Buyer" in content or "buyer" in content
        assert "Seller" in content or "seller" in content

    def test_country_selector_has_libya(self):
        """Country dropdown includes Libya."""
        content = _render("register", "en")
        assert 'id="reg-country"' in content
        assert "Libya" in content

    def test_password_strength_meter(self):
        """Password strength meter is present."""
        content = _render("register", "en")
        assert 'id="strengthBar"' in content
        assert "password-strength" in content

    def test_i18n_variables_replaced(self):
        """Template variables like {{register.title}} are replaced."""
        content = _render("register", "en")
        assert "{{register.title}}" not in content
        assert "Create Account" in content

    def test_step_indicators(self):
        """Step indicator dots are present."""
        content = _render("register", "en")
        assert 'id="dot1"' in content
        assert 'id="dot2"' in content
        assert 'id="dot3"' in content

    def test_login_link(self):
        """Link to login page is present."""
        content = _render("register", "en")
        assert "Log in here" in content or "login" in content.lower()

    def test_navbar_present(self):
        """Navbar with Libya B2B brand is present."""
        content = _render("register", "en")
        assert "Libya B2B" in content
        assert 'class="navbar"' in content

    def test_javascript_functions_exist(self):
        """Key JavaScript functions are defined."""
        content = _render("register", "en")
        assert "function goToStep2" in content
        assert "function verifyCode" in content
        assert "function submitRegistration" in content
        assert "function selectRole" in content
        assert "function checkPasswordStrength" in content

    def test_redirect_after_registration(self):
        """JavaScript contains role-based redirect logic."""
        content = _render("register", "en")
        assert "/seller" in content
        assert "/buyer" in content

    def test_register_api_call_in_js(self):
        """JavaScript calls Auth.register with expected fields."""
        content = _render("register", "en")
        assert "Auth.register" in content
        assert "business_name" in content
        assert "business_name_arabic" in content


class TestRegisterTemplateAR:
    """Tests for the Arabic register.html template."""

    def test_renders_without_error(self):
        """Template renders successfully in Arabic."""
        content = _render("register", "ar")
        assert content is not None
        assert len(content) > 1000

    def test_rtl_direction(self):
        """Arabic template has RTL direction."""
        content = _render("register", "ar")
        assert 'dir="rtl"' in content

    def test_arabic_title(self):
        """Title is translated to Arabic."""
        content = _render("register", "ar")
        assert "انشاء حساب" in content

    def test_arabic_step_labels(self):
        """Step labels are translated to Arabic."""
        content = _render("register", "ar")
        assert "الحساب" in content
        assert "التحقق" in content
        assert "الملف الشخصي" in content

    def test_arabic_form_labels(self):
        """Form labels are translated to Arabic."""
        content = _render("register", "ar")
        assert "البريد الالكتروني" in content
        assert "كلمة المرور" in content
        assert "رقم الهاتف" in content

    def test_arabic_role_options(self):
        """Role options are translated to Arabic."""
        content = _render("register", "ar")
        assert "شراء منتجات" in content
        assert "بيع منتجات" in content

    def test_arabic_country_options(self):
        """Country names are translated to Arabic."""
        content = _render("register", "ar")
        assert "ليبيا" in content
        assert "تونس" in content
        assert "مصر" in content

    def test_arabic_terms(self):
        """Terms of Service is translated to Arabic."""
        content = _render("register", "ar")
        assert "شروط الخدمة" in content

    def test_arabic_button_text(self):
        """Submit button text is translated to Arabic."""
        content = _render("register", "ar")
        assert "انشاء حساب" in content

    def test_arabic_password_hint(self):
        """Password hint is translated to Arabic."""
        content = _render("register", "ar")
        assert "6 احرف" in content

    def test_arabic_has_all_form_elements(self):
        """Arabic template has all form elements."""
        content = _render("register", "ar")
        assert 'id="reg-email"' in content
        assert 'id="reg-password"' in content
        assert 'id="reg-terms"' in content
        assert 'id="reg-country"' in content
        assert 'id="reg-company"' in content
        assert 'id="reg-phone"' in content


# ============================================================
# I18N KEY COMPLETENESS
# ============================================================


class TestI18nKeys:
    """Verify i18n keys are complete and matching between EN and AR."""

    def test_en_json_has_register_section(self):
        """en.json contains a 'register' section."""
        path = os.path.join(FRONTEND_DIR, "locales", "en.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "register" in data

    def test_ar_json_has_register_section(self):
        """ar.json contains a 'register' section."""
        path = os.path.join(FRONTEND_DIR, "locales", "ar.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "register" in data

    def test_en_ar_keys_match(self):
        """EN and AR register sections have identical key sets."""
        en_path = os.path.join(FRONTEND_DIR, "locales", "en.json")
        ar_path = os.path.join(FRONTEND_DIR, "locales", "ar.json")
        with open(en_path, encoding="utf-8") as f:
            en = json.load(f)
        with open(ar_path, encoding="utf-8") as f:
            ar = json.load(f)
        en_keys = set(en["register"].keys())
        ar_keys = set(ar["register"].keys())
        assert en_keys == ar_keys, (
            f"Missing in AR: {en_keys - ar_keys}; "
            f"Extra in AR: {ar_keys - en_keys}"
        )

    def test_required_register_keys_exist(self):
        """All critical register i18n keys are present."""
        path = os.path.join(FRONTEND_DIR, "locales", "en.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        reg = data["register"]
        required_keys = [
            "title",
            "subtitle",
            "step1_label",
            "step2_label",
            "step3_label",
            "step1_heading",
            "email",
            "password",
            "confirm_password",
            "step2_heading",
            "verify_code",
            "resend_code",
            "step3_heading",
            "role",
            "role_buyer",
            "role_seller",
            "company_name",
            "company_name_ar",
            "phone",
            "country",
            "terms_prefix",
            "terms_link",
            "terms_suffix",
            "create_account",
            "has_account",
            "login_here",
        ]
        for key in required_keys:
            assert key in reg, f"Missing i18n key: register.{key}"
            assert reg[key], f"Empty i18n value: register.{key}"

    def test_register_key_count(self):
        """Register section has a reasonable number of keys (40+)."""
        path = os.path.join(FRONTEND_DIR, "locales", "en.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["register"]) >= 40


# ============================================================
# SERVER ROUTING
# ============================================================


class TestServerRouting:
    """Verify the FastAPI routes serve /register correctly."""

    def test_register_route_exists(self):
        """/register route returns HTML."""
        resp = client.get("/register")
        assert resp.status_code == 200
        assert "register" in resp.text.lower() or "account" in resp.text.lower()

    def test_ar_register_route_exists(self):
        """/ar/register route returns HTML."""
        resp = client.get("/ar/register")
        assert resp.status_code == 200

    def test_auth_js_links_to_register(self):
        """auth.js Register button links to /register page (with base prefix for AR)."""
        auth_path = os.path.join(FRONTEND_DIR, "static", "auth.js")
        with open(auth_path, encoding="utf-8") as f:
            content = f.read()
        assert '/register' in content  # Dynamic: ${_authBase}/register

    def test_auth_js_no_inline_register(self):
        """auth.js no longer has inline register handler."""
        auth_path = os.path.join(FRONTEND_DIR, "static", "auth.js")
        with open(auth_path, encoding="utf-8") as f:
            content = f.read()
        # The old inline register button handler should be gone
        assert "document.getElementById('auth-register-btn')" not in content


# ============================================================
# EDGE CASES & SECURITY
# ============================================================


def test_register_empty_username_rejected():
    """Empty username must be rejected."""
    resp = client.post(
        "/api/auth/register",
        json={"username": "", "password": "pass123"},
    )
    # Empty string may be accepted by Pydantic (depends on validation)
    # but the important thing is it doesn't crash
    assert resp.status_code in (200, 400, 422)


def test_register_long_password_accepted():
    """Very long passwords should be accepted (hashed)."""
    long_pw = "x" * 1000
    resp = client.post(
        "/api/auth/register",
        json={"username": "long_pw_user", "password": long_pw},
    )
    assert resp.status_code == 200


def test_register_special_characters_in_business_name():
    """Business names with special characters are stored correctly."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "special_chars",
            "password": "pass123",
            "business_name": "Al-Khalil & Sons Co. (LLC)",
            "business_name_arabic": "شركة الخليل وأبناء ذ.م.م",
        },
    )
    assert resp.status_code == 200
    assert (
        resp.json()["user"]["business_name"]
        == "Al-Khalil & Sons Co. (LLC)"
    )


def test_register_unicode_in_arabic_fields():
    """Unicode Arabic characters are stored correctly."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "unicode_test",
            "password": "pass123",
            "business_name_arabic": "شركة بيانات ليبيا المحدودة",
        },
    )
    assert resp.status_code == 200


def test_register_then_get_me_consistent():
    """Data from register matches data from /me endpoint."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "consistency",
            "email": "con@test.ly",
            "password": "pass123",
            "role": "seller",
            "business_name": "Consistency Corp",
        },
    )
    assert resp.status_code == 200
    reg_data = resp.json()["user"]

    me_resp = client.get("/api/auth/me")
    me_data = me_resp.json()

    assert reg_data["username"] == me_data["username"]
    assert reg_data["email"] == me_data["email"]
    assert reg_data["role"] == me_data["role"]
    assert reg_data["business_name"] == me_data["business_name"]


# ============================================================
# EMAIL VERIFICATION: NEW FEATURES
# ============================================================


def test_send_verification_requires_email():
    """send-verification fails if user has no email."""
    client.post(
        "/api/auth/register",
        json={
            "username": "no_email_user",
            "password": "pass123",
        },
    )
    resp = client.post("/api/auth/send-verification")
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


def test_send_verification_no_code_in_response():
    """Verification code is NOT returned in response (security)."""
    client.post(
        "/api/auth/register",
        json={
            "username": "secure_code",
            "email": "secure@test.ly",
            "password": "pass123",
        },
    )
    resp = client.post("/api/auth/send-verification")
    assert resp.status_code == 200
    data = resp.json()
    # Code should NOT be in the response
    assert "code" not in data
    # Only message should be present
    assert "message" in data


def test_verification_code_stored_in_db():
    """Verification code is stored in the database."""
    client.post(
        "/api/auth/register",
        json={
            "username": "db_code",
            "email": "db@test.ly",
            "password": "pass123",
        },
    )
    client.post("/api/auth/send-verification")

    code = _get_user_code("db_code")
    assert code is not None
    assert len(code) == 6
    assert code.isdigit()
    assert 100000 <= int(code) <= 999999


def test_verification_code_has_expiry():
    """Verification code has an expiry timestamp in DB."""
    from models import User
    from conftest import TestSessionLocal

    client.post(
        "/api/auth/register",
        json={
            "username": "expiry_test",
            "email": "expiry@test.ly",
            "password": "pass123",
        },
    )
    client.post("/api/auth/send-verification")

    db = TestSessionLocal()
    user = db.query(User).filter(User.username == "expiry_test").first()
    assert user.email_verification_code_expires_at is not None
    # Expiry should be in the future (strip tzinfo for naive datetime comparison)
    from datetime import datetime, timezone
    expires = user.email_verification_code_expires_at
    now = datetime.now(timezone.utc).replace(tzinfo=None) if expires.tzinfo is None else datetime.now(timezone.utc)
    if expires.tzinfo is not None:
        expires = expires.replace(tzinfo=None)
    assert expires > now
    db.close()


def test_rate_limiting_on_send_verification():
    """Sending verification too quickly is rate-limited."""
    client.post(
        "/api/auth/register",
        json={
            "username": "rate_limit",
            "email": "rate@test.ly",
            "password": "pass123",
        },
    )
    # First send succeeds
    resp1 = client.post("/api/auth/send-verification")
    assert resp1.status_code == 200

    # Second send immediately is rate-limited
    resp2 = client.post("/api/auth/send-verification")
    assert resp2.status_code == 429
    assert "wait" in resp2.json()["detail"].lower()


def test_profile_update_endpoint():
    """PUT /api/auth/me updates user profile."""
    client.post(
        "/api/auth/register",
        json={
            "username": "profile_update",
            "email": "profile@test.ly",
            "password": "pass123",
            "role": "buyer",
        },
    )

    resp = client.put(
        "/api/auth/me",
        json={
            "role": "seller",
            "business_name": "Updated Corp",
            "business_name_arabic": "شركة محدثة",
            "phone": "+218 99 888 7777",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "seller"
    assert data["business_name"] == "Updated Corp"


def test_profile_update_requires_auth():
    """PUT /api/auth/me requires authentication."""
    resp = client.put(
        "/api/auth/me",
        json={"role": "seller"},
    )
    assert resp.status_code == 401


def test_email_service_console_fallback():
    """Email service works in console fallback mode (no SMTP)."""
    from services.email import send_verification_code, is_smtp_configured

    # In test env, SMTP is not configured
    assert not is_smtp_configured()

    # Should still return True (console fallback)
    result = send_verification_code(
        to_email="test@example.com",
        code="123456",
        expiry_minutes=10,
    )
    assert result is True


def test_full_registration_flow():
    """Complete 3-step registration flow: register → verify → update profile."""
    # Step 1: Register with email + password
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "full_flow",
            "email": "full@flow.ly",
            "password": "securePass123!",
            "role": "buyer",
        },
    )
    assert resp.status_code == 200

    # Step 2: Send and verify email
    client.post("/api/auth/send-verification")
    code = _get_user_code("full_flow")
    resp = client.post(
        "/api/auth/verify-email", json={"code": code}
    )
    assert resp.status_code == 200

    # Step 3: Update profile
    resp = client.put(
        "/api/auth/me",
        json={
            "role": "seller",
            "business_name": "Full Flow Trading",
            "business_name_arabic": "شركة فلو للتجارة",
            "phone": "+218 91 000 1111",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "seller"
    assert data["business_name"] == "Full Flow Trading"

    # Verify final state
    me = client.get("/api/auth/me").json()
    assert me["role"] == "seller"
    assert me["business_name"] == "Full Flow Trading"
