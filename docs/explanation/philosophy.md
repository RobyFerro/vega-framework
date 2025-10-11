# Vega Framework Philosophy

## Why Vega Exists

Most Python frameworks focus on **how to build** applications, but few enforce **how to architect** them properly. FastAPI shows you how to create endpoints, SQLAlchemy shows you how to query databases, but neither tells you where business logic should live or how to keep your code maintainable as it grows.

Vega Framework was born from **production experience** building complex Python applications that became unmaintainable over time. We've seen:

- Business logic scattered across routes, models, and utility files
- Database queries mixed with HTTP handling
- Impossible-to-test code due to tight coupling
- Fear of changing anything because dependencies are unclear
- New developers struggling to understand where things belong

**Vega solves this** by enforcing Clean Architecture principles through its structure and patterns.

## Core Philosophy

### 1. Architecture Over Code

> "Any organization that designs a system will produce a design whose structure is a copy of the organization's communication structure." - Conway's Law

Your code structure **matters more** than individual lines of code. A well-architected application with average code is better than poorly-structured brilliant code.

**Vega's approach**:
- Enforces clear layer separation (Domain, Application, Infrastructure, Presentation)
- Makes architectural violations difficult or impossible
- Provides patterns that guide correct architecture
- Validates architecture with `vega doctor`

### 2. Business Logic is Sacred

Your business logic - the rules, operations, and workflows that make your application valuable - should be:

- **Independent** of frameworks (FastAPI, Django, etc.)
- **Independent** of databases (PostgreSQL, MongoDB, etc.)
- **Independent** of UI (Web, CLI, GraphQL, etc.)
- **Testable** without any infrastructure
- **Readable** by business stakeholders, not just developers

**Why this matters**:

Imagine you need to:
- Migrate from PostgreSQL to MongoDB
- Expose your API via GraphQL instead of REST
- Add a CLI interface alongside your web API
- Test your business logic without a database

If your business logic is pure and isolated (Vega's Domain layer), these changes are **trivial**. If it's mixed with framework code, you'll rewrite everything.

**Example of the problem**:
```python
# ❌ Business logic mixed with framework
@app.post("/orders")
async def create_order(request: Request):
    # FastAPI-specific code
    data = await request.json()

    # SQLAlchemy-specific code
    order = OrderModel(
        customer_id=data['customer_id'],
        total=data['total']
    )
    session.add(order)
    session.commit()

    # Stripe-specific code
    stripe.Charge.create(
        amount=order.total,
        currency="usd",
        source=data['token']
    )

    return {"id": order.id}
```

**Problems**:
- Can't test without FastAPI, database, and Stripe
- Can't reuse for CLI or GraphQL
- Business rules (validation, stock checks) are missing
- Coupled to specific technologies

**Vega's solution**:
```python
# ✅ Pure business logic (Domain layer)
class PlaceOrder(Interactor[Order]):
    """
    Place an order - pure business logic.
    No framework, no database, no HTTP.
    """
    def __init__(self, customer_id: str, items: List[OrderItem]):
        self.customer_id = customer_id
        self.items = items

    @bind
    async def call(
        self,
        order_repo: OrderRepository,      # Abstract interface
        payment_service: PaymentService,  # Abstract interface
        inventory: InventoryService       # Abstract interface
    ) -> Order:
        # Pure business rules
        if not self.items:
            raise EmptyOrderError()

        # Check stock (business rule)
        for item in self.items:
            if not await inventory.has_stock(item.product_id, item.quantity):
                raise InsufficientStockError(item.product_id)

        # Calculate total (business rule)
        total = sum(item.price * item.quantity for item in self.items)

        # Create order entity (business model)
        order = Order(
            id=generate_id(),
            customer_id=self.customer_id,
            items=self.items,
            total=total,
            status=OrderStatus.PENDING
        )

        # Save through abstract interface
        order = await order_repo.save(order)

        # Process payment through abstract interface
        result = await payment_service.charge(total, self.customer_id)
        if not result.success:
            raise PaymentFailedError()

        return order

# ✅ FastAPI route (Presentation layer) - just wiring
@router.post("/orders")
async def create_order_api(request: CreateOrderRequest):
    """HTTP endpoint - just delegates to business logic"""
    try:
        order = await PlaceOrder(
            customer_id=request.customer_id,
            items=request.items
        )
        return {"order": order}
    except InsufficientStockError as e:
        raise HTTPException(400, str(e))

# ✅ CLI command (Presentation layer) - same business logic
@click.command()
@async_command
async def create_order_cli(customer_id: str, ...):
    """CLI command - same business logic"""
    try:
        order = await PlaceOrder(customer_id=customer_id, items=items)
        click.echo(f"Order created: {order.id}")
    except InsufficientStockError as e:
        click.echo(f"Error: {e}", err=True)
```

Notice how the **same business logic** works for both HTTP and CLI. You can test it without either. You can swap PostgreSQL for MongoDB without changing it.

### 3. Dependency Inversion

> "High-level policy should not depend on low-level details. Both should depend on abstractions."

This is **the most important principle** in Clean Architecture.

**Traditional dependency flow (WRONG)**:
```
Business Logic → PostgreSQL
Business Logic → Stripe API
Business Logic → FastAPI
```

Your valuable business logic depends on technical details. Change PostgreSQL to MongoDB? Rewrite business logic. Change Stripe to PayPal? Rewrite business logic.

**Vega's dependency flow (CORRECT)**:
```
Business Logic → Repository Interface
                      ↑
                 PostgreSQL Implementation

Business Logic → Payment Service Interface
                      ↑
                 Stripe Implementation
```

Business logic depends on **abstractions** (interfaces). Implementations depend on those abstractions. Now:
- Change PostgreSQL to MongoDB → just change implementation, business logic unchanged
- Change Stripe to PayPal → just change implementation, business logic unchanged
- Test business logic → use mock implementations, no real services needed

**This is what Vega enforces** through its structure:

```python
# Domain layer - defines WHAT you need
class OrderRepository(Repository[Order]):
    """Abstract interface - domain doesn't care HOW"""
    async def save(self, order: Order) -> Order:
        pass

# Infrastructure layer - implements HOW
class PostgresOrderRepository(OrderRepository):
    """Concrete implementation - PostgreSQL-specific"""
    async def save(self, order: Order) -> Order:
        # PostgreSQL code here
        pass

class MongoOrderRepository(OrderRepository):
    """Alternative implementation - MongoDB-specific"""
    async def save(self, order: Order) -> Order:
        # MongoDB code here
        pass

# Container - wires everything together
container = Container({
    OrderRepository: PostgresOrderRepository  # Swap to MongoOrderRepository anytime
})
```

### 4. Single Responsibility

Each component should do **one thing** and do it well.

**Vega's patterns enforce this**:

- **Interactor** = One use case = One business operation
  - `CreateUser` does ONE thing: create a user
  - `SendWelcomeEmail` does ONE thing: send email
  - NOT `CreateUserAndSendEmail` (two responsibilities)

- **Mediator** = One workflow = Orchestration only
  - `UserRegistrationFlow` orchestrates multiple interactors
  - Doesn't contain business logic itself
  - Just calls: `CreateUser` → `SendWelcomeEmail` → `CreateAuditLog`

- **Repository** = One entity = Data access for that entity
  - `UserRepository` manages User entities
  - NOT `UserAndOrderRepository` (two entities)

**Why this matters**:

When each component has a single responsibility:
- **Easy to understand** - you know exactly what it does
- **Easy to test** - test one thing at a time
- **Easy to change** - change one thing without breaking others
- **Easy to reuse** - reuse in different contexts

### 5. Testability First

If your code is hard to test, **your architecture is wrong**.

Vega makes testing trivial:

```python
# No database needed
class MockUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        return user

# No email service needed
class MockEmailService(EmailService):
    async def send(self, to: str, subject: str):
        pass

# Test pure business logic
async def test_create_user():
    container = Container({
        UserRepository: MockUserRepository,
        EmailService: MockEmailService,
    })

    user = await CreateUser(name="Test", email="test@test.com")
    assert user.name == "Test"
```

No Docker, no database, no external services, no HTTP server. Just **pure business logic testing**.

### 6. Convention Over Configuration

Vega provides **sensible defaults** and **clear conventions**:

- **Project structure** - Always the same 4 layers
- **File locations** - Entities in `domain/entities/`, routes in `presentation/web/routes/`
- **Naming** - `CreateUser` not `UserCreator`, `UserRepository` not `UserRepo`
- **Patterns** - Interactor, Mediator, Repository, Service
- **Dependency injection** - Automatic via type hints
- **Auto-discovery** - Routes and commands automatically registered

You don't spend time deciding "where should this file go?" or "what should I name this?" The framework tells you.

**Benefits**:
- **Consistency** - All Vega projects look similar
- **Onboarding** - New developers understand the structure immediately
- **Tooling** - CLI can generate components because structure is predictable
- **Maintainability** - Know where to find things

### 7. Explicit Over Implicit

Vega prefers **explicit, clear code** over "magic":

**Explicit dependencies**:
```python
@bind
async def call(
    self,
    user_repo: UserRepository,     # Explicitly declared
    email_service: EmailService,   # Clear what's needed
    payment_service: PaymentService
):
    # You can see exactly what this interactor needs
```

**Explicit business rules**:
```python
# ✅ Clear business rule
if order.total < Decimal("10.00"):
    raise MinimumOrderNotMetError("Order must be at least $10")

# ❌ Unclear magic number
if order.total < 10:
    raise ValueError("Invalid order")
```

**Explicit architecture**:
```
domain/
├── entities/        # Clearly business entities
├── repositories/    # Clearly data abstractions
├── services/        # Clearly external services
└── interactors/     # Clearly use cases

infrastructure/
├── repositories/    # Clearly implementations
└── services/        # Clearly implementations
```

You can look at the structure and **immediately understand** what's what.

## When to Use Vega

### ✅ Use Vega When

- Building **complex business applications** (not simple CRUD)
- Need **long-term maintainability** (multi-year projects)
- Have **complex business rules** that will evolve
- Multiple **delivery mechanisms** (API + CLI + background jobs)
- Want **high test coverage** of business logic
- Team needs **clear architecture guidance**
- Planning to **scale** the application and team

**Examples**:
- E-commerce platforms
- Financial systems
- Healthcare applications
- Enterprise SaaS products
- Complex workflow systems
- Multi-tenant applications

### ❌ Consider Alternatives When

- Building **simple CRUD** with minimal business logic
- **Prototyping** or MVPs that may be thrown away
- **Very small projects** (1-2 files)
- Team **strongly prefers** different architecture
- Need **extreme performance** (microseconds matter)

**Examples**:
- Simple REST API wrapping a database
- Weekend hackathon project
- Static website with minimal backend
- Proof of concept

## The Vega Way

Here's how development works with Vega:

### 1. Start with Domain

**Think about business first**, not technology:

- What business entities exist? → Create entities
- What operations does the business need? → Create interactors
- What data access is needed? → Define repository interfaces
- What external services are needed? → Define service interfaces

**Don't think about**:
- What database to use
- What web framework to use
- How to deploy
- API endpoints

That comes later.

### 2. Define Interfaces

Define **what you need**, not how it's implemented:

```python
# Define WHAT you need (domain layer)
class PaymentService(Service):
    async def charge(self, amount: Decimal, customer_id: str) -> PaymentResult:
        pass

# Implement HOW later (infrastructure layer)
class StripePaymentService(PaymentService):
    async def charge(self, amount: Decimal, customer_id: str) -> PaymentResult:
        # Stripe API calls here
        pass
```

This lets you:
- **Develop business logic** without waiting for infrastructure
- **Test easily** with mock implementations
- **Swap implementations** without changing business logic

### 3. Implement Use Cases

One business operation = one interactor:

```python
class PlaceOrder(Interactor[Order]):
    """Place a customer order - single, focused responsibility"""
    pass

class CancelOrder(Interactor[Order]):
    """Cancel an existing order - separate responsibility"""
    pass
```

NOT:
```python
class OrderManager:  # ❌ Too broad, unclear responsibility
    def place_order(self): pass
    def cancel_order(self): pass
    def refund_order(self): pass
    def ship_order(self): pass
```

### 4. Build Infrastructure

Only now implement the technical details:

```python
# Implement repositories with actual databases
class PostgresOrderRepository(OrderRepository):
    pass

# Implement services with actual APIs
class StripePaymentService(PaymentService):
    pass

# Configure dependency injection
container = Container({
    OrderRepository: PostgresOrderRepository,
    PaymentService: StripePaymentService,
})
```

### 5. Add Presentation

Finally, add user interfaces (API, CLI):

```python
# FastAPI route - just wiring
@router.post("/orders")
async def create_order(request: CreateOrderRequest):
    return await PlaceOrder(...)

# CLI command - same business logic
@click.command()
async def create_order_cli(...):
    return await PlaceOrder(...)
```

Notice: **Business logic is unchanged**. We just added different ways to access it.

### 6. Test Everything

Domain layer tests (no infrastructure):
```python
# Fast, isolated, no dependencies
async def test_place_order():
    # Use mocks - no database, no APIs
    order = await PlaceOrder(...)
    assert order.status == OrderStatus.PENDING
```

Infrastructure tests (with real dependencies):
```python
# Test actual PostgreSQL repository
async def test_postgres_repository():
    # Use test database
    order = await repository.save(...)
```

Presentation tests (HTTP, CLI):
```python
# Test HTTP endpoint
def test_create_order_endpoint():
    response = client.post("/orders", ...)
    assert response.status_code == 200
```

## Summary

Vega Framework is built on these principles:

1. **Architecture matters more than individual code**
2. **Business logic is sacred and must be isolated**
3. **Dependencies always point inward (dependency inversion)**
4. **Single responsibility for all components**
5. **Testability is non-negotiable**
6. **Convention over configuration**
7. **Explicit over implicit**

When you follow these principles, you get:
- **Maintainable** code that scales with your team
- **Testable** business logic without infrastructure
- **Flexible** architecture that adapts to change
- **Clear** structure that new developers understand
- **Confidence** to refactor and improve

**Vega doesn't just help you build applications. It helps you build them right.**

## Next Steps

- [Clean Architecture](architecture/clean-architecture.md) - Deep dive into architecture
- [Quick Start](../tutorials/quickstart.md) - Build your first Vega project
- [Building Domain Layer](../how-to/build-domain-layer.md) - Start with business logic
