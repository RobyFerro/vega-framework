"""
Test Default Auto-Publish

This demonstrates that ALL events auto-publish by default!
No need for auto_publish=True anymore - it's the default behavior!
"""
import asyncio
import sys
from dataclasses import dataclass
from vega.events import Event, subscribe

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Define events WITHOUT auto_publish parameter - it's default now!
@dataclass(frozen=True)
class UserCreated(Event):
    """User created event - auto-publishes by default!"""
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class OrderPlaced(Event):
    """Order placed event - auto-publishes by default!"""
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class EmailSent(Event):
    """Email sent event - auto-publishes by default!"""
    recipient: str
    subject: str

    def __post_init__(self):
        super().__init__()


# Event Handlers
@subscribe(UserCreated)
async def welcome_user(event: UserCreated):
    """Welcome new user"""
    print(f"👋 Welcome {event.name}!")
    print(f"   Email: {event.email}")
    print(f"   User ID: {event.user_id}")


@subscribe(OrderPlaced)
async def process_order(event: OrderPlaced):
    """Process order"""
    print(f"📦 Processing order {event.order_id}")
    print(f"   Amount: ${event.amount}")


@subscribe(EmailSent)
async def log_email(event: EmailSent):
    """Log email"""
    print(f"📧 Email sent to {event.recipient}")
    print(f"   Subject: {event.subject}")


async def main():
    """Test default auto-publish behavior"""
    print("=" * 80)
    print("🚀 Testing Default Auto-Publish Behavior")
    print("=" * 80)
    print()
    print("All events auto-publish by default - just like Interactors!")
    print()
    print("-" * 80)
    print()

    # Just await the event constructor - that's it!
    print("Code: await UserCreated(user_id='123', email='john@test.com', name='John')")
    print()
    await UserCreated(
        user_id="123",
        email="john@test.com",
        name="John"
    )

    print()
    print("-" * 80)
    print()

    print("Code: await OrderPlaced(order_id='ORD-001', amount=99.99)")
    print()
    await OrderPlaced(
        order_id="ORD-001",
        amount=99.99
    )

    print()
    print("-" * 80)
    print()

    print("Code: await EmailSent(recipient='john@test.com', subject='Welcome!')")
    print()
    await EmailSent(
        recipient="john@test.com",
        subject="Welcome!"
    )

    print()
    print("=" * 80)
    print("✅ All events auto-published successfully!")
    print("=" * 80)
    print()
    print("💡 This is the default behavior - no need for auto_publish=True!")
    print("   If you need to disable it (rare), use: Event, auto_publish=False")
    print()


if __name__ == "__main__":
    asyncio.run(main())
