# Async Listener - Quick Reference

Riferimento rapido per il sistema Async Listener di Vega Framework.

## 📦 Setup Iniziale

```bash
# 1. Installa dipendenze (es. SQS)
poetry add aioboto3

# 2. Configura driver in config.py
from vega.di import Container
from vega.listeners.drivers.sqs import SQSDriver
from vega.listeners.driver import QueueDriver

container = Container({
    QueueDriver: SQSDriver,
})

# 3. Genera listener
vega generate listener SendEmail --queue emails --workers 3

# 4. Esegui
vega listener run
```

## 🎨 Pattern Base

### Auto-Ack (Raccomandato)

```python
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind

@job_listener(queue="emails", workers=3)
class EmailListener(JobListener):
    @bind
    async def handle(self, message: Message, email_service: EmailService):
        await email_service.send(**message.body)
        # ✅ Auto-ack su successo
        # ❌ Auto-reject su errore
```

### Manual Ack

```python
@job_listener(queue="orders", auto_ack=False)
class OrderListener(JobListener):
    @bind
    async def handle(self, message: Message, context: MessageContext):
        try:
            await self.process(message.body)
            await context.ack()  # Esplicito
        except TemporaryError:
            await context.reject(requeue=True)  # Retry
        except PermanentError:
            await context.reject(requeue=False)  # DLQ
```

### Con Retry

```python
@job_listener(
    queue="api-calls",
    retry_on_error=True,
    max_retries=5
)
class APIListener(JobListener):
    @bind
    async def handle(self, message: Message, api: APIClient):
        # Retry automatico con exponential backoff
        await api.call(message.body)
```

## ⚙️ Parametri Decorator

```python
@job_listener(
    queue="nome-coda",          # Required: Nome coda
    workers=1,                  # Worker concorrenti (default: 1)
    auto_ack=True,             # Auto-acknowledge (default: True)
    visibility_timeout=30,      # Secondi (default: 30)
    max_messages=1,            # Messaggi per poll (default: 1)
    retry_on_error=False,      # Retry automatico (default: False)
    max_retries=3              # Tentativi max (default: 3)
)
```

## 🔄 Lifecycle Hooks

```python
@job_listener(queue="jobs")
class MyListener(JobListener):
    async def on_startup(self):
        # Chiamato UNA volta all'avvio
        self.client = await SomeClient.connect()

    async def on_shutdown(self):
        # Chiamato UNA volta allo shutdown
        await self.client.close()

    async def on_error(self, message: Message, error: Exception):
        # Chiamato PER OGNI errore dopo retry
        logger.error(f"Failed: {error}")

    @bind
    async def handle(self, message: Message):
        # Processamento messaggio
        pass
```

## 📨 Message & Context

```python
# Message
message.id                  # ID messaggio
message.body               # Dict payload
message.data               # Alias per body
message.attributes         # Metadata
message.receipt_handle     # Handle interno
message.received_count     # Numero ricezioni
message.timestamp          # Timestamp ricezione

# MessageContext (solo auto_ack=False)
await context.ack()                              # Acknowledge
await context.reject(requeue=True)              # Reject con retry
await context.reject(requeue=False)             # Reject → DLQ
await context.extend_visibility(seconds=300)    # Estendi timeout
```

## 🔌 Driver SQS

```python
from vega.listeners.drivers.sqs import SQSDriver
from vega.di import bean, Scope

@bean(
    region_name="us-east-1",
    aws_access_key_id=None,          # None = usa IAM role
    aws_secret_access_key=None,
    endpoint_url=None,               # LocalStack: "http://localhost:4566"
    scope=Scope.SINGLETON,
    interface=QueueDriver
)
class MySQSDriver(SQSDriver):
    pass
```

## 💉 Dependency Injection

```python
from vega.di import bind

@job_listener(queue="orders")
class OrderListener(JobListener):
    @bind
    async def handle(
        self,
        message: Message,
        # Tutte auto-iniettate!
        user_repo: UserRepository,
        email_service: EmailService,
        payment_service: PaymentService
    ):
        # Usa dipendenze
        pass
```

## 🧪 Testing

```python
from tests.functional.test_listener_workflows import MockQueueDriver

async def test_listener():
    # Mock driver
    driver = MockQueueDriver()
    message = driver.add_message("test-queue", {"data": "test"})

    # Testa listener
    listener = MyListener()
    await listener.handle(message)

    # Assert
    assert "msg-id" in driver.acknowledged
```

## 📊 Monitoring Pattern

```python
from prometheus_client import Counter, Histogram

processed = Counter('messages_processed', 'Messages', ['listener', 'status'])
duration = Histogram('processing_duration', 'Duration', ['listener'])

@job_listener(queue="jobs")
class MonitoredListener(JobListener):
    @bind
    async def handle(self, message: Message):
        with duration.labels(listener='MonitoredListener').time():
            try:
                await self.process(message.body)
                processed.labels(listener='MonitoredListener', status='ok').inc()
            except Exception:
                processed.labels(listener='MonitoredListener', status='error').inc()
                raise
```

## 🔧 Troubleshooting Quick Fixes

| Problema | Soluzione |
|----------|-----------|
| No messaggi ricevuti | Verifica driver registrato: `Summon(QueueDriver)` |
| Messaggi duplicati | Aumenta `visibility_timeout` |
| Worker bloccati | Evita operazioni sync, usa `async/await` |
| Memory leak | Usa context manager per risorse |
| Slow shutdown | Aggiungi `await asyncio.sleep(0)` in loop lunghi |

## 📝 Comandi CLI

```bash
# Lista listener
vega listener list

# Esegui listener
vega listener run
vega listener run --path ./project

# Genera listener
vega generate listener <Nome>
vega generate listener SendEmail --queue emails --workers 3
vega generate listener ProcessOrder --retry --max-retries 5

# Testing
poetry run pytest -m listeners
poetry run pytest tests/unit/test_listeners.py -v
```

## 🎯 Use Cases Comuni

### Email/Notifiche
```python
@job_listener(queue="emails", workers=5, retry_on_error=True, max_retries=3)
```

### Image/Video Processing
```python
@job_listener(queue="media", workers=2, visibility_timeout=300)
```

### API Webhooks
```python
@job_listener(queue="webhooks", workers=3, retry_on_error=False)
```

### Long Jobs
```python
@job_listener(queue="reports", workers=1, visibility_timeout=600)
```

### High Throughput
```python
@job_listener(queue="analytics", workers=10, max_messages=10)
```

## ✅ Best Practices Checklist

- [ ] Handler idempotenti (controlla duplicati)
- [ ] Visibility timeout adeguato al tempo processing
- [ ] Worker count bilanciato (I/O bound → molti, CPU bound → pochi)
- [ ] Logging strutturato con context
- [ ] Monitoring metrics (Prometheus/DataDog)
- [ ] DLQ configurata per messaggi falliti
- [ ] Error handling differenziato (temporaneo vs permanente)
- [ ] Testing con MockQueueDriver
- [ ] Cleanup risorse in on_shutdown
- [ ] Gestione cancellation per graceful shutdown

## 🔗 Collegamenti Rapidi

- **Documentazione Completa**: [ASYNC_LISTENERS.md](ASYNC_LISTENERS.md)
- **Test Coverage**: [../tests/LISTENER_TESTS.md](../tests/LISTENER_TESTS.md)
- **Codice**: `vega/listeners/`
- **Esempi**: `docs/examples/listeners/`

---

💡 **Tip**: Per debugging, usa `vega listener list` per vedere tutti i listener registrati!
