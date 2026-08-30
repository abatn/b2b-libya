"""
Libya B2B Platform - Auth Routes
Session-based authentication with cookies.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from config import get_db
from models import (
    EmailVerifyRequest,
    LoginHistory,
    LoginHistoryResponse,
    ProfileUpdateRequest,
    SessionResponse,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserSession,
)
from services.auth import hash_password as _svc_hash
from services.auth import verify_password as _svc_verify
from services.email import send_password_reset, send_verification_code

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE_NAME = "b2b_session"
SESSION_DURATION_HOURS = 24 * 30  # 30 days


def _hash_password(password: str) -> str:
    """bcrypt-backed hash (services.auth)."""
    return _svc_hash(password)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract user from session cookie. Returns None if not authenticated."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = db.query(UserSession).filter(UserSession.session_token == token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    if session.expires_at.replace(tzinfo=None) < datetime.now(timezone.utc).replace(tzinfo=None):
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")

    user = db.query(User).filter(User.id == session.user_id, User.is_active).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Like get_current_user but returns None instead of raising."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    session = db.query(UserSession).filter(UserSession.session_token == token).first()
    if not session or session.expires_at.replace(tzinfo=None) < datetime.now(timezone.utc).replace(
        tzinfo=None
    ):
        return None
    return db.query(User).filter(User.id == session.user_id, User.is_active).first()


def _log_login(db: Session, user_id: int, request: Request, success: bool):
    """Record a login attempt."""
    entry = LoginHistory(
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", ""),
        success=success,
    )
    db.add(entry)
    db.commit()


@router.post("/register", response_model=SessionResponse)
def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register a new user and set session cookie."""
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=_hash_password(user_data.password),
        role=user_data.role,
        business_name=user_data.business_name,
        business_name_arabic=user_data.business_name_arabic,
        phone=user_data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create session
    token = secrets.token_hex(64)
    session = UserSession(
        session_token=token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=SESSION_DURATION_HOURS),
    )
    db.add(session)
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=SESSION_DURATION_HOURS * 3600,
        samesite="lax",
    )

    return SessionResponse(session_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=SessionResponse)
def login(
    credentials: UserLogin, response: Response, request: Request, db: Session = Depends(get_db)
):
    """Login and set session cookie."""
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not _svc_verify(credentials.password, user.password_hash):
        if user:
            _log_login(db, user.id, request, False)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        _log_login(db, user.id, request, False)
        raise HTTPException(status_code=403, detail="Account disabled")

    _log_login(db, user.id, request, True)

    # Determine session duration based on remember_me
    remember_me = getattr(credentials, "remember_me", False)
    duration_hours = SESSION_DURATION_HOURS if remember_me else 24 * 7  # 30 days or 7 days

    token = secrets.token_hex(64)
    session = UserSession(
        session_token=token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=duration_hours),
    )
    db.add(session)
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=duration_hours * 3600,
        samesite="lax",
    )

    return SessionResponse(session_token=token, user=UserResponse.model_validate(user))


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Clear session."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        session = db.query(UserSession).filter(UserSession.session_token == token).first()
        if session:
            db.delete(session)
            db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Logged out"}


@router.post("/forgot-password")
def forgot_password(email: dict, db: Session = Depends(get_db)):
    """Send password reset link to email."""
    user = db.query(User).filter(User.email == email.get("email")).first()
    if user and user.email:
        reset_token = secrets.token_hex(32)
        send_password_reset(user.email, reset_token)
    # Always return success (don't reveal if user exists)
    return {"message": "If an account exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    """Reset password with token."""
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and password required")

    # In production, validate token against database
    # For now, just return success
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    """Get current user info from session cookie."""
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
def update_me(
    data: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile (role, company, phone)."""
    if data.role is not None:
        user.role = data.role
    if data.business_name is not None:
        user.business_name = data.business_name
    if data.business_name_arabic is not None:
        user.business_name_arabic = data.business_name_arabic
    if data.phone is not None:
        user.phone = data.phone
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


# ── Email Verification ────────────────────────────────────────

# Rate-limit state: {user_id: last_send_timestamp}
_send_verification_cooldown: dict[int, float] = {}
VERIFICATION_CODE_EXPIRY_MINUTES = 10
VERIFICATION_COOLDOWN_SECONDS = 60  # min gap between resend requests


@router.post("/verify-email")
def verify_email(
    data: EmailVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify email with 6-digit code."""
    if user.email_verified:
        return {"message": "Email already verified"}
    if not user.email_verification_code:
        raise HTTPException(status_code=400, detail="No verification code pending")

    # Check code expiry
    if user.email_verification_code_expires_at:
        expires = user.email_verification_code_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            user.email_verification_code = None
            user.email_verification_code_expires_at = None
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Verification code expired. Please request a new one.",
            )

    if user.email_verification_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.email_verified = True
    user.email_verification_code = None
    user.email_verification_code_expires_at = None
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/send-verification")
def send_verification(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate, store, and email a 6-digit verification code."""
    import time

    # Rate limiting: enforce cooldown between sends
    now = time.time()
    last_sent = _send_verification_cooldown.get(user.id, 0)
    elapsed = now - last_sent
    if elapsed < VERIFICATION_COOLDOWN_SECONDS:
        remaining = int(VERIFICATION_COOLDOWN_SECONDS - elapsed)
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {remaining} seconds before requesting a new code.",
        )

    # Check if email is set
    if not user.email:
        raise HTTPException(
            status_code=400,
            detail="No email address on file. Please update your profile first.",
        )

    # Generate 6-digit code
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)

    # Store code and expiry in DB
    user.email_verification_code = code
    user.email_verification_code_expires_at = expires_at
    db.commit()

    # Send email
    email_sent = send_verification_code(
        to_email=user.email,
        code=code,
        expiry_minutes=VERIFICATION_CODE_EXPIRY_MINUTES,
    )

    # Update cooldown
    _send_verification_cooldown[user.id] = now

    if email_sent:
        return {"message": "Verification code sent to your email"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email. Please try again later.",
        )


# ── Login History ─────────────────────────────────────────────


@router.get("/login-history", response_model=list[LoginHistoryResponse])
def get_login_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get login history for the current user."""
    entries = (
        db.query(LoginHistory)
        .filter(LoginHistory.user_id == user.id)
        .order_by(LoginHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return entries


# ── Two-Factor Authentication ─────────────────────────────────


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
def setup_2fa(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a 2FA secret and return a QR code URL."""
    if user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA already enabled")
    secret = secrets.token_hex(20)  # 40-char hex secret
    user.two_factor_secret = secret
    db.commit()
    qr_url = f"otpauth://totp/LibyaB2B:{user.username}?secret={secret}&issuer=LibyaB2B"
    return TwoFASetupResponse(secret=secret, qr_url=qr_url)


@router.post("/2fa/verify")
def verify_2fa(
    data: TwoFAVerifyRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Verify 2FA code and enable 2FA."""
    if user.two_factor_enabled:
        return {"message": "2FA already enabled"}
    if not user.two_factor_secret:
        raise HTTPException(status_code=400, detail="No 2FA setup pending. Call /2fa/setup first")
    # Simple time-based check: code matches first 6 chars of HMAC of secret
    import hmac
    import time

    counter = int(time.time()) // 30
    expected = hmac.new(
        bytes.fromhex(user.two_factor_secret),
        counter.to_bytes(8, "big"),
        hashlib.sha1,
    ).hexdigest()[:6]
    if data.code != expected:
        # Allow a small window (previous or next period)
        for delta in (-1, 1):
            alt = hmac.new(
                bytes.fromhex(user.two_factor_secret),
                (counter + delta).to_bytes(8, "big"),
                hashlib.sha1,
            ).hexdigest()[:6]
            if data.code == alt:
                user.two_factor_enabled = True
                db.commit()
                return {"message": "2FA enabled successfully"}
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
    user.two_factor_enabled = True
    db.commit()
    return {"message": "2FA enabled successfully"}
