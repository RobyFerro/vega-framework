"""
Event Middleware Example

This example demonstrates event middleware for cross-cutting concerns:
- Logging middleware
- Metrics collection
- Validation
- Event enrichment
"""
import asyncio
import sys
from dataclasses import dataclass
from vega.events import Event, EventBus
from vega.events.middleware import (
    LoggingEventMiddleware,
    MetricsEventMiddleware,
    ValidationEventMiddleware,
    EnrichmentEventMiddleware
)

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Define Events
@dataclass(frozen=True)
class OrderPlaced(Event):
    """Event published when an order is placed"""
    order_id: str
    customer_id: str
    total_amount: float

    def __post_init__(self):
        super().__init__()


@dataclass(frozen=True)
class PaymentProcessed(Event):
    """Event published when payment is processed"""
    payment_id: str
    order_id: str
    amount: float

    def __post_init__(self):
        super().__init__()


async def main():
    """Run the middleware example"""
    print("=" * 70)
    print("🚀 Vega Events - Middleware Example")
    print("=" * 70)
    print()

    # Create event bus
    bus = EventBus()

    # 1. Add Logging Middleware
    print("📝 Adding LoggingEventMiddleware...")
    bus.add_middleware(LoggingEventMiddleware())
    print()

    # 2. Add Metrics Middleware
    print("📊 Adding MetricsEventMiddleware...")
    metrics_middleware = MetricsEventMiddleware()
    bus.add_middleware(metrics_middleware)
    print()

    # 3. Add Validation Middleware
    print("✅ Adding ValidationEventMiddleware...")
    validation_middleware = ValidationEventMiddleware()

    # Add validators
    def validate_order(event):
        if event.total_amount <= 0:
            raise ValueError(f"Invalid order amount: {event.total_amount}")
        if not event.order_id:
            raise ValueError("Order ID is required")

    def validate_payment(event):
        if event.amount <= 0:
            raise ValueError(f"Invalid payment amount: {event.amount}")

    validation_middleware.add_validator(OrderPlaced, validate_order)
    validation_middleware.add_validator(PaymentProcessed, validate_payment)
    bus.add_middleware(validation_middleware)
    print()

    # 4. Add Enrichment Middleware
    print("🎨 Adding EnrichmentEventMiddleware...")
    enrichment_middleware = EnrichmentEventMiddleware()

    # Add correlation ID to all events
    correlation_counter = 0

    def add_correlation_id(event):
        nonlocal correlation_counter
        correlation_counter += 1
        event.add_metadata('correlation_id', f"corr-{correlation_counter}")
        event.add_metadata('environment', 'production')

    enrichment_middleware.add_enricher(add_correlation_id)
    bus.add_middleware(enrichment_middleware)
    print()

    # Register event handlers
    @bus.subscribe(OrderPlaced)
    async def process_order(event: OrderPlaced):
        print(f"  💰 Processing order {event.order_id} (${event.total_amount})")
        print(f"     Correlation ID: {event.metadata.get('correlation_id')}")
        await asyncio.sleep(0.1)

    @bus.subscribe(PaymentProcessed)
    async def send_payment_confirmation(event: PaymentProcessed):
        print(f"  💳 Payment {event.payment_id} processed (${event.amount})")
        print(f"     Correlation ID: {event.metadata.get('correlation_id')}")
        await asyncio.sleep(0.05)

    # Publish events
    print("=" * 70)
    print("📢 Publishing Events")
    print("=" * 70)
    print()

    # Valid order
    print("1️⃣ Publishing valid order...")
    print()
    await bus.publish(OrderPlaced(
        order_id="ORD-001",
        customer_id="CUST-123",
        total_amount=99.99
    ))
    print()

    # Multiple valid payments
    print("2️⃣ Publishing multiple payments...")
    print()
    for i in range(3):
        await bus.publish(PaymentProcessed(
            payment_id=f"PAY-{i:03d}",
            order_id=f"ORD-{i:03d}",
            amount=50.0 + (i * 25)
        ))
    print()

    # Try invalid order (will fail validation)
    print("3️⃣ Attempting to publish invalid order (should fail)...")
    print()
    try:
        await bus.publish(OrderPlaced(
            order_id="ORD-INVALID",
            customer_id="CUST-456",
            total_amount=-10.0  # Invalid amount!
        ))
    except ValueError as e:
        print(f"  ❌ Validation failed (as expected): {e}")
    print()

    # Display metrics
    print("=" * 70)
    print("📊 Event Metrics")
    print("=" * 70)
    metrics = metrics_middleware.get_metrics()

    for event_name, stats in metrics.items():
        print(f"\n{event_name}:")
        print(f"  Count: {stats['count']}")
        print(f"  Avg Duration: {stats['avg_duration_ms']:.2f}ms")
        print(f"  Min Duration: {stats['min_duration_ms']:.2f}ms")
        print(f"  Max Duration: {stats['max_duration_ms']:.2f}ms")

    print()
    print("=" * 70)
    print("✅ Middleware example completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
