# Async Listeners - Background Job Processing

Guida completa al sistema di Async Listener in Vega Framework per processare job in background attraverso code di messaggi.

## 📋 Indice

- [Panoramica](#panoramica)
- [Concetti Base](#concetti-base)
- [Quick Start](#quick-start)
- [Architettura](#architettura)
- [Configurazione](#configurazione)
- [Pattern d'Uso](#pattern-duso)
- [Driver Disponibili](#driver-disponibili)
- [Dependency Injection](#dependency-injection)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Error Handling](#error-handling)
- [Esempi Pratici](#esempi-pratici)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Panoramica

Il sistema **Async Listener** permette di creare worker asincroni che processano messaggi da code (AWS SQS, RabbitMQ, Redis, ecc.) per implementare architetture event-driven e job processing scalabili.

### Caratteristiche Principali

- ✅ **Driver Agnostic** - Supporta multiple code (SQS, RabbitMQ, Redis)
- ✅ **Auto-Discovery** - Registrazione automatica dei listener
- ✅ **Dependency Injection** - Integrazione completa con sistema DI
- ✅ **Worker Concorrenti** - Scalabilità orizzontale configurabile
- ✅ **Error Handling** - Retry automatico con exponential backoff
- ✅ **Lifecycle Hooks** - Controllo completo su startup/shutdown/error
- ✅ **Long Polling** - Efficienza energetica e riduzione costi API
- ✅ **Graceful Shutdown** - Gestione pulita di SIGTERM/SIGINT
- ✅ **Clean Architecture** - Separazione domain/infrastructure

### Quando Usare i Listener

- 📧 **Invio email/notifiche** asincrone
- 🖼️ **Processing media** (resize immagini, video encoding)
- 📊 **Report generation** in background
- 🔄 **Sync/replicazione** dati tra sistemi
- 📈 **Analytics processing** batch
- 🧹 **Cleanup tasks** periodici
- 🔔 **Webhook processing** da servizi esterni
- 💳 **Payment processing** asincrono

## 🚀 Quick Start

### 1. Installazione

Il sistema listener è già incluso in Vega Framework. Assicurati di avere le dipendenze:

```bash
# Per AWS SQS
poetry add aioboto3

# Per RabbitMQ (futuro)
poetry add aio-pika

# Per Redis (futuro)
poetry add redis
```

### 2. Configurazione Base

**config.py**:
```python
from vega.di import Container
from vega.listeners.drivers.sqs import SQSDriver
from vega.listeners.driver import QueueDriver

# Registra il driver di coda
container = Container({
    QueueDriver: SQSDriver,
})
```

### 3. Crea il Tuo Primo Listener

```bash
# Genera scheletro listener
vega generate listener SendWelcomeEmail --queue welcome-emails --workers 3
```

**infrastructure/listeners/send_welcome_email_listener.py**:
```python
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind
from domain.services import EmailService

@job_listener(queue="welcome-emails", workers=3)
class SendWelcomeEmailListener(JobListener):
    """Invia email di benvenuto ai nuovi utenti"""

    @bind
    async def handle(self, message: Message, email_service: EmailService) -> None:
        """
        Processa messaggio dalla coda.

        Formato messaggio atteso:
        {
            "user_id": "123",
            "email": "user@example.com",
            "name": "John Doe"
        }
        """
        data = message.body

        await email_service.send_welcome(
            to=data['email'],
            name=data['name']
        )

        # Messaggio auto-acknowledged se successo!
```

### 4. Esegui i Listener

```bash
# Avvia tutti i listener
vega listener run

# Da codice Python
poetry run python -c "
from vega.discovery import discover_listeners
from vega.listeners.manager import ListenerManager
import config  # Inizializza container
import asyncio

listeners = discover_listeners('infrastructure')
manager = ListenerManager(listeners)
asyncio.run(manager.start())
"
```

## 🏗️ Architettura

### Componenti Principali

```
┌─────────────────────────────────────────────────────────────┐
│                    ListenerManager                          │
│  - Gestisce lifecycle                                       │
│  - Crea worker tasks                                        │
│  - Graceful shutdown                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├──► QueueDriver (Interface)
                      │    └──► SQSDriver
                      │    └──► RabbitMQDriver (futuro)
                      │    └──► RedisDriver (futuro)
                      │
                      ├──► JobListener (tuo codice)
                      │    └──► handle(message) + DI
                      │    └──► on_startup/shutdown/error
                      │
                      └──► Message + MessageContext
                           └──► ack/reject/extend_visibility
```

### Flusso di Esecuzione

```
1. Manager.start()
   ↓
2. Risolve QueueDriver dal container DI
   ↓
3. Connette al servizio di code (SQS/RabbitMQ/etc)
   ↓
4. Per ogni Listener:
   ├─ Istanzia listener
   ├─ Chiama on_startup()
   └─ Crea N worker tasks (basati su workers=N)
   ↓
5. Ogni worker:
   ├─ Long polling sulla coda (10s wait)
   ├─ Riceve messaggi
   ├─ Per ogni messaggio:
   │  ├─ Crea scope_context per DI
   │  ├─ Chiama handle() con dependency injection
   │  ├─ Su successo → ack()
   │  ├─ Su errore → retry o reject()
   │  └─ Chiama on_error() se fallisce
   └─ Loop infinito fino a shutdown
   ↓
6. Su SIGTERM/SIGINT:
   ├─ Cancella tutti i worker tasks
   ├─ Chiama on_shutdown() per ogni listener
   └─ Disconnette driver
```

## ⚙️ Configurazione

### Parametri del Decorator

```python
@job_listener(
    queue="nome-coda",           # Nome della coda da ascoltare
    workers=3,                   # Numero worker concorrenti (default: 1)
    auto_ack=True,              # Auto-acknowledge su successo (default: True)
    visibility_timeout=30,       # Timeout visibilità in secondi (default: 30)
    max_messages=1,             # Max messaggi per poll (default: 1)
    retry_on_error=False,       # Retry automatico su errore (default: False)
    max_retries=3               # Tentativi massimi (default: 3)
)
```

### Configurazione Driver SQS

**settings.py**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # SQS Configuration
    sqs_endpoint_url: str | None = None  # Per localstack

    class Config:
        env_file = ".env"

settings = Settings()
```

**config.py**:
```python
from vega.di import Container, Scope, bean
from vega.listeners.drivers.sqs import SQSDriver
from vega.listeners.driver import QueueDriver
from settings import settings

@bean(
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    endpoint_url=settings.sqs_endpoint_url,
    scope=Scope.SINGLETON,
    interface=QueueDriver
)
class ConfiguredSQSDriver(SQSDriver):
    pass

# O manualmente
container = Container({
    QueueDriver: ConfiguredSQSDriver
})
```

## 🎨 Pattern d'Uso

### 1. Auto-Acknowledgment (Raccomandato)

**Quando usarlo**: Per la maggior parte dei casi d'uso

```python
@job_listener(queue="email-queue", auto_ack=True)
class SendEmailListener(JobListener):
    @bind
    async def handle(self, message: Message, email_service: EmailService):
        # Processa messaggio
        await email_service.send(**message.body)
        # ✅ Auto-acknowledged se successo
        # ❌ Auto-rejected se eccezione
```

**Vantaggi**:
- ✅ Codice più semplice
- ✅ Gestione automatica ack/reject
- ✅ Meno possibilità di errori

### 2. Manual Acknowledgment

**Quando usarlo**: Controllo fine-grained su ack/reject

```python
@job_listener(queue="orders", auto_ack=False, workers=5)
class ProcessOrderListener(JobListener):
    @bind
    async def handle(
        self,
        message: Message,
        context: MessageContext,
        order_repo: OrderRepository
    ):
        try:
            order = await order_repo.get(message.body['order_id'])
            await self.validate_order(order)
            await self.process_payment(order)
            await self.ship_order(order)

            # ✅ Successo completo
            await context.ack()

        except PaymentTemporaryError:
            # 💳 Errore temporaneo pagamento - riprova dopo
            await context.reject(requeue=True, visibility_timeout=300)

        except ValidationError as e:
            # ❌ Errore validazione - non ritentare (DLQ)
            await context.reject(requeue=False)
            logger.error(f"Invalid order: {e}")
```

**Vantaggi**:
- ✅ Controllo granulare su retry
- ✅ Gestione differenziata errori temporanei/permanenti
- ✅ Custom visibility timeout per retry

### 3. Retry con Exponential Backoff

**Quando usarlo**: API esterne instabili, rate limiting

```python
@job_listener(
    queue="api-calls",
    retry_on_error=True,
    max_retries=5,
    workers=10,
    visibility_timeout=60
)
class CallExternalAPIListener(JobListener):
    @bind
    async def handle(self, message: Message, api_client: APIClient):
        # Retry automatico fino a 5 volte con backoff esponenziale
        # Tentativo 1: immediato
        # Tentativo 2: dopo 0.5s
        # Tentativo 3: dopo 1s
        # Tentativo 4: dopo 2s
        # Tentativo 5: dopo 4s
        result = await api_client.call(message.body['endpoint'])

        # Se fallisce 5 volte → rejected
```

### 4. Long-Running Jobs

**Quando usarlo**: Processing pesante (video, report, ML)

```python
@job_listener(
    queue="video-processing",
    visibility_timeout=300,  # 5 minuti iniziali
    workers=2
)
class ProcessVideoListener(JobListener):
    @bind
    async def handle(
        self,
        message: Message,
        context: MessageContext,
        storage: StorageService
    ):
        video_url = message.body['video_url']

        # Estendi timeout per lavoro lungo
        await context.extend_visibility(600)  # Altri 10 minuti

        # Processing pesante
        video = await storage.download(video_url)
        processed = await self.encode_video(video)  # Lungo!
        await storage.upload(processed)

        await context.ack()
```

### 5. Batch Processing

**Quando usarlo**: Aggregazione messaggi, bulk operations

```python
@job_listener(
    queue="analytics-events",
    max_messages=10,  # Ricevi fino a 10 messaggi per volta
    workers=3
)
class AnalyticsListener(JobListener):
    @bind
    async def handle(self, message: Message, analytics_repo: AnalyticsRepository):
        # Anche se richiedi 10 messaggi, ogni messaggio viene
        # processato individualmente dal framework
        event = message.body
        await analytics_repo.save_event(event)
```

## 🔌 Driver Disponibili

### AWS SQS Driver

**Setup**:
```bash
poetry add aioboto3
```

**Configurazione**:
```python
from vega.listeners.drivers.sqs import SQSDriver

@bean(
    region_name="us-east-1",
    aws_access_key_id="YOUR_KEY",  # O None per IAM role
    aws_secret_access_key="YOUR_SECRET",  # O None
    endpoint_url=None,  # Per localstack: "http://localhost:4566"
    scope=Scope.SINGLETON,
    interface=QueueDriver
)
class MySQSDriver(SQSDriver):
    pass
```

**Formato Nome Coda**:
- Nome semplice: `"my-queue"` → cerca in account AWS
- ARN completo: `"arn:aws:sqs:us-east-1:123456789012:my-queue"`
- URL completo: `"https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"`

**Testing con LocalStack**:
```bash
# Avvia LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Configura endpoint
export SQS_ENDPOINT_URL="http://localhost:4566"
```

### RabbitMQ Driver (Futuro)

```python
# Coming soon!
from vega.listeners.drivers.rabbitmq import RabbitMQDriver
```

### Redis Streams Driver (Futuro)

```python
# Coming soon!
from vega.listeners.drivers.redis import RedisDriver
```

### Custom Driver

Implementa l'interfaccia `QueueDriver`:

```python
from vega.listeners.driver import QueueDriver
from vega.listeners.message import Message

class MyCustomDriver(QueueDriver):
    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        visibility_timeout: int = 30,
        wait_time: int = 0
    ) -> List[Message]:
        # Implementa polling
        pass

    async def acknowledge(self, message: Message) -> None:
        # Implementa acknowledgment
        pass

    async def reject(
        self,
        message: Message,
        requeue: bool = True,
        visibility_timeout: Optional[int] = None
    ) -> None:
        # Implementa rejection
        pass

    async def extend_visibility(self, message: Message, seconds: int) -> None:
        # Implementa estensione timeout
        pass

    async def get_queue_attributes(self, queue_name: str) -> Dict[str, Any]:
        # Implementa query attributi
        pass
```

## 💉 Dependency Injection

I listener supportano **dependency injection completa** tramite il decorator `@bind`:

```python
from vega.di import bind
from domain.repositories import UserRepository, OrderRepository
from domain.services import EmailService, PaymentService

@job_listener(queue="orders")
class ProcessOrderListener(JobListener):
    @bind
    async def handle(
        self,
        message: Message,
        # Tutte queste dipendenze sono auto-iniettate!
        user_repo: UserRepository,
        order_repo: OrderRepository,
        email_service: EmailService,
        payment_service: PaymentService
    ):
        order_data = message.body

        user = await user_repo.get(order_data['user_id'])
        order = await order_repo.create(order_data)

        payment = await payment_service.charge(user, order)

        await email_service.send_order_confirmation(user.email, order)
```

### Scope delle Dipendenze

Il framework gestisce automaticamente gli scope:

- **SINGLETON** - Condiviso tra tutti i messaggi
- **SCOPED** - Unico per ogni messaggio (dentro scope_context)
- **TRANSIENT** - Nuovo ad ogni risoluzione

```python
from vega.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class EmailService:
    """Condiviso tra tutti i worker e messaggi"""
    pass

@injectable(scope=Scope.SCOPED)
class DatabaseSession:
    """Nuovo per ogni messaggio processato"""
    pass

@injectable(scope=Scope.TRANSIENT)
class RequestTracker:
    """Nuovo ad ogni uso"""
    pass
```

## 🔄 Lifecycle Hooks

Ogni listener può implementare hook opzionali per il lifecycle:

### on_startup()

Chiamato **una volta** quando il listener parte, prima dei worker.

```python
@job_listener(queue="emails")
class EmailListener(JobListener):
    async def on_startup(self) -> None:
        """
        Inizializzazione:
        - Connessioni database
        - Cache warming
        - Validazione configurazione
        """
        self.email_client = await EmailClient.connect()
        self.template_cache = await self.load_templates()
        logger.info("EmailListener started successfully")

    @bind
    async def handle(self, message: Message):
        # Usa self.email_client inizializzato
        await self.email_client.send(**message.body)
```

### on_shutdown()

Chiamato **una volta** quando il listener si ferma, dopo i worker.

```python
@job_listener(queue="emails")
class EmailListener(JobListener):
    async def on_shutdown(self) -> None:
        """
        Cleanup:
        - Chiudi connessioni
        - Flush buffer
        - Salva stato
        """
        await self.email_client.close()
        await self.flush_metrics()
        logger.info("EmailListener stopped gracefully")

    @bind
    async def handle(self, message: Message):
        await self.email_client.send(**message.body)
```

### on_error()

Chiamato **per ogni messaggio** che fallisce dopo tutti i retry.

```python
@job_listener(queue="payments", retry_on_error=True, max_retries=3)
class PaymentListener(JobListener):
    async def on_error(self, message: Message, error: Exception) -> None:
        """
        Gestione errori:
        - Logging su Sentry/DataDog
        - Notifiche team
        - Salvataggio su DLQ custom
        """
        import sentry_sdk

        # Log su Sentry
        sentry_sdk.capture_exception(error)

        # Notifica team
        await self.notify_team(
            f"Payment failed after 3 retries: {message.id}",
            error=str(error),
            order_id=message.body.get('order_id')
        )

        # Salva per analisi
        await self.save_failed_message(message, error)

    @bind
    async def handle(self, message: Message, payment_service: PaymentService):
        await payment_service.process(message.body)
```

## ⚠️ Error Handling

### Strategie di Error Handling

#### 1. Let It Fail (Auto-Ack)

```python
@job_listener(queue="notifications", auto_ack=True)
class NotificationListener(JobListener):
    @bind
    async def handle(self, message: Message, notifier: NotificationService):
        # Qualsiasi eccezione → reject e log
        await notifier.send(message.body)
```

- ✅ Semplice
- ⚠️ Messaggio perso se errore permanente

#### 2. Retry Everything (Retry On Error)

```python
@job_listener(
    queue="api-sync",
    retry_on_error=True,
    max_retries=5
)
class APISyncListener(JobListener):
    @bind
    async def handle(self, message: Message, api: APIClient):
        # Retry automatico per QUALSIASI eccezione
        await api.sync(message.body)
```

- ✅ Resiliente
- ⚠️ Può mascherare errori permanenti

#### 3. Selective Retry (Manual Ack)

```python
@job_listener(queue="orders", auto_ack=False)
class OrderListener(JobListener):
    @bind
    async def handle(
        self,
        message: Message,
        context: MessageContext,
        service: OrderService
    ):
        try:
            await service.process(message.body)
            await context.ack()

        except TemporaryNetworkError as e:
            # Retry: errore temporaneo
            await context.reject(requeue=True)

        except ValidationError as e:
            # No retry: errore permanente → DLQ
            await context.reject(requeue=False)
            logger.error(f"Invalid order: {e}")

        except PaymentDeclined as e:
            # No retry ma notifica utente
            await context.reject(requeue=False)
            await self.notify_user_payment_failed(message.body)
```

- ✅ Controllo fine-grained
- ✅ Gestione ottimale
- ⚠️ Più codice

### Dead Letter Queue (DLQ)

Configura DLQ a livello di coda AWS:

```python
# AWS SQS DLQ Configuration (esempio con boto3)
import boto3

sqs = boto3.client('sqs')

# Crea DLQ
dlq = sqs.create_queue(QueueName='orders-dlq')

# Configura main queue con DLQ
main_queue = sqs.create_queue(
    QueueName='orders',
    Attributes={
        'RedrivePolicy': json.dumps({
            'deadLetterTargetArn': dlq['QueueArn'],
            'maxReceiveCount': '3'  # Dopo 3 tentativi → DLQ
        })
    }
)
```

Crea listener per DLQ:

```python
@job_listener(queue="orders-dlq", workers=1)
class OrderDLQListener(JobListener):
    """Gestisce ordini falliti per investigazione"""

    async def handle(self, message: Message):
        # Log per investigazione
        logger.error(f"Order in DLQ: {message.body}")

        # Salva in database per review manuale
        await self.save_for_manual_review(message)

        # Notifica team
        await self.alert_team(message)
```

## 📚 Esempi Pratici

### Esempio 1: Sistema di Notifiche Email

```python
# domain/services/email_service.py
from abc import ABC, abstractmethod

class EmailService(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str):
        pass

# infrastructure/services/sendgrid_email_service.py
from vega.di import injectable, Scope
import httpx

@injectable(scope=Scope.SINGLETON)
class SendgridEmailService(EmailService):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def send_email(self, to: str, subject: str, body: str):
        response = await self.client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": "noreply@myapp.com"},
                "subject": subject,
                "content": [{"type": "text/html", "value": body}]
            }
        )
        response.raise_for_status()

# infrastructure/listeners/send_email_listener.py
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind
from domain.services import EmailService

@job_listener(
    queue="email-notifications",
    workers=5,
    retry_on_error=True,
    max_retries=3
)
class SendEmailListener(JobListener):
    """
    Invia email in modo asincrono.

    Formato messaggio:
    {
        "to": "user@example.com",
        "subject": "Welcome!",
        "body": "<h1>Welcome</h1>"
    }
    """

    @bind
    async def handle(self, message: Message, email_service: EmailService):
        data = message.body
        await email_service.send_email(
            to=data['to'],
            subject=data['subject'],
            body=data['body']
        )

    async def on_error(self, message: Message, error: Exception):
        # Log errore per debugging
        logger.error(
            f"Failed to send email to {message.body.get('to')}: {error}"
        )

# Pubblica messaggio (da un interactor)
import boto3
import json

class RegisterUser(Interactor[User]):
    @bind
    async def call(self, ...):
        user = await self.create_user(...)

        # Pubblica messaggio SQS per email asincrona
        sqs = boto3.client('sqs')
        sqs.send_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/123/email-notifications',
            MessageBody=json.dumps({
                'to': user.email,
                'subject': 'Welcome to MyApp!',
                'body': f'<h1>Hi {user.name}!</h1>'
            })
        )

        return user
```

### Esempio 2: Image Processing Pipeline

```python
# infrastructure/listeners/resize_image_listener.py
from vega.listeners import JobListener, job_listener, Message, MessageContext
from vega.di import bind
from PIL import Image
import io

@job_listener(
    queue="image-processing",
    workers=3,
    visibility_timeout=120,  # 2 minuti
    auto_ack=False
)
class ResizeImageListener(JobListener):
    """
    Ridimensiona immagini caricate.

    Formato messaggio:
    {
        "image_url": "s3://bucket/original/photo.jpg",
        "sizes": [{"width": 800, "height": 600}, {"width": 200, "height": 200}],
        "output_prefix": "s3://bucket/resized/"
    }
    """

    @bind
    async def handle(
        self,
        message: Message,
        context: MessageContext,
        storage: StorageService
    ):
        data = message.body

        try:
            # Estendi timeout per processing lungo
            await context.extend_visibility(180)  # 3 minuti totali

            # Download immagine
            image_data = await storage.download(data['image_url'])
            image = Image.open(io.BytesIO(image_data))

            # Resize per ogni dimensione richiesta
            for size in data['sizes']:
                resized = image.resize((size['width'], size['height']))

                # Upload versione ridimensionata
                output = io.BytesIO()
                resized.save(output, format=image.format)

                filename = f"{size['width']}x{size['height']}_photo.jpg"
                await storage.upload(
                    data['output_prefix'] + filename,
                    output.getvalue()
                )

            await context.ack()

        except StorageError as e:
            # Errore storage temporaneo - retry
            await context.reject(requeue=True, visibility_timeout=300)

        except Exception as e:
            # Errore processing - non retry
            await context.reject(requeue=False)
            logger.error(f"Image processing failed: {e}")

    async def on_startup(self):
        logger.info("Image processing listener started")

    async def on_error(self, message: Message, error: Exception):
        # Notifica team per immagini che falliscono
        await self.alert_team(f"Image failed: {message.body['image_url']}")
```

### Esempio 3: Webhook Handler

```python
# infrastructure/listeners/stripe_webhook_listener.py
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind
import stripe

@job_listener(
    queue="stripe-webhooks",
    workers=2,
    retry_on_error=False  # No retry per webhook (idempotency)
)
class StripeWebhookListener(JobListener):
    """
    Processa webhook da Stripe.

    Formato messaggio:
    {
        "event_type": "payment_intent.succeeded",
        "event_id": "evt_123",
        "data": {...}
    }
    """

    @bind
    async def handle(
        self,
        message: Message,
        payment_repo: PaymentRepository,
        user_repo: UserRepository
    ):
        event_type = message.body['event_type']
        event_data = message.body['data']

        if event_type == 'payment_intent.succeeded':
            await self.handle_payment_success(event_data, payment_repo, user_repo)

        elif event_type == 'payment_intent.payment_failed':
            await self.handle_payment_failed(event_data, payment_repo)

        elif event_type == 'customer.subscription.created':
            await self.handle_subscription_created(event_data, user_repo)

        # Messaggio auto-acknowledged se successo

    async def handle_payment_success(self, data, payment_repo, user_repo):
        payment_intent_id = data['id']

        # Aggiorna database
        payment = await payment_repo.get_by_stripe_id(payment_intent_id)
        payment.status = 'succeeded'
        await payment_repo.save(payment)

        # Notifica utente
        user = await user_repo.get(payment.user_id)
        await self.send_receipt(user.email, payment)

    async def on_error(self, message: Message, error: Exception):
        # Webhook falliti sono critici - alert immediato
        await self.page_on_call_engineer(
            f"Stripe webhook failed: {message.body['event_id']}",
            error=str(error)
        )
```

## ✨ Best Practices

### 1. Idempotenza

**Problema**: Messaggi possono essere processati più volte.

**Soluzione**: Rendi handler idempotenti.

```python
@job_listener(queue="orders")
class ProcessOrderListener(JobListener):
    @bind
    async def handle(self, message: Message, order_repo: OrderRepository):
        order_id = message.body['order_id']

        # ✅ Controlla se già processato
        order = await order_repo.get(order_id)
        if order.status == 'processed':
            logger.info(f"Order {order_id} already processed, skipping")
            return  # Idempotente!

        # Processa ordine
        await self.process_order(order)
        order.status = 'processed'
        await order_repo.save(order)
```

### 2. Visibilità del Messaggio

**Problema**: Worker muore durante processing → messaggio torna in coda.

**Soluzione**: Imposta `visibility_timeout` appropriato.

```python
# ❌ Troppo corto - messaggio torna prima di finire
@job_listener(queue="video", visibility_timeout=30)  # 30s

# ✅ Adeguato al tempo di processing
@job_listener(queue="video", visibility_timeout=600)  # 10 minuti
```

### 3. Worker Count

**Problema**: Troppe/poche worker → inefficienza.

**Soluzione**: Bilancia workers vs carico.

```python
# Leggeri, I/O bound → molti worker
@job_listener(queue="emails", workers=10)

# Pesanti, CPU bound → pochi worker
@job_listener(queue="video-encoding", workers=2)

# Mission critical → worker dedicati
@job_listener(queue="payments", workers=5)
```

### 4. Logging Strutturato

```python
import structlog

logger = structlog.get_logger()

@job_listener(queue="orders")
class OrderListener(JobListener):
    @bind
    async def handle(self, message: Message):
        # Log strutturato per debugging
        logger.info(
            "processing_order",
            order_id=message.body['order_id'],
            user_id=message.body['user_id'],
            message_id=message.id,
            received_count=message.received_count
        )

        await self.process_order(message.body)

        logger.info(
            "order_processed",
            order_id=message.body['order_id'],
            duration_ms=self.duration
        )
```

### 5. Monitoring & Metrics

```python
from prometheus_client import Counter, Histogram

messages_processed = Counter('listener_messages_processed', 'Messages processed', ['listener', 'status'])
processing_duration = Histogram('listener_processing_duration', 'Processing duration', ['listener'])

@job_listener(queue="orders")
class OrderListener(JobListener):
    @bind
    async def handle(self, message: Message):
        with processing_duration.labels(listener='OrderListener').time():
            try:
                await self.process(message.body)
                messages_processed.labels(listener='OrderListener', status='success').inc()
            except Exception:
                messages_processed.labels(listener='OrderListener', status='error').inc()
                raise
```

### 6. Testing

**Usa MockQueueDriver per unit test**:

```python
# tests/unit/test_order_listener.py
from tests.fixtures import MockQueueDriver
from infrastructure.listeners import OrderListener

async def test_order_listener_processes_message():
    # Arrange
    driver = MockQueueDriver()
    message = driver.add_message("orders", {"order_id": "123"})

    listener = OrderListener()

    # Act
    await listener.handle(message)

    # Assert
    assert "123" in driver.acknowledged
```

## 🔧 Troubleshooting

### Problema: Listener non riceve messaggi

**Diagnosi**:
```python
# Verifica driver configurato
from vega.di import Summon
from vega.listeners.driver import QueueDriver

driver = Summon(QueueDriver)
print(f"Driver: {driver.__class__.__name__}")

# Verifica listener registrati
from vega.listeners.registry import get_listener_registry
print(f"Listeners: {get_listener_registry()}")

# Verifica coda SQS
attrs = await driver.get_queue_attributes("my-queue")
print(f"Messages in queue: {attrs.get('ApproximateNumberOfMessages')}")
```

**Soluzioni**:
- ✅ Verifica QueueDriver registrato in container
- ✅ Verifica nome coda corretto
- ✅ Verifica credenziali AWS
- ✅ Verifica listener importato (auto-discovery)

### Problema: Messaggi processati più volte

**Causa**: Visibility timeout troppo breve.

**Soluzione**:
```python
# Aumenta visibility timeout
@job_listener(queue="slow-jobs", visibility_timeout=300)
```

### Problema: Worker bloccati

**Causa**: Deadlock o operazione bloccante.

**Soluzione**:
```python
# ❌ Evita operazioni sincrone bloccanti
def blocking_operation():
    time.sleep(10)  # Blocca event loop!

# ✅ Usa async
async def async_operation():
    await asyncio.sleep(10)  # Non blocca
```

### Problema: Memory leak

**Causa**: Risorse non rilasciate.

**Soluzione**:
```python
@job_listener(queue="files")
class FileListener(JobListener):
    @bind
    async def handle(self, message: Message):
        # ❌ File handle non chiuso
        file = open('large_file.txt')
        process(file)

        # ✅ Usa context manager
        async with aiofiles.open('large_file.txt') as file:
            await process(file)
        # File chiuso automaticamente
```

### Problema: Slow shutdown

**Causa**: Worker non risponde a cancellation.

**Soluzione**:
```python
# ✅ Handler rispetta cancellation
@job_listener(queue="jobs")
class JobListener(JobListener):
    @bind
    async def handle(self, message: Message):
        for item in message.body['items']:
            # Permetti cancellazione tra items
            await asyncio.sleep(0)
            await self.process(item)
```

## 📖 Comandi CLI

```bash
# Lista listener disponibili
vega listener list

# Esegui tutti i listener
vega listener run

# Esegui da directory specifica
vega listener run --path ./my-project

# Genera nuovo listener
vega generate listener <Nome>
vega generate listener SendEmail --queue emails --workers 3
vega generate listener ProcessOrder --queue orders --workers 5 --retry

# Alias
vega generate event-handler <Nome>  # Alias per listener
```

## 🔗 Risorse

- **Codice**: `vega/listeners/`
- **Test**: `tests/unit/test_listeners.py`, `tests/LISTENER_TESTS.md`
- **Esempi**: Vedi sezione [Esempi Pratici](#esempi-pratici)
- **AWS SQS Docs**: https://docs.aws.amazon.com/sqs/
- **Clean Architecture**: https://blog.cleancoder.com/

---

**Domande o problemi?** Apri una issue su GitHub o consulta la documentazione ufficiale Vega Framework.
