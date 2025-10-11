"""
Auto-Publish Example

This example demonstrates the auto-publish feature using metaclass.
Auto-publish is ENABLED BY DEFAULT - just like Interactors!

This is the CLEANEST syntax possible out of the box!
"""
import asyncio
import sys
from dataclasses import dataclass
from vega.events import Event, subscribe

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Example 1: Auto-publish (ENABLED BY DEFAULT!)
@dataclass(frozen=True)
class OrderPlaced(Event):  # Auto-publish is the default!
    """Order placed event - auto-publishes when created (default behavior)"""
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()


# Example 2: More auto-publish events (still using defaults!)
@dataclass(frozen=True)
class PaymentReceived(Event):  # No need for auto_publish=True - it's the default!
    """Payment event - auto-publishes when created!"""
    payment_id: str
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class OrderShipped(Event):  # Auto-publish is default!
    """Shipping event - auto-publishes when created!"""
    order_id: str
    tracking_number: str

    def __post_init__(self):
        super().__init__()


# Example 3: Manual publish - DISABLE auto-publish when you need control
@dataclass(frozen=True)
class RefundProcessed(Event, auto_publish=False):  # ← Explicitly disable auto-publish
    """Refund event - requires manual .publish() because auto_publish=False"""
    refund_id: str
    order_id: str
    amount: float

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


@subscribe(RefundProcessed)
async def process_refund(event: RefundProcessed):
    """Process refund"""
    print(f"💸 Processing refund {event.refund_id} for order {event.order_id}")
    await asyncio.sleep(0.05)
    print(f"   ✅ Refund processed: ${event.amount}")


async def main():
    """Run the auto-publish example"""
    print("=" * 80)
    print("🚀 Vega Events - Auto-Publish Example")
    print("=" * 80)
    print()
    print("⭐ AUTO-PUBLISH IS ENABLED BY DEFAULT - just like Interactors!")
    print()

    # Example 1: Auto-publish (default behavior!)
    print("📝 Example 1: Auto-Publish (ENABLED BY DEFAULT)")
    print("-" * 80)
    print()
    print("Code:")
    print("  class OrderPlaced(Event):  # Auto-publish is default!")
    print("      ...")
    print()
    print("  # Just await the constructor - that's it!")
    print("  await OrderPlaced(order_id='ORD-001', amount=99.99)")
    print()

    # Auto-publishes automatically!
    await OrderPlaced(order_id="ORD-001", amount=99.99)

    print()

    # Example 2: More auto-publish events
    print("📝 Example 2: Multiple Auto-Publish Events (Default Behavior)")
    print("-" * 80)
    print()

    # All auto-publish by default!
    await PaymentReceived(
        payment_id="PAY-001",
        order_id="ORD-001",
        amount=99.99
    )

    await OrderShipped(
        order_id="ORD-001",
        tracking_number="TRACK-12345"
    )

    print()

    # Example 3: Manual publish (when you need control)
    print("📝 Example 3: Manual Publish (auto_publish=False)")
    print("-" * 80)
    print()
    print("Code:")
    print("  class RefundProcessed(Event, auto_publish=False):  # Disable!")
    print("      ...")
    print()
    print("  event = RefundProcessed(...)")
    print("  event.add_metadata('reason', 'customer_request')")
    print("  await event.publish()  # Manual publish")
    print()

    # Manual publish - requires auto_publish=False
    event = RefundProcessed(
        refund_id="REF-001",
        order_id="ORD-001",
        amount=99.99
    )
    event.add_metadata('reason', 'customer_request')
    event.add_metadata('processed_by', 'admin')
    await event.publish()

    print()

    # Example 4: In a workflow (all auto-publish by default!)
    print("📝 Example 4: In a Workflow (all auto-publish by default!)")
    print("-" * 80)
    print()
    print("Code:")
    print("  async def process_order_workflow(order_id, amount):")
    print("      # All events auto-publish - ultra-clean!")
    print("      await OrderPlaced(order_id=order_id, amount=amount)")
    print("      await PaymentReceived(...)")
    print("      await OrderShipped(...)")
    print()

    async def process_order_workflow(order_id, amount):
        """Complete order workflow - all auto-publish!"""
        # All events auto-publish by default!
        await OrderPlaced(order_id=order_id, amount=amount)
        await PaymentReceived(
            payment_id="PAY-002",
            order_id=order_id,
            amount=amount
        )
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

    print("🌟 Auto-publish (DEFAULT - recommended!):")
    print("   class UserCreated(Event):  # Auto-publish is default!")
    print("       ...")
    print()
    print("   await UserCreated(user_id='123', email='test@test.com')")
    print()

    print("✅ Manual publish (when you need control):")
    print("   class UserCreated(Event, auto_publish=False):  # Disable")
    print("       ...")
    print()
    print("   event = UserCreated(...)")
    print("   event.add_metadata('source', 'api')")
    print("   await event.publish()")
    print()

    print("❌ Verbose syntax (avoid):")
    print("   bus = get_event_bus()")
    print("   await bus.publish(event)")
    print()

    print("=" * 80)
    print("💡 When to Use Each:")
    print("-" * 80)
    print()
    print("Auto-publish (default) - 95% of cases:")
    print("  ✅ Ultra-clean syntax - just await Event(...)")
    print("  ✅ Consistent with Interactor pattern")
    print("  ✅ No configuration needed")
    print()
    print("Manual publish (auto_publish=False) - rare cases:")
    print("  ⚠️ When you need to inspect/modify event before publishing")
    print("  ⚠️ When publishing conditionally")
    print("  ⚠️ When you need the event instance")
    print()

    print("=" * 80)
    print("✅ Auto-publish example completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
