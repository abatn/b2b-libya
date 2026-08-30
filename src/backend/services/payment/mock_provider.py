"""
Libya B2B Platform - Mock Payment Provider
For testing and development without real API access.
"""

import uuid
from datetime import datetime
from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus


class MockProvider(PaymentProvider):
    """
    Mock payment provider for testing.

    Simulates payment flow without real API calls.
    Use in development/testing environments.
    """

    def __init__(self):
        self._transactions: dict[str, PaymentResult] = {}

    @property
    def name(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Mock Payment (Testing)"

    @property
    def is_available(self) -> bool:
        return True

    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str = "LYD",
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        """Create mock payment - always succeeds."""
        transaction_id = f"MOCK-{uuid.uuid4().hex[:12].upper()}"

        result = PaymentResult(
            success=True,
            transaction_id=transaction_id,
            status=PaymentStatus.COMPLETED,
            message="Mock payment completed successfully",
            provider=self.name,
            amount=amount,
            currency=currency,
            created_at=datetime.utcnow(),
            metadata={
                "order_id": order_id,
                "description": description,
                **(metadata or {}),
            },
        )

        self._transactions[transaction_id] = result
        return result

    def verify_payment(self, transaction_id: str) -> PaymentResult:
        """Verify mock payment - always returns completed."""
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
        """Refund mock payment - always succeeds."""
        if transaction_id not in self._transactions:
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                message="Transaction not found for refund",
                provider=self.name,
            )

        original = self._transactions[transaction_id]
        refund_amount = amount or original.amount

        result = PaymentResult(
            success=True,
            transaction_id=f"REFUND-{uuid.uuid4().hex[:12].upper()}",
            status=PaymentStatus.REFUNDED,
            message=f"Mock refund of {refund_amount} {original.currency}",
            provider=self.name,
            amount=refund_amount,
            currency=original.currency,
            metadata={
                "original_transaction": transaction_id,
                "reason": reason,
            },
        )

        # Update original transaction status
        original.status = PaymentStatus.REFUNDED
        return result
