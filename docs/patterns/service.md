# Service Pattern

A **Service** provides an abstraction over external systems and third-party integrations, keeping the domain layer independent of external APIs.

## Core Concept

```
Domain defines WHAT external operations are needed
Infrastructure defines HOW to integrate with external systems
```

## When to Use

Use a Service when you need to:
- Integrate with external APIs (payment, email, SMS)
- Abstract cloud services (storage, messaging, ML)
- Wrap third-party SDKs
- Enable testing without real external services
- Allow switching between providers

## Basic Example

```python
from vega.patterns import Service
from abc import abstractmethod
from typing import Optional

# Domain Layer - Abstract interface
class EmailService(Service):
    """Defines what email operations are needed"""

    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email"""
        pass

    @abstractmethod
    async def send_template(
        self,
        to: str,
        template_id: str,
        variables: dict
    ) -> bool:
        """Send templated email"""
        pass

# Infrastructure Layer - Concrete implementation
from vega.di import injectable, Scope
import sendgrid

@injectable(scope=Scope.SINGLETON)
class SendgridEmailService(EmailService):
    """Implements how to send emails with Sendgrid"""

    def __init__(self, api_key: str):
        self.client = sendgrid.SendGridAPIClient(api_key)
        self.default_from = "noreply@example.com"

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> bool:
        message = sendgrid.Mail(
            from_email=from_email or self.default_from,
            to_emails=to,
            subject=subject,
            html_content=body
        )
        try:
            response = await self.client.send(message)
            return response.status_code == 202
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    async def send_template(
        self,
        to: str,
        template_id: str,
        variables: dict
    ) -> bool:
        message = sendgrid.Mail(
            from_email=self.default_from,
            to_emails=to
        )
        message.template_id = template_id
        message.dynamic_template_data = variables
        try:
            response = await self.client.send(message)
            return response.status_code == 202
        except Exception:
            return False
```

## Key Principles

### 1. Interface in Domain, Implementation in Infrastructure

```
project/
├── domain/
│   └── services/
│       ├── email_service.py           # Abstract interface
│       ├── payment_service.py         # Abstract interface
│       └── storage_service.py         # Abstract interface
└── infrastructure/
    └── services/
        ├── sendgrid_email_service.py      # Sendgrid
        ├── mailgun_email_service.py       # Mailgun
        ├── stripe_payment_service.py      # Stripe
        ├── paypal_payment_service.py      # PayPal
        ├── s3_storage_service.py          # AWS S3
        └── azure_storage_service.py       # Azure Blob
```

### 2. Domain-Specific Methods

Services should use domain language, not technical jargon:

```python
# ✅ Good - domain language
class PaymentService(Service):
    async def charge_customer(self, amount: float, token: str) -> PaymentResult:
        pass

    async def refund_payment(self, payment_id: str) -> bool:
        pass

# ❌ Bad - technical jargon
class PaymentService(Service):
    async def stripe_create_charge(self, amount: float, token: str):  # ❌ Stripe-specific
        pass

    async def call_api(self, endpoint: str, data: dict):  # ❌ Too generic
        pass
```

### 3. Hide Implementation Details

```python
# ✅ Good - hides provider details
class StorageService(Service):
    async def upload_file(self, key: str, content: bytes) -> str:
        """Returns public URL"""
        pass

# ❌ Bad - exposes provider details
class StorageService(Service):
    async def upload_to_s3_bucket(self, bucket: str, key: str, content: bytes):
        pass
```

## Dependency Injection Wiring

Wire services in your container configuration:

```python
# config.py
from vega.di import Container
from domain.services.email_service import EmailService
from domain.services.payment_service import PaymentService
from infrastructure.services.sendgrid_email_service import SendgridEmailService
from infrastructure.services.stripe_payment_service import StripePaymentService

container = Container({
    # Map abstract interfaces to concrete implementations
    EmailService: SendgridEmailService,
    PaymentService: StripePaymentService,
})
```

## Real-World Examples

### Example 1: Payment Service with Multiple Providers

```python
# domain/services/payment_service.py
from dataclasses import dataclass

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str
    message: str

class PaymentService(Service):
    @abstractmethod
    async def charge(
        self,
        amount: float,
        currency: str,
        payment_token: str,
        description: str
    ) -> PaymentResult:
        """Charge a payment method"""
        pass

    @abstractmethod
    async def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None
    ) -> PaymentResult:
        """Refund a transaction (full or partial)"""
        pass

    @abstractmethod
    async def get_transaction_status(
        self,
        transaction_id: str
    ) -> str:
        """Get status of a transaction"""
        pass

# infrastructure/services/stripe_payment_service.py
import stripe

@injectable(scope=Scope.SINGLETON)
class StripePaymentService(PaymentService):
    def __init__(self, api_key: str):
        stripe.api_key = api_key

    async def charge(
        self,
        amount: float,
        currency: str,
        payment_token: str,
        description: str
    ) -> PaymentResult:
        try:
            charge = await stripe.Charge.create_async(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                source=payment_token,
                description=description
            )
            return PaymentResult(
                success=True,
                transaction_id=charge.id,
                message="Payment successful"
            )
        except stripe.error.CardError as e:
            return PaymentResult(
                success=False,
                transaction_id="",
                message=str(e)
            )

    async def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None
    ) -> PaymentResult:
        try:
            refund_data = {"charge": transaction_id}
            if amount:
                refund_data["amount"] = int(amount * 100)

            refund = await stripe.Refund.create_async(**refund_data)
            return PaymentResult(
                success=True,
                transaction_id=refund.id,
                message="Refund successful"
            )
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                transaction_id="",
                message=str(e)
            )

    async def get_transaction_status(self, transaction_id: str) -> str:
        charge = await stripe.Charge.retrieve_async(transaction_id)
        return charge.status

# infrastructure/services/paypal_payment_service.py
import paypalrestsdk

@injectable(scope=Scope.SINGLETON)
class PayPalPaymentService(PaymentService):
    def __init__(self, client_id: str, client_secret: str):
        paypalrestsdk.configure({
            "mode": "live",
            "client_id": client_id,
            "client_secret": client_secret
        })

    async def charge(
        self,
        amount: float,
        currency: str,
        payment_token: str,
        description: str
    ) -> PaymentResult:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {
                    "total": str(amount),
                    "currency": currency
                },
                "description": description
            }]
        })

        if payment.create():
            return PaymentResult(
                success=True,
                transaction_id=payment.id,
                message="Payment successful"
            )
        else:
            return PaymentResult(
                success=False,
                transaction_id="",
                message=payment.error
            )

    async def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None
    ) -> PaymentResult:
        sale = paypalrestsdk.Sale.find(transaction_id)
        refund_data = {}
        if amount:
            refund_data["amount"] = {
                "total": str(amount),
                "currency": "USD"
            }

        refund = sale.refund(refund_data)
        if refund.success():
            return PaymentResult(
                success=True,
                transaction_id=refund.id,
                message="Refund successful"
            )
        else:
            return PaymentResult(
                success=False,
                transaction_id="",
                message=refund.error
            )
```

### Example 2: Storage Service

```python
# domain/services/storage_service.py
from typing import Optional

class StorageService(Service):
    @abstractmethod
    async def upload(
        self,
        key: str,
        content: bytes,
        content_type: str
    ) -> str:
        """Upload file and return public URL"""
        pass

    @abstractmethod
    async def download(self, key: str) -> Optional[bytes]:
        """Download file content"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete file"""
        pass

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get signed URL for file"""
        pass

# infrastructure/services/s3_storage_service.py
import boto3
from botocore.exceptions import ClientError

@injectable(scope=Scope.SINGLETON)
class S3StorageService(StorageService):
    def __init__(
        self,
        bucket_name: str,
        aws_access_key: str,
        aws_secret_key: str,
        region: str = "us-east-1"
    ):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

    async def upload(
        self,
        key: str,
        content: bytes,
        content_type: str
    ) -> str:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        except ClientError as e:
            raise StorageError(f"Failed to upload: {e}")

    async def download(self, key: str) -> Optional[bytes]:
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
        except ClientError:
            return None

    async def delete(self, key: str) -> bool:
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError:
            return False

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expires_in
        )

# infrastructure/services/azure_storage_service.py
from azure.storage.blob import BlobServiceClient

@injectable(scope=Scope.SINGLETON)
class AzureStorageService(StorageService):
    def __init__(self, connection_string: str, container_name: str):
        self.blob_service = BlobServiceClient.from_connection_string(
            connection_string
        )
        self.container_name = container_name

    async def upload(
        self,
        key: str,
        content: bytes,
        content_type: str
    ) -> str:
        blob_client = self.blob_service.get_blob_client(
            container=self.container_name,
            blob=key
        )
        blob_client.upload_blob(
            content,
            content_settings={"content_type": content_type}
        )
        return blob_client.url

    async def download(self, key: str) -> Optional[bytes]:
        blob_client = self.blob_service.get_blob_client(
            container=self.container_name,
            blob=key
        )
        try:
            return blob_client.download_blob().readall()
        except Exception:
            return None

    async def delete(self, key: str) -> bool:
        blob_client = self.blob_service.get_blob_client(
            container=self.container_name,
            blob=key
        )
        try:
            blob_client.delete_blob()
            return True
        except Exception:
            return False
```

### Example 3: SMS Service

```python
# domain/services/sms_service.py
class SMSService(Service):
    @abstractmethod
    async def send_sms(
        self,
        to: str,
        message: str
    ) -> bool:
        """Send SMS message"""
        pass

    @abstractmethod
    async def send_verification_code(
        self,
        to: str,
        code: str
    ) -> bool:
        """Send verification code"""
        pass

# infrastructure/services/twilio_sms_service.py
from twilio.rest import Client

@injectable(scope=Scope.SINGLETON)
class TwilioSMSService(SMSService):
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str
    ):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    async def send_sms(self, to: str, message: str) -> bool:
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            return message.sid is not None
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False

    async def send_verification_code(self, to: str, code: str) -> bool:
        message = f"Your verification code is: {code}"
        return await self.send_sms(to, message)
```

### Example 4: Email Service with Templates

```python
# domain/services/email_service.py
@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    content_type: str

class EmailService(Service):
    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None
    ) -> bool:
        pass

    @abstractmethod
    async def send_template(
        self,
        to: str,
        template_id: str,
        variables: dict
    ) -> bool:
        pass

    @abstractmethod
    async def send_bulk(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> int:
        """Returns number of emails sent successfully"""
        pass

# infrastructure/services/mailgun_email_service.py
import requests

@injectable(scope=Scope.SINGLETON)
class MailgunEmailService(EmailService):
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://api.mailgun.net/v3/{domain}"

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None
    ) -> bool:
        data = {
            "from": from_email or f"noreply@{self.domain}",
            "to": to,
            "subject": subject,
            "html": body
        }

        files = []
        if attachments:
            files = [
                ("attachment", (att.filename, att.content, att.content_type))
                for att in attachments
            ]

        response = requests.post(
            f"{self.base_url}/messages",
            auth=("api", self.api_key),
            data=data,
            files=files or None
        )
        return response.status_code == 200

    async def send_template(
        self,
        to: str,
        template_id: str,
        variables: dict
    ) -> bool:
        data = {
            "from": f"noreply@{self.domain}",
            "to": to,
            "template": template_id,
            **{f"v:{k}": v for k, v in variables.items()}
        }

        response = requests.post(
            f"{self.base_url}/messages",
            auth=("api", self.api_key),
            data=data
        )
        return response.status_code == 200

    async def send_bulk(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> int:
        sent = 0
        for recipient in recipients:
            if await self.send(recipient, subject, body):
                sent += 1
        return sent
```

## Testing with Services

### Unit Testing with Mock Service

```python
import pytest

class MockEmailService(EmailService):
    def __init__(self):
        self.sent_emails = []

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> bool:
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body,
            "from": from_email
        })
        return True

    async def send_template(
        self,
        to: str,
        template_id: str,
        variables: dict
    ) -> bool:
        self.sent_emails.append({
            "to": to,
            "template_id": template_id,
            "variables": variables
        })
        return True

async def test_send_welcome_email():
    # Setup container with mock
    mock_email = MockEmailService()
    container = Container({EmailService: lambda: mock_email})
    set_container(container)

    # Execute interactor
    await SendWelcomeEmail(email="test@test.com", name="John")

    # Verify
    assert len(mock_email.sent_emails) == 1
    assert mock_email.sent_emails[0]["to"] == "test@test.com"
    assert "Welcome" in mock_email.sent_emails[0]["subject"]
```

## Best Practices

### ✅ DO

```python
# Define interface in domain layer
# domain/services/email_service.py
class EmailService(Service):
    pass

# Implement in infrastructure layer
# infrastructure/services/sendgrid_email_service.py
class SendgridEmailService(EmailService):
    pass

# Use domain language
async def send_welcome_email(self, to: str) -> bool:
    pass

# Hide provider details
async def charge_customer(self, amount: float) -> PaymentResult:
    pass

# Use @injectable for DI
@injectable(scope=Scope.SINGLETON)
class StripePaymentService(PaymentService):
    pass

# Return domain types
@dataclass
class PaymentResult:
    success: bool
    transaction_id: str

async def charge(...) -> PaymentResult:
    pass
```

### ❌ DON'T

```python
# Don't implement in domain layer
class EmailService(Service):
    async def send(self, to: str):
        sendgrid.send(...)  # ❌ Implementation in domain

# Don't use provider names in methods
async def send_with_sendgrid(self, to: str):  # ❌ Provider-specific
    pass

# Don't expose provider types
import stripe
async def charge(...) -> stripe.Charge:  # ❌ Provider type
    pass

# Don't add provider-specific methods
class EmailService(Service):
    async def get_sendgrid_client(self):  # ❌ Provider-specific
        pass

# Don't put business logic in services
async def send_email(self, to: str, body: str):
    if len(body) < 10:  # ❌ Business logic
        raise ValueError("Body too short")
    ...
```

## CLI Generation

Generate services using the CLI:

```bash
vega generate service EmailService
vega generate service PaymentService
vega generate service StorageService
```

## Next Steps

- [Interactor](interactor.md) - Single-purpose use cases
- [Mediator](mediator.md) - Complex workflow orchestration
- [Repository](repository.md) - Data persistence abstraction
- [Dependency Injection](../core/dependency-injection.md) - Learn DI system
