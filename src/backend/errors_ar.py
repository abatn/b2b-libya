"""
Libya B2B Platform - Arabische Fehlermeldungen
Sprint 6: Arabische Lokalisierung
Projektversion: v1.6
"""

from typing import Dict

# ============================================================
# ARABISCHE FEHLERMELDUNGEN
# ============================================================

ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    # Produkt-Fehler
    "product_not_found": {
        "en": "Product not found",
        "ar": "المنتج غير موجود",
        "code": "ERR_PRODUCT_001",
    },
    "product_inactive": {
        "en": "Product is inactive",
        "ar": "المنتج غير نشط",
        "code": "ERR_PRODUCT_002",
    },
    "product_out_of_stock": {
        "en": "Product is out of stock",
        "ar": "المنتج غير متوفر في المخزون",
        "code": "ERR_PRODUCT_003",
    },
    "product_price_invalid": {
        "en": "Invalid price",
        "ar": "سعر غير صالح",
        "code": "ERR_PRODUCT_004",
    },
    # Bestellungs-Fehler
    "order_not_found": {"en": "Order not found", "ar": "الطلب غير موجود", "code": "ERR_ORDER_001"},
    "order_already_delivered": {
        "en": "Order already delivered",
        "ar": "تم التوصيل بالفعل",
        "code": "ERR_ORDER_002",
    },
    "order_already_cancelled": {
        "en": "Order already cancelled",
        "ar": "تم إلغاء الطلب بالفعل",
        "code": "ERR_ORDER_003",
    },
    "order_amount_invalid": {
        "en": "Invalid order amount",
        "ar": "مبلغ الطلب غير صالح",
        "code": "ERR_ORDER_004",
    },
    # QR-Code-Fehler
    "qr_code_invalid": {"en": "Invalid QR code", "ar": "رمز QR غير صالح", "code": "ERR_QR_001"},
    "qr_code_expired": {"en": "QR code expired", "ar": "انتهت صلاحية رمز QR", "code": "ERR_QR_002"},
    "qr_code_already_scanned": {
        "en": "QR code already scanned",
        "ar": "تم مسح رمز QR بالفعل",
        "code": "ERR_QR_003",
    },
    # Chatbot-Fehler
    "chat_session_not_found": {
        "en": "Chat session not found",
        "ar": "جلسة المحادثة غير موجودة",
        "code": "ERR_CHAT_001",
    },
    "chat_message_too_long": {
        "en": "Message too long",
        "ar": "الرسالة طويلة جداً",
        "code": "ERR_CHAT_002",
    },
    "chat_intent_not_recognized": {
        "en": "Intent not recognized",
        "ar": "لم يتم التعرف على النية",
        "code": "ERR_CHAT_003",
    },
    # Sync-Fehler
    "sync_failed": {"en": "Synchronization failed", "ar": "فشلت المزامنة", "code": "ERR_SYNC_001"},
    "sync_checksum_mismatch": {
        "en": "Checksum mismatch - data modified",
        "ar": "عدم تطابق التحقق - تم تعديل البيانات",
        "code": "ERR_SYNC_002",
    },
    "sync_max_retries": {
        "en": "Max retries exceeded",
        "ar": "تم تجاوز الحد الأقصى للمحاولات",
        "code": "ERR_SYNC_003",
    },
    # Allgemeine Fehler
    "unauthorized": {"en": "Unauthorized", "ar": "غير مصرح", "code": "ERR_AUTH_001"},
    "forbidden": {"en": "Forbidden", "ar": "محظور", "code": "ERR_AUTH_002"},
    "internal_error": {
        "en": "Internal server error",
        "ar": "خطأ داخلي في الخادم",
        "code": "ERR_SERVER_001",
    },
    "validation_error": {
        "en": "Validation error",
        "ar": "خطأ في التحقق",
        "code": "ERR_VALIDATION_001",
    },
    "rate_limit_exceeded": {
        "en": "Rate limit exceeded",
        "ar": "تم تجاوز حد الطلبات",
        "code": "ERR_RATE_001",
    },
}

# ============================================================
# ARABISCHE ERFOLGSMELDUNGEN
# ============================================================

SUCCESS_MESSAGES: Dict[str, Dict[str, str]] = {
    "product_created": {
        "en": "Product created successfully",
        "ar": "تم إنشاء المنتج بنجاح",
        "code": "SUCCESS_PRODUCT_001",
    },
    "product_updated": {
        "en": "Product updated successfully",
        "ar": "تم تحديث المنتج بنجاح",
        "code": "SUCCESS_PRODUCT_002",
    },
    "product_deleted": {
        "en": "Product deleted successfully",
        "ar": "تم حذف المنتج بنجاح",
        "code": "SUCCESS_PRODUCT_003",
    },
    "order_created": {
        "en": "Order created successfully",
        "ar": "تم إنشاء الطلب بنجاح",
        "code": "SUCCESS_ORDER_001",
    },
    "order_delivered": {
        "en": "Order delivered successfully",
        "ar": "تم التوصيل بنجاح",
        "code": "SUCCESS_ORDER_002",
    },
    "qr_code_generated": {
        "en": "QR code generated successfully",
        "ar": "تم إنشاء رمز QR بنجاح",
        "code": "SUCCESS_QR_001",
    },
    "sync_completed": {
        "en": "Synchronization completed",
        "ar": "اكتملت المزامنة",
        "code": "SUCCESS_SYNC_001",
    },
    "chat_message_sent": {
        "en": "Message sent successfully",
        "ar": "تم إرسال الرسالة بنجاح",
        "code": "SUCCESS_CHAT_001",
    },
}

# ============================================================
# HILFSFUNKTIONEN
# ============================================================


def get_error_message(error_key: str, language: str = "ar") -> str:
    """
    Fehlermeldung abrufen.

    Args:
        error_key: Schlüssel der Fehlermeldung
        language: Sprache (en/ar)

    Returns:
        Fehlermeldung in der gewünschten Sprache
    """
    if error_key in ERROR_MESSAGES:
        return ERROR_MESSAGES[error_key].get(language, ERROR_MESSAGES[error_key]["en"])
    return "Unbekannter Fehler" if language == "ar" else "Unknown error"


def get_error_code(error_key: str) -> str:
    """Fehlercode abrufen"""
    if error_key in ERROR_MESSAGES:
        return ERROR_MESSAGES[error_key].get("code", "ERR_UNKNOWN")
    return "ERR_UNKNOWN"


def get_success_message(success_key: str, language: str = "ar") -> str:
    """Erfolgsmeldung abrufen"""
    if success_key in SUCCESS_MESSAGES:
        return SUCCESS_MESSAGES[success_key].get(language, SUCCESS_MESSAGES[success_key]["en"])
    return "تم بنجاح" if language == "ar" else "Success"


def get_all_errors(language: str = "ar") -> Dict[str, str]:
    """Alle Fehlermeldungen in einer Sprache abrufen"""
    return {key: msgs.get(language, msgs["en"]) for key, msgs in ERROR_MESSAGES.items()}


def get_all_success(language: str = "ar") -> Dict[str, str]:
    """Alle Erfolgsmeldungen in einer Sprache abrufen"""
    return {key: msgs.get(language, msgs["en"]) for key, msgs in SUCCESS_MESSAGES.items()}
