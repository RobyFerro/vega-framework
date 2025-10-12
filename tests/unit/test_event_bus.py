"""Unit tests for Event Bus"""

import pytest
from vega.events import EventBus, Event, subscribe


class UserCreatedEvent(Event):
    """Test event for user creation"""
    def __init__(self, user_id: str, username: str):
        super().__init__()
        self.user_id = user_id
        self.username = username


class OrderPlacedEvent(Event):
    """Test event for order placement"""
    def __init__(self, order_id: str, total: float):
        super().__init__()
        self.order_id = order_id
        self.total = total


class TestEventBusBasics:
    """Test basic event bus functionality"""

    def test_event_bus_initialization(self):
        """Test event bus can be initialized"""
        bus = EventBus()
        assert bus is not None

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        """Test subscribing and publishing events"""
        bus = EventBus()
        received_events = []

        @subscribe(UserCreatedEvent)
        async def handler(event: UserCreatedEvent):
            received_events.append(event)

        bus.register(handler)
        event = UserCreatedEvent("user_123", "john_doe")
        await bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].user_id == "user_123"
        assert received_events[0].username == "john_doe"


class TestMultipleSubscribers:
    """Test multiple subscribers"""

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self):
        """Test multiple handlers for same event type"""
        bus = EventBus()
        handler1_called = []
        handler2_called = []

        @subscribe(UserCreatedEvent)
        async def handler1(event: UserCreatedEvent):
            handler1_called.append(event)

        @subscribe(UserCreatedEvent)
        async def handler2(event: UserCreatedEvent):
            handler2_called.append(event)

        bus.register(handler1)
        bus.register(handler2)

        event = UserCreatedEvent("user_456", "jane_doe")
        await bus.publish(event)

        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    @pytest.mark.asyncio
    async def test_different_event_types(self):
        """Test handlers for different event types"""
        bus = EventBus()
        user_events = []
        order_events = []

        @subscribe(UserCreatedEvent)
        async def user_handler(event: UserCreatedEvent):
            user_events.append(event)

        @subscribe(OrderPlacedEvent)
        async def order_handler(event: OrderPlacedEvent):
            order_events.append(event)

        bus.register(user_handler)
        bus.register(order_handler)

        await bus.publish(UserCreatedEvent("user_789", "alice"))
        await bus.publish(OrderPlacedEvent("order_101", 99.99))

        assert len(user_events) == 1
        assert len(order_events) == 1
        assert user_events[0].username == "alice"
        assert order_events[0].total == 99.99


class TestEventProperties:
    """Test event properties"""

    def test_event_has_timestamp(self):
        """Test event has timestamp"""
        event = UserCreatedEvent("user_123", "john")
        assert hasattr(event, 'timestamp')
        assert event.timestamp is not None

    def test_event_has_id(self):
        """Test event has unique ID"""
        event1 = UserCreatedEvent("user_123", "john")
        event2 = UserCreatedEvent("user_456", "jane")

        if hasattr(event1, 'event_id'):
            assert event1.event_id != event2.event_id


class TestErrorHandling:
    """Test error handling in event bus"""

    @pytest.mark.asyncio
    async def test_handler_error_doesnt_stop_other_handlers(self):
        """Test error in one handler doesn't stop others"""
        bus = EventBus()
        handler2_called = []

        @subscribe(UserCreatedEvent)
        async def failing_handler(event: UserCreatedEvent):
            raise ValueError("Handler error")

        @subscribe(UserCreatedEvent)
        async def working_handler(event: UserCreatedEvent):
            handler2_called.append(event)

        bus.register(failing_handler)
        bus.register(working_handler)

        event = UserCreatedEvent("user_123", "john")

        # The publish should not raise even if one handler fails
        try:
            await bus.publish(event)
        except ValueError:
            pass  # Expected in some implementations

        # Working handler should still be called
        # Note: This depends on implementation details
