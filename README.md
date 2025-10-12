# Vega Framework

An enterprise-ready Python framework that enforces Clean Architecture for building maintainable and scalable applications.

## Why Vega?

Traditional Python frameworks show you **how to build** but don't enforce **how to architect**. Vega provides:

- ✅ **Clean Architecture** - Enforced separation of concerns
- ✅ **Dependency Injection** - Zero boilerplate, type-safe DI
- ✅ **Business Logic First** - Pure, testable, framework-independent
- ✅ **CLI Scaffolding** - Generate entire projects and components
- ✅ **Async Support** - Full async/await for CLI and web
- ✅ **Vega Web (Starlette) & SQLAlchemy** - Built-in integrations when needed

**[Read the Philosophy →](docs/explanation/philosophy.md)** to understand why architecture matters.

## Quick Start

### Installation

```bash
pip install vega-framework
```

### Create Your First Project

```bash
# Create project
vega init my-app
cd my-app

# Install dependencies
poetry install

# Generate components
vega generate entity User
vega generate repository UserRepository --impl memory
vega generate interactor CreateUser

# Run your app
poetry run python main.py
```

### Your First Use Case

```python
# domain/interactors/create_user.py
from vega.patterns import Interactor
from vega.di import bind

class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        # Pure business logic - no framework code!
        user = User(name=self.name, email=self.email)
        return await repository.save(user)

# Usage - clean and simple
user = await CreateUser(name="John", email="john@example.com")
```

**[See Full Quick Start →](docs/tutorials/quickstart.md)**

## Key Concepts

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│      Presentation (CLI, Web)        │  User interfaces
├─────────────────────────────────────┤
│      Application (Workflows)        │  Multi-step operations
├─────────────────────────────────────┤
│      Domain (Business Logic)        │  Core business rules
├─────────────────────────────────────┤
│      Infrastructure (Technical)     │  Databases, APIs
└─────────────────────────────────────┘
```

**[Learn Clean Architecture →](docs/explanation/architecture/clean-architecture.md)**

### Core Patterns

- **[Interactor](docs/explanation/patterns/interactor.md)** - Single-purpose use case
- **[Mediator](docs/explanation/patterns/mediator.md)** - Complex workflow orchestration
- **[Repository](docs/explanation/patterns/repository.md)** - Data persistence abstraction
- **[Service](docs/explanation/patterns/service.md)** - External service abstraction

### Dependency Injection

```python
# Define what you need (domain)
class UserRepository(Repository[User]):
    async def save(self, user: User) -> User:
        pass

# Implement how it works (infrastructure)
@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # PostgreSQL implementation
        pass

# Wire it together (config)
container = Container({
    UserRepository: PostgresUserRepository
})
```

**[Learn Dependency Injection →](docs/explanation/core/dependency-injection.md)**

## CLI Commands

### Project Management

```bash
vega init my-app                      # Create new project
vega init my-api --template web       # Create with Vega Web
vega doctor                           # Validate architecture
vega update                           # Update framework
```

### Code Generation

```bash
# Domain layer
vega generate entity Product
vega generate repository ProductRepository --impl sql
vega generate interactor CreateProduct

# Application layer
vega generate mediator CheckoutWorkflow

# Presentation layer
vega generate router Product          # Vega Web (requires: vega add web)
vega generate command create-product  # CLI

# Infrastructure
vega generate model Product           # SQLAlchemy (requires: vega add db)
```

### Add Features

```bash
vega add web         # Add Vega Web support
vega add sqlalchemy  # Add database support
```

### Database Migrations

```bash
vega migrate init                    # Initialize database
vega migrate create -m "add users"   # Create migration
vega migrate upgrade                 # Apply migrations
vega migrate downgrade              # Rollback
```

**[See All CLI Commands →](docs/reference/cli/overview.md)**

## Event System

Built-in event-driven architecture support:

```python
from vega.events import Event, subscribe

# Define event
@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str

# Subscribe to event
@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    await email_service.send(event.email, "Welcome!")

# Publish event
await UserCreated(user_id="123", email="test@test.com").publish()
```

**[Learn Event System →](docs/explanation/events/overview.md)**

## Documentation

### Getting Started
- [Installation](docs/how-to/install.md)
- [Quick Start](docs/tutorials/quickstart.md)
- [Project Structure](docs/explanation/project-structure.md)

### Core Concepts
- [Philosophy](docs/explanation/philosophy.md) - Why Vega exists
- [Clean Architecture](docs/explanation/architecture/clean-architecture.md) - Architecture principles
- [Dependency Injection](docs/explanation/core/dependency-injection.md) - DI system
- [Patterns](docs/explanation/patterns/interactor.md) - Interactor, Mediator, Repository, Service

### Guides
- [Use Vega Web](docs/how-to/use-vega-web.md) - Build HTTP APIs with Vega's router and middleware
- [Building Domain Layer](docs/how-to/build-domain-layer.md) - Business logic first
- [CLI Reference](docs/reference/cli/overview.md) - All CLI commands
- [Events System](docs/explanation/events/overview.md) - Event-driven architecture

### Reference
- [Changelog](docs/reference/CHANGELOG.md)
- [Roadmap](docs/reference/ROADMAP.md)

**[Browse All Documentation →](docs/README.md)**

## Perfect For

- E-commerce platforms
- Financial systems
- Enterprise SaaS applications
- AI/RAG applications
- Complex workflow systems
- Multi-tenant applications
- Any project requiring clean architecture

## Example Project

```
my-app/
├── domain/                    # Business logic
│   ├── entities/             # Business objects
│   ├── repositories/         # Data interfaces
│   ├── services/             # External service interfaces
│   └── interactors/          # Use cases
├── application/              # Workflows
│   └── mediators/            # Complex orchestrations
├── infrastructure/           # Implementations
│   ├── repositories/         # Database code
│   └── services/             # API integrations
├── presentation/             # User interfaces
│   ├── cli/                  # CLI commands
│   └── web/                  # Vega Web routes
├── config.py                 # Dependency injection
├── settings.py               # Configuration
└── main.py                   # Entry point
```

## Why Clean Architecture?

**Without Vega:**
```python
# ❌ Business logic mixed with framework code
@app.post("/orders")
async def create_order(request: Request):
    data = await request.json()
    order = OrderModel(**data)  # SQLAlchemy
    session.add(order)
    stripe.Charge.create(...)   # Stripe
    return {"id": order.id}
```

**Problems:**
- Can't test without the web framework, database, and Stripe
- Can't reuse for CLI or other interfaces
- Business rules are unclear
- Tightly coupled to specific technologies

**With Vega:**
```python
# ✅ Pure business logic (Domain)
class PlaceOrder(Interactor[Order]):
    @bind
    async def call(
        self,
        order_repo: OrderRepository,
        payment_service: PaymentService
    ) -> Order:
        # Pure business logic - testable, reusable
        order = Order(...)
        await payment_service.charge(...)
        return await order_repo.save(order)

# ✅ Vega Web route (Presentation) - just wiring
@router.post("/orders")
async def create_order_api(request: CreateOrderRequest):
    return await PlaceOrder(...)

# ✅ CLI command (Presentation) - same logic
@click.command()
async def create_order_cli(...):
    return await PlaceOrder(...)
```

**Benefits:**
- ✅ Test business logic without any infrastructure
- ✅ Same logic works for Web, CLI, GraphQL, etc.
- ✅ Swap databases without changing business code
- ✅ Clear business rules and operations

## Community & Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/RobyFerro/vega-framework/issues)
- **Documentation**: [Complete guides and API reference](docs/README.md)
- **Examples**: Check `examples/` directory for working code

## Contributing

Contributions are welcome! This framework is extracted from production code and battle-tested in real-world applications.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for developers who care about architecture.**

[Get Started →](docs/tutorials/quickstart.md) | [Read Philosophy →](docs/explanation/philosophy.md) | [View Documentation →](docs/README.md)

