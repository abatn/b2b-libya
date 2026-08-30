"""
Libya B2B Platform - Payment Service
High-level service integrating Payment SDK with business logic.
"""

from typing import Optional

from .base import PaymentResult
from .gateway import PaymentGateway, get_payment_gateway


def generate_invoice_text(order: dict) -> str:
    """Generate a plain-text invoice for an order."""
    lines = [
        "=" * 50,
        "  LIBYA B2B PLATFORM - INVOICE",
        "=" * 50,
        "",
        f"  Order Number:  {order.get('order_number', 'N/A')}",
        f"  Date:          {order.get('date', 'N/A')}",
        f"  Payment:       {order.get('payment_method', 'COD')}",
        f"  Status:        {order.get('status', 'pending')}",
        "",
        "-" * 50,
        "  ITEMS",
        "-" * 50,
    ]
    for item in order.get("items", []):
        name = item.get("name", "Item")
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        lines.append(f"  {name:<30} {qty:>5} x {price:>10.2f} LYD")
    lines.append("-" * 50)
    lines.append(f"  {'TOTAL:':<35} {order.get('total_amount', 0):>15.2f} LYD")
    lines.append("=" * 50)
    lines.append("")
    lines.append("  Thank you for your order!")
    lines.append("  Libya B2B Platform | Alibaba Model")
    lines.append("=" * 50)
    return "\n".join(lines)


def generate_invoice_base64(order: dict) -> str:
    """Return the invoice as a base64-encoded UTF-8 string for download."""
    import base64

    text = generate_invoice_text(order)
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class PaymentService:
    """
    High-level payment service.

    Integrates PaymentGateway with business logic.
    """

    def __init__(self, gateway: Optional[PaymentGateway] = None):
        self.gateway = gateway or get_payment_gateway()

    def process_payment(
        self,
        order_id: int,
        amount: float,
        method: str = "cod",
        currency: str = "LYD",
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        """
        Process payment for an order.

        Args:
            order_id: Internal order ID
            amount: Payment amount
            method: Payment method
            currency: Currency code
            description: Payment description
            metadata: Additional data

        Returns:
            PaymentResult with transaction details
        """
        return self.gateway.pay(
            order_id=order_id,
            amount=amount,
            method=method,
            currency=currency,
            description=description,
            metadata=metadata,
        )

    def get_payment_status(
        self,
        provider: str,
        transaction_id: str,
    ) -> PaymentResult:
        """Check payment status."""
        return self.gateway.verify(provider, transaction_id)

    def refund_payment(
        self,
        provider: str,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> PaymentResult:
        """Process refund."""
        return self.gateway.refund(
            provider_name=provider,
            transaction_id=transaction_id,
            amount=amount,
            reason=reason,
        )

    def get_available_methods(self) -> list[dict]:
        """Get list of available payment methods."""
        methods = [
            {
                "id": "cod",
                "name": "Cash on Delivery",
                "name_ar": "الدفع عند الاستلام",
                "available": True,
                "description": "Pay when you receive your order",
                "description_ar": "ادفع عندما تتلقى طلبك",
            },
        ]

        # Add configured providers
        for provider_info in self.gateway.list_providers():
            if provider_info["name"] != "mock":
                methods.append(
                    {
                        "id": provider_info["name"],
                        "name": provider_info["display_name"],
                        "name_ar": self._get_arabic_name(provider_info["name"]),
                        "available": provider_info["is_available"],
                        "description": f"Pay via {provider_info['display_name']}",
                        "description_ar": self._get_arabic_description(provider_info["name"]),
                    }
                )

        return methods

    def _get_arabic_name(self, provider: str) -> str:
        """Get Arabic name for payment method."""
        names = {
            "sadad": "سداد",
            "fawry": "فوري",
            "moamalat": "المؤملات",
            "cod": "الدفع عند الاستلام",
        }
        return names.get(provider, provider)

    def _get_arabic_description(self, provider: str) -> str:
        """Get Arabic description for payment method."""
        descriptions = {
            "sadad": "ادفع عبر سداد",
            "fawry": "ادفع عبر فوري",
            "moamalat": "ادفع ببطاقة بنكية",
            "cod": "ادفع عندما تتلقى طلبك",
        }
        return descriptions.get(provider, f"ادفع عبر {provider}")
