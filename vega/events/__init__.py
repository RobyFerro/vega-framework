"""Event system for domain events and event-driven architecture"""
from vega.events.event import Event, PublishableEventMeta
from vega.events.bus import EventBus, get_event_bus, set_event_bus
from vega.events.decorators import subscribe, event_handler, trigger
from vega.events.middleware import (
    EventMiddleware,
    LoggingEventMiddleware,
    MetricsEventMiddleware,
    ValidationEventMiddleware,
    EnrichmentEventMiddleware,
)

__all__ = [
    # Core
    'Event',
    'PublishableEventMeta',
    'EventBus',
    'get_event_bus',
    'set_event_bus',
    # Decorators
    'subscribe',
    'event_handler',
    'trigger',
    # Middleware
    'EventMiddleware',
    'LoggingEventMiddleware',
    'MetricsEventMiddleware',
    'ValidationEventMiddleware',
    'EnrichmentEventMiddleware',
]
