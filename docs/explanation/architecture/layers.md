# Architecture Layers

Vega Framework implements a strict 4-layer architecture. This document explains each layer in detail.

## Overview

```
┌─────────────────────────────────────┐
│      Presentation Layer             │  User interfaces (CLI, Web)
├─────────────────────────────────────┤
│      Application Layer              │  Workflows and orchestration
├─────────────────────────────────────┤
│      Domain Layer (CORE)            │  Business logic
├─────────────────────────────────────┤
│      Infrastructure Layer           │  Technical implementations
└─────────────────────────────────────┘
```

## Domain Layer (Core)

The innermost layer containing pure business logic.

### Purpose

Keep business logic isolated, testable, and independent of any framework or technology.

### Contains

1. **Entities** - Business data structures
2. **Repository Interfaces** - Data persistence contracts
3. **Service Interfaces** - External service contracts
4. **Interactors** - Single-purpose use cases

### Rules

- ✅ **NO** dependencies on any other layer
- ✅ **NO** framework code (FastAPI, SQLAlchemy, etc.)
- ✅ **NO** infrastructure details
- ✅ Pure Python only
- ✅ Only defines interfaces, never implementations

### Examples

**Entity**:
```python
# domain/entities/product.py
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Product:
    id: str
    name: str
    price: Decimal
    stock: int
```

**Repository Interface**:
```python
# domain/repositories/product_repository.py
from vega.patterns import Repository
from domain.entities.product import Product

class ProductRepository(Repository[Product]):
    async def find_by_name(self, name: str) -> List[Product]:
        pass

    async def update_stock(self, product_id: str, quantity: int):
        pass
```

**Service Interface**:
```python
# domain/services/payment_service.py
from vega.patterns import Service

class PaymentService(Service):
    async def charge(self, amount: Decimal, token: str) -> PaymentResult:
        pass
```

**Interactor**:
```python
# domain/interactors/purchase_product.py
from vega.patterns import Interactor
from vega.di import bind

class PurchaseProduct(Interactor[Order]):
    def __init__(self, product_id: str, quantity: int):
        self.product_id = product_id
        self.quantity = quantity

    @bind
    async def call(
        self,
        product_repo: ProductRepository,
        payment_service: PaymentService
    ) -> Order:
        # Pure business logic
        product = await product_repo.find_by_id(self.product_id)

        if product.stock < self.quantity:
            raise InsufficientStockError()

        total = product.price * self.quantity
        result = await payment_service.charge(total, self.payment_token)

        if not result.success:
            raise PaymentFailedError()

        await product_repo.update_stock(product.id, -self.quantity)

        return Order(...)
```

## Application Layer

Orchestrates domain use cases into complex workflows.

### Purpose

Manage multi-step business workflows while remaining independent of technical details.

### Contains

1. **Mediators** - Multi-step workflows
2. **Application Services** - Coordinate domain operations

### Rules

- ✅ Depends **only** on domain layer
- ✅ **NO** infrastructure dependencies
- ✅ **NO** knowledge of HTTP, databases, or external services
- ✅ Orchestrates interactors without implementation details

### Examples

**Mediator**:
```python
# application/mediators/checkout_workflow.py
from vega.patterns import Mediator

class CheckoutWorkflow(Mediator[Order]):
    def __init__(self, cart_id: str, payment_token: str):
        self.cart_id = cart_id
        self.payment_token = payment_token

    async def call(self) -> Order:
        # Get cart
        cart = await GetCart(self.cart_id)

        # Validate cart
        await ValidateCart(cart.id)

        # Purchase each product
        for item in cart.items:
            await PurchaseProduct(item.product_id, item.quantity)

        # Create order
        order = await CreateOrder(cart.items)

        # Process payment
        await ProcessPayment(order.id, self.payment_token)

        # Send confirmation
        await SendOrderConfirmation(order.id)

        # Clear cart
        await ClearCart(self.cart_id)

        return order
```

## Infrastructure Layer

Provides concrete implementations of domain interfaces.

### Purpose

Isolate all technical details and external dependencies, ensuring they can be swapped without impacting business logic.

### Contains

1. **Repository Implementations** - Database-specific code
2. **Service Implementations** - External API integrations
3. **Database Models** - ORM models (SQLAlchemy)
4. **Adapters** - Technology-specific clients
5. **Configuration** - DI container setup

### Rules

- ✅ Implements domain interfaces
- ✅ Contains **ALL** technology-specific code
- ✅ Depends on domain layer
- ✅ Should be easily replaceable
- ✅ **NO** business logic

### Examples

**Repository Implementation**:
```python
# infrastructure/repositories/postgres_product_repository.py
from vega.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class PostgresProductRepository(ProductRepository):
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def find_by_name(self, name: str) -> List[Product]:
        async with self.db.session() as session:
            result = await session.execute(
                select(ProductModel).where(ProductModel.name.like(f"%{name}%"))
            )
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]

    async def update_stock(self, product_id: str, quantity: int):
        async with self.db.session() as session:
            product = await session.get(ProductModel, product_id)
            product.stock += quantity
            await session.commit()

    def _to_entity(self, model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            price=model.price,
            stock=model.stock
        )
```

**Service Implementation**:
```python
# infrastructure/services/stripe_payment_service.py
import stripe
from vega.di import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class StripePaymentService(PaymentService):
    def __init__(self, settings: Settings):
        stripe.api_key = settings.STRIPE_API_KEY

    async def charge(self, amount: Decimal, token: str) -> PaymentResult:
        try:
            charge = stripe.Charge.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                source=token
            )
            return PaymentResult(success=True, transaction_id=charge.id)
        except stripe.error.CardError as e:
            return PaymentResult(success=False, error=str(e))
```

## Presentation Layer

Handles user interaction through different interfaces.

### Purpose

Provide interfaces for users to interact with the application while keeping business logic independent.

### Contains

1. **Web API** - FastAPI routes and controllers
2. **CLI** - Command-line interface commands
3. **Request/Response Models** - Data transfer objects
4. **Middleware** - Request/response processing

### Rules

- ✅ Depends on application and domain layers
- ✅ Handles input validation and formatting
- ✅ Translates external requests into domain operations
- ✅ **NO** business logic
- ✅ Can use infrastructure for framework setup

### Examples

**Web API Route**:
```python
# presentation/web/routes/product_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class PurchaseRequest(BaseModel):
    product_id: str
    quantity: int
    payment_token: str

@router.post("/products/purchase")
async def purchase_product(request: PurchaseRequest):
    try:
        order = await PurchaseProduct(
            product_id=request.product_id,
            quantity=request.quantity
        )
        return {"order": order}
    except InsufficientStockError:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    except PaymentFailedError:
        raise HTTPException(status_code=402, detail="Payment failed")
```

**CLI Command**:
```python
# presentation/cli/commands/product_commands.py
import click
from vega.cli.utils import async_command

@click.command()
@click.option('--product-id', required=True)
@click.option('--quantity', type=int, required=True)
@click.option('--token', required=True)
@async_command
async def purchase_product(product_id: str, quantity: int, token: str):
    """Purchase a product"""
    import config  # Initialize DI

    try:
        order = await PurchaseProduct(
            product_id=product_id,
            quantity=quantity
        )
        click.echo(f"Order created: {order.id}")
    except InsufficientStockError:
        click.echo("Error: Insufficient stock", err=True)
    except PaymentFailedError:
        click.echo("Error: Payment failed", err=True)
```

## Layer Dependencies

The **Dependency Rule** states that dependencies always point inward:

```
┌─────────────────────┐
│   Presentation      │───┐
└─────────────────────┘   │
                          ↓
┌─────────────────────┐   │
│   Infrastructure    │   │
└─────────────────────┘   │
         ↓                ↓
┌─────────────────────┐   │
│   Application       │───┘
└─────────────────────┘
         ↓
┌─────────────────────┐
│   Domain (CORE)     │
└─────────────────────┘
```

### Valid Dependencies

- ✅ Presentation → Application
- ✅ Presentation → Domain
- ✅ Application → Domain
- ✅ Infrastructure → Domain (implements interfaces)

### Invalid Dependencies

- ❌ Domain → Infrastructure
- ❌ Domain → Application
- ❌ Domain → Presentation
- ❌ Application → Infrastructure
- ❌ Application → Presentation

## Testing Each Layer

### Domain Layer Testing

Test without any infrastructure:

```python
class MockProductRepository(ProductRepository):
    async def find_by_id(self, id: str) -> Product:
        return Product(id=id, name="Test", price=Decimal("10.00"), stock=100)

async def test_purchase_product():
    container = Container({
        ProductRepository: MockProductRepository,
        PaymentService: MockPaymentService,
    })
    set_container(container)

    order = await PurchaseProduct(product_id="123", quantity=2)
    assert order.total == Decimal("20.00")
```

### Application Layer Testing

Test workflow orchestration:

```python
async def test_checkout_workflow():
    # Mock all dependencies
    container = Container({
        ProductRepository: MockProductRepository,
        PaymentService: MockPaymentService,
        # ... other mocks
    })

    order = await CheckoutWorkflow(cart_id="123", payment_token="tok_test")
    assert order.status == "completed"
```

### Infrastructure Layer Testing

Test with real or test databases:

```python
async def test_postgres_repository():
    # Use test database
    repo = PostgresProductRepository(test_db)
    product = Product(id="1", name="Test", price=Decimal("10"), stock=10)

    await repo.save(product)
    found = await repo.find_by_id("1")

    assert found.name == "Test"
```

### Presentation Layer Testing

Test HTTP endpoints:

```python
from fastapi.testclient import TestClient

def test_purchase_endpoint():
    client = TestClient(app)
    response = client.post("/products/purchase", json={
        "product_id": "123",
        "quantity": 2,
        "payment_token": "tok_test"
    })
    assert response.status_code == 200
```

## Next Steps

- [Dependency Rule](dependency-rule.md) - Understanding dependency flow
- [Patterns](../patterns/interactor.md) - Learn Vega patterns
- [Dependency Injection](../core/dependency-injection.md) - Learn DI system
