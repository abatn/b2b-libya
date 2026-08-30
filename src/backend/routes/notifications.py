"""
Libya B2B Platform — Push Notification Routes
Subscribe to push, list notifications, mark as read.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from pywebpush import WebPushException, webpush

    _HAS_WEBPUSH = True
except ImportError:
    _HAS_WEBPUSH = False
    WebPushException = Exception

from config import get_db
from models import (
    Notification,
    NotificationResponse,
    PushSubscription,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    User,
)
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# VAPID keys — loaded from files or environment variables
# Generate with: py_vapid --generate (see vapid_keys/ directory)


def _load_vapid_key(filename: str, env_var: str) -> str:
    """Load VAPID key from file first, then environment variable."""
    # Try file in same directory as this module
    module_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(module_dir, filename)
    if os.path.exists(filepath):
        with open(filepath) as f:
            return f.read().strip()
    # Try backend root directory
    backend_dir = os.path.dirname(module_dir)
    filepath = os.path.join(backend_dir, filename)
    if os.path.exists(filepath):
        with open(filepath) as f:
            return f.read().strip()
    return os.environ.get(env_var, "")


VAPID_PRIVATE_KEY = _load_vapid_key("vapid_private.pem", "VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = _load_vapid_key("vapid_public_key.txt", "VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {"sub": "mailto:admin@libyab2b.com"}


def _send_push(subscription: PushSubscription, title: str, body: str, url: str | None = None):
    """Send a push notification to a single subscription."""
    if not _HAS_WEBPUSH or not VAPID_PRIVATE_KEY:
        return  # pywebpush not installed or VAPID not configured — skip push

    try:
        import json  # noqa: E402

        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps({"title": title, "body": body, "url": url or "/"}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS,
        )
        subscription.last_used_at = datetime.now(timezone.utc)
        return True
    except WebPushException:
        # Subscription expired or invalid — deactivate
        subscription.is_active = False
        return False
    except Exception:
        return False


def send_order_notification(user_id: int, order_id: int, status: str, lang: str = "en"):
    """Create + push a notification for order status change."""
    from config import SessionLocal  # noqa: E402

    db = SessionLocal()
    try:
        status_messages = {
            "confirmed": {
                "en": ("Order Confirmed", f"Your order #{order_id} has been confirmed."),
                "ar": ("تم تأكيد الطلب", f"تم تأكيد طلبك رقم #{order_id}."),
            },
            "shipped": {
                "en": ("Order Shipped", f"Your order #{order_id} has been shipped."),
                "ar": ("تم شحن الطلب", f"تم شحن طلبك رقم #{order_id}."),
            },
            "delivered": {
                "en": ("Order Delivered", f"Your order #{order_id} has been delivered."),
                "ar": ("تم توصيل الطلب", f"تم توصيل طلبك رقم #{order_id}."),
            },
            "cancelled": {
                "en": ("Order Cancelled", f"Your order #{order_id} has been cancelled."),
                "ar": ("تم إلغاء الطلب", f"تم إلغاء طلبك رقم #{order_id}."),
            },
        }

        if status not in status_messages:
            return

        en_title, en_body = status_messages[status]["en"]
        ar_title, ar_body = status_messages[status]["ar"]

        # Create in-app notification
        notif = Notification(
            user_id=user_id,
            type="order_status",
            title=en_title,
            title_ar=ar_title,
            body=en_body,
            body_ar=ar_body,
            url=f"/tracking?order={order_id}",
            related_id=order_id,
        )
        db.add(notif)
        db.flush()

        # Send push to all active subscriptions
        subs = (
            db.query(PushSubscription)
            .filter(PushSubscription.user_id == user_id, PushSubscription.is_active)
            .all()
        )

        title = ar_title if lang == "ar" else en_title
        body = ar_body if lang == "ar" else en_body

        for sub in subs:
            if _send_push(sub, title, body, f"/tracking?order={order_id}"):
                notif.is_pushed = True

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


# ── Endpoints ──────────────────────────────────────────────


@router.get("/vapid-public-key")
def get_vapid_public_key():
    """Return the VAPID public key for the frontend to use when subscribing."""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Push notifications not configured")
    return {"publicKey": VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=PushSubscriptionResponse)
def subscribe(
    data: PushSubscriptionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a push subscription for the current user."""
    # Check if endpoint already exists
    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == data.endpoint).first()
    if existing:
        existing.user_id = user.id
        existing.is_active = True
        existing.last_used_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    sub = PushSubscription(
        user_id=user.id,
        endpoint=data.endpoint,
        p256dh=data.p256dh,
        auth=data.auth,
        user_agent=data.user_agent,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/subscribe")
def unsubscribe(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deactivate all push subscriptions for the current user."""
    count = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user.id, PushSubscription.is_active)
        .update({"is_active": False})
    )
    db.commit()
    return {"message": f"Deactivated {count} subscription(s)"}


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notifications for the current user."""
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(not Notification.is_read)
    return q.order_by(Notification.created_at.desc()).limit(limit).all()


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get count of unread notifications."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, not Notification.is_read)
        .count()
    )
    return {"count": count}


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.post("/read-all")
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, not Notification.is_read)
        .update({"is_read": True})
    )
    db.commit()
    return {"message": f"Marked {count} notification(s) as read"}
