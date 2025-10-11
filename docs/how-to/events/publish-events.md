# Event Publishing Syntax Guide

Vega Events offers **two main syntaxes** for publishing events. **Auto-publish is enabled by default** (like Interactors!), providing ultra-clean syntax out of the box.

---

## Syntax Comparison

### Auto-Publish Syntax (Default - Recommended)

**Auto-publish is ENABLED BY DEFAULT!** Just await the event constructor:

```python
from dataclasses import dataclass
from vega.events import Event

@dataclass(frozen=True)
class UserCreated(Event):  # Auto-publish is enabled by default!
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()

# Event is automatically published when instantiated!
await UserCreated(user_id="123", email="test@test.com", name="Test")
```

**When to use**:
- **Default choice for 95% of scenarios**
- In workflows where the event should be published immediately
- For fire-and-forget events
- In Interactor/Mediator patterns (consistent syntax!)
- When you want the cleanest possible code

**Advantages**:
- [OK] Cleanest syntax - just like Interactors!
- [OK] No `.publish()` call needed
- [OK] Perfect for event-driven workflows
- [OK] **Enabled by default** - no configuration needed!

**Limitations**:
- Cannot inspect/modify event before publishing
- Cannot publish conditionally (event is always published)
- Event instance is not accessible (returns coroutine)

---

### Manual Publish Syntax (When You Need Control)

**Disable auto-publish** when you need to inspect/modify the event first:

```python
from dataclasses import dataclass
from vega.events import Event

@dataclass(frozen=True)
class UserCreated(Event, auto_publish=False):  # <- Disable auto-publish
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()

# Create event but don't publish yet
event = UserCreated(user_id="123", email="test@test.com", name="Test")

# Add metadata or inspect
event.add_metadata('source', 'api')

# Manually publish when ready
await event.publish()
```

**When to use**:
- When you need to inspect/modify the event before publishing
- When publishing conditionally
- When you need the event instance for testing or logging

**Advantages**:
- Full control over when event is published
- Can add metadata before publishing
- Can inspect event properties
- Can publish conditionally

---

### Verbose Syntax (Not Recommended)

Using the event bus directly - only needed for custom bus instances:

```python
from vega.events import get_event_bus

# Create event (with auto_publish=False)
event = UserCreated(user_id="123", email="test@test.com", name="Test")

# Get bus and publish
bus = get_event_bus()
await bus.publish(event)
```

**When to use**: Almost never. Only when you need a custom event bus instance.

---

## Detailed Examples

### Example 1: Auto-Publish in Workflows (Default Behavior)

```python
from vega.events import Event
from dataclasses import dataclass

# Auto-publish is enabled by default!
@dataclass(frozen=True)
class PaymentProcessed(Event):
    payment_id: str
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()

@dataclass(frozen=True)
class OrderShipped(Event):
    order_id: str
    tracking_number: str

    def __post_init__(self):
        super().__init__()


async def complete_order_workflow(order_id: str, amount: float):
    """Complete order processing workflow"""

    # Process payment - auto-publishes (default behavior)!
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

### Example 2: Manual Publish with Conditional Logic

```python
from vega.events import Event
from dataclasses import dataclass

# Disable auto-publish when you need control
@dataclass(frozen=True)
class OrderPlaced(Event, auto_publish=False):  # <- Disable auto-publish
    order_id: str
    amount: float
    customer_email: str

    def __post_init__(self):
        super().__init__()


async def place_order(order_id: str, amount: float, customer_email: str):
    """Place an order and optionally publish event"""

    # Create order...
    order = save_order(order_id, amount, customer_email)

    # Create event (doesn't auto-publish because auto_publish=False)
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

### Example 3: Mixed Approach

```python
from vega.events import Event
from dataclasses import dataclass

# Disable auto-publish for events that need metadata
@dataclass(frozen=True)
class UserRegistered(Event, auto_publish=False):
    user_id: str
    email: str

    def __post_init__(self):
        super().__init__()

# Keep auto-publish for simple fire-and-forget events (default)
@dataclass(frozen=True)
class WelcomeEmailScheduled(Event):  # auto-publish is default!
    user_id: str
    email: str

    def __post_init__(self):
        super().__init__()


async def register_user(email: str, password: str):
    """Register new user"""

    # Create user...
    user = create_user(email, password)

    # Main event - manual publish with metadata (auto_publish=False)
    event = UserRegistered(user_id=user.id, email=user.email)
    event.add_metadata('registration_source', 'web')
    await event.publish()

    # Side-effect event - auto-publishes (default behavior)!
    await WelcomeEmailScheduled(user_id=user.id, email=user.email)

    return user
```

### Example 4: Integration with Interactors

```python
from vega.patterns import Interactor
from vega.di import bind
from vega.events import Event
from dataclasses import dataclass

# Auto-publish is default - consistent with Interactor syntax!
@dataclass(frozen=True)
class UserCreated(Event):  # No auto_publish=True needed!
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

        # Publish event - auto-publishes by default!
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

## Decision Guide

Use this flowchart to decide which syntax to use:

```
Do you need a custom event bus?
-- YES -> Use: bus.publish(event)
-- NO
    v
    Do you need to modify the event before publishing?
    -- YES -> Use: auto_publish=False + event.publish()
    -- NO
        v
        Do you need conditional publishing?
        -- YES -> Use: auto_publish=False + event.publish()
        -- NO
            v
            [OK] Use default auto-publish (await Event(...))
```

**Key Point**: Auto-publish is **enabled by default**. Only use `auto_publish=False` when you need control over when/if the event is published.

---

## Performance Notes

All three syntaxes have identical performance:
- Auto-publish uses metaclass (zero runtime overhead)
- `.publish()` calls the same underlying bus
- `bus.publish()` is the same method

**Choose based on code clarity, not performance!**

---

## Best Practices

### DO

```python
# Use default auto-publish for most events (cleanest!)
@dataclass(frozen=True)
class StepCompleted(Event):  # Auto-publish is default!
    ...

# Usage - ultra-clean syntax!
await StepCompleted(step_id="123")

# Disable auto-publish only when you need metadata or conditional logic
@dataclass(frozen=True)
class UserCreated(Event, auto_publish=False):
    ...

event = UserCreated(...)
event.add_metadata('source', 'api')
await event.publish()

# Use consistent style within a module
```

### DON'T

```python
# Don't unnecessarily disable auto-publish
@dataclass(frozen=True)
class SimpleEvent(Event, auto_publish=False):  # [Avoid] Unnecessary!
    ...

event = SimpleEvent(...)
await event.publish()
# Just use default auto-publish: await SimpleEvent(...)

# Don't try to get the event object with auto-publish enabled (default)
event = UserCreated(...)  # [Avoid] This returns a coroutine, not the event!
# Use auto_publish=False if you need the event instance

# Don't use verbose syntax unless absolutely necessary
bus = get_event_bus()
await bus.publish(event)  # [Avoid] Prefer: await event.publish() or just await Event(...)
```

---

## Summary

| Syntax | Code | Use Case | Auto-Publish? |
|--------|------|----------|---------------|
| **Auto-Publish (Default)** | `await EventName(...)` | 95% of scenarios (recommended) | [OK] Enabled by default |
| **Manual Publish** | `event.publish()` | When you need control | [Avoid] Use `auto_publish=False` |
| **Verbose** | `bus.publish(event)` | Custom event bus | [Avoid] Use `auto_publish=False` |

**Key Takeaway**: Auto-publish is **enabled by default**, giving you the cleanest syntax out of the box. Only use `auto_publish=False` when you specifically need to inspect/modify events before publishing or publish conditionally.

**Recommendation**:
- [OK] **Default**: Use auto-publish (just `await Event(...)`) for most events
- [Warning] **Rare**: Use `auto_publish=False` only when you need conditional logic or metadata

---

## See Also

- [README.md](README.md) - Full event system documentation
- [EVENT_BUS_SUMMARY.md](../../EVENT_BUS_SUMMARY.md) - Implementation summary
- [Examples](../../examples/events/) - Working examples
  - [auto_publish_example.py](../../examples/events/auto_publish_example.py) - Auto-publish demo
  - [simple_syntax_example.py](../../examples/events/simple_syntax_example.py) - Simple syntax demo
