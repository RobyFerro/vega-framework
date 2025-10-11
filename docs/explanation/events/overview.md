# Vega Events Concepts

Use this guide to understand the principles and architectural decisions behind Vega's event-driven subsystem.

## Features

- **Event Bus** - Publish/subscribe pattern for domain events
- **Async Support** - Full async/await support for event handlers
- **Auto-Publish** - Ultra-clean syntax with metaclass-powered instant publishing (enabled by default!)
- **Auto-Discovery** - Automatically discover and register event handlers from your package
- **@trigger Decorator** - Automatically trigger events after Interactor completion
- **Priority Ordering** - Control handler execution order
- **Retry Logic** - Automatic retries for failed handlers
- **Middleware** - Cross-cutting concerns (logging, metrics, validation)
- **Event Inheritance** - Handlers for base events receive derived events
- **Type-Safe** - Full type hints support

## Auto-Discovery

Vega Events provides automatic discovery and registration of event handlers from your package.

### Basic Auto-Discovery

```python
from vega.discovery import discover_event_handlers

# In your application startup (e.g., main.py or __init__.py)
def setup_events():
    """Automatically discover and register all event handlers"""
    # Discovers handlers in 'myproject.events' package
    discover_event_handlers("myproject")
```

### Custom Configuration

```python
from vega.discovery import discover_event_handlers

def setup_events():
    """Discover handlers from custom location"""
    # Specify custom events subpackage
    discover_event_handlers(
        base_package="myproject",
        events_subpackage="application.events"
    )
```

### Project Structure

```
myproject/
├── events/
│   ├── __init__.py
│   ├── user_handlers.py    # @subscribe(UserCreated)
│   ├── order_handlers.py   # @subscribe(OrderPlaced)
│   └── payment_handlers.py # @subscribe(PaymentProcessed)
└── main.py
```

```python
# main.py
from vega.discovery import discover_event_handlers

def main():
    # This will import all modules in myproject/events/
    # and trigger @subscribe decorator registration
    discover_event_handlers("myproject")

    # Now all handlers are registered and ready!
    # You can start publishing events
```

### How It Works

1. `discover_event_handlers()` scans the events directory for Python modules
2. Imports each module (except `__init__.py`)
3. The `@subscribe()` decorators in those modules automatically register handlers
4. All handlers are now subscribed to the global event bus

### Benefits

- No manual imports required
- Automatic handler registration
- Clean separation of concerns
- Easy to add new handlers (just create a new file)

## @trigger Decorator

The `@trigger` decorator automatically publishes events after an Interactor completes, providing seamless integration between use cases and domain events.

### Basic Usage

```python
from vega.patterns import Interactor
from vega.events import Event, trigger
from vega.di import bind
from dataclasses import dataclass

@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()

@trigger(UserCreated)  # Automatically trigger event after completion
class CreateUser(Interactor[dict]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> dict:
        user = await repository.create(name=self.name, email=self.email)

        # Return dict that matches UserCreated constructor
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name
        }

# Usage
result = await CreateUser(name="John", email="john@test.com")
# After call() completes:
# 1. Returns result to caller
# 2. Automatically publishes UserCreated event with result as input
# 3. All @subscribe(UserCreated) handlers are triggered
```

### How It Works

1. Interactor executes and returns a result
2. The `@trigger` decorator intercepts the result
3. Creates an event instance using the result:
   - If result is a `dict`: `event(**result)`
   - If result is an object: `event(result)`
4. Publishes the event automatically (using auto-publish)
5. All subscribed handlers receive the event

### Workflow Integration

Perfect for domain events that should always be triggered after a use case:

```python
@dataclass(frozen=True)
class OrderPlaced(Event):
    order_id: str
    customer_id: str
    total_amount: float

    def __post_init__(self):
        super().__init__()

@trigger(OrderPlaced)
class PlaceOrder(Interactor[dict]):
    def __init__(self, customer_id: str, items: list):
        self.customer_id = customer_id
        self.items = items

    @bind
    async def call(self, repository: OrderRepository) -> dict:
        order = await repository.create_order(
            customer_id=self.customer_id,
            items=self.items
        )

        return {
            "order_id": order.id,
            "customer_id": order.customer_id,
            "total_amount": order.total_amount
        }

# Handlers automatically receive the event
@subscribe(OrderPlaced)
async def send_order_confirmation(event: OrderPlaced):
    await email_service.send_confirmation(event.customer_id, event.order_id)

@subscribe(OrderPlaced)
async def update_inventory(event: OrderPlaced):
    await inventory_service.reserve_items(event.order_id)

# Execute - handlers run automatically!
result = await PlaceOrder(customer_id="123", items=[...])
```

### Benefits

- Clean separation between business logic and events
- No manual event publishing in Interactor code
- Consistent pattern across use cases
- Works seamlessly with auto-publish

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

### Middlewareso

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

**Option 1: Using @trigger decorator (Recommended)**

```python
from vega.patterns import Interactor
from vega.di import bind
from vega.events import trigger

@trigger(UserCreated)  # Automatically publishes event after completion
class CreateUser(Interactor[dict]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> dict:
        # Domain logic
        user = User(name=self.name, email=self.email)
        user = await repository.save(user)

        # Return data for event - auto-published by @trigger!
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name
        }
```

**Option 2: Manual publishing (when you need more control)**

```python
from vega.patterns import Interactor
from vega.di import bind

class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        # Domain logic
        user = User(name=self.name, email=self.email)
        user = await repository.save(user)

        # Publish domain event (auto-publish enabled by default)
        await UserCreated(
            user_id=user.id,
            email=user.email,
            name=user.name
        )

        return user
```

### In Mediators

```python
from vega.patterns import Mediator

class UserRegistrationWorkflow(Mediator[User]):
    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = password

    async def call(self) -> User:
        # Create user (auto-publishes UserCreated via @trigger)
        user = await CreateUser(self.name, self.email)

        # Set password
        await SetUserPassword(user.id, self.password)

        # Publish workflow completion event (auto-publish is default)
        await UserRegistrationCompleted(
            user_id=user.id,
            email=user.email
        )

        return user
```

## Event Naming Conventions

Events should be named in **past tense** to indicate something that happened:

- **Good**:
- `UserCreated`
- `OrderPlaced`
- `PaymentProcessed`
- `EmailSent`
- `InventoryUpdated`

x **Bad**:

- `CreateUser` (this is a command/action, not an event)
- `PlaceOrder` (command)
- `SendEmail` (command)

## Best Practices

### 1. Keep Events Immutable

Use `@dataclass(frozen=True)` to ensure events cannot be modified:

```python
@dataclass(frozen=True)  # - Immutable
class UserCreated(Event):
    user_id: str
    email: str
```

### 2. Include All Relevant Data

Events should contain all data needed by handlers:

```python
# - Good - includes all relevant data
@dataclass(frozen=True)
class OrderPlaced(Event):
    order_id: str
    customer_id: str
    items: List[OrderItem]
    total_amount: Decimal
    currency: str

# x Bad - handlers need to fetch additional data
@dataclass(frozen=True)
class OrderPlaced(Event):
    order_id: str  # Handlers must fetch order details
```

### 3. One Event Per Domain Action

Create specific events for specific domain actions:

```python
# - Good - specific events
@dataclass(frozen=True)
class UserEmailChanged(Event):
    user_id: str
    old_email: str
    new_email: str

@dataclass(frozen=True)
class UserPasswordChanged(Event):
    user_id: str
    changed_at: datetime

# x Bad - generic event
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
    # - Check if email already sent
    if await email_log.has_sent(event.user_id, 'welcome'):
        return

    await email_service.send(event.email, "Welcome!")
    await email_log.record(event.user_id, 'welcome')
```

### 5. Don't Publish Events in Handlers

Avoid publishing events from within event handlers to prevent cascading complexity:

```python
# x Bad - publishing from handler
@subscribe(UserCreated)
async def on_user_created(event: UserCreated):
    await WelcomeEmailSent(...)  # x Cascading events

# - Good - publish from domain logic
class CreateUser(Interactor[User]):
    async def call(self, ...):
        user = await repository.save(user)

        # Publish all related events here (auto-publish is default)
        await UserCreated(...)
        await WelcomeEmailScheduled(...)
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

## Related Resources

- Follow the tutorial in ../../tutorials/events/getting-started.md
- Apply publishing patterns from ../../how-to/events/publish-events.md
- Consult the API reference at ../../reference/events/api.md
