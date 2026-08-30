"""
Libya B2B Platform - Payment Gateway Manager
Unified interface for all payment providers.
"""

from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus
from .fawry_provider import FawryProvider
from .moamalat_provider import MoamalatProvider
from .mock_provider import MockProvider
from .sadad_provider import SadadProvider


class PaymentGateway:
    """
    Payment Gateway Manager.

    Provides unified interface for all payment providers.
    Usage:
        gateway = PaymentGateway()

        # Use specific provider
        result = gateway.provider('sadad').create_payment(order_id=1, amount=100)

        # Use default provider (COD)
        result = gateway.pay(order_id=1, amount=100, method='cod')
    """

    def __init__(self):
        self._providers: dict[str, PaymentProvider] = {}
        self._default_provider: str = "cod"

        # Register all providers
        self.register(MockProvider())
        self.register(SadadProvider())
        self.register(FawryProvider())
        self.register(MoamalatProvider())

    def register(self, provider: PaymentProvider) -> None:
        """Register a payment provider."""
        self._providers[provider.name] = provider

    def provider(self, name: str) -> PaymentProvider:
        """Get a specific payment provider."""
        if name not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ValueError(f"Provider '{name}' not registered. Available: {available}")
        return self._providers[name]

    def set_default(self, name: str) -> None:
        """Set default payment provider."""
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        self._default_provider = name

    def pay(
        self,
        order_id: int,
        amount: float,
        method: str = "cod",
        currency: str = "LYD",
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        """
        Process payment using specified method.

        Args:
            order_id: Internal order ID
            amount: Payment amount
            method: Payment method ('cod', 'sadad', 'fawry', 'moamalat', 'mock')
            currency: Currency code (default: LYD)
            description: Payment description
            metadata: Additional data

        Returns:
            PaymentResult with transaction details
        """
        # Handle COD specially (no provider needed)
        if method.lower() == "cod":
            return PaymentResult(
                success=True,
                transaction_id=f"COD-{order_id}",
                status=PaymentStatus.COMPLETED,
                message="Cash on Delivery - pay on receipt",
                provider="cod",
                amount=amount,
                currency=currency,
                metadata={"order_id": order_id},
            )

        # Use specified provider
        try:
            provider = self.provider(method)
            return provider.create_payment(
                order_id=order_id,
                amount=amount,
                currency=currency,
                description=description,
                metadata=metadata,
            )
        except ValueError as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=str(e),
                provider=method,
                amount=amount,
                currency=currency,
            )

    def verify(self, provider_name: str, transaction_id: str) -> PaymentResult:
        """Verify payment status with specific provider."""
        try:
            provider = self.provider(provider_name)
            return provider.verify_payment(transaction_id)
        except ValueError as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=str(e),
                provider=provider_name,
            )

    def refund(
        self,
        provider_name: str,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> PaymentResult:
        """Refund payment with specific provider."""
        try:
            provider = self.provider(provider_name)
            return provider.refund(
                transaction_id=transaction_id,
                amount=amount,
                reason=reason,
            )
        except ValueError as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                message=str(e),
                provider=provider_name,
            )

    def list_providers(self) -> list[dict]:
        """List all registered providers with status."""
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "is_available": p.is_available,
            }
            for p in self._providers.values()
        ]

    def get_available_providers(self) -> list[str]:
        """Get list of available (configured) provider names."""
        return [p.name for p in self._providers.values() if p.is_available]


# Singleton instance
_gateway: Optional[PaymentGateway] = None


def get_payment_gateway() -> PaymentGateway:
    """Get or create PaymentGateway singleton."""
    global _gateway
    if _gateway is None:
        _gateway = PaymentGateway()
    return _gateway
