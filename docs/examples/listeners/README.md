# Async Listener - Esempi Pratici

Raccolta di esempi completi e pronti all'uso per implementare listener comuni.

## 📁 Struttura

```
examples/listeners/
├── README.md                           # Questo file
├── 01_email_notifications.py          # Sistema notifiche email
├── 02_image_processing.py             # Pipeline processing immagini
├── 03_webhook_handler.py              # Handler webhook esterni
├── 04_payment_processing.py           # Processing pagamenti
├── 05_report_generation.py            # Generazione report batch
├── 06_data_sync.py                    # Sincronizzazione dati
└── 07_cleanup_tasks.py                # Task di pulizia periodici
```

## 🚀 Come Usare gli Esempi

1. **Copia il file** nella tua directory `infrastructure/listeners/`
2. **Adatta le dipendenze** ai tuoi repository/service
3. **Configura la coda** in AWS/LocalStack
4. **Testa** con messaggi di esempio
5. **Deploy** e monitora

## 📚 Esempi Disponibili

### 1. Email Notifications
**File**: `01_email_notifications.py`
**Use Case**: Inviare email transazionali (welcome, reset password, conferme)
**Complessità**: ⭐ Facile

### 2. Image Processing
**File**: `02_image_processing.py`
**Use Case**: Resize, crop, watermark automatico immagini
**Complessità**: ⭐⭐ Media

### 3. Webhook Handler
**File**: `03_webhook_handler.py`
**Use Case**: Processare webhook da Stripe, PayPal, GitHub
**Complessità**: ⭐⭐ Media

### 4. Payment Processing
**File**: `04_payment_processing.py`
**Use Case**: Processamento asincrono pagamenti con retry
**Complessità**: ⭐⭐⭐ Avanzata

### 5. Report Generation
**File**: `05_report_generation.py`
**Use Case**: Generare PDF/Excel report in background
**Complessità**: ⭐⭐ Media

### 6. Data Synchronization
**File**: `06_data_sync.py`
**Use Case**: Sincronizzare dati tra database/API
**Complessità**: ⭐⭐⭐ Avanzata

### 7. Cleanup Tasks
**File**: `07_cleanup_tasks.py`
**Use Case**: Pulizia automatica file temporanei, vecchi record
**Complessità**: ⭐ Facile

## 🧪 Testing degli Esempi

Ogni esempio include unit test in `tests/examples/listeners/`:

```bash
# Testa singolo esempio
poetry run pytest tests/examples/listeners/test_01_email_notifications.py

# Testa tutti gli esempi
poetry run pytest tests/examples/listeners/ -v
```

## 📝 Template Base

Usa questo template per creare nuovi listener:

```python
"""
<Nome Listener> - <Descrizione breve>

Formato messaggio atteso:
{
    "field1": "value1",
    "field2": "value2"
}
"""
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind
from domain.services import MyService
import logging

logger = logging.getLogger(__name__)


@job_listener(
    queue="my-queue",
    workers=3,
    auto_ack=True,
    visibility_timeout=30,
    retry_on_error=False,
    max_retries=3
)
class MyListener(JobListener):
    """
    Descrizione dettagliata del listener.

    Attributes:
        Eventuali attributi di istanza
    """

    async def on_startup(self) -> None:
        """Inizializzazione (opzionale)"""
        logger.info("MyListener started")

    async def on_shutdown(self) -> None:
        """Cleanup (opzionale)"""
        logger.info("MyListener stopped")

    async def on_error(self, message: Message, error: Exception) -> None:
        """Gestione errori (opzionale)"""
        logger.error(f"Error processing {message.id}: {error}")

    @bind
    async def handle(self, message: Message, my_service: MyService) -> None:
        """
        Processa messaggio dalla coda.

        Args:
            message: Messaggio da processare
            my_service: Servizio iniettato automaticamente

        Raises:
            ValueError: Se messaggio non valido
            ServiceError: Se servizio esterno fallisce
        """
        # Validazione input
        if not message.body.get('field1'):
            raise ValueError("field1 is required")

        # Business logic
        result = await my_service.do_something(message.body)

        # Log successo
        logger.info(f"Processed message {message.id}: {result}")
```

## 🔗 Risorse

- [Documentazione Completa](../../ASYNC_LISTENERS.md)
- [Quick Reference](../../LISTENER_QUICK_REFERENCE.md)
- [Test Coverage](../../../tests/LISTENER_TESTS.md)

---

**Contribuisci!** Hai un esempio interessante? Aggiungi un PR con il tuo listener!
