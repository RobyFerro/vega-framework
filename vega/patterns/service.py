"""Service pattern for external integrations"""
from abc import ABC


class Service(ABC):
    """
    Base service interface for external integrations.

    Service pattern provides abstraction over external services,
    allowing domain layer to remain independent of third-party APIs.

    Key principles:
    - Abstract interface defined in domain layer
    - Concrete implementations in infrastructure layer
    - Represents external dependencies (email, payment, storage, etc.)

    Example:
        from vega.patterns import Service

        # Domain layer: Abstract interface
        class EmailService(Service):
            @abstractmethod
            async def send(self, to: str, subject: str, body: str) -> bool:
                pass

        class PaymentService(Service):
            @abstractmethod
            async def charge(self, amount: float, token: str) -> PaymentResult:
                pass

        # Infrastructure layer: Concrete implementations
        class SendgridEmailService(EmailService):
            async def send(self, to: str, subject: str, body: str) -> bool:
                # Sendgrid API integration
                pass

        class StripePaymentService(PaymentService):
            async def charge(self, amount: float, token: str) -> PaymentResult:
                # Stripe API integration
                pass
    """
    pass
