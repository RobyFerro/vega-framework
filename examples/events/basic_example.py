"""
Basic Event Bus Example

This example demonstrates the core functionality of the Vega Events system:
- Defining events
- Subscribing to events
- Publishing events
- Multiple handlers for same event
"""
import asyncio
import sys
from dataclasses import dataclass
from vega.events import Event, get_event_bus, subscribe

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# 1. Define Events
@dataclass(frozen=True)
class UserCreated(Event):
    """Event published when a new user is created"""
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class UserDeleted(Event):
    """Event published when a user is deleted"""
    user_id: str
    deleted_by: str

    def __post_init__(self):
        super().__init__()


# 2. Define Event Handlers
@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    """Send welcome email to new user"""
    print(f"📧 Sending welcome email to {event.email}")
    await asyncio.sleep(0.1)  # Simulate email sending
    print(f"✅ Welcome email sent to {event.name}")


@subscribe(UserCreated, priority=10)
async def create_user_profile(event: UserCreated):
    """Create user profile (runs first due to priority)"""
    print(f"👤 Creating user profile for {event.name}")
    await asyncio.sleep(0.05)
    print(f"✅ Profile created for user {event.user_id}")


@subscribe(UserCreated)
async def add_to_mailing_list(event: UserCreated):
    """Add user to mailing list"""
    print(f"📬 Adding {event.email} to mailing list")
    await asyncio.sleep(0.05)
    print(f"✅ Added to mailing list")


@subscribe(UserDeleted)
async def cleanup_user_data(event: UserDeleted):
    """Cleanup user data on deletion"""
    print(f"🗑️  Cleaning up data for user {event.user_id}")
    await asyncio.sleep(0.1)
    print(f"✅ User data cleaned up")


@subscribe(UserDeleted)
async def send_deletion_notification(event: UserDeleted):
    """Send notification about user deletion"""
    print(f"📧 Sending deletion notification (deleted by {event.deleted_by})")
    await asyncio.sleep(0.05)
    print(f"✅ Notification sent")


# 3. Main Application
async def main():
    """Run the example"""
    print("=" * 60)
    print("🚀 Vega Events - Basic Example")
    print("=" * 60)
    print()

    bus = get_event_bus()

    # Example 1: Create a user
    print("📝 Example 1: Creating a new user")
    print("-" * 60)

    user_created = UserCreated(
        user_id="user-123",
        email="john.doe@example.com",
        name="John Doe"
    )

    print(f"Publishing event: {user_created.event_name}")
    print(f"Event ID: {user_created.event_id}")
    print(f"Timestamp: {user_created.timestamp}")
    print()

    await bus.publish(user_created)

    print()
    print("✨ All UserCreated handlers completed!")
    print()

    # Example 2: Delete a user
    print("📝 Example 2: Deleting a user")
    print("-" * 60)

    user_deleted = UserDeleted(
        user_id="user-123",
        deleted_by="admin"
    )

    print(f"Publishing event: {user_deleted.event_name}")
    print()

    await bus.publish(user_deleted)

    print()
    print("✨ All UserDeleted handlers completed!")
    print()

    # Example 3: Multiple events
    print("📝 Example 3: Publishing multiple events")
    print("-" * 60)

    events = [
        UserCreated(
            user_id=f"user-{i}",
            email=f"user{i}@example.com",
            name=f"User {i}"
        )
        for i in range(1, 4)
    ]

    for event in events:
        print(f"Publishing: {event.name} ({event.email})")

    await bus.publish_many(events)

    print()
    print("✨ All events published!")
    print()

    # Show statistics
    print("📊 Event Bus Statistics")
    print("-" * 60)
    print(f"UserCreated subscribers: {bus.get_subscriber_count(UserCreated)}")
    print(f"UserDeleted subscribers: {bus.get_subscriber_count(UserDeleted)}")
    print()

    print("=" * 60)
    print("✅ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
