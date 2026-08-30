"""
Libya B2B Platform - Payment SDK Base Classes
Provider-Abstraktion für libysche Zahlungsmethoden
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    """Payment status states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


@dataclass
class PaymentResult:
    """Unified payment result from any provider."""

    success: bool
    transaction_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    message: str = ""
    provider: str = ""
    amount: float = 0.0
    currency: str = "LYD"
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "success": self.success,
            "transaction_id": self.transaction_id,
            "status": self.status.value,
            "message": self.message,
            "provider": self.provider,
            "amount": self.amount,
            "currency": self.currency,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class PaymentProvider(ABC):
    """
    Abstract base class for all payment providers.

    Each provider (SADAD, Fawry, Moamalat, etc.) must implement
    these methods to ensure consistent behavior across all
    payment methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'sadad', 'fawry', 'moamalat')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'SADAD Payment')."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API keys configured)."""
        pass

    @abstractmethod
    def create_payment(
        self,
        order_id: int,
        amount: float,
        currency: str = "LYD",
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        """
        Create a new payment transaction.

        Args:
            order_id: Internal order ID
            amount: Payment amount
            currency: Currency code (default: LYD)
            description: Payment description
            metadata: Additional data for provider

        Returns:
            PaymentResult with transaction details
        """
        pass

    @abstractmethod
    def verify_payment(self, transaction_id: str) -> PaymentResult:
        """
        Verify payment status by transaction ID.

        Args:
            transaction_id: Provider's transaction ID

        Returns:
            PaymentResult with current status
        """
        pass

    @abstractmethod
    def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> PaymentResult:
        """
        Refund a payment (full or partial).

        Args:
            transaction_id: Original transaction ID
            amount: Refund amount (None = full refund)
            reason: Refund reason

        Returns:
            PaymentResult with refund details
        """
        pass

    def get_payment_url(self, transaction_id: str) -> Optional[str]:
        """
        Get payment URL for redirect (optional).

        Some providers require user redirect to complete payment.
        Returns None if not applicable.
        """
        return None

    def supports_webhook(self) -> bool:
        """Check if provider supports webhooks for async notifications."""
        return False

    def process_webhook(self, payload: dict) -> Optional[PaymentResult]:
        """
        Process incoming webhook from provider.

        Args:
            payload: Webhook payload from provider

        Returns:
            PaymentResult if valid webhook, None otherwise
        """
        return None
