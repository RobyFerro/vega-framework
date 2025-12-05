# Async Listeners - Release Notes

**Branch**: `feature/async-listener`
**Data**: 2025-12-05
**Status**: ✅ Documentazione Completa | ⚠️ Bug da Risolvere | ✅ Test Unitari Completi

## 🎯 Overview

Implementazione completa del sistema **Async Listener** per background job processing con code di messaggi (SQS, RabbitMQ, Redis).

## ✨ Nuove Funzionalità

### Core System
- ✅ **JobListener** - Classe base per listener asincroni
- ✅ **@job_listener** - Decorator per registrazione listener
- ✅ **Message & MessageContext** - Data structures per messaggi
- ✅ **QueueDriver** - Interfaccia astratta per driver code
- ✅ **ListenerManager** - Orchestratore lifecycle listener
- ✅ **Registry System** - Sistema registrazione globale

### Driver
- ✅ **SQSDriver** - Driver AWS SQS completo (richiede aioboto3)
- 🔄 **RabbitMQDriver** - Pianificato per v1.2
- 🔄 **RedisDriver** - Pianificato per v1.2

### Auto-Discovery
- ✅ **discover_listeners()** - Auto-discovery da package
- ✅ Integrazione con sistema discovery esistente

### CLI Commands
- ✅ **vega listener run** - Esegue tutti i listener
- ✅ **vega listener list** - Lista listener registrati
- ✅ **vega generate listener** - Genera nuovo listener con template

### Features
- ✅ **Auto-Acknowledgment** - Ack/reject automatico su successo/errore
- ✅ **Manual Acknowledgment** - Controllo fine-grained con MessageContext
- ✅ **Retry Logic** - Exponential backoff automatico
- ✅ **Worker Concorrenti** - Scalabilità orizzontale configurabile
- ✅ **Long Polling** - Efficienza energetica (wait_time configurabile)
- ✅ **Lifecycle Hooks** - on_startup/shutdown/error
- ✅ **Dependency Injection** - Integrazione completa con sistema DI
- ✅ **Graceful Shutdown** - SIGTERM/SIGINT handling

## 📚 Documentazione Creata

### Guide Principali
1. **[docs/ASYNC_LISTENERS.md](docs/ASYNC_LISTENERS.md)** (98KB)
   - Guida completa al sistema
   - Architettura e componenti
   - Tutti i pattern d'uso
   - Configurazione driver
   - Best practices
   - Troubleshooting

2. **[docs/LISTENER_QUICK_REFERENCE.md](docs/LISTENER_QUICK_REFERENCE.md)** (8KB)
   - Reference rapido per sviluppatori
   - Pattern comuni
   - Comandi CLI
   - Quick fixes troubleshooting

3. **[docs/FEATURES.md](docs/FEATURES.md)** (12KB)
   - Overview completo features framework
   - Include sezione dedicata async listener

### Esempi Pratici
4. **[docs/examples/listeners/](docs/examples/listeners/)**
   - **README.md** - Indice esempi
   - **01_email_notifications.py** - Sistema email asincrone
   - **02_image_processing.py** - Pipeline processing immagini
   - **03_webhook_handler.py** - Handler webhook esterni (Stripe, GitHub)

### Test Documentation
5. **[tests/LISTENER_TESTS.md](tests/LISTENER_TESTS.md)**
   - Coverage report completo
   - Test status per componente
   - Known issues
   - Future improvements

### Integration
6. **[docs/README.md](docs/README.md)** - Aggiornato con sezione Async Listeners

## 🧪 Test Suite

### Test Creati
- **29 test unitari** - TUTTI PASSANO ✅
  - 20 test in `test_listeners.py`
  - 9 test in `test_listener_discovery.py`

### Coverage per Componente
| Componente | Coverage | Status |
|------------|----------|--------|
| `decorators.py` | 100% | ✅ Completo |
| `message.py` | 100% | ✅ Completo |
| `registry.py` | 100% | ✅ Completo |
| `__init__.py` | 100% | ✅ Completo |
| `listener.py` | 92% | ✅ Quasi completo |
| `discovery/listeners.py` | 93% | ✅ Quasi completo |
| `driver.py` | 71% | ⚠️ Metodi astratti (normale) |
| `manager.py` | 13% | ❌ Bloccato da bug |
| `drivers/sqs.py` | 0% | ⚠️ Richiede integration test |

### Test Implementati ma Bloccati
- **10 test funzionali** in `test_listener_workflows.py`
  - Mock QueueDriver completo
  - Test workflow auto-ack/manual-ack
  - Test lifecycle hooks
  - Test dependency injection
  - ⚠️ Bloccati da bug in manager (vedi sotto)

## ⚠️ Known Issues

### Bug Critico: scope_context() Non Async-Compatible

**Location**: `vega/listeners/manager.py:212`

**Problema**:
```python
async with scope_context():  # ❌ TypeError!
    await listener.handle(message)
```

**Root Cause**:
`scope_context()` in `vega/di/scope.py` è un context manager **sincrono** (usa `@contextmanager` e `yield`), ma viene usato come **async context manager** nel ListenerManager.

**Error**:
```
TypeError: '_GeneratorContextManager' object does not support the asynchronous context manager protocol
```

**Impact**:
- ❌ Blocca tutti i test funzionali del manager
- ❌ Listener manager non funzionante in produzione
- ✅ Non impatta test unitari (tutti passano)

**Soluzioni Possibili**:

1. **Convertire scope_context() ad async** (raccomandato):
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def scope_context():
    was_active = _scope_manager.is_scope_active()
    if not was_active:
        _scope_manager.set_scope_active(True)
    try:
        yield
    finally:
        if not was_active:
            _scope_manager.set_scope_active(False)
            _scope_manager.clear_scoped_cache()
```

2. **Rimuovere uso di scope_context** dal manager:
```python
# Rimuovi async with scope_context()
# Gestisci scope manualmente se necessario
```

3. **Usare wrapper sincrono**:
```python
with scope_context():  # Sync
    await listener.handle(message)
```

**Priority**: 🔴 **Alta** - Blocca funzionalità core

## 📁 File Modificati/Creati

### Codice Sorgente (già nel branch)
```
vega/listeners/
├── __init__.py
├── decorators.py
├── driver.py
├── listener.py
├── manager.py
├── message.py
├── registry.py
└── drivers/
    ├── __init__.py
    └── sqs.py

vega/discovery/
└── listeners.py

vega/cli/commands/
└── listener.py

vega/cli/templates/infrastructure/
└── listener.py.j2
```

### Documentazione (NUOVA)
```
docs/
├── ASYNC_LISTENERS.md              (98 KB - Guida completa)
├── LISTENER_QUICK_REFERENCE.md     (8 KB - Reference rapido)
├── FEATURES.md                      (12 KB - Features overview)
├── README.md                        (aggiornato)
└── examples/listeners/
    ├── README.md
    ├── 01_email_notifications.py
    ├── 02_image_processing.py
    └── 03_webhook_handler.py
```

### Test (NUOVI)
```
tests/
├── LISTENER_TESTS.md                    (Coverage report)
├── unit/
│   ├── test_listeners.py                (20 test - ✅ passing)
│   └── test_listener_discovery.py       (9 test - ✅ passing)
├── functional/
│   └── test_listener_workflows.py       (10 test - ⚠️ blocked)
└── conftest.py                          (aggiornato con marker)
```

## 🎯 Checklist Pre-Merge

### ✅ Completato
- [x] Implementazione core system
- [x] SQS Driver
- [x] Auto-discovery
- [x] CLI commands
- [x] Template generation
- [x] Documentazione completa
- [x] Quick reference
- [x] Esempi pratici (3)
- [x] Test unitari (29/29 passing)
- [x] Test coverage report
- [x] Mock driver per testing
- [x] Marker pytest
- [x] Integration con docs esistente

### ⚠️ Da Risolvere Prima del Merge
- [ ] **Bug scope_context()** - CRITICO
- [ ] Test funzionali (bloccati da bug)
- [ ] Integration test con SQS reale (opzionale)

### 🔄 Post-Merge / v1.2
- [ ] RabbitMQ Driver
- [ ] Redis Driver
- [ ] Metrics & monitoring
- [ ] DLQ enhancements
- [ ] Batch processing
- [ ] Performance benchmarks

## 📊 Statistiche

### Linee di Codice
- **Codice**: ~2,000 righe (già nel branch)
- **Test**: ~800 righe (nuovo)
- **Documentazione**: ~2,500 righe (nuovo)
- **Esempi**: ~500 righe (nuovo)
- **Totale Nuovo**: ~3,800 righe

### Coverage
- **Unit Test Coverage**: ~95% (componenti core)
- **Functional Coverage**: 0% (bloccato da bug)
- **Overall Coverage**: ~75% (escludendo manager e drivers)

### Documentazione
- **Guide**: 2 (completa + quick reference)
- **Esempi**: 3 (email, images, webhooks)
- **Test Docs**: 1 (coverage report)
- **Feature Docs**: 1 (features overview)

## 🚀 Come Usare

### Setup Rapido
```bash
# 1. Installa dipendenze
poetry add aioboto3  # Per SQS

# 2. Configura driver in config.py
from vega.listeners.drivers.sqs import SQSDriver
container = Container({QueueDriver: SQSDriver})

# 3. Genera listener
vega generate listener SendEmail --queue emails --workers 3

# 4. Implementa handle()
# Vedi docs/ASYNC_LISTENERS.md per esempi

# 5. Esegui
vega listener run
```

### Esempio Minimo
```python
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind

@job_listener(queue="emails", workers=3)
class EmailListener(JobListener):
    @bind
    async def handle(self, message: Message, email_service: EmailService):
        await email_service.send(**message.body)
```

## 📖 Risorse

### Documentazione
- **Guida Completa**: [docs/ASYNC_LISTENERS.md](docs/ASYNC_LISTENERS.md)
- **Quick Reference**: [docs/LISTENER_QUICK_REFERENCE.md](docs/LISTENER_QUICK_REFERENCE.md)
- **Esempi**: [docs/examples/listeners/](docs/examples/listeners/)

### Test
- **Unit Tests**: `poetry run pytest -m "unit and listeners" -v`
- **Coverage**: [tests/LISTENER_TESTS.md](tests/LISTENER_TESTS.md)

### Comandi
```bash
vega listener run              # Esegui listener
vega listener list             # Lista listener
vega generate listener <Nome>  # Genera listener
```

## 🤝 Contributors

- **Roberto Ferro** - Implementazione iniziale (branch feature/async-listener)
- **Claude (Anthropic)** - Documentazione completa e test suite

## 📅 Timeline

- **2025-11-27**: Commit iniziale - "Implementata logica per gestire lavori asincroni (non testata)"
- **2025-12-05**: Documentazione completa e test suite
- **TBD**: Bug fix scope_context() e merge to master

## 🎓 Next Steps

1. **Fix Bug scope_context()** - Priority alta
2. **Run functional tests** - Dopo bug fix
3. **Integration testing** - Con LocalStack SQS
4. **Code review** - Team review
5. **Merge to master** - Dopo tests passing
6. **Release v1.1** - Con async listeners

---

**Vega Framework** - Clean Architecture for Python
**Feature**: Async Listeners
**Status**: ✅ Documentazione Completa | ⚠️ Bug da Risolvere
