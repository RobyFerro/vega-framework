# Dependency Injection

Vega Framework provides automatic, type-safe dependency injection with zero boilerplate.

## Core Concepts

### 1. Container - Maps Interfaces to Implementations

```python
from vega.di import Container, set_container

container = Container({
    UserRepository: PostgresUserRepository,  # Interface → Implementation
    EmailService: SendgridEmailService,
})

set_container(container)
```

### 2. @bind - Method-Level Injection

Automatically injects dependencies into methods based on type hints:

```python
from vega.di import bind

class CreateUser(Interactor[User]):
    @bind
    async def call(self, repository: UserRepository) -> User:
        # repository is automatically injected
        return await repository.save(user)
```

### 3. @injectable - Class-Level Injection

Automatically injects dependencies into constructors:

```python
from vega.di import injectable

@injectable
class UserService:
    def __init__(self, repository: UserRepository):
        # repository is automatically injected
        self.repository = repository
```

## @bind Decorator

### Basic Usage

```python
@bind
async def call(self, repository: UserRepository):
    # Dependencies injected based on type hints
    user = await repository.find_by_id("123")
```

### How It Works

1. Inspects method type hints
2. Finds matching types in container
3. Resolves dependencies
4. Injects into method call

### Multiple Dependencies

```python
@bind
async def call(
    self,
    user_repo: UserRepository,
    email_service: EmailService,
    payment_service: PaymentService
):
    # All three dependencies auto-injected
    pass
```

### With Manual Parameters

You can mix auto-injected and manual parameters:

```python
@bind
async def call(
    self,
    repository: UserRepository,  # Auto-injected
    manual_param: str  # Manually provided
):
    pass

# Usage
await interactor.call(manual_param="value")
```

### Scopes

Control dependency lifetimes:

```python
# SCOPED (default) - One instance per operation
@bind
async def call(self, repository: UserRepository):
    pass

# SINGLETON - One instance for entire app
@bind(scope=Scope.SINGLETON)
async def call(self, config: ConfigService):
    pass

# TRANSIENT - New instance every time
@bind(scope=Scope.TRANSIENT)
async def call(self, temp: TempService):
    pass
```

## @injectable Decorator

### Basic Usage

```python
@injectable
class PostgresUserRepository(UserRepository):
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
```

### How It Works

1. Intercepts `__init__` call
2. Inspects constructor type hints
3. Resolves dependencies from container
4. Passes to original `__init__`

### With Scope

```python
@injectable(scope=Scope.SINGLETON)
class ConfigService:
    def __init__(self, settings: Settings):
        self.settings = settings
```

### Multiple Dependencies

```python
@injectable
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        payment_service: PaymentService,
        email_service: EmailService
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.payment_service = payment_service
        self.email_service = email_service
```

## Container Configuration

### Basic Setup

```python
# config.py
from vega.di import Container, set_container

container = Container({
    # Repositories
    UserRepository: PostgresUserRepository,
    ProductRepository: PostgresProductRepository,
    OrderRepository: PostgresOrderRepository,

    # Services
    EmailService: SendgridEmailService,
    PaymentService: StripePaymentService,
    StorageService: S3StorageService,
})

set_container(container)
```

### Environment-Based Configuration

```python
from settings import settings

if settings.ENV == "development":
    container = Container({
        UserRepository: InMemoryUserRepository,  # Fast for dev
        EmailService: FakeEmailService,  # No real emails
    })
elif settings.ENV == "production":
    container = Container({
        UserRepository: PostgresUserRepository,  # Production DB
        EmailService: SendgridEmailService,  # Real emails
    })

set_container(container)
```

### Concrete Services

Register concrete classes directly:

```python
container = Container({
    # Abstract → Implementation
    UserRepository: PostgresUserRepository,

    # Concrete services (no interface)
    DatabaseManager: DatabaseManager,
    Settings: Settings,
})
```

## Scopes

### Scope.TRANSIENT (Default for @injectable)

New instance created every time:

```python
@injectable(scope=Scope.TRANSIENT)
class Calculator:
    pass

# Each call creates a new instance
calc1 = container.resolve(Calculator)
calc2 = container.resolve(Calculator)
assert calc1 is not calc2  # Different instances
```

**Use when**: Stateless services, temporary objects

### Scope.SCOPED (Default for @bind)

One instance per operation/request:

```python
@bind(scope=Scope.SCOPED)
async def call(self, repository: UserRepository):
    pass

# Within the same operation:
# - First call creates instance
# - Subsequent calls in same operation reuse instance
# - Next operation creates new instance
```

**Use when**: Request-specific state, database connections

### Scope.SINGLETON

One instance for entire application:

```python
@injectable(scope=Scope.SINGLETON)
class ConfigService:
    pass

# Only one instance exists
config1 = container.resolve(ConfigService)
config2 = container.resolve(ConfigService)
assert config1 is config2  # Same instance
```

**Use when**: Configuration, caches, shared state

## Real-World Example

### config.py

```python
from vega.di import Container, set_container, Scope
from settings import settings

# Domain interfaces
from domain.repositories.user_repository import UserRepository
from domain.repositories.product_repository import ProductRepository
from domain.services.email_service import EmailService
from domain.services.payment_service import PaymentService

# Infrastructure implementations
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from infrastructure.repositories.postgres_product_repository import PostgresProductRepository
from infrastructure.services.sendgrid_email_service import SendgridEmailService
from infrastructure.services.stripe_payment_service import StripePaymentService
from infrastructure.database_manager import DatabaseManager

# Singleton database manager
@injectable(scope=Scope.SINGLETON)
class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)

# Configure container
container = Container({
    # Repositories
    UserRepository: PostgresUserRepository,
    ProductRepository: PostgresProductRepository,

    # Services
    EmailService: SendgridEmailService,
    PaymentService: StripePaymentService,

    # Infrastructure (concrete)
    DatabaseManager: DatabaseManager,
})

set_container(container)
```

### Repository Implementation

```python
# infrastructure/repositories/postgres_user_repository.py
from vega.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    def __init__(self, db_manager: DatabaseManager):
        # DatabaseManager auto-injected
        self.db = db_manager

    async def save(self, user: User) -> User:
        async with self.db.session() as session:
            # ...
            pass
```

### Interactor Using DI

```python
# domain/interactors/create_user.py
class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(
        self,
        user_repo: UserRepository,  # Auto-injected
        email_service: EmailService  # Auto-injected
    ) -> User:
        # Create user
        user = User(name=self.name, email=self.email)
        user = await user_repo.save(user)

        # Send welcome email
        await email_service.send(
            to=user.email,
            subject="Welcome!",
            body=f"Hello {user.name}"
        )

        return user
```

## Testing

### Mock Dependencies

```python
class MockUserRepository(UserRepository):
    def __init__(self):
        self.users = {}

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        return user

class MockEmailService(EmailService):
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str):
        self.sent_emails.append({"to": to, "subject": subject})

async def test_create_user():
    # Setup test container
    test_container = Container({
        UserRepository: MockUserRepository,
        EmailService: MockEmailService,
    })
    set_container(test_container)

    # Execute
    user = await CreateUser(name="Test", email="test@test.com")

    # Assert
    assert user.name == "Test"
```

### Manual Override

```python
@bind
async def call(
    self,
    repository: UserRepository,
    email_service: EmailService
):
    pass

# Override specific dependency
mock_email = MockEmailService()
await interactor.call(email_service=mock_email)
```

## Common Patterns

### Pattern 1: Repository with DB Manager

```python
@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
```

### Pattern 2: Service with Settings

```python
@injectable(scope=Scope.SINGLETON)
class SendgridEmailService(EmailService):
    def __init__(self, settings: Settings):
        self.api_key = settings.SENDGRID_API_KEY
```

### Pattern 3: Service with Multiple Dependencies

```python
@injectable
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_service: PaymentService,
        email_service: EmailService
    ):
        self.order_repo = order_repo
        self.payment_service = payment_service
        self.email_service = email_service
```

## Troubleshooting

### Issue: Dependency Not Found

```python
# Error: UserRepository not in container

# Fix: Register in container
container = Container({
    UserRepository: PostgresUserRepository,  # Add this
})
```

### Issue: Circular Dependencies

```python
# ServiceA depends on ServiceB
# ServiceB depends on ServiceA

# Fix: Refactor to remove circular dependency
# or use lazy initialization
```

### Issue: Wrong Scope

```python
# Problem: Database connection as TRANSIENT
@injectable(scope=Scope.TRANSIENT)
class DatabaseManager:  # ❌ Creates new connection every time
    pass

# Fix: Use SINGLETON
@injectable(scope=Scope.SINGLETON)
class DatabaseManager:  # ✅ One connection pool
    pass
```

## Best Practices

### ✅ DO

```python
# Use interfaces in domain
@bind
async def call(self, repository: UserRepository):  # ✅ Interface
    pass

# Use scopes appropriately
@injectable(scope=Scope.SINGLETON)
class DatabaseManager:  # ✅ Singleton for shared resources
    pass

# Environment-based config
if settings.ENV == "test":
    container = Container({
        UserRepository: MockUserRepository,  # ✅ Mocks for testing
    })
```

### ❌ DON'T

```python
# Don't use concrete implementations in domain
@bind
async def call(self, repository: PostgresUserRepository):  # ❌ Concrete class
    pass

# Don't create instances manually
repository = PostgresUserRepository()  # ❌ Breaks DI

# Don't use wrong scopes
@injectable(scope=Scope.TRANSIENT)
class ExpensiveCache:  # ❌ Should be SINGLETON
    pass
```

## Next Steps

- [Scopes](scopes.md) - Deep dive into scope management
- [Container](container.md) - Advanced container configuration
- [Interactor](../patterns/interactor.md) - Using DI with interactors
