# CleanArch Framework

A lightweight Python framework for building applications with **Clean Architecture** principles.

## Features

- ✅ **Automatic Dependency Injection** - Zero boilerplate, type-safe DI
- ✅ **Clean Architecture Patterns** - Interactor, Mediator, Repository, Service
- ✅ **Scope Management** - Singleton, Scoped, Transient lifetimes
- ✅ **Type-Safe** - Full type hints support
- ✅ **Framework-Agnostic** - Works with any domain (web, AI, IoT, fintech, etc.)
- ✅ **Lightweight** - No unnecessary dependencies

## Quick Start

### Installation

```bash
# Currently: Add to your Python path
# Future: pip install cleanarch
```

### Basic Example

```python
from cleanarch.patterns import Interactor, Repository
from cleanarch.di import bind, injectable, Scope, Container, set_container
from dataclasses import dataclass
from typing import Optional

# 1. Define your entity
@dataclass
class User:
    id: str
    name: str
    email: str

# 2. Define repository interface (domain layer)
class UserRepository(Repository[User]):
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

# 3. Implement repository (infrastructure layer)
@injectable(scope=Scope.SINGLETON)
class MemoryUserRepository(UserRepository):
    def __init__(self):
        self._storage = {}

    async def get(self, id: str) -> Optional[User]:
        return self._storage.get(id)

    async def save(self, user: User) -> User:
        self._storage[user.id] = user
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        for user in self._storage.values():
            if user.email == email:
                return user
        return None

# 4. Create use case (domain layer)
class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind  # Auto-inject dependencies!
    async def call(self, repository: UserRepository) -> User:
        user = User(id="123", name=self.name, email=self.email)
        return await repository.save(user)

# 5. Setup DI container
container = Container({
    UserRepository: MemoryUserRepository,
})
set_container(container)

# 6. Use it!
user = await CreateUser(name="John", email="john@example.com")
print(user)  # User(id='123', name='John', email='john@example.com')
```

## Core Concepts

### Dependency Injection

The framework provides automatic dependency injection through decorators:

#### `@bind` - Method-level DI

```python
from cleanarch.di import bind

class MyInteractor(Interactor[Result]):
    @bind
    async def call(self, repository: UserRepository) -> Result:
        # repository is automatically injected!
        return await repository.find_all()
```

#### `@injectable` - Class-level DI

```python
from cleanarch.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class EmailService:
    def __init__(self, smtp_host: str = "localhost"):
        self.smtp_host = smtp_host

    async def send(self, to: str, message: str):
        # Send email logic
        pass
```

### Scopes

CleanArch supports three dependency scopes:

- **SINGLETON**: One instance for entire application
- **SCOPED**: One instance per operation/request
- **TRANSIENT**: New instance every time

```python
from cleanarch.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class ConfigService:
    # Single instance shared across app
    pass

@injectable(scope=Scope.SCOPED)
class RequestContext:
    # New instance per request, shared within that request
    pass

@injectable(scope=Scope.TRANSIENT)
class TemporaryService:
    # New instance every time
    pass
```

### Architecture Patterns

#### Interactor - Single Use Case

```python
from cleanarch.patterns import Interactor
from cleanarch.di import bind

class PlaceOrder(Interactor[Order]):
    def __init__(self, customer_id: str, items: list):
        self.customer_id = customer_id
        self.items = items

    @bind
    async def call(
        self,
        order_repo: OrderRepository,
        payment: PaymentService
    ) -> Order:
        order = Order(customer_id=self.customer_id, items=self.items)
        await payment.charge(order.total)
        return await order_repo.save(order)

# Usage (metaclass auto-calls call())
order = await PlaceOrder(customer_id="123", items=[...])
```

#### Mediator - Complex Workflow

```python
from cleanarch.patterns import Mediator

class CheckoutWorkflow(Mediator[Order]):
    def __init__(self, cart_id: str):
        self.cart_id = cart_id

    async def call(self) -> Order:
        # Orchestrate multiple use cases
        cart = await GetCart(self.cart_id)
        order = await PlaceOrder(cart.customer_id, cart.items)
        await SendConfirmationEmail(order.customer_email)
        await ClearCart(self.cart_id)
        return order

# Usage
order = await CheckoutWorkflow(cart_id="456")
```

#### Repository - Data Persistence

```python
from cleanarch.patterns import Repository

class ProductRepository(Repository[Product]):
    @abstractmethod
    async def find_by_category(self, category: str) -> list[Product]:
        pass

    @abstractmethod
    async def find_in_stock(self) -> list[Product]:
        pass
```

#### Service - External Integration

```python
from cleanarch.patterns import Service

class PaymentService(Service):
    @abstractmethod
    async def charge(self, amount: float, token: str) -> PaymentResult:
        pass

# Implementation
class StripePaymentService(PaymentService):
    async def charge(self, amount: float, token: str) -> PaymentResult:
        # Stripe API integration
        pass
```

## Project Structure

```
your_app/
├── domain/
│   ├── entities/          # Business entities
│   │   └── user.py
│   ├── repositories/      # Repository interfaces
│   │   └── user_repository.py
│   ├── services/          # Service interfaces
│   │   └── email_service.py
│   └── interactors/       # Use cases
│       └── create_user.py
│
├── application/
│   └── mediators/         # Complex workflows
│       └── user_registration_flow.py
│
├── infrastructure/
│   ├── repositories/      # Repository implementations
│   │   └── postgres_user_repository.py
│   └── services/          # Service implementations
│       └── sendgrid_email_service.py
│
├── config.py              # DI container setup
└── main.py
```

## Configuration

### Setup DI Container

```python
# config.py
from cleanarch.di import Container, set_container

SERVICES = {
    UserRepository: PostgresUserRepository,
    EmailService: SendgridEmailService,
    PaymentService: StripePaymentService,
}

container = Container(SERVICES)
set_container(container)
```

### Application Settings

```python
from cleanarch.settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = Field(default="my-app")
    debug: bool = Field(default=False)
    database_url: str = Field(...)
    stripe_api_key: str = Field(...)

settings = Settings()  # Loads from .env
```

## Examples

See the `examples/` directory for complete examples:

- **TODO App** - Simple CRUD application demonstrating core concepts

## Architecture Benefits

### Clean Architecture

- ✅ **Domain Layer** independent of infrastructure
- ✅ **Testable** - Easy to mock dependencies
- ✅ **Flexible** - Swap implementations without changing domain logic
- ✅ **Maintainable** - Clear separation of concerns

### Compared to Other Frameworks

| Feature | CleanArch | NestJS | Spring Boot | Django |
|---------|-----------|--------|-------------|--------|
| Language | Python | TypeScript | Java | Python |
| DI Auto-resolution | ✅ | ✅ | ✅ | ❌ |
| Clean Architecture | ✅ | Partial | ✅ | ❌ |
| Lightweight | ✅ | ❌ | ❌ | ❌ |
| Domain-agnostic | ✅ | ❌ (Web) | ❌ (Enterprise) | ❌ (Web) |

## Use Cases

CleanArch is perfect for:

- 🤖 AI/RAG applications
- 🛒 E-commerce platforms
- 💰 Fintech systems
- 📱 Mobile backends
- 🌐 Microservices
- 🔧 CLI tools
- 🎮 Game backends
- ... **any Python application**!

## Roadmap

- [ ] CLI scaffolding tool (`cleanarch init`, `cleanarch generate`)
- [ ] PyPI package
- [ ] Plugin ecosystem (cleanarch-postgres, cleanarch-redis, etc.)
- [ ] FastAPI integration
- [ ] Event-driven architecture support
- [ ] Documentation website

## License

MIT

## Contributing

Contributions welcome! This framework is extracted from production code and battle-tested.
