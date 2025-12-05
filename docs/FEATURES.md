# Vega Framework - Features Overview

Panoramica completa delle funzionalità del framework Vega.

## 🎯 Core Features

### Clean Architecture
- ✅ Separazione Domain/Application/Infrastructure/Presentation
- ✅ Dependency Rule enforcement
- ✅ Framework-agnostic domain layer

### Dependency Injection
- ✅ Container IoC completo
- ✅ `@injectable` per classi
- ✅ `@bind` per metodi
- ✅ Tre scope: Singleton, Scoped, Transient
- ✅ `@bean` per auto-registrazione
- ✅ `Summon()` per service locator

### Design Patterns
- ✅ **Interactor** - Use case pattern con metaclass auto-call
- ✅ **Mediator** - Orchestrazione workflow complessi
- ✅ **Repository** - Astrazione data persistence
- ✅ **Service** - Astrazione servizi esterni

## 🌐 Vega Web

Framework web built on Starlette con API FastAPI-like:

- ✅ **VegaApp** - ASGI application
- ✅ **Router** - Routing modulare
- ✅ **OpenAPI** - Schema auto-generation
- ✅ **Swagger UI** - Documentazione interattiva (`/docs`)
- ✅ **ReDoc** - Documentazione alternativa (`/redoc`)
- ✅ **Dependency Injection** - Integrata nelle route
- ✅ **Route Middleware** - Middleware per route specifiche
- ✅ **Request/Response** - Type-safe models
- ✅ **WebSocket** - Support completo

**Documentazione**: [Vega Web Guide](VEGA_WEB.md) *(da creare)*

## 🎪 Event System

Sistema event-driven nativo con publish/subscribe:

- ✅ **EventBus** - Message broker interno
- ✅ **@subscribe** - Decorator per handler
- ✅ **Event.publish()** - Publishing asincrono
- ✅ **@trigger** - Auto-publish dopo interactor
- ✅ **Event Middleware** - Interceptors per eventi
- ✅ **Type-safe** - Event dataclass-based

**Esempio**:
```python
@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str

@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    await email_service.send(event.email, "Welcome!")

# Trigger
await UserCreated(user_id="123", email="test@test.com").publish()
```

## 🔄 Async Listeners (NEW!)

Sistema per background job processing con code di messaggi:

- ✅ **Driver Agnostic** - SQS, RabbitMQ, Redis
- ✅ **Auto-Discovery** - Registrazione automatica listener
- ✅ **Worker Concorrenti** - Scalabilità orizzontale
- ✅ **Retry Logic** - Exponential backoff automatico
- ✅ **Lifecycle Hooks** - on_startup/shutdown/error
- ✅ **Long Polling** - Efficienza energetica
- ✅ **Graceful Shutdown** - SIGTERM/SIGINT handling
- ✅ **DI Integration** - Full dependency injection

**Documentazione Completa**: [Async Listeners Guide](ASYNC_LISTENERS.md)

**Quick Start**:
```python
from vega.listeners import JobListener, job_listener, Message
from vega.di import bind

@job_listener(queue="emails", workers=3)
class SendEmailListener(JobListener):
    @bind
    async def handle(self, message: Message, email_service: EmailService):
        await email_service.send(**message.body)
```

**CLI**:
```bash
vega listener run              # Esegui tutti i listener
vega listener list             # Lista listener registrati
vega generate listener <Nome>  # Genera nuovo listener
```

## 🔍 Auto-Discovery

Sistema di auto-discovery per componenti:

- ✅ **discover_beans()** - Bean discovery automatica
- ✅ **discover_routers()** - Route discovery
- ✅ **discover_event_handlers()** - Event handler discovery
- ✅ **discover_listeners()** - Job listener discovery *(NEW!)*
- ✅ **discover_commands()** - CLI command discovery

**Esempio**:
```python
from vega.discovery import discover_beans, discover_routers, discover_listeners

# Auto-register tutto
discover_beans("infrastructure")
discover_routers(app, "presentation.web.routes")
discover_listeners("infrastructure.listeners")
```

## ⚙️ Settings Management

Configuration management con Pydantic v2:

- ✅ **BaseSettings** - Type-safe settings
- ✅ **.env support** - Environment variables
- ✅ **Validation** - Automatic type validation
- ✅ **Nested Config** - Complex configurations

## 🛠️ CLI Tools

Potente CLI per scaffolding e gestione:

### Project Management
```bash
vega init my-app                    # Nuovo progetto
vega init my-api --template web     # Con Vega Web
vega doctor                         # Valida architettura
vega update                         # Aggiorna framework
```

### Code Generation
```bash
# Domain
vega generate entity Product
vega generate repository ProductRepository
vega generate repository Product --impl memory
vega generate service EmailService
vega generate interactor CreateProduct

# Application
vega generate mediator CheckoutWorkflow

# Presentation
vega generate router Product                    # Web router
vega generate command create-product            # CLI command
vega generate middleware Logging
vega generate webmodel CreateUserRequest

# Infrastructure
vega generate model Product                     # SQLAlchemy
vega generate listener SendEmail --queue emails # Async listener (NEW!)

# Events
vega generate event UserCreated
vega generate subscriber SendWelcomeEmail
```

### Feature Management
```bash
vega add web         # Aggiungi Vega Web
vega add sqlalchemy  # Aggiungi database support
```

### Database Migrations
```bash
vega migrate init                    # Init database
vega migrate create -m "add users"   # Crea migration
vega migrate upgrade                 # Applica migrations
```

### Development Server
```bash
vega web run         # Esegui dev server

# Listener management (NEW!)
vega listener run    # Esegui job listeners
vega listener list   # Lista listener attivi
```

## 🧪 Testing

Framework di testing integrato:

- ✅ **Pytest** - Test runner
- ✅ **pytest-asyncio** - Async test support
- ✅ **Test Fixtures** - Shared fixtures
- ✅ **Test Markers** - unit, functional, integration
- ✅ **Coverage** - pytest-cov integration

**Test Structure**:
```
tests/
├── unit/           # Unit tests
├── functional/     # Functional tests
└── integration/    # Integration tests
```

**Run Tests**:
```bash
pytest                  # All tests
pytest -m unit         # Unit only
pytest -m functional   # Functional only
pytest --cov=vega      # With coverage
```

## 📊 Monitoring & Observability

- ✅ **Structured Logging** - JSON logging support
- ✅ **Metrics** - Prometheus integration ready
- ✅ **Error Tracking** - Sentry integration ready
- ✅ **Request Tracing** - Built-in middleware

## 🔒 Security

- ✅ **CORS Middleware** - Configurable CORS
- ✅ **Authentication** - Built-in auth middleware
- ✅ **Input Validation** - Pydantic models
- ✅ **SQL Injection** - Safe with SQLAlchemy
- ✅ **XSS Protection** - Response escaping

## 📦 Supported Databases

- ✅ **PostgreSQL** - Via SQLAlchemy
- ✅ **MySQL** - Via SQLAlchemy
- ✅ **SQLite** - Via SQLAlchemy
- ✅ **In-Memory** - For testing
- ✅ **MongoDB** - Custom implementation
- ✅ **Redis** - Custom implementation

## 📨 Message Queues

- ✅ **AWS SQS** - Native support (NEW!)
- 🔄 **RabbitMQ** - Coming soon
- 🔄 **Redis Streams** - Coming soon
- ✅ **Custom Drivers** - Extensible interface

## 🚀 Performance

- ✅ **Async/Await** - Full async support
- ✅ **Connection Pooling** - Database pools
- ✅ **Lazy Loading** - On-demand imports
- ✅ **Caching** - Built-in caching support
- ✅ **Batch Operations** - Bulk processing

## 📚 Documentation

| Feature | Documentation | Status |
|---------|--------------|--------|
| **Getting Started** | [README.md](../README.md) | ✅ Complete |
| **Clean Architecture** | [CLAUDE.md](../CLAUDE.md) | ✅ Complete |
| **Async Listeners** | [ASYNC_LISTENERS.md](ASYNC_LISTENERS.md) | ✅ Complete |
| **Quick Reference** | [LISTENER_QUICK_REFERENCE.md](LISTENER_QUICK_REFERENCE.md) | ✅ Complete |
| **Examples** | [examples/listeners/](examples/listeners/) | ✅ 3 esempi |
| **Vega Web** | *To be created* | ⏳ Pending |
| **Events** | *To be created* | ⏳ Pending |
| **Testing Guide** | [tests/README.md](../tests/README.md) | ✅ Complete |
| **API Reference** | *To be generated* | ⏳ Pending |

## 🎯 Roadmap

### v1.1 (Current - Async Listeners)
- ✅ Async Listener system
- ✅ SQS Driver
- ✅ Auto-discovery listeners
- ✅ CLI commands for listeners
- ⚠️ Bug fix: scope_context async support

### v1.2 (Planned)
- 🔄 RabbitMQ Driver
- 🔄 Redis Streams Driver
- 🔄 Listener metrics & monitoring
- 🔄 Dead Letter Queue enhancements
- 🔄 Batch message processing

### v2.0 (Future)
- 🔄 GraphQL support
- 🔄 gRPC support
- 🔄 WebSocket advanced features
- 🔄 Distributed tracing
- 🔄 Service mesh integration

## 💡 Philosophy

Vega Framework è costruito sui seguenti principi:

1. **Clean Architecture First** - Architettura pulita non è opzionale
2. **Type Safety** - Type hints ovunque possibile
3. **Explicit over Implicit** - Chiaro e verboso > magico e conciso
4. **Convention over Configuration** - Sensible defaults
5. **Developer Experience** - CLI tools e scaffolding
6. **Production Ready** - Non solo per prototipi
7. **Testability** - Testing facile e naturale

## 🤝 Contributing

Contribuisci al progetto:

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Apri Pull Request

**Guidelines**:
- Segui Clean Architecture principles
- Aggiungi test per nuove feature
- Mantieni >80% code coverage
- Documenta API pubbliche
- Usa type hints

## 📄 License

MIT License - Vedi [LICENSE](../LICENSE) per dettagli

---

**Vega Framework** - Clean Architecture for Python
