"""
Libya B2B Platform - Auth Service
Password hashing and session management helpers.

v6.0: bcrypt for new passwords, SHA-256 backward compatibility.
"""

import hashlib
import secrets

try:
    import bcrypt as _bcrypt

    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False


def hash_password(password: str) -> str:
    """Hash password with bcrypt (new standard).
    Falls back to SHA-256 if bcrypt is unavailable.
    """
    if _HAS_BCRYPT:
        return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash.
    Supports both bcrypt (new) and SHA-256 (legacy) hashes.
    """
    if not password_hash:
        return False
    if _HAS_BCRYPT and password_hash.startswith("$2"):
        return _bcrypt.checkpw(password.encode(), password_hash.encode())
    # Legacy SHA-256 fallback
    return hashlib.sha256(password.encode()).hexdigest() == password_hash


def generate_session_token() -> str:
    return secrets.token_hex(64)
