from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PaymentIntent:
    transaction_id: str
    amount: float
    currency: str
    provider: str


@dataclass
class PaymentResult:
    transaction_id: str
    success: bool


class PaymentProvider(ABC):
    """Abstraction so a real Tunisian payment provider can replace the mock
    later without changing callers. Implementations must be idempotent."""

    @abstractmethod
    def create_payment(self, amount: float, currency: str) -> PaymentIntent:
        ...

    @abstractmethod
    def confirm(self, transaction_id: str, outcome: str) -> PaymentResult:
        ...
