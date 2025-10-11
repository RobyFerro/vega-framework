# Tutorial: Getting Started with Vega Events

This tutorial walks through the essential workflow for working with Vega's event system: defining events, subscribing handlers, and publishing domain notifications.

## Prerequisites
- Python 3.10+ with async/await experience
- Vega Framework installed (see ../../how-to/install.md)
- Familiarity with dataclasses

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

**Auto-Publish Syntax (Default - Recommended)** - Events publish themselves automatically:

```python
async def create_user(name: str, email: str):
    # Create user logic...
    user = User(id="123", name=name, email=email)

    # Publish event - Ultra-clean syntax!
    # The event is automatically published when instantiated!
    await UserCreated(
        user_id=user.id,
        email=user.email,
        name=user.name
    )

    return user
```

**Manual Publish Syntax** - When you need to inspect/modify the event first:

```python
async def create_user(name: str, email: str):
    user = User(id="123", name=name, email=email)

    # Disable auto-publish for this event class
    @dataclass(frozen=True)
    class UserCreated(Event, auto_publish=False):  # Disable auto-publish
        user_id: str
        email: str
        name: str

        def __post_init__(self):
            super().__init__()

    # Create event
    event = UserCreated(
        user_id=user.id,
        email=user.email,
        name=user.name
    )

    # Add metadata or inspect before publishing
    event.add_metadata('source', 'api')

    # Manually publish
    await event.publish()

    return user
```

**Note**: Auto-publish is enabled by default. Only use `auto_publish=False` when you need to inspect or modify the event before publishing.

## Next Steps
- Follow publishing patterns in ../../how-to/events/publish-events.md
- Deep dive into concepts in ../../explanation/events/overview.md
- Review APIs in ../../reference/events/api.md
