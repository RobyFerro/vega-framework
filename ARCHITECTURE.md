# Vega Framework - Architecture

This document explains the architectural principles and patterns of the Vega Framework.

## Table of Contents

- [Overview](#overview)
- [Clean Architecture Layers](#clean-architecture-layers)
- [Core Patterns](#core-patterns)
- [Dependency Injection](#dependency-injection)
- [Project Structure](#project-structure)
- [Best Practices](#best-practices)

## Overview

Vega Framework is built on **Clean Architecture** principles, ensuring:

- **Separation of Concerns** - Clear boundaries between business logic and infrastructure
- **Dependency Rule** - Dependencies point inward, domain layer knows nothing about infrastructure
- **Testability** - Easy to mock dependencies and test in isolation
- **Flexibility** - Swap implementations without changing business logic

## Clean Architecture Layers

### 1. Domain Layer

The core business logic, independent of any framework or external dependency.

**Contains:**
- **Entities** - Business objects and data structures
- **Repository Interfaces** - Data persistence abstractions
- **Service Interfaces** - External service abstractions
- **Interactors (Use Cases)** - Business operations

**Rules:**
- No dependencies on infrastructure
- No framework-specific code
- Pure business logic

### 2. Application Layer

Coordinates domain use cases and manages workflows.

**Contains:**
- **Mediators** - Multi-step workflows that orchestrate interactors

**Rules:**
- Can depend on domain layer
- No dependencies on infrastructure details
- Orchestrates business operations

### 3. Infrastructure Layer

Implements interfaces defined in domain layer with specific technologies.

**Contains:**
- **Repository Implementations** - Database, file system, API clients
- **Service Implementations** - Email providers, payment gateways, etc.
- **Framework Adapters** - FastAPI routes, CLI commands

**Rules:**
- Implements domain interfaces
- Contains technology-specific code
- Should be easily replaceable

## Core Patterns

### Interactor - Single Use Case

An **Interactor** represents a single, focused business operation.

**Key Characteristics:**
- One interactor = one use case
- Constructor receives input parameters
- `call()` method executes business logic
- Dependencies injected via `@bind` decorator
- Metaclass auto-calls `call()` on instantiation

**Example:**

```python
from vega.patterns import Interactor
from vega.di import bind

class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        # Dependencies auto-injected
        user = User(name=self.name, email=self.email)
        return await repository.save(user)

# Usage - metaclass auto-calls call()
user = await CreateUser(name="John", email="john@example.com")
```

### Mediator - Complex Workflow

A **Mediator** orchestrates multiple interactors to accomplish complex business operations.

**Key Characteristics:**
- Coordinates multiple use cases
- Represents a business workflow
- No external dependencies in constructor
- Calls multiple interactors

**Example:**

```python
from vega.patterns import Mediator

class CheckoutWorkflow(Mediator[Order]):
    def __init__(self, cart_id: str, payment_method: str):
        self.cart_id = cart_id
        self.payment_method = payment_method

    async def call(self) -> Order:
        # Orchestrate multiple interactors
        cart = await GetCart(self.cart_id)
        order = await CreateOrder(cart.items)
        await ProcessPayment(order.id, self.payment_method)
        await SendConfirmationEmail(order.customer_email)
        await ClearCart(self.cart_id)
        return order

# Usage
order = await CheckoutWorkflow(cart_id="123", payment_method="stripe")
```

### Repository - Data Persistence

A **Repository** provides abstraction over data persistence.

**Key Characteristics:**
- Abstract interface in domain layer
- Concrete implementation in infrastructure layer
- Generic type `T` represents entity type
- Standard CRUD operations

**Example:**

```python
from vega.patterns import Repository
from typing import Optional, List

# Domain layer - Interface
class UserRepository(Repository[User]):
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    async def find_active_users(self) -> List[User]:
        pass

# Infrastructure layer - Implementation
from vega.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    async def find_by_email(self, email: str) -> Optional[User]:
        # PostgreSQL-specific implementation
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1", email
            )
            return User(**row) if row else None

    async def find_active_users(self) -> List[User]:
        # PostgreSQL-specific implementation
        async with self.db.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users WHERE active = true")
            return [User(**row) for row in rows]
```

### Service - External Integration

A **Service** provides abstraction over external services and APIs.

**Key Characteristics:**
- Abstract interface in domain layer
- Concrete implementation in infrastructure layer
- Represents third-party dependencies

**Example:**

```python
from vega.patterns import Service
from abc import abstractmethod

# Domain layer - Interface
class EmailService(Service):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool:
        pass

class PaymentService(Service):
    @abstractmethod
    async def charge(self, amount: float, token: str) -> PaymentResult:
        pass

# Infrastructure layer - Implementations
@injectable(scope=Scope.SINGLETON)
class SendgridEmailService(EmailService):
    async def send(self, to: str, subject: str, body: str) -> bool:
        # Sendgrid API integration
        pass

@injectable(scope=Scope.SINGLETON)
class StripePaymentService(PaymentService):
    async def charge(self, amount: float, token: str) -> PaymentResult:
        # Stripe API integration
        pass
```

## Dependency Injection

Vega provides automatic dependency injection through decorators and a container.

### Container Setup

```python
from vega.di import Container, set_container

# Map interfaces to implementations
container = Container({
    UserRepository: PostgresUserRepository,
    EmailService: SendgridEmailService,
    PaymentService: StripePaymentService,
})

set_container(container)
```

### @bind - Method-Level DI

Injects dependencies into a method based on type hints.

```python
from vega.di import bind, Scope

class MyInteractor(Interactor[Result]):
    @bind
    async def call(self, repository: UserRepository) -> Result:
        # repository automatically injected
        return await repository.find_all()

# Custom scope
@bind(scope=Scope.SINGLETON)
async def get_config(service: ConfigService) -> dict:
    return service.load()
```

### @injectable - Class-Level DI

Injects dependencies into constructor.

```python
from vega.di import injectable, Scope

@injectable
class MyService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

@injectable(scope=Scope.SINGLETON)
class ConfigService:
    def __init__(self, settings: SettingsRepository):
        self.settings = settings
```

### Dependency Scopes

Vega supports three dependency lifetimes:

| Scope | Behavior | Use Case |
|-------|----------|----------|
| **TRANSIENT** | New instance every time | Stateless services, temporary objects |
| **SCOPED** | One instance per operation/request | Request-specific state, database connections |
| **SINGLETON** | One instance for entire application | Configuration, caches, shared state |

**Example:**

```python
@injectable(scope=Scope.SINGLETON)
class ConfigService:
    # Shared across entire application
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

## Project Structure

Vega projects follow a standard structure:

```
my-app/
├── domain/
│   ├── entities/
│   │   ├── __init__.py
│   │   └── user.py              # Business entities
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repository.py   # Repository interfaces
│   ├── services/
│   │   ├── __init__.py
│   │   └── email_service.py     # Service interfaces
│   └── interactors/
│       ├── __init__.py
│       └── create_user.py       # Use cases
│
├── application/
│   └── mediators/
│       ├── __init__.py
│       └── registration_flow.py # Workflows
│
├── infrastructure/
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── postgres_user_repository.py
│   └── services/
│       ├── __init__.py
│       └── sendgrid_email_service.py
│
├── config.py                     # DI container configuration
├── settings.py                   # Application settings
└── main.py                       # Entry point
```

## Best Practices

### 1. Keep Domain Pure

✅ **Do:**
```python
# Domain layer
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
```

❌ **Don't:**
```python
# Domain layer - NO framework dependencies!
from sqlalchemy import Column, String

class User(Base):  # ❌ Database dependency in domain
    __tablename__ = 'users'
```

### 2. Interface Segregation

✅ **Do:**
```python
class UserRepository(Repository[User]):
    async def find_by_email(self, email: str) -> Optional[User]:
        pass
```

❌ **Don't:**
```python
# Too many responsibilities
class UserRepository(Repository[User]):
    async def send_email(self, user: User): pass  # ❌ Not repository concern
    async def charge_card(self, user: User): pass  # ❌ Not repository concern
```

### 3. Single Responsibility

✅ **Do:**
```python
class CreateUser(Interactor[User]):
    # Single responsibility: create user
    pass

class SendWelcomeEmail(Interactor[None]):
    # Single responsibility: send email
    pass
```

❌ **Don't:**
```python
class CreateUserAndSendEmail(Interactor[User]):
    # ❌ Too many responsibilities
    pass
```

### 4. Use Mediators for Workflows

✅ **Do:**
```python
class UserRegistrationFlow(Mediator[User]):
    async def call(self) -> User:
        user = await CreateUser(self.name, self.email)
        await SendWelcomeEmail(user.email)
        return user
```

### 5. Proper Scoping

```python
# Configuration - SINGLETON
@injectable(scope=Scope.SINGLETON)
class AppConfig:
    pass

# Database connection pool - SINGLETON
@injectable(scope=Scope.SINGLETON)
class DatabasePool:
    pass

# Request context - SCOPED
@injectable(scope=Scope.SCOPED)
class RequestContext:
    pass

# Temporary calculator - TRANSIENT
@injectable(scope=Scope.TRANSIENT)
class PriceCalculator:
    pass
```

### 6. Testing

Vega's architecture makes testing straightforward:

```python
# Mock repositories
class MockUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        return user

# Test interactor
async def test_create_user():
    container = Container({
        UserRepository: MockUserRepository,
    })
    set_container(container)

    user = await CreateUser(name="Test", email="test@example.com")
    assert user.name == "Test"
```

## Conclusion

Vega Framework enforces clean architecture principles through:

- **Clear layer separation** - Domain, Application, Infrastructure
- **Dependency inversion** - Interfaces in domain, implementations in infrastructure
- **Automatic DI** - Type-safe dependency injection
- **Focused patterns** - Interactor, Mediator, Repository, Service
- **Testability** - Easy to mock and test

Follow these patterns to build maintainable, scalable Python applications.
