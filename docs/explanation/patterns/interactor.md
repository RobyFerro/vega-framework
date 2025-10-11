# Interactor Pattern

An **Interactor** represents a single, focused business operation (use case).

## Core Concept

```
One Interactor = One Use Case = One Business Operation
```

## Basic Example

```python
from vega.patterns import Interactor
from vega.di import bind
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository

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

## Key Principles

### 1. Single Responsibility

Each interactor does ONE thing:

```python
# ✅ Good - single responsibility
class CreateUser(Interactor[User]):
    pass

class SendWelcomeEmail(Interactor[None]):
    pass

# ❌ Bad - multiple responsibilities
class CreateUserAndSendEmail(Interactor[User]):
    pass
```

### 2. Constructor = Input Parameters

```python
class PurchaseProduct(Interactor[Order]):
    def __init__(self, product_id: str, quantity: int, payment_token: str):
        self.product_id = product_id
        self.quantity = quantity
        self.payment_token = payment_token
```

### 3. Dependencies via @bind

Dependencies are injected automatically based on type hints:

```python
@bind
async def call(
    self,
    product_repo: ProductRepository,  # Auto-injected
    payment_service: PaymentService,  # Auto-injected
    inventory_service: InventoryService  # Auto-injected
) -> Order:
    # Use dependencies
    product = await product_repo.find_by_id(self.product_id)
    # ...
```

### 4. Pure Business Logic

No framework code, no SQL, no HTTP - just business rules:

```python
@bind
async def call(self, repository: UserRepository) -> User:
    # Validate business rules
    if not self.email or '@' not in self.email:
        raise ValueError("Invalid email")

    # Check business constraints
    existing = await repository.find_by_email(self.email)
    if existing:
        raise UserAlreadyExistsError(self.email)

    # Execute business operation
    user = User(name=self.name, email=self.email)
    return await repository.save(user)
```

## How It Works

### Metaclass Magic

The `InteractorMeta` metaclass automatically calls `call()` when you instantiate the interactor:

```python
# What you write:
user = await CreateUser(name="John", email="john@test.com")

# What happens internally:
# 1. CreateUser.__init__(name="John", email="john@test.com")
# 2. instance.call() is automatically called
# 3. Dependencies are injected via @bind
# 4. Result is returned
```

This gives you clean syntax similar to function calls.

### Dependency Injection

The `@bind` decorator inspects type hints and resolves dependencies from the container:

```python
# Container configuration
container = Container({
    UserRepository: PostgresUserRepository,
})

# When @bind is called:
# 1. Inspects call() type hints
# 2. Finds UserRepository parameter
# 3. Resolves to PostgresUserRepository from container
# 4. Injects the instance
```

## Real-World Examples

### Example 1: Create User with Validation

```python
class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = password

    @bind
    async def call(
        self,
        user_repo: UserRepository,
        password_service: PasswordService
    ) -> User:
        # Validate
        if len(self.password) < 8:
            raise WeakPasswordError()

        # Check uniqueness
        existing = await user_repo.find_by_email(self.email)
        if existing:
            raise UserAlreadyExistsError(self.email)

        # Hash password
        hashed = await password_service.hash(self.password)

        # Create user
        user = User(
            id=generate_uuid(),
            name=self.name,
            email=self.email,
            password_hash=hashed,
            created_at=datetime.now()
        )

        return await user_repo.save(user)
```

### Example 2: Purchase Product with Stock Check

```python
class PurchaseProduct(Interactor[Order]):
    def __init__(self, product_id: str, quantity: int):
        self.product_id = product_id
        self.quantity = quantity

    @bind
    async def call(
        self,
        product_repo: ProductRepository,
        inventory_service: InventoryService
    ) -> Order:
        # Get product
        product = await product_repo.find_by_id(self.product_id)
        if not product:
            raise ProductNotFoundError(self.product_id)

        # Check stock
        available = await inventory_service.check_stock(self.product_id)
        if available < self.quantity:
            raise InsufficientStockError(self.product_id, available, self.quantity)

        # Reserve inventory
        await inventory_service.reserve(self.product_id, self.quantity)

        # Create order
        order = Order(
            id=generate_uuid(),
            product_id=self.product_id,
            quantity=self.quantity,
            total=product.price * self.quantity,
            status="pending"
        )

        return order
```

### Example 3: Update User Email with Verification

```python
class UpdateUserEmail(Interactor[User]):
    def __init__(self, user_id: str, new_email: str):
        self.user_id = user_id
        self.new_email = new_email

    @bind
    async def call(
        self,
        user_repo: UserRepository,
        email_service: EmailService
    ) -> User:
        # Get user
        user = await user_repo.find_by_id(self.user_id)
        if not user:
            raise UserNotFoundError(self.user_id)

        # Validate email
        if not self.new_email or '@' not in self.new_email:
            raise InvalidEmailError(self.new_email)

        # Check if email is already used
        existing = await user_repo.find_by_email(self.new_email)
        if existing and existing.id != self.user_id:
            raise EmailAlreadyUsedError(self.new_email)

        # Update email
        old_email = user.email
        user.email = self.new_email
        user.email_verified = False
        user = await user_repo.save(user)

        # Send verification email
        await email_service.send_verification(user.email)

        return user
```

## Testing

Interactors are easy to test with mocks:

```python
class MockUserRepository(UserRepository):
    def __init__(self):
        self.users = {}

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self.users.values() if u.email == email), None)

async def test_create_user():
    # Setup container with mocks
    container = Container({
        UserRepository: MockUserRepository,
    })
    set_container(container)

    # Execute interactor
    user = await CreateUser(name="Test", email="test@test.com")

    # Assertions
    assert user.name == "Test"
    assert user.email == "test@test.com"

async def test_create_user_duplicate_email():
    container = Container({
        UserRepository: MockUserRepository,
    })
    set_container(container)

    # Create first user
    await CreateUser(name="First", email="test@test.com")

    # Try to create duplicate
    with pytest.raises(UserAlreadyExistsError):
        await CreateUser(name="Second", email="test@test.com")
```

## Scopes

Control dependency lifetimes with scopes:

```python
# Default: SCOPED (new instance per operation)
@bind
async def call(self, repository: UserRepository):
    pass

# SINGLETON (one instance for entire app)
@bind(scope=Scope.SINGLETON)
async def call(self, config_service: ConfigService):
    pass

# TRANSIENT (new instance every time)
@bind(scope=Scope.TRANSIENT)
async def call(self, temp_service: TempService):
    pass
```

## Best Practices

### ✅ DO

```python
# Keep it simple and focused
class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

# Use domain exceptions
if not user:
    raise UserNotFoundError(user_id)

# Validate business rules
if quantity <= 0:
    raise InvalidQuantityError(quantity)

# Return domain entities
return User(...)
```

### ❌ DON'T

```python
# Don't mix multiple operations
class CreateUserAndSendEmailAndLogAndNotify(Interactor[User]):
    pass  # ❌ Too much responsibility

# Don't use framework types
from fastapi import HTTPException
raise HTTPException(...)  # ❌ Framework in domain

# Don't access database directly
async def call(self):
    await db.execute("INSERT ...")  # ❌ No SQL in interactor

# Don't return framework types
from fastapi import Response
return Response(...)  # ❌ Return domain entities
```

## CLI Generation

Generate interactors using the CLI:

```bash
vega generate interactor CreateUser
vega generate interactor UpdateUserEmail
vega generate interactor PurchaseProduct
```

## Next Steps

- [Mediator](mediator.md) - Orchestrate multiple interactors
- [Repository](repository.md) - Data persistence abstraction
- [Service](service.md) - External service abstraction
- [Dependency Injection](../core/dependency-injection.md) - Learn DI system
