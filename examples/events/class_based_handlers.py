"""
Class-Based Event Handlers Example

Demonstrates organizing event handlers into classes with dependencies.
Note: Use @subscribe for standalone functions, not class methods.

For class-based handlers, register them manually after instantiation.
"""
import asyncio
import sys
from dataclasses import dataclass
from vega.events import Event, get_event_bus, subscribe

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Define Events
@dataclass(frozen=True)
class OrderPlaced(Event):
    """Event when an order is placed"""
    order_id: str
    customer_email: str
    total: float

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class PaymentReceived(Event):
    """Event when payment is received"""
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()


# Class-based handlers with dependency injection
class OrderEventHandlers:
    """
    Class to organize all order-related event handlers.

    This approach is useful when handlers need shared dependencies
    or when you want to organize handlers logically.
    """

    def __init__(self, email_service=None, notification_service=None, bus=None):
        """
        Initialize handlers with dependencies.

        In a real app, these would be injected via DI container.
        """
        self.email_service = email_service or "MockEmailService"
        self.notification_service = notification_service or "MockNotificationService"
        self.bus = bus or get_event_bus()

        # Register handlers manually
        self.bus.subscribe(OrderPlaced, self.send_order_confirmation)
        self.bus.subscribe(OrderPlaced, self.notify_warehouse, priority=10)
        self.bus.subscribe(PaymentReceived, self.send_payment_receipt)

    async def send_order_confirmation(self, event: OrderPlaced):
        """Send order confirmation email"""
        print(f"📧 [{self.email_service}] Sending order confirmation to {event.customer_email}")
        print(f"   Order: {event.order_id}, Total: ${event.total}")
        await asyncio.sleep(0.05)
        print(f"   ✅ Confirmation email sent")

    async def notify_warehouse(self, event: OrderPlaced):
        """Notify warehouse about new order (high priority)"""
        print(f"🏭 [{self.notification_service}] Notifying warehouse about order {event.order_id}")
        await asyncio.sleep(0.05)
        print(f"   ✅ Warehouse notified")

    async def send_payment_receipt(self, event: PaymentReceived):
        """Send payment receipt"""
        print(f"💳 [{self.email_service}] Sending payment receipt")
        print(f"   Order: {event.order_id}, Amount: ${event.amount}")
        await asyncio.sleep(0.05)
        print(f"   ✅ Receipt sent")


class AnalyticsEventHandlers:
    """Separate class for analytics-related handlers"""

    def __init__(self, analytics_service=None, bus=None):
        self.analytics_service = analytics_service or "MockAnalyticsService"
        self.bus = bus or get_event_bus()

        # Register handlers manually
        self.bus.subscribe(OrderPlaced, self.track_order)
        self.bus.subscribe(PaymentReceived, self.track_payment)

    async def track_order(self, event: OrderPlaced):
        """Track order in analytics"""
        print(f"📊 [{self.analytics_service}] Tracking order event")
        print(f"   Order: {event.order_id}, Total: ${event.total}")
        await asyncio.sleep(0.05)
        print(f"   ✅ Order tracked")

    async def track_payment(self, event: PaymentReceived):
        """Track payment in analytics"""
        print(f"📊 [{self.analytics_service}] Tracking payment event")
        print(f"   Amount: ${event.amount}")
        await asyncio.sleep(0.05)
        print(f"   ✅ Payment tracked")


async def main():
    """Run the class-based handlers example"""
    print("=" * 70)
    print("🚀 Vega Events - Class-Based Handlers Example")
    print("=" * 70)
    print()

    # Initialize handler classes with dependencies
    print("📦 Initializing event handler classes...")
    order_handlers = OrderEventHandlers(
        email_service="SendgridService",
        notification_service="SlackNotificationService"
    )
    analytics_handlers = AnalyticsEventHandlers(
        analytics_service="MixpanelService"
    )
    print(f"   ✅ OrderEventHandlers initialized")
    print(f"   ✅ AnalyticsEventHandlers initialized")
    print()

    bus = get_event_bus()

    # Show registered handlers
    print("📋 Registered Event Handlers:")
    print(f"   OrderPlaced: {bus.get_subscriber_count(OrderPlaced)} handlers")
    print(f"   PaymentReceived: {bus.get_subscriber_count(PaymentReceived)} handlers")
    print()

    # Example 1: Place an order
    print("=" * 70)
    print("📝 Example 1: Placing an order")
    print("=" * 70)
    print()

    order_event = OrderPlaced(
        order_id="ORD-12345",
        customer_email="customer@example.com",
        total=299.99
    )

    print(f"Publishing: {order_event.event_name}")
    print(f"Event ID: {order_event.event_id}")
    print()

    await bus.publish(order_event)

    print()
    print("✨ Order event processed!")
    print()

    # Example 2: Process payment
    print("=" * 70)
    print("📝 Example 2: Processing payment")
    print("=" * 70)
    print()

    payment_event = PaymentReceived(
        order_id="ORD-12345",
        amount=299.99
    )

    print(f"Publishing: {payment_event.event_name}")
    print(f"Event ID: {payment_event.event_id}")
    print()

    await bus.publish(payment_event)

    print()
    print("✨ Payment event processed!")
    print()

    # Example 3: Multiple orders
    print("=" * 70)
    print("📝 Example 3: Processing multiple orders")
    print("=" * 70)
    print()

    orders = [
        OrderPlaced(f"ORD-{i:05d}", f"customer{i}@example.com", 100 + (i * 50))
        for i in range(1, 4)
    ]

    for order in orders:
        print(f"Publishing order {order.order_id}...")
    print()

    await bus.publish_many(orders)

    print()
    print("✨ All orders processed!")
    print()

    print("=" * 70)
    print("✅ Class-based handlers example completed!")
    print("=" * 70)
    print()
    print("💡 Key Benefits:")
    print("   - Organize related handlers into classes")
    print("   - Share dependencies across handlers")
    print("   - Better testability (can mock dependencies)")
    print("   - Cleaner code organization")
    print()


if __name__ == "__main__":
    asyncio.run(main())
