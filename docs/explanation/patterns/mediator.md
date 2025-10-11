# Mediator Pattern

A **Mediator** orchestrates multiple use cases to accomplish a complex business workflow.

## Core Concept

```
One Mediator = One Complex Workflow = Multiple Interactors
```

## When to Use

Use a Mediator when you need to:
- Coordinate multiple Interactors in a specific order
- Execute a multi-step business process
- Handle complex workflows with multiple dependencies
- Implement saga patterns or transaction workflows

## Basic Example

```python
from vega.patterns import Mediator
from domain.interactors.create_order import CreateOrder
from domain.interactors.process_payment import ProcessPayment
from domain.interactors.send_confirmation import SendConfirmation

class CheckoutWorkflow(Mediator[Order]):
    def __init__(self, cart_id: str, payment_method: str):
        self.cart_id = cart_id
        self.payment_method = payment_method

    async def call(self) -> Order:
        # Step 1: Create order from cart
        order = await CreateOrder(cart_id=self.cart_id)

        # Step 2: Process payment
        payment = await ProcessPayment(
            order_id=order.id,
            amount=order.total,
            payment_method=self.payment_method
        )

        # Step 3: Send confirmation
        await SendConfirmation(
            email=order.customer_email,
            order_id=order.id
        )

        return order

# Usage - metaclass auto-calls call()
order = await CheckoutWorkflow(
    cart_id="cart-123",
    payment_method="stripe"
)
```

## Key Differences: Mediator vs Interactor

| Aspect | Interactor | Mediator |
|--------|-----------|----------|
| **Purpose** | Single business operation | Complex workflow |
| **Responsibility** | One focused task | Orchestrates multiple tasks |
| **Dependencies** | Repositories, Services | Interactors, Mediators |
| **Complexity** | Simple, focused | Complex, multi-step |
| **Example** | CreateUser | UserRegistrationWorkflow |

```python
# ✅ Interactor - single operation
class CreateUser(Interactor[User]):
    @bind
    async def call(self, repository: UserRepository) -> User:
        user = User(...)
        return await repository.save(user)

# ✅ Mediator - orchestrates multiple interactors
class UserRegistrationWorkflow(Mediator[User]):
    async def call(self) -> User:
        user = await CreateUser(...)
        await SendWelcomeEmail(user.email)
        await CreateUserProfile(user.id)
        await NotifyAdmins(user.id)
        return user
```

## How It Works

### Metaclass Magic

Like Interactors, the `MediatorMeta` metaclass automatically calls `call()`:

```python
# What you write:
order = await CheckoutWorkflow(cart_id="123", payment_method="stripe")

# What happens internally:
# 1. CheckoutWorkflow.__init__(cart_id="123", payment_method="stripe")
# 2. instance.call() is automatically called
# 3. Orchestrates multiple interactors
# 4. Returns final result
```

### No Dependency Injection

Unlike Interactors, Mediators don't use `@bind` because they orchestrate Interactors (which handle their own dependencies):

```python
# ❌ Don't use @bind in Mediators
class CheckoutWorkflow(Mediator[Order]):
    @bind  # ❌ Not needed
    async def call(self, repository: OrderRepository) -> Order:
        pass

# ✅ Let Interactors handle dependencies
class CheckoutWorkflow(Mediator[Order]):
    async def call(self) -> Order:
        # Interactors handle their own dependencies
        order = await CreateOrder(...)
        await ProcessPayment(...)
        return order
```

## Real-World Examples

### Example 1: E-commerce Checkout

```python
class CheckoutWorkflow(Mediator[Order]):
    def __init__(
        self,
        cart_id: str,
        payment_method: str,
        shipping_address: Address,
        customer_id: str
    ):
        self.cart_id = cart_id
        self.payment_method = payment_method
        self.shipping_address = shipping_address
        self.customer_id = customer_id

    async def call(self) -> Order:
        # Step 1: Validate cart and inventory
        cart = await GetCart(self.cart_id)
        await ValidateInventory(cart.items)

        # Step 2: Calculate totals with tax and shipping
        pricing = await CalculateOrderPricing(
            items=cart.items,
            shipping_address=self.shipping_address
        )

        # Step 3: Create order
        order = await CreateOrder(
            customer_id=self.customer_id,
            items=cart.items,
            total=pricing.total,
            tax=pricing.tax,
            shipping_cost=pricing.shipping
        )

        # Step 4: Process payment
        try:
            payment = await ProcessPayment(
                order_id=order.id,
                amount=order.total,
                payment_method=self.payment_method
            )
        except PaymentFailedError:
            await CancelOrder(order.id)
            raise

        # Step 5: Reserve inventory
        await ReserveInventory(order.items)

        # Step 6: Clear cart
        await ClearCart(self.cart_id)

        # Step 7: Send confirmations
        await SendOrderConfirmation(order.id, order.customer_email)
        await NotifyWarehouse(order.id)

        return order
```

### Example 2: User Registration with Verification

```python
class UserRegistrationWorkflow(Mediator[User]):
    def __init__(
        self,
        email: str,
        password: str,
        name: str,
        company: Optional[str] = None
    ):
        self.email = email
        self.password = password
        self.name = name
        self.company = company

    async def call(self) -> User:
        # Step 1: Create user account
        user = await CreateUser(
            email=self.email,
            password=self.password,
            name=self.name
        )

        # Step 2: Create user profile
        profile = await CreateUserProfile(
            user_id=user.id,
            company=self.company
        )

        # Step 3: Generate verification token
        token = await GenerateVerificationToken(user.id)

        # Step 4: Send verification email
        await SendVerificationEmail(
            email=user.email,
            token=token,
            name=user.name
        )

        # Step 5: Create default settings
        await CreateUserSettings(user.id)

        # Step 6: Subscribe to newsletter (if opted in)
        if self.company:
            await SubscribeToNewsletter(user.email)

        # Step 7: Log registration event
        await LogUserRegistration(user.id)

        return user
```

### Example 3: Order Fulfillment with Compensation

```python
class OrderFulfillmentWorkflow(Mediator[Shipment]):
    def __init__(self, order_id: str):
        self.order_id = order_id

    async def call(self) -> Shipment:
        # Step 1: Get order
        order = await GetOrder(self.order_id)

        # Step 2: Validate order can be fulfilled
        await ValidateOrderStatus(order.id)

        # Step 3: Pick items from warehouse
        try:
            picked_items = await PickOrderItems(order.items)
        except ItemNotAvailableError as e:
            # Compensation: Update inventory and notify
            await UpdateInventoryStatus(e.item_id, "out_of_stock")
            await NotifyCustomer(order.customer_id, "item_unavailable")
            raise

        # Step 4: Create shipment
        shipment = await CreateShipment(
            order_id=order.id,
            items=picked_items,
            address=order.shipping_address
        )

        # Step 5: Generate shipping label
        label = await GenerateShippingLabel(shipment.id)

        # Step 6: Update order status
        await UpdateOrderStatus(order.id, "shipped")

        # Step 7: Notify customer
        await SendShippingNotification(
            email=order.customer_email,
            tracking_number=label.tracking_number
        )

        return shipment
```

## Error Handling and Compensation

Mediators often need to handle errors and compensate for failures:

```python
class BookingWorkflow(Mediator[Booking]):
    async def call(self) -> Booking:
        # Create booking
        booking = await CreateBooking(...)

        try:
            # Charge customer
            payment = await ProcessPayment(...)

            try:
                # Reserve resource
                reservation = await ReserveResource(...)
                return booking

            except ReservationError:
                # Compensate: Refund payment
                await RefundPayment(payment.id)
                await CancelBooking(booking.id)
                raise

        except PaymentError:
            # Compensate: Cancel booking
            await CancelBooking(booking.id)
            raise
```

## Testing

Test mediators by mocking the interactors they orchestrate:

```python
import pytest
from unittest.mock import AsyncMock, patch

async def test_checkout_workflow():
    # Mock interactors
    with patch('domain.interactors.create_order.CreateOrder') as mock_create, \
         patch('domain.interactors.process_payment.ProcessPayment') as mock_payment, \
         patch('domain.interactors.send_confirmation.SendConfirmation') as mock_confirm:

        # Setup mocks
        mock_order = Order(id="order-123", total=100.0)
        mock_create.return_value = AsyncMock(return_value=mock_order)
        mock_payment.return_value = AsyncMock(return_value=Payment(id="pay-123"))
        mock_confirm.return_value = AsyncMock(return_value=None)

        # Execute workflow
        result = await CheckoutWorkflow(
            cart_id="cart-123",
            payment_method="stripe"
        )

        # Verify order of operations
        assert mock_create.called
        assert mock_payment.called
        assert mock_confirm.called
        assert result.id == "order-123"

async def test_checkout_workflow_payment_failure():
    with patch('domain.interactors.create_order.CreateOrder') as mock_create, \
         patch('domain.interactors.process_payment.ProcessPayment') as mock_payment:

        # Setup mocks
        mock_create.return_value = AsyncMock(return_value=Order(id="order-123"))
        mock_payment.side_effect = PaymentFailedError("Card declined")

        # Verify error is propagated
        with pytest.raises(PaymentFailedError):
            await CheckoutWorkflow(
                cart_id="cart-123",
                payment_method="stripe"
            )
```

## Best Practices

### ✅ DO

```python
# Keep workflows focused on orchestration
class CheckoutWorkflow(Mediator[Order]):
    async def call(self) -> Order:
        order = await CreateOrder(...)
        await ProcessPayment(...)
        return order

# Use clear step comments
async def call(self) -> Order:
    # Step 1: Create order
    order = await CreateOrder(...)

    # Step 2: Process payment
    await ProcessPayment(...)

    # Step 3: Send confirmation
    await SendConfirmation(...)

# Handle errors with compensation
try:
    payment = await ProcessPayment(...)
except PaymentError:
    await CancelOrder(order.id)
    raise

# Use descriptive workflow names
class UserRegistrationWorkflow(Mediator[User]):
    pass

class OrderFulfillmentWorkflow(Mediator[Shipment]):
    pass
```

### ❌ DON'T

```python
# Don't use @bind in Mediators
class CheckoutWorkflow(Mediator[Order]):
    @bind  # ❌ Not needed
    async def call(self, repository: OrderRepository):
        pass

# Don't put business logic in Mediators
class CheckoutWorkflow(Mediator[Order]):
    async def call(self) -> Order:
        # ❌ Business logic belongs in Interactors
        if quantity < 0:
            raise InvalidQuantityError()
        order = Order(...)
        return order

# Don't access repositories directly
class CheckoutWorkflow(Mediator[Order]):
    async def call(self) -> Order:
        # ❌ Use Interactors instead
        order = await self.order_repository.save(...)

# Don't create simple workflows
class CreateUser(Mediator[User]):  # ❌ Use Interactor instead
    async def call(self) -> User:
        return await CreateUserInteractor(...)
```

## CLI Generation

Generate mediators using the CLI:

```bash
vega generate mediator CheckoutWorkflow
vega generate mediator UserRegistrationWorkflow
vega generate mediator OrderFulfillmentWorkflow
```

## Next Steps

- [Interactor](interactor.md) - Single-purpose use cases
- [Repository](repository.md) - Data persistence abstraction
- [Service](service.md) - External service abstraction
- [Dependency Injection](../core/dependency-injection.md) - Learn DI system
