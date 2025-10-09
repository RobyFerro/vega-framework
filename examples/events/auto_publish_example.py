"""
Auto-Publish Example

This example demonstrates the auto-publish feature using metaclass.
With auto_publish=True, events are automatically published when instantiated!

This is the CLEANEST syntax possible - just like Interactors!
"""
import asyncio
import sys
from dataclasses import dataclass
from vega.events import Event, subscribe

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Example 1: Manual publish (default)
@dataclass(frozen=True)
class OrderPlaced(Event):
    """Order placed event - requires manual .publish()"""
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()


# Example 2: Auto-publish enabled (ultra-clean!)
@dataclass(frozen=True)
class PaymentReceived(Event, auto_publish=True):
    """Payment event - auto-publishes when created!"""
    payment_id: str
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class OrderShipped(Event, auto_publish=True):
    """Shipping event - auto-publishes when created!"""
    order_id: str
    tracking_number: str

    def __post_init__(self):
        super().__init__()


# Event Handlers
@subscribe(OrderPlaced)
async def process_order(event: OrderPlaced):
    """Process order when placed"""
    print(f"📦 Processing order {event.order_id} (${event.amount})")
    await asyncio.sleep(0.05)
    print(f"   ✅ Order processed")


@subscribe(PaymentReceived)
async def confirm_payment(event: PaymentReceived):
    """Confirm payment received"""
    print(f"💳 Payment received: {event.payment_id}")
    print(f"   Order: {event.order_id}, Amount: ${event.amount}")
    await asyncio.sleep(0.05)
    print(f"   ✅ Payment confirmed")


@subscribe(OrderShipped)
async def send_tracking_email(event: OrderShipped):
    """Send tracking information"""
    print(f"📧 Sending tracking email for order {event.order_id}")
    print(f"   Tracking: {event.tracking_number}")
    await asyncio.sleep(0.05)
    print(f"   ✅ Tracking email sent")


async def main():
    """Run the auto-publish example"""
    print("=" * 80)
    print("🚀 Vega Events - Auto-Publish Example")
    print("=" * 80)
    print()
    print("This demonstrates the CLEANEST syntax possible - like Interactors!")
    print()

    # Example 1: Manual publish (traditional way)
    print("📝 Example 1: Manual Publish (default behavior)")
    print("-" * 80)
    print()
    print("Code:")
    print("  event = OrderPlaced(order_id='ORD-001', amount=99.99)")
    print("  await event.publish()")
    print()

    event = OrderPlaced(order_id="ORD-001", amount=99.99)
    await event.publish()

    print()

    # Example 2: Auto-publish (ultra-clean!)
    print("📝 Example 2: Auto-Publish (enabled with auto_publish=True)")
    print("-" * 80)
    print()
    print("Code:")
    print("  @dataclass(frozen=True)")
    print("  class PaymentReceived(Event, auto_publish=True):")
    print("      ...")
    print()
    print("  # Just await the constructor - that's it!")
    print("  await PaymentReceived(payment_id='PAY-001', order_id='ORD-001', amount=99.99)")
    print()

    # Auto-publish in action!
    await PaymentReceived(
        payment_id="PAY-001",
        order_id="ORD-001",
        amount=99.99
    )

    print()

    # Example 3: Multiple auto-publish events
    print("📝 Example 3: Multiple Auto-Publish Events")
    print("-" * 80)
    print()

    await OrderShipped(
        order_id="ORD-001",
        tracking_number="TRACK-12345"
    )

    print()

    # Example 4: In a workflow (like Interactors)
    print("📝 Example 4: In a Workflow (similar to Interactors)")
    print("-" * 80)
    print()
    print("Code:")
    print("  async def process_order_workflow(order_id, amount):")
    print("      # Step 1: Place order")
    print("      order = OrderPlaced(order_id=order_id, amount=amount)")
    print("      await order.publish()")
    print()
    print("      # Step 2: Process payment (auto-publish)")
    print("      await PaymentReceived(")
    print("          payment_id='PAY-002',")
    print("          order_id=order_id,")
    print("          amount=amount")
    print("      )")
    print()
    print("      # Step 3: Ship order (auto-publish)")
    print("      await OrderShipped(")
    print("          order_id=order_id,")
    print("          tracking_number='TRACK-67890'")
    print("      )")
    print()

    async def process_order_workflow(order_id, amount):
        """Complete order workflow with mixed publish styles"""
        # Manual publish
        order = OrderPlaced(order_id=order_id, amount=amount)
        await order.publish()

        # Auto-publish
        await PaymentReceived(
            payment_id="PAY-002",
            order_id=order_id,
            amount=amount
        )

        # Auto-publish
        await OrderShipped(
            order_id=order_id,
            tracking_number="TRACK-67890"
        )

    await process_order_workflow("ORD-002", 149.99)

    print()

    # Syntax comparison
    print("=" * 80)
    print("📊 Syntax Comparison")
    print("=" * 80)
    print()

    print("❌ Old verbose syntax:")
    print("   from vega.events import get_event_bus")
    print("   bus = get_event_bus()")
    print("   event = UserCreated(...)")
    print("   await bus.publish(event)")
    print()

    print("✅ Simple syntax:")
    print("   event = UserCreated(...)")
    print("   await event.publish()")
    print()

    print("🌟 Ultra-clean syntax (auto-publish):")
    print("   class UserCreated(Event, auto_publish=True):")
    print("       ...")
    print()
    print("   await UserCreated(user_id='123', email='test@test.com')")
    print()

    print("=" * 80)
    print("💡 When to Use Each:")
    print("-" * 80)
    print()
    print("Manual publish (.publish()):")
    print("  - When you need to inspect/modify event before publishing")
    print("  - When publishing conditionally")
    print("  - Default, safe choice")
    print()
    print("Auto-publish (auto_publish=True):")
    print("  - In workflows where event should ALWAYS be published")
    print("  - For fire-and-forget events")
    print("  - Cleanest syntax - like Interactors!")
    print()

    print("=" * 80)
    print("✅ Auto-publish example completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
