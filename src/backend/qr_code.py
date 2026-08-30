"""
Libya B2B Platform - QR-Code Module
Sprint 2: QR-Code-Generierung und Scan-Funktion
Projektversion: v1.2
"""

import base64
import hashlib
import io
from datetime import datetime
from typing import Optional

import qrcode
import qrcode.constants
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

# ============================================================
# QR-CODE GENERATION
# ============================================================


def generate_order_qr_code(
    order_number: str,
    total_amount: float,
    currency: str = "LYD",
    delivery_address: Optional[str] = None,
) -> str:
    """
    QR-Code fuer eine Bestellung generieren.

    Enthaelt:
    - Bestellnummer
    - Betrag
    - Waehrung
    - Lieferadresse
    - Timestamp (Hash)

    Args:
        order_number: Einzigartige Bestellnummer
        total_amount: Gesamtbetrag
        currency: Waehrung (Standard: LYD)
        delivery_address: Lieferadresse (optional)

    Returns:
        Base64-kodiertes QR-Code-Bild
    """

    # QR-Code-Daten zusammenstellen
    timestamp_hash = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]

    qr_data = {
        "platform": "LIBYA_B2B",
        "version": "1.0",
        "order": order_number,
        "amount": total_amount,
        "currency": currency,
        "address": delivery_address or "N/A",
        "hash": timestamp_hash,
        "timestamp": datetime.now().isoformat(),
    }

    # QR-Code als String
    qr_string = "|".join([f"{k}:{v}" for k, v in qr_data.items()])

    # QR-Code erstellen
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)

    # Bild generieren (mit abgerundeten Ecken)
    try:
        img = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
    except Exception:
        # Fallback ohne speziellen Stil
        img = qr.make_image(fill_color="black", back_color="white")

    # In Base64 konvertieren
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return img_base64


def generate_delivery_qr_code(
    order_number: str,
    delivery_photo_url: Optional[str] = None,
    gps_lat: Optional[float] = None,
    gps_lon: Optional[float] = None,
) -> str:
    """
    QR-Code fuer Lieferungsverifikation generieren.

    Enthaelt:
    - Bestellnummer
    - Foto-URL
    - GPS-Koordinaten
    - Lieferzeitpunkt
    """

    qr_data = {
        "type": "DELIVERY_VERIFICATION",
        "order": order_number,
        "photo": delivery_photo_url or "N/A",
        "lat": str(gps_lat) if gps_lat else "N/A",
        "lon": str(gps_lon) if gps_lon else "N/A",
        "delivered_at": datetime.now().isoformat(),
    }

    qr_string = "|".join([f"{k}:{v}" for k, v in qr_data.items()])

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="green", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return img_base64


# ============================================================
# QR-CODE PARSING
# ============================================================


def parse_qr_code(qr_string: str) -> dict:
    """
    QR-Code-String parsen.

    Args:
        qr_string: QR-Code-Inhalt als String

    Returns:
        Dictionary mit geparsten Daten
    """

    result = {}

    try:
        # Format: "LIBYA_B2B|key:value|key:value|..."
        pairs = qr_string.split("|")

        # Erstes Element ist die Platform
        if pairs:
            result["platform"] = pairs[0]

        # Restliche Elemente sind key:value Paare
        for pair in pairs[1:]:
            if ":" in pair:
                key, value = pair.split(":", 1)
                result[key.strip()] = value.strip()
        for pair in pairs:
            if ":" in pair:
                key, value = pair.split(":", 1)
                result[key.strip()] = value.strip()
    except Exception as e:
        result["error"] = str(e)

    return result


def validate_order_qr_code(qr_data: dict) -> bool:
    """
    QR-Code fuer Bestellung validieren.

    Prueft:
    - Platform ist "LIBYA_B2B"
    - Bestellnummer vorhanden
    - Betrag positiv
    """

    required_fields = ["platform", "order", "amount", "currency"]

    # Pflichtfelder pruefen
    for field in required_fields:
        if field not in qr_data:
            return False

    # Platform pruefen
    if qr_data.get("platform") != "LIBYA_B2B":
        return False

    # Betrag pruefen
    try:
        amount = float(qr_data.get("amount", 0))
        if amount <= 0:
            return False
    except ValueError:
        return False

    return True


# ============================================================
# QR-CODE VERIFIKATION
# ============================================================


def verify_delivery(qr_data: dict, expected_order: str, tolerance_meters: float = 100.0) -> dict:
    """
    Lieferung anhand von QR-Code-Daten verifizieren.

    Args:
        qr_data: Geparste QR-Code-Daten
        expected_order: Erwartete Bestellnummer
        tolerance_meters: GPS-Toleranz in Metern

    Returns:
        Verifikationsergebnis
    """

    result = {
        "verified": False,
        "order_match": False,
        "has_photo": False,
        "has_gps": False,
        "timestamp_valid": False,
        "errors": [],
    }

    # Bestellnummer pruefen
    if qr_data.get("order") == expected_order:
        result["order_match"] = True
    else:
        result["errors"].append(
            f"Bestellnummer stimmt nicht ueberein: {qr_data.get('order')} vs {expected_order}"
        )

    # Foto pruefen
    if qr_data.get("photo") and qr_data.get("photo") != "N/A":
        result["has_photo"] = True
    else:
        result["errors"].append("Kein Lieferfoto vorhanden")

    # GPS pruefen
    if (
        "lat" in qr_data
        and "lon" in qr_data
        and qr_data.get("lat") != "N/A"
        and qr_data.get("lon") != "N/A"
    ):
        result["has_gps"] = True
    else:
        result["errors"].append("Keine GPS-Koordinaten vorhanden")

    # Zeitstempel pruefen
    if qr_data.get("delivered_at"):
        try:
            delivered_at = datetime.fromisoformat(qr_data["delivered_at"])
            if delivered_at <= datetime.now():
                result["timestamp_valid"] = True
            else:
                result["errors"].append("Lieferzeitpunkt in der Zukunft")
        except ValueError:
            result["errors"].append("Ungueltiger Zeitstempel")

    # Gesamtergebnis
    if (
        result["order_match"]
        and result["has_photo"]
        and result["has_gps"]
        and result["timestamp_valid"]
    ):
        result["verified"] = True

    return result


# ============================================================
# HILFSFUNKTIONEN
# ============================================================


def get_qr_code_as_bytes(order_number: str, total_amount: float) -> bytes:
    """QR-Code als Bytes zurueckgeben (fuer Download)"""

    qr_string = f"LIBYA_B2B|order:{order_number}|amount:{total_amount}|currency:LYD"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    return buffer.getvalue()


def calculate_qr_code_hash(order_number: str) -> str:
    """Eindeutigen Hash fuer QR-Code berechnen"""

    data = f"LIBYA_B2B_{order_number}_{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]
