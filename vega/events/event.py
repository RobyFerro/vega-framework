"""Base Event class for domain events"""
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


class PublishableEventMeta(type):
    """
    Metaclass for auto-publishing events.

    Automatically publishes the event after instantiation,
    allowing ultra-clean syntax:

        await UserCreated(user_id="123", email="test@test.com")

    Instead of:
        event = UserCreated(user_id="123", email="test@test.com")
        await event.publish()
    """

    def __call__(cls, *args, **kwargs):
        """
        Create instance and return publish() coroutine (auto-publish is always enabled).

        To disable auto-publish on an event class (rare):
            class UserCreated(Event, auto_publish=False):
                ...
        """
        instance = super().__call__(*args, **kwargs)

        # Auto-publish is enabled by default, can be disabled with auto_publish=False
        if getattr(cls, '_auto_publish', True):  # Default is True now!
            return instance.publish()

        return instance


class Event(metaclass=PublishableEventMeta):
    """
    Base class for domain events.

    An event represents something that has happened in the domain.
    Events are immutable and should be named in past tense.

    Key Characteristics:
    - Immutable (use frozen dataclass or read-only properties)
    - Named in past tense (UserCreated, OrderPlaced, PaymentProcessed)
    - Contains all data needed by handlers
    - Auto-generates event_id and timestamp
    - Auto-publishes by default (like Interactors!)

    Example - Auto-publish (default, ultra-clean syntax):
        from vega.events import Event
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class UserCreated(Event):
            user_id: str
            email: str
            name: str

            def __post_init__(self):
                super().__init__()

        # Event is auto-published when instantiated! Just await it!
        await UserCreated(user_id="123", email="test@test.com", name="Test")

    Example - Disable auto-publish (rare, when you need to inspect first):
        @dataclass(frozen=True)
        class UserCreated(Event, auto_publish=False):
            user_id: str
            email: str
            name: str

            def __post_init__(self):
                super().__init__()

        # Manual publish
        event = UserCreated(user_id="123", email="test@test.com", name="Test")
        # ... inspect or modify event ...
        await event.publish()
    """

    def __init_subclass__(cls, auto_publish: bool = True, **kwargs):
        """
        Hook to configure auto-publish behavior.

        Args:
            auto_publish: If False, event will NOT auto-publish when instantiated (default: True)
        """
        super().__init_subclass__(**kwargs)
        cls._auto_publish = auto_publish

    def __init__(self):
        """Initialize event with auto-generated metadata"""
        # Use object.__setattr__ to bypass frozen dataclass
        object.__setattr__(self, '_event_id', str(uuid4()))
        object.__setattr__(self, '_timestamp', datetime.now(timezone.utc))
        object.__setattr__(self, '_metadata', {})

    @property
    def event_id(self) -> str:
        """Unique identifier for this event instance"""
        return self._event_id

    @property
    def timestamp(self) -> datetime:
        """When this event was created"""
        return self._timestamp

    @property
    def event_name(self) -> str:
        """Name of the event (class name)"""
        return self.__class__.__name__

    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata attached to the event"""
        return self._metadata

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the event.

        Useful for adding correlation IDs, user context, etc.

        Args:
            key: Metadata key
            value: Metadata value
        """
        # Access metadata dict directly to modify it
        if not hasattr(self, '_metadata'):
            object.__setattr__(self, '_metadata', {})
        self._metadata[key] = value

    async def publish(self) -> None:
        """
        Publish this event to the global event bus.

        This is a convenience method to avoid importing get_event_bus().

        Example:
            event = UserCreated(user_id="123", email="test@test.com", name="Test")
            await event.publish()  # Simple!

        Note:
            This uses the global event bus. If you need a custom bus,
            call bus.publish(event) directly.
        """
        # Import here to avoid circular dependency
        from vega.events.bus import get_event_bus
        bus = get_event_bus()
        await bus.publish(self)

    def __repr__(self) -> str:
        return f"{self.event_name}(event_id={self.event_id}, timestamp={self.timestamp})"
