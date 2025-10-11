# The Dependency Rule

The **Dependency Rule** is the most important principle in Clean Architecture: **dependencies always point inward**.

## The Rule

> Source code dependencies must point only inward, toward higher-level policies.

In Vega Framework:

```
Presentation → Application → Domain ← Infrastructure
```

- **Domain** is the center and has NO outward dependencies
- **Application** depends only on Domain
- **Infrastructure** implements Domain interfaces
- **Presentation** uses Application and Domain

## Why It Matters

### 1. Business Logic Independence

Your core business logic (Domain layer) doesn't know about:
- Databases
- Web frameworks
- External APIs
- UI implementations

This means you can:
- ✅ Change databases without touching business logic
- ✅ Swap frameworks without refactoring
- ✅ Test without infrastructure
- ✅ Reuse business logic across different interfaces

### 2. Flexibility

```python
# Domain layer - doesn't know about PostgreSQL
class UserRepository(Repository[User]):
    async def save(self, user: User) -> User:
        pass

# Infrastructure - implements for PostgreSQL
class PostgresUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # PostgreSQL-specific code
        pass

# Can easily swap to MongoDB
class MongoUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # MongoDB-specific code
        pass
```

### 3. Testability

```python
# Easy to test with mocks
class MockUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        return user

# Test without database
container = Container({UserRepository: MockUserRepository})
user = await CreateUser(name="Test", email="test@test.com")
```

## Valid Dependencies

### ✅ Presentation → Domain

```python
# presentation/web/routes/user_routes.py
from domain.interactors.create_user import CreateUser  # ✅ OK

@router.post("/users")
async def create_user(request: CreateUserRequest):
    user = await CreateUser(name=request.name, email=request.email)
    return {"user": user}
```

### ✅ Presentation → Application

```python
# presentation/cli/commands/user_commands.py
from application.mediators.user_registration_flow import UserRegistrationFlow  # ✅ OK

@click.command()
@async_command
async def register_user(name: str, email: str):
    user = await UserRegistrationFlow(name=name, email=email)
```

### ✅ Application → Domain

```python
# application/mediators/user_registration_flow.py
from domain.interactors.create_user import CreateUser  # ✅ OK
from domain.interactors.send_welcome_email import SendWelcomeEmail  # ✅ OK

class UserRegistrationFlow(Mediator[User]):
    async def call(self) -> User:
        user = await CreateUser(self.name, self.email)
        await SendWelcomeEmail(user.email)
        return user
```

### ✅ Infrastructure → Domain (Implements Interfaces)

```python
# infrastructure/repositories/postgres_user_repository.py
from domain.repositories.user_repository import UserRepository  # ✅ OK
from domain.entities.user import User  # ✅ OK

class PostgresUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # Implementation
        pass
```

## Invalid Dependencies

### ❌ Domain → Infrastructure

**WRONG**:
```python
# domain/interactors/create_user.py
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository  # ❌ WRONG

class CreateUser(Interactor[User]):
    @bind
    async def call(self, repository: PostgresUserRepository):  # ❌ Concrete implementation
        pass
```

**CORRECT**:
```python
# domain/interactors/create_user.py
from domain.repositories.user_repository import UserRepository  # ✅ CORRECT

class CreateUser(Interactor[User]):
    @bind
    async def call(self, repository: UserRepository):  # ✅ Abstract interface
        pass
```

### ❌ Domain → Application

**WRONG**:
```python
# domain/interactors/create_user.py
from application.mediators.user_registration_flow import UserRegistrationFlow  # ❌ WRONG

class CreateUser(Interactor[User]):
    async def call(self) -> User:
        # Domain should not know about application workflows
        pass
```

### ❌ Domain → Presentation

**WRONG**:
```python
# domain/interactors/create_user.py
from fastapi import HTTPException  # ❌ WRONG - Framework dependency

class CreateUser(Interactor[User]):
    async def call(self) -> User:
        if not self.email:
            raise HTTPException(status_code=400, detail="Email required")  # ❌ WRONG
```

**CORRECT**:
```python
# domain/interactors/create_user.py
class CreateUser(Interactor[User]):
    async def call(self) -> User:
        if not self.email:
            raise ValueError("Email required")  # ✅ CORRECT - Domain exception

# presentation/web/routes/user_routes.py
@router.post("/users")
async def create_user(request: CreateUserRequest):
    try:
        user = await CreateUser(name=request.name, email=request.email)
        return {"user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))  # ✅ Handle in presentation
```

### ❌ Application → Infrastructure

**WRONG**:
```python
# application/mediators/user_registration_flow.py
from infrastructure.services.sendgrid_email_service import SendgridEmailService  # ❌ WRONG

class UserRegistrationFlow(Mediator[User]):
    def __init__(self, email_service: SendgridEmailService):  # ❌ Concrete implementation
        self.email_service = email_service
```

**CORRECT**:
```python
# application/mediators/user_registration_flow.py
# Don't inject services directly - use interactors
class UserRegistrationFlow(Mediator[User]):
    async def call(self) -> User:
        user = await CreateUser(self.name, self.email)
        await SendWelcomeEmail(user.email)  # ✅ Interactor handles service
        return user
```

## Dependency Inversion Principle

The Dependency Rule relies on **Dependency Inversion**:

> High-level modules should not depend on low-level modules. Both should depend on abstractions.

### Example

```python
# ❌ Direct dependency (wrong)
class OrderService:
    def __init__(self):
        self.db = PostgreSQLDatabase()  # Depends on concrete implementation

# ✅ Dependency inversion (correct)
class OrderService:
    def __init__(self, repository: OrderRepository):  # Depends on abstraction
        self.repository = repository

# Infrastructure implements the abstraction
class PostgresOrderRepository(OrderRepository):
    pass

# Container maps abstraction to implementation
container = Container({
    OrderRepository: PostgresOrderRepository
})
```

## How Vega Enforces the Rule

### 1. Directory Structure

```
domain/          # Cannot import from other layers
├── entities/
├── repositories/    # Interfaces only
├── services/        # Interfaces only
└── interactors/

application/     # Can only import from domain
└── mediators/

infrastructure/  # Implements domain interfaces
├── repositories/
└── services/

presentation/    # Uses domain and application
├── cli/
└── web/
```

### 2. Abstract Base Classes

```python
# Domain defines interfaces
from vega.patterns import Repository, Service

class UserRepository(Repository[User]):  # Abstract
    pass

class EmailService(Service):  # Abstract
    pass
```

### 3. Dependency Injection

```python
# config.py maps abstractions to implementations
from vega.di import Container

container = Container({
    UserRepository: PostgresUserRepository,  # Domain → Infrastructure
    EmailService: SendgridEmailService,      # Domain → Infrastructure
})
```

### 4. CLI Validation

```bash
vega doctor
```

Checks for dependency violations:
- Domain importing from infrastructure
- Application importing from infrastructure
- Missing abstractions

## Best Practices

### 1. Always Use Interfaces in Domain

```python
# ✅ Good
@bind
async def call(self, repository: UserRepository):  # Interface
    pass

# ❌ Bad
@bind
async def call(self, repository: PostgresUserRepository):  # Concrete implementation
    pass
```

### 2. Handle Framework Concerns in Presentation

```python
# ✅ Good - Framework in presentation
@router.post("/users")
async def create_user(request: CreateUserRequest):
    try:
        user = await CreateUser(name=request.name, email=request.email)
        return {"user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ❌ Bad - Framework in domain
class CreateUser(Interactor[User]):
    async def call(self) -> User:
        if not self.email:
            raise HTTPException(status_code=400, detail="Invalid")  # ❌ Framework dependency
```

### 3. Use Domain Exceptions

```python
# domain/exceptions.py
class DomainException(Exception):
    pass

class UserAlreadyExistsError(DomainException):
    pass

class InsufficientStockError(DomainException):
    pass

# domain/interactors/create_user.py
class CreateUser(Interactor[User]):
    async def call(self) -> User:
        existing = await self.repository.find_by_email(self.email)
        if existing:
            raise UserAlreadyExistsError(self.email)  # ✅ Domain exception
```

### 4. Keep Domain Pure

```python
# ✅ Good - Pure Python
@dataclass
class User:
    id: str
    name: str
    email: str

# ❌ Bad - Framework dependency
from sqlalchemy import Column, String

class User(Base):  # ❌ SQLAlchemy in domain
    __tablename__ = 'users'
```

## Testing the Dependency Rule

### Automated Checks

```bash
# Validate architecture
vega doctor

# Check for import violations
grep -r "from infrastructure" domain/
grep -r "from application" domain/
grep -r "from presentation" domain/
```

### Manual Review

Review imports in each layer:

```python
# domain/ should only import from domain/
# application/ should only import from domain/ and application/
# infrastructure/ can import from domain/
# presentation/ can import from domain/ and application/
```

## Common Mistakes

### Mistake 1: Injecting Concrete Implementations

```python
# ❌ Wrong
@bind
async def call(self, db: PostgreSQLConnection):
    pass

# ✅ Correct
@bind
async def call(self, repository: UserRepository):
    pass
```

### Mistake 2: Using Framework Types in Domain

```python
# ❌ Wrong
from fastapi import Request

class CreateUser(Interactor[User]):
    def __init__(self, request: Request):  # ❌ Framework type
        pass

# ✅ Correct
class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):  # ✅ Simple types
        pass
```

### Mistake 3: Business Logic in Presentation

```python
# ❌ Wrong
@router.post("/users")
async def create_user(request: CreateUserRequest):
    user = User(name=request.name, email=request.email)
    await db.save(user)  # ❌ Business logic in route
    await email_service.send(...)  # ❌ Business logic in route

# ✅ Correct
@router.post("/users")
async def create_user(request: CreateUserRequest):
    user = await CreateUser(name=request.name, email=request.email)  # ✅ Delegate to interactor
```

## Benefits of Following the Rule

1. **Testability** - Test business logic without infrastructure
2. **Flexibility** - Swap implementations easily
3. **Maintainability** - Clear boundaries and responsibilities
4. **Scalability** - Add features without breaking existing code
5. **Reusability** - Use same business logic in CLI and Web

## Next Steps

- [Clean Architecture](clean-architecture.md) - Overall architecture principles
- [Layers](layers.md) - Deep dive into each layer
- [Dependency Injection](../core/dependency-injection.md) - Learn DI system
