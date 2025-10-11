# Clean Architecture

Vega Framework is built on **Clean Architecture** principles, ensuring maintainable and testable code.

## What is Clean Architecture?

Clean Architecture is a software design philosophy that separates concerns into layers, with dependencies pointing inward. The core business logic is isolated from external concerns like databases, frameworks, and UI.

## Key Principles

### 1. Separation of Concerns

Each layer has a specific responsibility:
- **Domain**: Business logic
- **Application**: Workflows
- **Infrastructure**: Technical implementations
- **Presentation**: User interfaces

### 2. Dependency Rule

Dependencies always point **inward**, toward the business logic:

```
Presentation → Application → Domain ← Infrastructure
```

The domain layer (core) knows nothing about outer layers.

### 3. Independence of Frameworks

Your business logic doesn't depend on FastAPI, SQLAlchemy, or any framework. This means:
- ✅ Easy to test
- ✅ Easy to change frameworks
- ✅ Framework updates don't break business logic

### 4. Testability

Pure business logic can be tested without:
- Database
- Web server
- External APIs
- Infrastructure

### 5. Independence of UI

The same business logic works with:
- CLI interface
- Web API (FastAPI)
- GraphQL (future)
- gRPC (future)

### 6. Independence of Database

Business logic doesn't know about PostgreSQL, MongoDB, or any database. You can:
- Swap databases without changing business logic
- Test with in-memory implementations
- Use different databases per environment

## Benefits

### Maintainability

Clear boundaries make code easier to understand and modify:

```python
# Domain layer - pure business logic
class CreateUser(Interactor[User]):
    @bind
    async def call(self, repository: UserRepository) -> User:
        user = User(name=self.name, email=self.email)
        return await repository.save(user)
```

No framework code, no SQL, no HTTP - just business logic.

### Testability

Easy to test with mocks:

```python
class MockUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        return user

# Test without database
container = Container({UserRepository: MockUserRepository})
user = await CreateUser(name="Test", email="test@test.com")
assert user.name == "Test"
```

### Flexibility

Change implementations without touching business logic:

```python
# Development
container = Container({
    UserRepository: InMemoryUserRepository,  # Fast for dev
})

# Production
container = Container({
    UserRepository: PostgresUserRepository,  # Production DB
})
```

### Scalability

Add new features without breaking existing code:
- New use cases = new interactors
- New workflows = new mediators
- New interfaces = new presentation layer

## How Vega Enforces Clean Architecture

### 1. Layer Separation

Vega's project structure enforces layer boundaries:

```
domain/          # Can't import from other layers
application/     # Can only import from domain
infrastructure/  # Implements domain interfaces
presentation/    # Uses domain and application
```

### 2. Dependency Injection

DI decouples business logic from implementations:

```python
# Domain defines interface
class UserRepository(Repository[User]):
    pass

# Infrastructure implements
class PostgresUserRepository(UserRepository):
    pass

# Container maps them
container = Container({
    UserRepository: PostgresUserRepository
})
```

### 3. Abstract Patterns

Vega's patterns enforce abstractions:
- **Repository**: Abstract data access
- **Service**: Abstract external services
- **Interactor**: Single-purpose use case
- **Mediator**: Orchestration without implementation details

### 4. CLI Validation

`vega doctor` checks architectural violations:

```bash
vega doctor
```

Detects:
- Domain importing from infrastructure
- Missing abstractions
- Incorrect dependencies

## Common Violations and Fixes

### ❌ Domain Depending on Framework

**Wrong**:
```python
# domain/entities/user.py
from sqlalchemy import Column, String

class User(Base):  # ❌ SQLAlchemy in domain
    __tablename__ = 'users'
```

**Correct**:
```python
# domain/entities/user.py
@dataclass
class User:  # ✅ Pure Python
    id: str
    name: str
    email: str

# infrastructure/models/user_model.py
from sqlalchemy import Column, String

class UserModel(Base):  # ✅ SQLAlchemy in infrastructure
    __tablename__ = 'users'
```

### ❌ Business Logic in Presentation

**Wrong**:
```python
# presentation/web/routes/user_routes.py
@router.post("/users")
async def create_user(request: CreateUserRequest):
    # ❌ Business logic in route
    user = User(name=request.name, email=request.email)
    await db.save(user)
    return user
```

**Correct**:
```python
# presentation/web/routes/user_routes.py
@router.post("/users")
async def create_user(request: CreateUserRequest):
    # ✅ Delegate to interactor
    user = await CreateUser(name=request.name, email=request.email)
    return user
```

### ❌ Repository Mixing Concerns

**Wrong**:
```python
# domain/repositories/user_repository.py
class UserRepository(Repository[User]):
    async def save(self, user: User) -> User:
        pass

    async def send_email(self, user: User):  # ❌ Not repository concern
        pass
```

**Correct**:
```python
# domain/repositories/user_repository.py
class UserRepository(Repository[User]):
    async def save(self, user: User) -> User:
        pass

# domain/services/email_service.py
class EmailService(Service):
    async def send(self, to: str, subject: str, body: str):
        pass
```

## Real-World Example

Let's build a user registration feature following Clean Architecture:

### 1. Domain Layer (Business Logic)

```python
# domain/entities/user.py
@dataclass
class User:
    id: str
    name: str
    email: str
    created_at: datetime

# domain/repositories/user_repository.py
class UserRepository(Repository[User]):
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    async def save(self, user: User) -> User:
        pass

# domain/services/email_service.py
class EmailService(Service):
    async def send(self, to: str, subject: str, body: str):
        pass

# domain/interactors/create_user.py
class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        # Check if email exists
        existing = await repository.find_by_email(self.email)
        if existing:
            raise ValueError("Email already exists")

        # Create user
        user = User(
            id=generate_id(),
            name=self.name,
            email=self.email,
            created_at=datetime.now()
        )

        return await repository.save(user)

# domain/interactors/send_welcome_email.py
class SendWelcomeEmail(Interactor[None]):
    def __init__(self, email: str, name: str):
        self.email = email
        self.name = name

    @bind
    async def call(self, email_service: EmailService):
        await email_service.send(
            to=self.email,
            subject="Welcome!",
            body=f"Hello {self.name}, welcome to our platform!"
        )
```

### 2. Application Layer (Workflow)

```python
# application/mediators/user_registration_flow.py
class UserRegistrationFlow(Mediator[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    async def call(self) -> User:
        # Create user
        user = await CreateUser(self.name, self.email)

        # Send welcome email
        await SendWelcomeEmail(user.email, user.name)

        return user
```

### 3. Infrastructure Layer (Implementations)

```python
# infrastructure/repositories/postgres_user_repository.py
@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    async def find_by_email(self, email: str) -> Optional[User]:
        async with db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1", email
            )
            return User(**row) if row else None

    async def save(self, user: User) -> User:
        async with db.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, name, email, created_at) VALUES ($1, $2, $3, $4)",
                user.id, user.name, user.email, user.created_at
            )
            return user

# infrastructure/services/sendgrid_email_service.py
@injectable(scope=Scope.SINGLETON)
class SendgridEmailService(EmailService):
    async def send(self, to: str, subject: str, body: str):
        # Sendgrid API integration
        pass
```

### 4. Presentation Layer (Interfaces)

```python
# presentation/web/routes/user_routes.py
router = APIRouter()

@router.post("/users/register")
async def register_user(request: RegisterUserRequest):
    user = await UserRegistrationFlow(
        name=request.name,
        email=request.email
    )
    return {"user": user}

# presentation/cli/commands/user_commands.py
@click.command()
@click.option('--name', required=True)
@click.option('--email', required=True)
@async_command
async def register_user(name: str, email: str):
    user = await UserRegistrationFlow(name=name, email=email)
    click.echo(f"Registered: {user.name}")
```

### 5. Configuration

```python
# config.py
container = Container({
    UserRepository: PostgresUserRepository,
    EmailService: SendgridEmailService,
})
```

Notice how:
- ✅ Same business logic works for both CLI and Web
- ✅ Easy to swap PostgreSQL for MongoDB
- ✅ Easy to swap Sendgrid for Mailgun
- ✅ Can test without database or email service

## Next Steps

- [Layers](layers.md) - Deep dive into each layer
- [Dependency Rule](dependency-rule.md) - Understanding dependencies
- [Patterns](../patterns/interactor.md) - Learn Vega patterns
