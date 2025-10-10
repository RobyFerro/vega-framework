"""
Simple Syntax Example

This example demonstrates the simplified syntax for publishing events.
No need to import get_event_bus() - just call event.publish()!
"""
import asyncio
import sys
from dataclasses import dataclass
from vega.events import Event, subscribe

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Define Events
@dataclass(frozen=True)
class UserRegistered(Event):
    """User registration event"""
    user_id: str
    email: str
    full_name: str

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class EmailVerified(Event):
    """Email verification event"""
    user_id: str
    email: str

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class ProfileCompleted(Event):
    """Profile completion event"""
    user_id: str
    completion_percentage: int

    def __post_init__(self):
        super().__init__()


# Event Handlers
@subscribe(UserRegistered)
async def send_welcome_email(event: UserRegistered):
    """Send welcome email to new user"""
    print(f"📧 Sending welcome email to {event.email}")
    await asyncio.sleep(0.05)
    print(f"   ✅ Welcome email sent to {event.full_name}")


@subscribe(UserRegistered)
async def create_user_profile(event: UserRegistered):
    """Create initial user profile"""
    print(f"👤 Creating profile for {event.full_name}")
    await asyncio.sleep(0.05)
    print(f"   ✅ Profile created for user {event.user_id}")


@subscribe(EmailVerified)
async def unlock_features(event: EmailVerified):
    """Unlock premium features after email verification"""
    print(f"🔓 Unlocking features for {event.email}")
    await asyncio.sleep(0.05)
    print(f"   ✅ Premium features unlocked")


@subscribe(ProfileCompleted)
async def award_completion_badge(event: ProfileCompleted):
    """Award badge for completing profile"""
    print(f"🏆 Awarding badge (profile {event.completion_percentage}% complete)")
    await asyncio.sleep(0.05)
    print(f"   ✅ Badge awarded to user {event.user_id}")


async def main():
    """Run the simple syntax example"""
    print("=" * 70)
    print("🚀 Vega Events - Simple Syntax Example")
    print("=" * 70)
    print()
    print("💡 No need to import get_event_bus() - just call event.publish()!")
    print()

    # Simulate user registration workflow
    print("📝 Simulating User Registration Workflow")
    print("-" * 70)
    print()

    # Step 1: User registers
    print("1️⃣  User registers...")
    registration_event = UserRegistered(
        user_id="usr_12345",
        email="john.doe@example.com",
        full_name="John Doe"
    )
    # Simple syntax - just call .publish()!
    await registration_event.publish()
    print()

    # Step 2: User verifies email
    print("2️⃣  User verifies email...")
    verification_event = EmailVerified(
        user_id="usr_12345",
        email="john.doe@example.com"
    )
    # No need for get_event_bus() - direct publish!
    await verification_event.publish()
    print()

    # Step 3: User completes profile
    print("3️⃣  User completes profile...")
    completion_event = ProfileCompleted(
        user_id="usr_12345",
        completion_percentage=100
    )
    # Clean and simple!
    await completion_event.publish()
    print()

    print("=" * 70)
    print("✅ Registration workflow completed!")
    print("=" * 70)
    print()

    # Compare old vs new syntax
    print("📊 Syntax Comparison:")
    print("-" * 70)
    print()
    print("❌ Old syntax (verbose):")
    print("   from vega.events import get_event_bus")
    print("   bus = get_event_bus()")
    print("   event = UserRegistered(...)")
    print("   await bus.publish(event)")
    print()
    print("✅ New syntax (clean):")
    print("   from vega.events import Event")
    print("   event = UserRegistered(...)")
    print("   await event.publish()  # That's it!")
    print()

    print("=" * 70)
    print("💡 Benefits:")
    print("   - Less imports needed")
    print("   - Cleaner code")
    print("   - More intuitive API")
    print("   - Same functionality")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
