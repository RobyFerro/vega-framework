"""Event middleware for cross-cutting concerns"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from vega.events.event import Event

logger = logging.getLogger(__name__)


class EventMiddleware(ABC):
    """
    Base class for event middleware.

    Middleware allows you to add cross-cutting concerns to event processing,
    such as logging, metrics, validation, or security checks.

    Middleware is executed in the order it was added to the event bus.

    Example:
        class LoggingMiddleware(EventMiddleware):
            async def before_publish(self, event: Event):
                print(f"Publishing: {event.event_name}")

            async def after_publish(self, event: Event):
                print(f"Published: {event.event_name}")

        bus = EventBus()
        bus.add_middleware(LoggingMiddleware())
    """

    @abstractmethod
    async def before_publish(self, event: Event) -> None:
        """
        Called before event is published to handlers.

        Use this to modify the event, add metadata, or perform validation.

        Args:
            event: Event about to be published
        """
        pass

    @abstractmethod
    async def after_publish(self, event: Event) -> None:
        """
        Called after all handlers have processed the event.

        Use this for cleanup, logging, or metrics collection.

        Args:
            event: Event that was published
        """
        pass


class LoggingEventMiddleware(EventMiddleware):
    """
    Middleware that logs all events.

    Logs event name, ID, and processing time.

    Example:
        from vega.events import EventBus, LoggingEventMiddleware

        bus = EventBus()
        bus.add_middleware(LoggingEventMiddleware())
    """

    def __init__(self, log_level: int = logging.DEBUG):
        """
        Initialize logging middleware.

        Args:
            log_level: Log level to use (default: DEBUG)
        """
        self.log_level = log_level
        self._start_times: Dict[str, float] = {}

    async def before_publish(self, event: Event) -> None:
        """Log event publication start"""
        self._start_times[event.event_id] = time.time()
        logger.log(
            self.log_level,
            f"Publishing event: {event.event_name} (id={event.event_id})"
        )

    async def after_publish(self, event: Event) -> None:
        """Log event publication completion with duration"""
        start_time = self._start_times.pop(event.event_id, None)
        if start_time:
            duration = (time.time() - start_time) * 1000  # ms
            logger.log(
                self.log_level,
                f"Event processed: {event.event_name} (id={event.event_id}, duration={duration:.2f}ms)"
            )


class MetricsEventMiddleware(EventMiddleware):
    """
    Middleware that collects metrics for events.

    Tracks:
    - Event count by type
    - Processing duration
    - Success/failure rates

    Example:
        middleware = MetricsEventMiddleware()
        bus.add_middleware(middleware)

        # Later, get metrics
        print(middleware.get_metrics())
    """

    def __init__(self):
        """Initialize metrics middleware"""
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._start_times: Dict[str, float] = {}

    async def before_publish(self, event: Event) -> None:
        """Record event start time"""
        self._start_times[event.event_id] = time.time()

        # Initialize metrics for this event type
        event_name = event.event_name
        if event_name not in self._metrics:
            self._metrics[event_name] = {
                'count': 0,
                'total_duration_ms': 0,
                'min_duration_ms': float('inf'),
                'max_duration_ms': 0,
            }

    async def after_publish(self, event: Event) -> None:
        """Record event completion and update metrics"""
        start_time = self._start_times.pop(event.event_id, None)
        if start_time is None:
            return

        duration_ms = (time.time() - start_time) * 1000

        # Update metrics
        event_name = event.event_name
        metrics = self._metrics[event_name]
        metrics['count'] += 1
        metrics['total_duration_ms'] += duration_ms
        metrics['min_duration_ms'] = min(metrics['min_duration_ms'], duration_ms)
        metrics['max_duration_ms'] = max(metrics['max_duration_ms'], duration_ms)
        metrics['avg_duration_ms'] = metrics['total_duration_ms'] / metrics['count']

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get collected metrics.

        Returns:
            Dictionary of metrics by event type
        """
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self._metrics.clear()
        self._start_times.clear()


class ValidationEventMiddleware(EventMiddleware):
    """
    Middleware that validates events before publishing.

    Ensures events meet certain criteria before being processed.

    Example:
        def validate_user_event(event):
            if hasattr(event, 'user_id') and not event.user_id:
                raise ValueError("user_id cannot be empty")

        middleware = ValidationEventMiddleware()
        middleware.add_validator(UserCreated, validate_user_event)

        bus.add_middleware(middleware)
    """

    def __init__(self):
        """Initialize validation middleware"""
        from typing import Type, Callable
        self._validators: Dict[Type[Event], list[Callable]] = {}

    def add_validator(self, event_type: type, validator: callable) -> None:
        """
        Add a validator for an event type.

        Args:
            event_type: Event type to validate
            validator: Validation function that raises on invalid event
        """
        if event_type not in self._validators:
            self._validators[event_type] = []
        self._validators[event_type].append(validator)

    async def before_publish(self, event: Event) -> None:
        """Validate event before publishing"""
        event_type = type(event)

        # Run validators for this event type
        if event_type in self._validators:
            for validator in self._validators[event_type]:
                # Run validator
                result = validator(event)
                # Await if async
                if hasattr(result, '__await__'):
                    await result

    async def after_publish(self, event: Event) -> None:
        """No action after publish"""
        pass


class EnrichmentEventMiddleware(EventMiddleware):
    """
    Middleware that enriches events with additional data.

    Automatically adds metadata like user context, correlation IDs, etc.

    Example:
        middleware = EnrichmentEventMiddleware()
        middleware.add_enricher(lambda event: event.add_metadata('tenant_id', 'abc123'))

        bus.add_middleware(middleware)
    """

    def __init__(self):
        """Initialize enrichment middleware"""
        self._enrichers: list[callable] = []

    def add_enricher(self, enricher: callable) -> None:
        """
        Add an enricher function.

        Enricher should modify the event in-place (e.g., add metadata).

        Args:
            enricher: Function that enriches the event
        """
        self._enrichers.append(enricher)

    async def before_publish(self, event: Event) -> None:
        """Enrich event before publishing"""
        for enricher in self._enrichers:
            # Run enricher
            result = enricher(event)
            # Await if async
            if hasattr(result, '__await__'):
                await result

    async def after_publish(self, event: Event) -> None:
        """No action after publish"""
        pass
