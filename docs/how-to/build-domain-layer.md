# Building the Domain Layer

The Domain Layer is the **heart** of your application. It contains pure business logic, independent of frameworks and infrastructure.

## Philosophy

> "The domain layer is where your business lives. It should read like a book about your business, not a technical manual."

### Core Principles

1. **Business First** - Code reflects business concepts, not technical concerns
2. **Framework Independence** - No FastAPI, SQLAlchemy, or external libraries
3. **Testability** - Easy to test without infrastructure
4. **Clarity** - A business analyst should understand the code

## What Goes in the Domain Layer?

### - YES - Domain Layer

```python
# Business entities
@dataclass
class Order:
    id: str
    customer_id: str
    total: Decimal
    status: OrderStatus

# Business rules
if order.total < Decimal("0"):
    raise InvalidOrderError("Order total cannot be negative")

# Business operations
class PlaceOrder(Interactor[Order]):
    async def call(self):
        # Pure business logic
        pass

# Business abstractions
class OrderRepository(Repository[Order]):
    async def find_by_customer(self, customer_id: str) -> List[Order]:
        pass
```

### x NO - NOT Domain Layer

```python
# x Database code
from sqlalchemy import Column, String
class Order(Base):
    __tablename__ = 'orders'

# x HTTP concerns
from fastapi import HTTPException
raise HTTPException(status_code=400)

# x External service details
import stripe
stripe.Charge.create(...)

# x UI concerns
def render_order_html(order):
    return f"<div>{order.id}</div>"
```

## Building Process

### Step 1: Understand the Business

Before writing code, understand:
- What is the business problem?
- What are the business rules?
- What operations does the business need?

**Example**: E-commerce order system
- Business problem: Process customer orders
- Business rules:
  - Order total must be positive
  - Products must be in stock
  - Customer must be verified
- Operations:
  - Place order
  - Cancel order
  - Refund order

### Step 2: Model Entities

Entities represent **business concepts**:

```python
# domain/entities/order.py
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass
class Order:
    """
    An order represents a customer's purchase.

    Business rules:
    - Total must be positive
    - Status transitions follow: pending -> confirmed -> shipped -> delivered
    - Cancelled orders cannot be modified
    """
    id: str
    customer_id: str
    items: List[OrderItem]
    total: Decimal
    status: OrderStatus
    created_at: datetime

    def can_be_cancelled(self) -> bool:
        """Order can only be cancelled if pending or confirmed"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def is_editable(self) -> bool:
        """Order is editable only when pending"""
        return self.status == OrderStatus.PENDING
```

**Key points**:
- Pure Python (no framework)
- Business terminology
- Business rules as methods
- Immutable when possible

### Step 3: Define Abstractions

Define **what you need**, not **how it's implemented**:

```python
# domain/repositories/order_repository.py
from vega.patterns import Repository
from domain.entities.order import Order

class OrderRepository(Repository[Order]):
    """
    Persistence abstraction for orders.

    The domain doesn't care HOW orders are stored (PostgreSQL, MongoDB, files).
    It only cares WHAT operations are available.
    """

    async def find_by_customer(self, customer_id: str) -> List[Order]:
        """Find all orders for a customer"""
        pass

    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        """Find all orders with given status"""
        pass

    async def save(self, order: Order) -> Order:
        """Save or update an order"""
        pass

# domain/services/payment_service.py
from vega.patterns import Service

class PaymentService(Service):
    """
    External payment processing abstraction.

    The domain doesn't care if you use Stripe, PayPal, or credit cards.
    It only defines what a payment service must do.
    """

    async def charge(self, amount: Decimal, customer_id: str) -> PaymentResult:
        """Charge a customer"""
        pass

    async def refund(self, transaction_id: str) -> bool:
        """Refund a transaction"""
        pass
```

**Key points**:
- Interfaces, not implementations
- Business-focused method names
- No technical details (no SQL, no HTTP)

### Step 4: Implement Use Cases

One interactor = one business operation:

```python
# domain/interactors/place_order.py
from vega.patterns import Interactor
from vega.di import bind

class PlaceOrder(Interactor[Order]):
    """
    Place an order for a customer.

    Business rules enforced:
    1. All products must be in stock
    2. Payment must be successful
    3. Customer must be verified
    """

    def __init__(
        self,
        customer_id: str,
        items: List[OrderItem],
        payment_method: str
    ):
        self.customer_id = customer_id
        self.items = items
        self.payment_method = payment_method

    @bind
    async def call(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        payment_service: PaymentService,
        inventory_service: InventoryService
    ) -> Order:
        # 1. Validate items
        if not self.items:
            raise EmptyOrderError("Order must contain at least one item")

        # 2. Check stock for all products
        for item in self.items:
            product = await product_repo.find_by_id(item.product_id)
            if not product:
                raise ProductNotFoundError(item.product_id)

            available = await inventory_service.check_stock(item.product_id)
            if available < item.quantity:
                raise InsufficientStockError(
                    product_id=item.product_id,
                    requested=item.quantity,
                    available=available
                )

        # 3. Calculate total
        total = sum(item.price * item.quantity for item in self.items)
        if total <= 0:
            raise InvalidOrderError("Order total must be positive")

        # 4. Process payment
        payment_result = await payment_service.charge(
            amount=total,
            customer_id=self.customer_id
        )
        if not payment_result.success:
            raise PaymentFailedError(payment_result.error)

        # 5. Reserve inventory
        for item in self.items:
            await inventory_service.reserve(item.product_id, item.quantity)

        # 6. Create order
        order = Order(
            id=generate_uuid(),
            customer_id=self.customer_id,
            items=self.items,
            total=total,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            payment_transaction_id=payment_result.transaction_id
        )

        # 7. Save order
        order = await order_repo.save(order)

        return order
```

**Key points**:
- Clear business logic flow
- Validates business rules
- Uses abstractions (repositories, services)
- Raises domain exceptions
- No framework code

## Business Logic vs Technical Logic

### Business Logic (Domain Layer)

```python
# - This is business logic:
if order.total < minimum_order_amount:
    raise OrderTooSmallError()

if not customer.is_verified:
    raise UnverifiedCustomerError()

if product.stock < quantity:
    raise InsufficientStockError()
```

### Technical Logic (Infrastructure Layer)

```python
# x This is NOT business logic:
if response.status_code != 200:
    raise HTTPError()

if connection.is_closed():
    connection.reconnect()

if cache.get(key) is None:
    cache.set(key, value)
```

## Domain Exceptions

Create specific exceptions for business errors:

```python
# domain/exceptions.py
class DomainException(Exception):
    """Base exception for all domain errors"""
    pass

class OrderException(DomainException):
    """Base exception for order-related errors"""
    pass

class EmptyOrderError(OrderException):
    """Order must contain at least one item"""
    pass

class InsufficientStockError(OrderException):
    """Not enough stock available"""
    def __init__(self, product_id: str, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}: "
            f"requested {requested}, available {available}"
        )

class PaymentFailedError(OrderException):
    """Payment processing failed"""
    pass
```

**Usage**:
```python
# Domain raises business exceptions
if product.stock < quantity:
    raise InsufficientStockError(product.id, quantity, product.stock)

# Presentation handles them
try:
    order = await PlaceOrder(...)
except InsufficientStockError as e:
    return {"error": str(e), "available": e.available}
```

## Real-World Example: E-commerce

### Entities

```python
# domain/entities/customer.py
@dataclass
class Customer:
    id: str
    name: str
    email: str
    is_verified: bool
    credit_limit: Decimal

# domain/entities/product.py
@dataclass
class Product:
    id: str
    name: str
    price: Decimal
    stock: int

# domain/entities/order.py
@dataclass
class Order:
    id: str
    customer_id: str
    items: List[OrderItem]
    total: Decimal
    status: OrderStatus
```

### Repositories

```python
# domain/repositories/customer_repository.py
class CustomerRepository(Repository[Customer]):
    async def find_by_email(self, email: str) -> Optional[Customer]:
        pass

# domain/repositories/product_repository.py
class ProductRepository(Repository[Product]):
    async def find_by_ids(self, ids: List[str]) -> List[Product]:
        pass

# domain/repositories/order_repository.py
class OrderRepository(Repository[Order]):
    async def find_by_customer(self, customer_id: str) -> List[Order]:
        pass
```

### Use Cases

```python
# domain/interactors/place_order.py
class PlaceOrder(Interactor[Order]):
    """Place a new order"""
    pass

# domain/interactors/cancel_order.py
class CancelOrder(Interactor[Order]):
    """Cancel an existing order"""
    pass

# domain/interactors/refund_order.py
class RefundOrder(Interactor[bool]):
    """Refund a cancelled or returned order"""
    pass
```

## Testing Domain Logic

Domain layer is easy to test:

```python
class MockOrderRepository(OrderRepository):
    def __init__(self):
        self.orders = {}

    async def save(self, order: Order) -> Order:
        self.orders[order.id] = order
        return order

class MockPaymentService(PaymentService):
    async def charge(self, amount: Decimal, customer_id: str) -> PaymentResult:
        return PaymentResult(success=True, transaction_id="test-123")

async def test_place_order():
    # Setup
    container = Container({
        OrderRepository: MockOrderRepository,
        PaymentService: MockPaymentService,
        # ... other mocks
    })
    set_container(container)

    # Execute
    order = await PlaceOrder(
        customer_id="cust-1",
        items=[OrderItem(product_id="prod-1", quantity=2, price=Decimal("10"))],
        payment_method="card"
    )

    # Assert
    assert order.status == OrderStatus.PENDING
    assert order.total == Decimal("20")
```

## Common Mistakes

### x Mistake 1: Putting Framework Code in Domain

```python
# x WRONG
from sqlalchemy import Column
from fastapi import HTTPException

class Order(Base):  # SQLAlchemy in domain
    __tablename__ = 'orders'

class PlaceOrder(Interactor[Order]):
    async def call(self):
        raise HTTPException(400, "Invalid")  # FastAPI in domain
```

### x Mistake 2: Not Enforcing Business Rules

```python
# x WRONG - No validation
class PlaceOrder(Interactor[Order]):
    async def call(self):
        order = Order(...)
        return await repository.save(order)  # Just saves, no validation

# - CORRECT - Validates business rules
class PlaceOrder(Interactor[Order]):
    async def call(self):
        if total < 0:
            raise InvalidOrderError()
        if stock < quantity:
            raise InsufficientStockError()
        # Now save
        return await repository.save(order)
```

### x Mistake 3: Mixing Multiple Operations

```python
# x WRONG - Too many responsibilities
class PlaceOrderAndSendEmailAndCreateInvoice(Interactor[Order]):
    pass

# - CORRECT - Single responsibility
class PlaceOrder(Interactor[Order]):
    pass

class SendOrderConfirmation(Interactor[None]):
    pass

# Use Mediator to orchestrate
class OrderWorkflow(Mediator[Order]):
    async def call(self):
        order = await PlaceOrder(...)
        await SendOrderConfirmation(order.id)
        return order
```

## Next Steps

- [Mediator pattern](../explanation/patterns/mediator.md) - Coordinate multiple interactors
- [Layer responsibilities](../explanation/architecture/layers.md) - Understand boundaries between layers
- [Generate components](../reference/cli/generate.md) - Scaffold new domain pieces with the CLI
