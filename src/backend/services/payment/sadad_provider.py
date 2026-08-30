"""
Libya B2B Platform - SADAD Payment Provider
Integration with SADAD (Almadar Aljadid) payment gateway.

API Documentation: developer.sadad.qa
"""

import hashlib
import hmac
import os
import uuid
from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus


class SadadProvider(PaymentProvider):
    """
    SADAD payment provider (Almadar Aljadid).

    Requires:
    - SADAD_MERCHANT_ID: Merchant ID from SADAD
    - SADAD_SECRET_KEY: Secret key for HMAC signing
    - SADAD_API_URL: API endpoint (sandbox or production)

    API Docs: developer.sadad.qa
    """

    def __init__(self):
        self._merchant_id = os.getenv("SADAD_MERCHANT_ID", "")
        self._secret_key = os.getenv("SADAD_SECRET_KEY", "")
        self._api_url = os.getenv("SADAD_API_URL", "https://sandbox.sadad.qa/v1")
        self._transactions: dict[str, PaymentResult] = {}

    @property
    def name(self) -> str:
        return "sadad"

    @property
    def display_name(self) -> str:
        return "SADAD Payment"

    @property
    def is_available(self) -> bool:
        return bool(self._merchant_id and self._secret_key)

    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature for SADAD API."""
        return hmac.new(self._secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str = "LYD",
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        """
        Create SADAD payment.

        SADAD API flow:
        1. Generate signature
        2. Send create-payment request
        3. Receive payment URL for user redirect
        """
        if not self.is_available:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message="SADAD not configured (missing merchant ID or secret key)",
                provider=self.name,
                amount=amount,
                currency=currency,
            )

        try:
            # Generate unique invoice number
            invoice_number = f"INV-{order_id}-{uuid.uuid4().hex[:8].upper()}"

            # Prepare request payload
            payload = {
                "merchantId": self._merchant_id,
                "invoiceNumber": invoice_number,
                "amount": str(amount),
                "currency": currency,
                "description": description or f"Order #{order_id}",
                "callbackUrl": metadata.get("callback_url", "") if metadata else "",
            }

            # Generate signature
            signature_payload = f"{self._merchant_id}{invoice_number}{amount}"
            signature = self._generate_signature(signature_payload)
            payload["signature"] = signature

            # TODO: Uncomment when SADAD API access is obtained
            # response = httpx.post(
            #     f"{self._api_url}/payment/create",
            #     json=payload,
            #     timeout=30
            # )
            # if response.status_code == 200:
            #     data = response.json()
            #     transaction_id = data.get("paymentId")
            #     payment_url = data.get("paymentUrl")
            #
            #     result = PaymentResult(
            #         success=True,
            #         transaction_id=transaction_id,
            #         status=PaymentStatus.PENDING,
            #         message="SADAD payment created",
            #         provider=self.name,
            #         amount=amount,
            #         currency=currency,
            #         metadata={
            #             "invoice_number": invoice_number,
            #             "payment_url": payment_url,
            #         },
            #     )
            #     self._transactions[transaction_id] = result
            #     return result

            # Mock response for development
            transaction_id = f"SADAD-{uuid.uuid4().hex[:12].upper()}"
            result = PaymentResult(
                success=True,
                transaction_id=transaction_id,
                status=PaymentStatus.PENDING,
                message="SADAD payment created (sandbox mode)",
                provider=self.name,
                amount=amount,
                currency=currency,
                metadata={
                    "invoice_number": invoice_number,
                    "sandbox": True,
                },
            )
            self._transactions[transaction_id] = result
            return result

        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=f"SADAD error: {str(e)}",
                provider=self.name,
                amount=amount,
                currency=currency,
            )

    def verify_payment(self, transaction_id: str) -> PaymentResult:
        """Verify SADAD payment status."""
        if transaction_id in self._transactions:
            return self._transactions[transaction_id]

        return PaymentResult(
            success=False,
            transaction_id=transaction_id,
            status=PaymentStatus.FAILED,
            message="Transaction not found",
            provider=self.name,
        )

    def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> PaymentResult:
        """Refund SADAD payment."""
        # TODO: Implement SADAD refund API when access is obtained
        return PaymentResult(
            success=False,
            transaction_id=transaction_id,
            status=PaymentStatus.FAILED,
            message="SADAD refund not yet implemented",
            provider=self.name,
        )

    def get_payment_url(self, transaction_id: str) -> Optional[str]:
        """Get SADAD payment URL for user redirect."""
        if transaction_id in self._transactions:
            return self._transactions[transaction_id].metadata.get("payment_url")
        return None
