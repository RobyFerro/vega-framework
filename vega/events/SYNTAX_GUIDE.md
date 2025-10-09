# Event Publishing Syntax Guide

Vega Events offers **three different syntaxes** for publishing events, from verbose to ultra-clean. Choose the one that best fits your use case!

---

## 📊 Syntax Comparison

### ❌ Verbose Syntax (Not Recommended)

```python
from vega.events import get_event_bus

# Create event
event = UserCreated(user_id="123", email="test@test.com", name="Test")

# Get bus and publish
bus = get_event_bus()
await bus.publish(event)
```

**When to use**: Almost never. Only when you need a custom event bus.

---

### ✅ Simple Syntax (Recommended Default)

```python
# Create event
event = UserCreated(user_id="123", email="test@test.com", name="Test")

# Publish
await event.publish()
```

**When to use**:
- Default choice for most scenarios
- When you need to inspect/modify the event before publishing
- When publishing conditionally
- When you want explicit control

**Advantages**:
- Clean and intuitive
- No need to import `get_event_bus()`
- Event can be inspected before publishing
- Can add metadata before publishing

---

### 🌟 Ultra-Clean Syntax (Auto-Publish)

**Step 1: Enable auto-publish on event class**

```python
from dataclasses import dataclass
from vega.events import Event

@dataclass(frozen=True)
class UserCreated(Event, auto_publish=True):  # ← Enable auto-publish
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()
```

**Step 2: Just await the constructor!**

```python
# Event is automatically published when instantiated!
await UserCreated(user_id="123", email="test@test.com", name="Test")
```

**When to use**:
- In workflows where the event should ALWAYS be published immediately
- For fire-and-forget events
- In Interactor/Mediator patterns (similar to how they work)
- When you want the cleanest possible syntax

**Advantages**:
- Cleanest syntax - just like Interactors!
- No `.publish()` call needed
- Perfect for event-driven workflows
- Enforces immediate publishing

**Limitations**:
- Cannot inspect/modify event before publishing
- Cannot publish conditionally (event is always published)
- Event instance is not accessible (returns coroutine)

---

## 🎯 Detailed Examples

### Example 1: Simple Syntax with Conditional Publishing

```python
from vega.events import Event
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderPlaced(Event):
    order_id: str
    amount: float
    customer_email: str

    def __post_init__(self):
        super().__init__()


async def place_order(order_id: str, amount: float, customer_email: str):
    """Place an order and optionally publish event"""

    # Create order...
    order = save_order(order_id, amount, customer_email)

    # Create event
    event = OrderPlaced(
        order_id=order.id,
        amount=order.amount,
        customer_email=order.customer_email
    )

    # Add metadata
    event.add_metadata('source', 'web_app')
    event.add_metadata('user_id', get_current_user_id())

    # Publish conditionally
    if order.amount > 100:  # Only publish for large orders
        await event.publish()

    return order
```

### Example 2: Auto-Publish in Workflows

```python
from vega.events import Event
from dataclasses import dataclass

# Enable auto-publish for workflow events
@dataclass(frozen=True)
class PaymentProcessed(Event, auto_publish=True):
    payment_id: str
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()

@dataclass(frozen=True)
class OrderShipped(Event, auto_publish=True):
    order_id: str
    tracking_number: str

    def __post_init__(self):
        super().__init__()


async def complete_order_workflow(order_id: str, amount: float):
    """Complete order processing workflow"""

    # Process payment - auto-publishes!
    await PaymentProcessed(
        payment_id=generate_payment_id(),
        order_id=order_id,
        amount=amount
    )

    # Ship order - auto-publishes!
    await OrderShipped(
        order_id=order_id,
        tracking_number=generate_tracking_number()
    )

    # Clean, sequential workflow!
```

### Example 3: Mixed Approach

```python
from vega.events import Event
from dataclasses import dataclass

# Manual publish for main events
@dataclass(frozen=True)
class UserRegistered(Event):
    user_id: str
    email: str

    def __post_init__(self):
        super().__init__()

# Auto-publish for side-effect events
@dataclass(frozen=True)
class WelcomeEmailSent(Event, auto_publish=True):
    user_id: str
    email: str

    def __post_init__(self):
        super().__init__()


async def register_user(email: str, password: str):
    """Register new user"""

    # Create user...
    user = create_user(email, password)

    # Main event - manual publish with metadata
    event = UserRegistered(user_id=user.id, email=user.email)
    event.add_metadata('registration_source', 'web')
    await event.publish()

    # Side-effect event - auto-publish
    await WelcomeEmailSent(user_id=user.id, email=user.email)

    return user
```

### Example 4: Integration with Interactors

```python
from vega.patterns import Interactor
from vega.di import bind
from vega.events import Event
from dataclasses import dataclass

# Auto-publish for Interactor events
@dataclass(frozen=True)
class UserCreated(Event, auto_publish=True):
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()


class CreateUser(Interactor[User]):
    """Create a new user"""

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        # Domain logic
        user = User(name=self.name, email=self.email)
        user = await repository.save(user)

        # Publish event - auto-publishes!
        await UserCreated(
            user_id=user.id,
            email=user.email,
            name=user.name
        )

        return user


# Usage - both use similar syntax!
user = await CreateUser(name="John", email="john@example.com")
```

---

## 🤔 Decision Guide

Use this flowchart to decide which syntax to use:

```
Do you need a custom event bus?
├─ YES → Use: bus.publish(event)
└─ NO
    ↓
    Do you need to modify the event before publishing?
    ├─ YES → Use: event.publish()
    └─ NO
        ↓
        Do you need conditional publishing?
        ├─ YES → Use: event.publish()
        └─ NO
            ↓
            Is this a workflow/always-publish scenario?
            ├─ YES → Use: auto_publish=True
            └─ NO → Use: event.publish() (default)
```

---

## ⚡ Performance Notes

All three syntaxes have identical performance:
- Auto-publish uses metaclass (zero runtime overhead)
- `.publish()` calls the same underlying bus
- `bus.publish()` is the same method

**Choose based on code clarity, not performance!**

---

## 🎨 Best Practices

### ✅ DO

```python
# Use auto-publish for workflow events
@dataclass(frozen=True)
class StepCompleted(Event, auto_publish=True):
    ...

# Use manual publish for events that need metadata
event = UserCreated(...)
event.add_metadata('source', 'api')
await event.publish()

# Use consistent style within a module
```

### ❌ DON'T

```python
# Don't mix styles unnecessarily
await UserCreated(...)  # auto-publish
await event.publish()   # manual publish
# Pick one approach per event type!

# Don't use auto-publish if you need the event object
event = UserCreated(...)  # Won't work with auto_publish=True!
# auto_publish returns a coroutine, not the event

# Don't use verbose syntax unless absolutely necessary
bus = get_event_bus()
await bus.publish(event)  # Prefer: await event.publish()
```

---

## 📚 Summary

| Syntax | Code | Use Case |
|--------|------|----------|
| **Verbose** | `await bus.publish(event)` | Custom event bus |
| **Simple** | `await event.publish()` | Default choice ✅ |
| **Auto-Publish** | `await EventName(...)` | Workflows, always-publish 🌟 |

**Recommendation**: Start with **Simple syntax** as default, use **Auto-Publish** for workflow events.

---

## 🔗 See Also

- [README.md](README.md) - Full event system documentation
- [EVENT_BUS_SUMMARY.md](../../EVENT_BUS_SUMMARY.md) - Implementation summary
- [Examples](../../examples/events/) - Working examples
  - [auto_publish_example.py](../../examples/events/auto_publish_example.py) - Auto-publish demo
  - [simple_syntax_example.py](../../examples/events/simple_syntax_example.py) - Simple syntax demo
