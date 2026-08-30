"""
Libya B2B Platform - Fawry Payment Provider
Integration with Fawry for E-Payment Services.

API Documentation: developer.fawry.com
"""

import os
import uuid
from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus


class FawryProvider(PaymentProvider):
    """
    Fawry payment provider.

    Requires:
    - FAWRY_MERCHANT_ID: Merchant ID from Fawry
    - FAWRY_API_KEY: API key for authentication
    - FAWRY_API_URL: API endpoint (sandbox or production)

    API Docs: developer.fawry.com
    """

    def __init__(self):
        self._merchant_id = os.getenv("FAWRY_MERCHANT_ID", "")
        self._api_key = os.getenv("FAWRY_API_KEY", "")
        self._api_url = os.getenv("FAWRY_API_URL", "https://sandbox.fawry.com/api/v2")
        self._transactions: dict[str, PaymentResult] = {}

    @property
    def name(self) -> str:
        return "fawry"

    @property
    def display_name(self) -> str:
        return "Fawry E-Payment"

    @property
    def is_available(self) -> bool:
        return bool(self._merchant_id and self._api_key)

    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str = "LYD",
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        """
        Create Fawry payment.

        Fawry API flow:
        1. Create charge request
        2. Receive payment URL or reference number
        3. User pays via Fawry app or kiosk
        """
        if not self.is_available:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message="Fawry not configured (missing merchant ID or API key)",
                provider=self.name,
                amount=amount,
                currency=currency,
            )

        try:
            # Generate unique reference
            reference_number = f"FAW-{order_id}-{uuid.uuid4().hex[:8].upper()}"

            # Prepare request payload
            {
                "merchantId": self._merchant_id,
                "apiKey": self._api_key,
                "referenceNumber": reference_number,
                "amount": amount,
                "currency": currency,
                "description": description or f"Order #{order_id}",
                "callbackUrl": metadata.get("callback_url", "") if metadata else "",
            }

            # TODO: Uncomment when Fawry API access is obtained
            # response = httpx.post(
            #     f"{self._api_url}/charge",
            #     json=payload,
            #     timeout=30
            # )
            # if response.status_code == 200:
            #     data = response.json()
            #     transaction_id = data.get("chargeId")
            #     payment_url = data.get("paymentUrl")
            #
            #     result = PaymentResult(
            #         success=True,
            #         transaction_id=transaction_id,
            #         status=PaymentStatus.PENDING,
            #         message="Fawry charge created",
            #         provider=self.name,
            #         amount=amount,
            #         currency=currency,
            #         metadata={
            #             "reference_number": reference_number,
            #             "payment_url": payment_url,
            #         },
            #     )
            #     self._transactions[transaction_id] = result
            #     return result

            # Mock response for development
            transaction_id = f"FAWRY-{uuid.uuid4().hex[:12].upper()}"
            result = PaymentResult(
                success=True,
                transaction_id=transaction_id,
                status=PaymentStatus.PENDING,
                message="Fawry payment created (sandbox mode)",
                provider=self.name,
                amount=amount,
                currency=currency,
                metadata={
                    "reference_number": reference_number,
                    "sandbox": True,
                },
            )
            self._transactions[transaction_id] = result
            return result

        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=f"Fawry error: {str(e)}",
                provider=self.name,
                amount=amount,
                currency=currency,
            )

    def verify_payment(self, transaction_id: str) -> PaymentResult:
        """Verify Fawry payment status."""
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
        """Refund Fawry payment."""
        # TODO: Implement Fawry refund API when access is obtained
        return PaymentResult(
            success=False,
            transaction_id=transaction_id,
            status=PaymentStatus.FAILED,
            message="Fawry refund not yet implemented",
            provider=self.name,
        )
