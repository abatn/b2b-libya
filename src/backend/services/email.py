"""
Libya B2B Platform - Email Service
Sends verification codes via SMTP. No paid dependencies (uses stdlib smtplib).
Falls back to console logging when SMTP is not configured.

Env vars:
    SMTP_HOST     - SMTP server hostname (e.g. smtp.gmail.com)
    SMTP_PORT     - SMTP server port (default: 587)
    SMTP_USERNAME - SMTP auth username
    SMTP_PASSWORD - SMTP auth password
    SMTP_FROM     - Sender email address
    SMTP_USE_TLS  - Use STARTTLS (default: true)
"""

import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


def is_smtp_configured() -> bool:
    """Check if SMTP credentials are available."""
    return bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)


# ── Email Templates ───────────────────────────────────────────

VERIFICATION_CODE_SUBJECT = "Libya B2B — Your Verification Code"

VERIFICATION_CODE_BODY_HTML = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f5f7fa;font-family:sans-serif;">
    <div style="max-width:480px;margin:40px auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">  # noqa: E501
        <div style="background:#1a1a2e;padding:30px;text-align:center;">
            <h1 style="color:#ff6a00;margin:0;font-size:1.6rem;">Libya B2B</h1>
        </div>
        <div style="padding:35px 30px;text-align:center;">
            <div style="font-size:3rem;margin-bottom:15px;">✉️</div>
            <h2 style="color:#1a1a2e;margin-bottom:10px;">Email Verification</h2>
            <p style="color:#888;margin-bottom:25px;line-height:1.6;">
                Use the following 6-digit code to verify your email.
                This code expires in <strong>{expiry_minutes} minutes</strong>.
            </p>
            <div style="background:#f8f9fa;border:2px dashed #e8e8e8;border-radius:8px;padding:20px;margin-bottom:25px;">  # noqa: E501
                <span style="font-size:2.5rem;font-weight:bold;color:#1a1a2e;letter-spacing:12px;">{code}</span>  # noqa: E501
            </div>
            <p style="color:#888;font-size:0.85rem;">
                If you did not request this code, please ignore this email.
            </p>
        </div>
        <div style="background:#f8f9fa;padding:20px 30px;text-align:center;border-top:1px solid #e8e8e8;">  # noqa: E501
            <p style="color:#888;font-size:0.75rem;margin:0;">
                © 2026 Libya B2B Platform. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""

VERIFICATION_CODE_BODY_TEXT = """\
Libya B2B — Email Verification
================================

Your verification code is: {code}

This code expires in {expiry_minutes} minutes.

If you did not request this code, please ignore this email.

© 2026 Libya B2B Platform
"""


# ── Core Sending Function ─────────────────────────────────────


def _send_smtp(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not is_smtp_configured():
        logger.warning("SMTP not configured — cannot send email to %s", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USE_TLS:
                server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        logger.info("Email sent to %s — subject: %s", to_email, subject)
        return True
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", to_email, exc)
        return False
    except OSError as exc:
        logger.error("Network error sending to %s: %s", to_email, exc)
        return False


# ── Public API ────────────────────────────────────────────────


def send_verification_code(
    to_email: str,
    code: str,
    expiry_minutes: int = 10,
) -> bool:
    """Send a 6-digit verification code email.

    Returns True if the email was sent successfully (or SMTP is
    not configured and the code was logged to console).
    """
    subject = VERIFICATION_CODE_SUBJECT

    body_text = VERIFICATION_CODE_BODY_TEXT.format(
        code=code,
        expiry_minutes=expiry_minutes,
    )
    body_html = VERIFICATION_CODE_BODY_HTML.format(
        code=code,
        expiry_minutes=expiry_minutes,
    )

    if is_smtp_configured():
        return _send_smtp(to_email, subject, body_text, body_html)

    # Fallback: log code to console (development / demo mode)
    logger.info(
        "DEV MODE — Verification code for %s: %s (expires in %dm)",
        to_email,
        code,
        expiry_minutes,
    )
    print(f"\n{'=' * 50}")
    print(f"  Verification code for {to_email}: {code}")
    print(f"  Expires in {expiry_minutes} minutes")
    print(f"{'=' * 50}\n")
    return True


def send_password_reset(
    to_email: str,
    reset_token: str,
    base_url: str = "http://localhost:3000",
) -> bool:
    """Send a password reset link email."""
    reset_url = f"{base_url}/reset-password?token={reset_token}"
    subject = "Libya B2B — Password Reset Request"

    body_text = (
        f"Libya B2B — Password Reset\n"
        f"{'=' * 40}\n\n"
        f"Click the link below to reset your password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in 1 hour.\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"© 2026 Libya B2B Platform"
    )
    body_html = (
        f"<!DOCTYPE html><html><body style='font-family:sans-serif;padding:40px;'>"
        f"<h2 style='color:#1a1a2e;'>Password Reset</h2>"
        f"<p>Click the button below to reset your password:</p>"
        f"<a href='{reset_url}' style='display:inline-block;padding:12px 24px;"
        f"background:#ff6a00;color:white;text-decoration:none;border-radius:8px;"
        f"font-weight:bold;'>Reset Password</a>"
        f"<p style='color:#888;font-size:0.85rem;margin-top:20px;'>"
        f"This link expires in 1 hour. If you did not request this, ignore this email.</p>"
        f"</body></html>"
    )

    if is_smtp_configured():
        return _send_smtp(to_email, subject, body_text, body_html)

    logger.info("DEV MODE — Password reset for %s: %s", to_email, reset_url)
    print(f"\n{'=' * 50}")
    print(f"  Password reset for {to_email}: {reset_url}")
    print(f"{'=' * 50}\n")
    return True
