import uuid

from app.services.payment.base import PaymentIntent, PaymentProvider, PaymentResult


class MockPaymentProvider(PaymentProvider):
    """Development/testing payment provider. Does not call any external service."""

    def create_payment(self, amount: float, currency: str) -> PaymentIntent:
        transaction_id = f"mock_{uuid.uuid4().hex}"
        return PaymentIntent(
            transaction_id=transaction_id, amount=amount, currency=currency, provider="mock"
        )

    def confirm(self, transaction_id: str, outcome: str) -> PaymentResult:
        return PaymentResult(transaction_id=transaction_id, success=(outcome == "success"))
