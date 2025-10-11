# Repository Pattern

A **Repository** provides an abstraction over data persistence, keeping the domain layer independent of infrastructure.

## Core Concept

```
Domain defines WHAT data operations are needed
Infrastructure defines HOW they're implemented
```

## When to Use

Use a Repository when you need to:
- Abstract data persistence (database, cache, file system)
- Keep domain layer independent of infrastructure
- Allow easy switching between data sources
- Enable testing without real databases

## Basic Example

```python
from vega.patterns import Repository
from typing import Optional, List
from abc import abstractmethod

# Domain Layer - Abstract interface
class UserRepository(Repository[User]):
    """Defines what operations are needed"""

    @abstractmethod
    async def get(self, id: str) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save or update user"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete user by ID"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        pass

    @abstractmethod
    async def find_active_users(self) -> List[User]:
        """Get all active users"""
        pass

# Infrastructure Layer - Concrete implementation
from vega.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    """Implements how operations work with PostgreSQL"""

    def __init__(self, db_session: DatabaseSession):
        self.db = db_session

    async def get(self, id: str) -> Optional[User]:
        result = await self.db.execute(
            "SELECT * FROM users WHERE id = $1", id
        )
        return User(**result) if result else None

    async def save(self, user: User) -> User:
        await self.db.execute(
            "INSERT INTO users (id, name, email) VALUES ($1, $2, $3) "
            "ON CONFLICT (id) DO UPDATE SET name = $2, email = $3",
            user.id, user.name, user.email
        )
        return user

    async def delete(self, id: str) -> bool:
        result = await self.db.execute(
            "DELETE FROM users WHERE id = $1", id
        )
        return result > 0

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            "SELECT * FROM users WHERE email = $1", email
        )
        return User(**result) if result else None

    async def find_active_users(self) -> List[User]:
        results = await self.db.execute(
            "SELECT * FROM users WHERE active = true"
        )
        return [User(**r) for r in results]
```

## Key Principles

### 1. Interface in Domain, Implementation in Infrastructure

```
project/
├── domain/
│   └── repositories/
│       └── user_repository.py        # Abstract interface
└── infrastructure/
    └── repositories/
        ├── postgres_user_repository.py    # PostgreSQL
        ├── mongo_user_repository.py       # MongoDB
        └── memory_user_repository.py      # In-memory (testing)
```

### 2. Generic Type Parameter

The `Repository[T]` generic indicates what entity type the repository manages:

```python
# Repository for User entities
class UserRepository(Repository[User]):
    pass

# Repository for Product entities
class ProductRepository(Repository[Product]):
    pass

# Repository for Order entities
class OrderRepository(Repository[Order]):
    pass
```

### 3. Domain-Specific Methods

Add methods that make sense for your domain:

```python
class OrderRepository(Repository[Order]):
    # Standard CRUD
    async def get(self, id: str) -> Optional[Order]:
        pass

    async def save(self, order: Order) -> Order:
        pass

    # Domain-specific queries
    async def find_by_customer(self, customer_id: str) -> List[Order]:
        pass

    async def find_pending_orders(self) -> List[Order]:
        pass

    async def find_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Order]:
        pass

    async def get_total_revenue(self, customer_id: str) -> float:
        pass
```

## Dependency Injection Wiring

Wire repositories in your container configuration:

```python
# config.py
from vega.di import Container
from domain.repositories.user_repository import UserRepository
from domain.repositories.product_repository import ProductRepository
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from infrastructure.repositories.postgres_product_repository import PostgresProductRepository

container = Container({
    # Map abstract interfaces to concrete implementations
    UserRepository: PostgresUserRepository,
    ProductRepository: PostgresProductRepository,
})
```

## Real-World Examples

### Example 1: User Repository with Multiple Implementations

```python
# domain/repositories/user_repository.py
class UserRepository(Repository[User]):
    @abstractmethod
    async def get(self, id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def search(self, query: str) -> List[User]:
        pass

# infrastructure/repositories/postgres_user_repository.py
@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    def __init__(self, db_session: DatabaseSession):
        self.db = db_session

    async def get(self, id: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.id == id)
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, user: User) -> User:
        model = self._to_model(user)
        self.db.add(model)
        await self.db.commit()
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        query = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def search(self, query: str) -> List[User]:
        stmt = select(UserModel).where(
            UserModel.name.ilike(f"%{query}%")
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            created_at=model.created_at
        )

    def _to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            created_at=entity.created_at
        )

# infrastructure/repositories/memory_user_repository.py
@injectable(scope=Scope.SINGLETON)
class MemoryUserRepository(UserRepository):
    """In-memory implementation for testing"""

    def __init__(self):
        self._users: Dict[str, User] = {}

    async def get(self, id: str) -> Optional[User]:
        return self._users.get(id)

    async def save(self, user: User) -> User:
        self._users[user.id] = user
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        return next(
            (u for u in self._users.values() if u.email == email),
            None
        )

    async def search(self, query: str) -> List[User]:
        return [
            u for u in self._users.values()
            if query.lower() in u.name.lower()
        ]
```

### Example 2: Order Repository with Complex Queries

```python
# domain/repositories/order_repository.py
class OrderRepository(Repository[Order]):
    @abstractmethod
    async def get(self, id: str) -> Optional[Order]:
        pass

    @abstractmethod
    async def save(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def find_by_customer(self, customer_id: str) -> List[Order]:
        pass

    @abstractmethod
    async def find_pending_orders(self) -> List[Order]:
        pass

    @abstractmethod
    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        pass

    @abstractmethod
    async def get_customer_total_spent(self, customer_id: str) -> float:
        pass

# infrastructure/repositories/postgres_order_repository.py
@injectable(scope=Scope.SINGLETON)
class PostgresOrderRepository(OrderRepository):
    def __init__(self, db_session: DatabaseSession):
        self.db = db_session

    async def get(self, id: str) -> Optional[Order]:
        query = (
            select(OrderModel)
            .options(joinedload(OrderModel.items))
            .where(OrderModel.id == id)
        )
        result = await self.db.execute(query)
        model = result.unique().scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, order: Order) -> Order:
        model = self._to_model(order)
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def find_by_customer(self, customer_id: str) -> List[Order]:
        query = (
            select(OrderModel)
            .where(OrderModel.customer_id == customer_id)
            .order_by(OrderModel.created_at.desc())
        )
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_pending_orders(self) -> List[Order]:
        query = (
            select(OrderModel)
            .where(OrderModel.status == "pending")
            .order_by(OrderModel.created_at)
        )
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        query = select(OrderModel).where(OrderModel.status == status.value)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_customer_total_spent(self, customer_id: str) -> float:
        query = select(func.sum(OrderModel.total)).where(
            OrderModel.customer_id == customer_id,
            OrderModel.status == "completed"
        )
        result = await self.db.execute(query)
        return result.scalar() or 0.0

    def _to_entity(self, model: OrderModel) -> Order:
        return Order(
            id=model.id,
            customer_id=model.customer_id,
            items=[self._item_to_entity(item) for item in model.items],
            total=model.total,
            status=OrderStatus(model.status),
            created_at=model.created_at
        )

    def _to_model(self, entity: Order) -> OrderModel:
        return OrderModel(
            id=entity.id,
            customer_id=entity.customer_id,
            total=entity.total,
            status=entity.status.value,
            created_at=entity.created_at
        )
```

### Example 3: Cached Repository

```python
@injectable(scope=Scope.SINGLETON)
class CachedUserRepository(UserRepository):
    """Repository with caching layer"""

    def __init__(
        self,
        db_repository: PostgresUserRepository,
        cache: CacheService
    ):
        self.db = db_repository
        self.cache = cache
        self.cache_ttl = 300  # 5 minutes

    async def get(self, id: str) -> Optional[User]:
        # Try cache first
        cached = await self.cache.get(f"user:{id}")
        if cached:
            return User(**cached)

        # Fallback to database
        user = await self.db.get(id)
        if user:
            await self.cache.set(
                f"user:{id}",
                user.dict(),
                ttl=self.cache_ttl
            )
        return user

    async def save(self, user: User) -> User:
        # Save to database
        user = await self.db.save(user)

        # Invalidate cache
        await self.cache.delete(f"user:{user.id}")
        await self.cache.delete(f"user:email:{user.email}")

        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        # Try cache first
        cached = await self.cache.get(f"user:email:{email}")
        if cached:
            return User(**cached)

        # Fallback to database
        user = await self.db.find_by_email(email)
        if user:
            await self.cache.set(
                f"user:email:{email}",
                user.dict(),
                ttl=self.cache_ttl
            )
        return user
```

## Testing with Repositories

### Unit Testing with Mock Repository

```python
import pytest
from domain.interactors.create_user import CreateUser

class MockUserRepository(UserRepository):
    def __init__(self):
        self.users = {}

    async def get(self, id: str) -> Optional[User]:
        return self.users.get(id)

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        return next(
            (u for u in self.users.values() if u.email == email),
            None
        )

async def test_create_user():
    # Setup container with mock
    mock_repo = MockUserRepository()
    container = Container({UserRepository: lambda: mock_repo})
    set_container(container)

    # Execute interactor
    user = await CreateUser(name="Test", email="test@test.com")

    # Verify
    assert user.name == "Test"
    assert user.email == "test@test.com"
    assert len(mock_repo.users) == 1

async def test_duplicate_email():
    mock_repo = MockUserRepository()
    container = Container({UserRepository: lambda: mock_repo})
    set_container(container)

    # Create first user
    await CreateUser(name="First", email="test@test.com")

    # Try duplicate
    with pytest.raises(UserAlreadyExistsError):
        await CreateUser(name="Second", email="test@test.com")
```

### Integration Testing with Real Database

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository

@pytest.fixture
async def db_session():
    engine = create_async_engine("postgresql+asyncpg://localhost/test_db")
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

async def test_user_repository_integration(db_session):
    # Use real repository
    repository = PostgresUserRepository(db_session)

    # Create user
    user = User(id="1", name="Test", email="test@test.com")
    saved = await repository.save(user)

    # Verify retrieval
    found = await repository.get("1")
    assert found.name == "Test"
    assert found.email == "test@test.com"

    # Verify find by email
    by_email = await repository.find_by_email("test@test.com")
    assert by_email.id == "1"
```

## Best Practices

### ✅ DO

```python
# Define interface in domain layer
# domain/repositories/user_repository.py
class UserRepository(Repository[User]):
    pass

# Implement in infrastructure layer
# infrastructure/repositories/postgres_user_repository.py
class PostgresUserRepository(UserRepository):
    pass

# Use domain-specific method names
async def find_by_email(self, email: str) -> Optional[User]:
    pass

async def find_active_users(self) -> List[User]:
    pass

# Return domain entities, not ORM models
async def get(self, id: str) -> Optional[User]:
    model = await self.db.get(id)
    return self._to_entity(model)  # Convert to domain entity

# Use @injectable for dependency injection
@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    pass
```

### ❌ DON'T

```python
# Don't implement in domain layer
# domain/repositories/user_repository.py
class UserRepository(Repository[User]):
    async def get(self, id: str):
        return await db.execute(...)  # ❌ Implementation in domain

# Don't expose ORM models
async def get(self, id: str) -> UserModel:  # ❌ Returns ORM model
    return await self.db.get(id)

# Don't add framework-specific methods
async def get_sqlalchemy_query(self):  # ❌ Framework-specific
    pass

# Don't put business logic in repositories
async def save(self, user: User) -> User:
    if user.age < 18:  # ❌ Business logic
        raise ValueError("Too young")
    return await self.db.save(user)

# Don't use concrete types in domain
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository

class CreateUser(Interactor[User]):
    @bind
    async def call(self, repository: PostgresUserRepository):  # ❌ Concrete type
        pass
```

## CLI Generation

Generate repositories using the CLI:

```bash
# Generate repository interface and implementations
vega generate repository UserRepository --impl sql
vega generate repository ProductRepository --impl memory
vega generate repository OrderRepository --impl mongo
```

## Next Steps

- [Interactor](interactor.md) - Single-purpose use cases
- [Mediator](mediator.md) - Complex workflow orchestration
- [Service](service.md) - External service abstraction
- [Dependency Injection](../core/dependency-injection.md) - Learn DI system
