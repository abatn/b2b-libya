"""
Tests for Libya B2B Platform - Payment SDK
"""

import pytest

# Adjust import path for tests
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from services.payment.base import PaymentProvider, PaymentResult, PaymentStatus
from services.payment.mock_provider import MockProvider
from services.payment.gateway import PaymentGateway, get_payment_gateway
from services.payment.sadad_provider import SadadProvider
from services.payment.fawry_provider import FawryProvider
from services.payment.moamalat_provider import MoamalatProvider
from services.payment.service import PaymentService


class TestPaymentResult:
    """Tests for PaymentResult dataclass."""

    def test_payment_result_creation(self):
        result = PaymentResult(
            success=True,
            transaction_id="TXN-123",
            status=PaymentStatus.COMPLETED,
            message="Payment successful",
            provider="mock",
            amount=100.0,
            currency="LYD",
        )
        assert result.success is True
        assert result.transaction_id == "TXN-123"
        assert result.status == PaymentStatus.COMPLETED
        assert result.amount == 100.0
        assert result.currency == "LYD"

    def test_payment_result_to_dict(self):
        result = PaymentResult(
            success=True,
            transaction_id="TXN-123",
            status=PaymentStatus.COMPLETED,
            message="Payment successful",
            provider="mock",
            amount=100.0,
            currency="LYD",
            metadata={"order_id": 1},
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["transaction_id"] == "TXN-123"
        assert d["status"] == "completed"
        assert d["amount"] == 100.0
        assert d["metadata"]["order_id"] == 1


class TestPaymentStatus:
    """Tests for PaymentStatus enum."""

    def test_status_values(self):
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.COMPLETED.value == "completed"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.REFUNDED.value == "refunded"
        assert PaymentStatus.CANCELLED.value == "cancelled"


class TestMockProvider:
    """Tests for MockProvider."""

    def setup_method(self):
        self.provider = MockProvider()

    def test_provider_name(self):
        assert self.provider.name == "mock"
        assert self.provider.display_name == "Mock Payment (Testing)"

    def test_is_available(self):
        assert self.provider.is_available is True

    def test_create_payment(self):
        result = self.provider.create_payment(
            order_id=1,
            amount=100.0,
            currency="LYD",
            description="Test payment",
        )
        assert result.success is True
        assert result.transaction_id.startswith("MOCK-")
        assert result.status == PaymentStatus.COMPLETED
        assert result.amount == 100.0

    def test_verify_payment(self):
        # Create payment first
        create_result = self.provider.create_payment(
            order_id=1,
            amount=100.0,
        )

        # Verify it
        verify_result = self.provider.verify_payment(
            create_result.transaction_id
        )
        assert verify_result.success is True
        assert verify_result.status == PaymentStatus.COMPLETED

    def test_verify_nonexistent_payment(self):
        result = self.provider.verify_payment("NONEXISTENT-TXN")
        assert result.success is False
        assert result.status == PaymentStatus.FAILED

    def test_refund_payment(self):
        # Create payment first
        create_result = self.provider.create_payment(
            order_id=1,
            amount=100.0,
        )

        # Refund it
        refund_result = self.provider.refund(
            create_result.transaction_id,
            amount=50.0,
            reason="Test refund",
        )
        assert refund_result.success is True
        assert refund_result.status == PaymentStatus.REFUNDED
        assert refund_result.amount == 50.0

    def test_refund_full_amount(self):
        create_result = self.provider.create_payment(
            order_id=1,
            amount=100.0,
        )

        refund_result = self.provider.refund(
            create_result.transaction_id,
            reason="Full refund",
        )
        assert refund_result.success is True
        assert refund_result.amount == 100.0  # Full refund


class TestSadadProvider:
    """Tests for SadadProvider (without API access)."""

    def setup_method(self):
        self.provider = SadadProvider()

    def test_provider_name(self):
        assert self.provider.name == "sadad"
        assert self.provider.display_name == "SADAD Payment"

    def test_is_not_available_without_config(self):
        # Without env vars, provider is not available
        assert self.provider.is_available is False

    def test_create_payment_fails_without_config(self):
        result = self.provider.create_payment(
            order_id=1,
            amount=100.0,
        )
        assert result.success is False
        assert "not configured" in result.message.lower()


class TestFawryProvider:
    """Tests for FawryProvider (without API access)."""

    def setup_method(self):
        self.provider = FawryProvider()

    def test_provider_name(self):
        assert self.provider.name == "fawry"
        assert self.provider.display_name == "Fawry E-Payment"

    def test_is_not_available_without_config(self):
        assert self.provider.is_available is False

    def test_create_payment_fails_without_config(self):
        result = self.provider.create_payment(
            order_id=1,
            amount=100.0,
        )
        assert result.success is False
        assert "not configured" in result.message.lower()


class TestMoamalatProvider:
    """Tests for MoamalatProvider (without API access)."""

    def setup_method(self):
        self.provider = MoamalatProvider()

    def test_provider_name(self):
        assert self.provider.name == "moamalat"
        assert self.provider.display_name == "Moamalat (Bank Card)"

    def test_is_not_available_without_config(self):
        assert self.provider.is_available is False

    def test_create_payment_fails_without_config(self):
        result = self.provider.create_payment(
            order_id=1,
            amount=100.0,
        )
        assert result.success is False
        assert "not configured" in result.message.lower()


class TestPaymentGateway:
    """Tests for PaymentGateway manager."""

    def setup_method(self):
        self.gateway = PaymentGateway()

    def test_register_provider(self):
        mock = MockProvider()
        self.gateway.register(mock)
        provider_names = [p["name"] for p in self.gateway.list_providers()]
        assert "mock" in provider_names

    def test_get_provider(self):
        mock = MockProvider()
        self.gateway.register(mock)
        provider = self.gateway.provider("mock")
        assert provider.name == "mock"

    def test_get_nonexistent_provider(self):
        with pytest.raises(ValueError) as exc_info:
            self.gateway.provider("nonexistent")
        assert "not registered" in str(exc_info.value).lower()

    def test_pay_with_cod(self):
        result = self.gateway.pay(
            order_id=1,
            amount=100.0,
            method="cod",
        )
        assert result.success is True
        assert result.status == PaymentStatus.COMPLETED
        assert result.provider == "cod"

    def test_pay_with_mock(self):
        result = self.gateway.pay(
            order_id=1,
            amount=100.0,
            method="mock",
        )
        assert result.success is True
        assert result.status == PaymentStatus.COMPLETED
        assert result.provider == "mock"

    def test_pay_with_unavailable_provider(self):
        # Use a provider name that's definitely not registered
        result = self.gateway.pay(
            order_id=1,
            amount=100.0,
            method="nonexistent_provider",
        )
        assert result.success is False

    def test_set_default_provider(self):
        mock = MockProvider()
        self.gateway.register(mock)
        self.gateway.set_default("mock")
        # Default is now mock
        assert self.gateway._default_provider == "mock"

    def test_list_providers(self):
        providers = self.gateway.list_providers()
        assert isinstance(providers, list)
        assert len(providers) >= 1  # At least mock

    def test_get_available_providers(self):
        available = self.gateway.get_available_providers()
        assert isinstance(available, list)
        assert "mock" in available  # Mock is always available


class TestPaymentService:
    """Tests for PaymentService (high-level)."""

    def setup_method(self):
        self.service = PaymentService()

    def test_process_cod_payment(self):
        result = self.service.process_payment(
            order_id=1,
            amount=100.0,
            method="cod",
        )
        assert result.success is True
        assert result.status == PaymentStatus.COMPLETED

    def test_process_mock_payment(self):
        result = self.service.process_payment(
            order_id=1,
            amount=100.0,
            method="mock",
        )
        assert result.success is True
        assert result.status == PaymentStatus.COMPLETED

    def test_get_available_methods(self):
        methods = self.service.get_available_methods()
        assert isinstance(methods, list)
        # COD should always be available
        cod_method = next((m for m in methods if m["id"] == "cod"), None)
        assert cod_method is not None
        assert cod_method["available"] is True

    def test_get_payment_status(self):
        # Create a mock payment first
        create_result = self.service.process_payment(
            order_id=1,
            amount=100.0,
            method="mock",
        )

        # Check status
        status_result = self.service.get_payment_status(
            provider="mock",
            transaction_id=create_result.transaction_id,
        )
        assert status_result.success is True
        assert status_result.status == PaymentStatus.COMPLETED

    def test_refund_payment(self):
        # Create a mock payment first
        create_result = self.service.process_payment(
            order_id=1,
            amount=100.0,
            method="mock",
        )

        # Refund it
        refund_result = self.service.refund_payment(
            provider="mock",
            transaction_id=create_result.transaction_id,
            amount=50.0,
            reason="Test refund",
        )
        assert refund_result.success is True
        assert refund_result.status == PaymentStatus.REFUNDED
