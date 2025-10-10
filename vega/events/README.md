# Vega Events - Domain Events & Event Bus

The Vega Events module provides a powerful event-driven architecture for your applications, enabling loose coupling and reactive programming patterns.

## Features

- ✅ **Event Bus** - Publish/subscribe pattern for domain events
- ✅ **Async Support** - Full async/await support for event handlers
- ✅ **Auto-Publish** - Ultra-clean syntax with metaclass-powered instant publishing
- ✅ **Priority Ordering** - Control handler execution order
- ✅ **Retry Logic** - Automatic retries for failed handlers
- ✅ **Middleware** - Cross-cutting concerns (logging, metrics, validation)
- ✅ **Event Inheritance** - Handlers for base events receive derived events
- ✅ **Type-Safe** - Full type hints support

## Quick Start

### 1. Define an Event

Events are immutable data classes that represent something that happened:

```python
from dataclasses import dataclass
from vega.events import Event

@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()
```

### 2. Subscribe to Events

Use the `@subscribe` decorator to register event handlers:

```python
from vega.events import subscribe

@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    """Send welcome email when user is created"""
    print(f"Sending welcome email to {event.email}")
    await email_service.send(
        to=event.email,
        subject="Welcome!",
        body=f"Hello {event.name}, welcome to our platform!"
    )

@subscribe(UserCreated)
async def create_audit_log(event: UserCreated):
    """Log user creation for audit trail"""
    await audit_service.log(f"User {event.user_id} created at {event.timestamp}")
```

### 3. Publish Events

**Simple Syntax (Recommended)** - Just call `.publish()` on the event:

```python
async def create_user(name: str, email: str):
    # Create user logic...
    user = User(id="123", name=name, email=email)

    # Publish event - Simple and clean!
    event = UserCreated(
        user_id=user.id,
        email=user.email,
        name=user.name
    )
    await event.publish()  # That's it!

    return user
```

**Alternative Syntax** - Using the event bus directly:

```python
from vega.events import get_event_bus

async def create_user(name: str, email: str):
    user = User(id="123", name=name, email=email)

    # Publish via event bus
    bus = get_event_bus()
    await bus.publish(UserCreated(
        user_id=user.id,
        email=user.email,
        name=user.name
    ))

    return user
```

## Advanced Usage

### Priority and Ordering

Control handler execution order with priorities:

```python
@subscribe(UserCreated, priority=100)
async def critical_handler(event: UserCreated):
    """Runs first due to higher priority"""
    pass

@subscribe(UserCreated, priority=0)
async def normal_handler(event: UserCreated):
    """Runs after critical handlers"""
    pass
```

### Retry on Failure

Automatically retry handlers that fail:

```python
@subscribe(UserCreated, retry_on_error=True, max_retries=5)
async def unreliable_handler(event: UserCreated):
    """Will retry up to 5 times on failure"""
    response = await external_api.call()
    if not response.ok:
        raise Exception("API call failed")
```

### Event Inheritance

Handlers for base events automatically receive derived events:

```python
@dataclass(frozen=True)
class UserEvent(Event):
    user_id: str

@dataclass(frozen=True)
class UserCreated(UserEvent):
    email: str

@dataclass(frozen=True)
class UserUpdated(UserEvent):
    changes: dict

# This handler receives ALL UserEvent subtypes
@subscribe(UserEvent)
async def handle_any_user_event(event: UserEvent):
    print(f"User event: {event.event_name}")
```

### Error Handling

Register global error handlers:

```python
from vega.events import get_event_bus

bus = get_event_bus()

@bus.on_error
async def log_event_errors(event, exception, handler_name):
    """Called when any handler fails"""
    logger.error(
        f"Handler '{handler_name}' failed for event '{event.event_name}': {exception}"
    )
    # Send to error tracking service
    await sentry.capture_exception(exception)
```

### Middleware

Add cross-cutting concerns with middleware:

```python
from vega.events import get_event_bus, LoggingEventMiddleware

bus = get_event_bus()

# Built-in logging middleware
bus.add_middleware(LoggingEventMiddleware())

# Custom middleware
from vega.events import EventMiddleware

class TenantContextMiddleware(EventMiddleware):
    async def before_publish(self, event: Event):
        # Add tenant context to all events
        tenant_id = get_current_tenant()
        event.add_metadata('tenant_id', tenant_id)

    async def after_publish(self, event: Event):
        # Cleanup after event is processed
        pass

bus.add_middleware(TenantContextMiddleware())
```

### Metrics Collection

Track event processing with built-in metrics middleware:

```python
from vega.events import get_event_bus
from vega.events.middleware import MetricsEventMiddleware

bus = get_event_bus()
metrics = MetricsEventMiddleware()
bus.add_middleware(metrics)

# Later, get metrics
stats = metrics.get_metrics()
print(stats)
# {
#     'UserCreated': {
#         'count': 150,
#         'avg_duration_ms': 45.2,
#         'min_duration_ms': 12.1,
#         'max_duration_ms': 234.5,
#     }
# }
```

### Validation

Validate events before publishing:

```python
from vega.events.middleware import ValidationEventMiddleware

def validate_user_created(event):
    if not event.email or '@' not in event.email:
        raise ValueError("Invalid email address")
    if not event.user_id:
        raise ValueError("user_id is required")

validation = ValidationEventMiddleware()
validation.add_validator(UserCreated, validate_user_created)

bus.add_middleware(validation)
```

### Event Enrichment

Automatically add metadata to events:

```python
from vega.events.middleware import EnrichmentEventMiddleware

enrichment = EnrichmentEventMiddleware()

# Add correlation ID
enrichment.add_enricher(
    lambda event: event.add_metadata('correlation_id', get_correlation_id())
)

# Add user context
enrichment.add_enricher(
    lambda event: event.add_metadata('triggered_by', get_current_user_id())
)

bus.add_middleware(enrichment)
```

## Integration with Vega Patterns

### In Interactors

```python
from vega.patterns import Interactor
from vega.di import bind
from vega.events import get_event_bus

class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        # Domain logic
        user = User(name=self.name, email=self.email)
        user = await repository.save(user)

        # Publish domain event
        bus = get_event_bus()
        await bus.publish(UserCreated(
            user_id=user.id,
            email=user.email,
            name=user.name
        ))

        return user
```

### In Mediators

```python
from vega.patterns import Mediator
from vega.events import get_event_bus

class UserRegistrationWorkflow(Mediator[User]):
    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = password

    async def call(self) -> User:
        # Create user
        user = await CreateUser(self.name, self.email)

        # Set password
        await SetUserPassword(user.id, self.password)

        # Publish workflow completion event
        bus = get_event_bus()
        await bus.publish(UserRegistrationCompleted(
            user_id=user.id,
            email=user.email
        ))

        return user
```

## Event Naming Conventions

Events should be named in **past tense** to indicate something that happened:

✅ **Good**:
- `UserCreated`
- `OrderPlaced`
- `PaymentProcessed`
- `EmailSent`
- `InventoryUpdated`

❌ **Bad**:
- `CreateUser` (this is a command/action, not an event)
- `PlaceOrder` (command)
- `SendEmail` (command)

## Best Practices

### 1. Keep Events Immutable

Use `@dataclass(frozen=True)` to ensure events cannot be modified:

```python
@dataclass(frozen=True)  # ✅ Immutable
class UserCreated(Event):
    user_id: str
    email: str
```

### 2. Include All Relevant Data

Events should contain all data needed by handlers:

```python
# ✅ Good - includes all relevant data
@dataclass(frozen=True)
class OrderPlaced(Event):
    order_id: str
    customer_id: str
    items: List[OrderItem]
    total_amount: Decimal
    currency: str

# ❌ Bad - handlers need to fetch additional data
@dataclass(frozen=True)
class OrderPlaced(Event):
    order_id: str  # Handlers must fetch order details
```

### 3. One Event Per Domain Action

Create specific events for specific domain actions:

```python
# ✅ Good - specific events
@dataclass(frozen=True)
class UserEmailChanged(Event):
    user_id: str
    old_email: str
    new_email: str

@dataclass(frozen=True)
class UserPasswordChanged(Event):
    user_id: str
    changed_at: datetime

# ❌ Bad - generic event
@dataclass(frozen=True)
class UserUpdated(Event):
    user_id: str
    changes: dict  # Too generic
```

### 4. Handlers Should Be Idempotent

Handlers may be called multiple times (retries), so make them idempotent:

```python
@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    # ✅ Check if email already sent
    if await email_log.has_sent(event.user_id, 'welcome'):
        return

    await email_service.send(event.email, "Welcome!")
    await email_log.record(event.user_id, 'welcome')
```

### 5. Don't Publish Events in Handlers

Avoid publishing events from within event handlers to prevent cascading complexity:

```python
# ❌ Bad - publishing from handler
@subscribe(UserCreated)
async def on_user_created(event: UserCreated):
    bus = get_event_bus()
    await bus.publish(WelcomeEmailSent(...))  # ❌ Cascading events

# ✅ Good - publish from domain logic
class CreateUser(Interactor[User]):
    async def call(self, ...):
        user = await repository.save(user)

        # Publish all related events here
        bus = get_event_bus()
        await bus.publish(UserCreated(...))
        await bus.publish(WelcomeEmailScheduled(...))
```

## Testing

### Testing Event Handlers

```python
import pytest
from vega.events import EventBus, set_event_bus

@pytest.fixture
def event_bus():
    """Create isolated event bus for tests"""
    bus = EventBus()
    set_event_bus(bus)
    yield bus
    # Cleanup
    bus.clear_subscribers()

async def test_user_created_handler(event_bus):
    """Test that welcome email is sent"""
    sent_emails = []

    @event_bus.subscribe(UserCreated)
    async def track_emails(event: UserCreated):
        sent_emails.append(event.email)

    # Publish event
    await event_bus.publish(UserCreated(
        user_id="123",
        email="test@test.com",
        name="Test User"
    ))

    # Assert
    assert "test@test.com" in sent_emails
```

### Mocking Event Bus

```python
from unittest.mock import AsyncMock

async def test_interactor_publishes_event():
    """Test that interactor publishes event"""
    mock_bus = AsyncMock()

    # Inject mock bus
    set_event_bus(mock_bus)

    # Execute interactor
    user = await CreateUser(name="Test", email="test@test.com")

    # Assert event was published
    mock_bus.publish.assert_called_once()
    event = mock_bus.publish.call_args[0][0]
    assert isinstance(event, UserCreated)
    assert event.email == "test@test.com"
```

## API Reference

### Event

Base class for all events.

**Properties**:
- `event_id: str` - Unique identifier (auto-generated UUID)
- `timestamp: datetime` - When event was created (auto-generated)
- `event_name: str` - Event class name
- `metadata: Dict[str, Any]` - Additional metadata

**Methods**:
- `add_metadata(key: str, value: Any)` - Add metadata to event

### EventBus

Central event bus for pub/sub.

**Methods**:
- `subscribe(event_type, handler, priority=0, retry_on_error=False, max_retries=3)` - Subscribe handler
- `unsubscribe(event_type, handler)` - Unsubscribe handler
- `publish(event)` - Publish event to all subscribers
- `publish_many(events)` - Publish multiple events
- `add_middleware(middleware)` - Add middleware
- `on_error(handler)` - Register error handler
- `clear_subscribers(event_type=None)` - Clear subscribers
- `get_subscriber_count(event_type)` - Get subscriber count

### Decorators

**`@subscribe(event_type, priority=0, retry_on_error=False, max_retries=3)`**

Subscribe function to event on global bus.

**`@event_handler(event_type, bus=None, priority=0, retry_on_error=False, max_retries=3)`**

Mark method as event handler with optional custom bus.

### Middleware

**Built-in Middleware**:
- `LoggingEventMiddleware` - Log all events
- `MetricsEventMiddleware` - Collect event metrics
- `ValidationEventMiddleware` - Validate events before publishing
- `EnrichmentEventMiddleware` - Auto-add metadata to events

**Custom Middleware**:

Extend `EventMiddleware` and implement:
- `async def before_publish(event: Event)` - Called before event is published
- `async def after_publish(event: Event)` - Called after handlers complete

## Performance Considerations

- **Async Handlers**: All handlers run concurrently (not sequentially)
- **Error Isolation**: Failed handlers don't block other handlers
- **Retry Overhead**: Use retry sparingly - exponential backoff adds delay
- **Middleware Order**: Middleware runs in order added - keep it lightweight

## Examples

See the [examples directory](../../examples/events/) for complete examples:
- Basic event publishing
- Event handlers with DI
- Middleware usage
- Testing strategies
- Integration with Interactors/Mediators

## License

Part of the Vega Framework - See LICENSE for details.
