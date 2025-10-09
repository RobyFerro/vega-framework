"""Event Bus implementation for pub/sub pattern"""
import asyncio
import logging
from typing import Type, Callable, List, Dict, Any, Optional
from collections import defaultdict

from vega.events.event import Event

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event Bus for publishing and subscribing to domain events.

    Supports:
    - Async event handlers
    - Multiple subscribers per event
    - Event inheritance (handlers for base events receive derived events)
    - Priority ordering
    - Error handling with retries
    - Middleware support

    Example:
        from vega.events import EventBus, Event

        bus = EventBus()

        # Subscribe to event
        @bus.subscribe(UserCreated)
        async def send_welcome_email(event: UserCreated):
            await email_service.send(event.email, "Welcome!")

        # Publish event
        await bus.publish(UserCreated(user_id="123", email="test@test.com"))
    """

    def __init__(self):
        """Initialize event bus"""
        self._subscribers: Dict[Type[Event], List[Dict[str, Any]]] = defaultdict(list)
        self._middleware: List[Any] = []
        self._error_handlers: List[Callable] = []

    def subscribe(
        self,
        event_type: Type[Event],
        handler: Optional[Callable] = None,
        priority: int = 0,
        retry_on_error: bool = False,
        max_retries: int = 3
    ):
        """
        Subscribe a handler to an event type.

        Can be used as a decorator or called directly.

        Args:
            event_type: Type of event to subscribe to
            handler: Handler function (if not used as decorator)
            priority: Handler priority (higher runs first)
            retry_on_error: Whether to retry on failure
            max_retries: Maximum retry attempts

        Returns:
            Handler function (for decorator usage) or None

        Example:
            # As decorator
            @bus.subscribe(UserCreated)
            async def handle_user_created(event: UserCreated):
                ...

            # Direct call
            bus.subscribe(UserCreated, handle_user_created)

            # With options
            @bus.subscribe(UserCreated, priority=10, retry_on_error=True)
            async def important_handler(event: UserCreated):
                ...
        """
        def decorator(func: Callable) -> Callable:
            subscriber_info = {
                'handler': func,
                'priority': priority,
                'retry_on_error': retry_on_error,
                'max_retries': max_retries,
            }

            # Add to subscribers list
            self._subscribers[event_type].append(subscriber_info)

            # Sort by priority (higher priority first)
            self._subscribers[event_type].sort(
                key=lambda x: x['priority'],
                reverse=True
            )

            logger.debug(
                f"Registered handler '{func.__name__}' for event '{event_type.__name__}' "
                f"(priority={priority})"
            )

            return func

        # If handler is provided, apply decorator immediately
        if handler is not None:
            return decorator(handler)

        # Otherwise return decorator for @subscribe usage
        return decorator

    def unsubscribe(self, event_type: Type[Event], handler: Callable) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event
            handler: Handler function to remove

        Returns:
            True if handler was found and removed, False otherwise
        """
        if event_type not in self._subscribers:
            return False

        initial_count = len(self._subscribers[event_type])
        self._subscribers[event_type] = [
            sub for sub in self._subscribers[event_type]
            if sub['handler'] != handler
        ]

        removed = initial_count > len(self._subscribers[event_type])
        if removed:
            logger.debug(f"Unsubscribed handler '{handler.__name__}' from '{event_type.__name__}'")

        return removed

    def add_middleware(self, middleware: 'EventMiddleware') -> None:
        """
        Add middleware to the event bus.

        Middleware is executed for all events in the order added.

        Args:
            middleware: Middleware instance
        """
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")

    def on_error(self, handler: Callable) -> Callable:
        """
        Register error handler for failed event processing.

        Error handlers receive (event, exception, handler_name) and should not raise.

        Example:
            @bus.on_error
            async def log_errors(event, exception, handler_name):
                logger.error(f"Handler {handler_name} failed: {exception}")
        """
        self._error_handlers.append(handler)
        return handler

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Executes all handlers in priority order. If a handler fails and has
        retry enabled, it will be retried up to max_retries times.

        Args:
            event: Event instance to publish

        Example:
            await bus.publish(UserCreated(user_id="123", email="test@test.com"))
        """
        logger.debug(f"Publishing event: {event.event_name} (id={event.event_id})")

        # Execute middleware (before)
        for middleware in self._middleware:
            await middleware.before_publish(event)

        # Get handlers for this event type and all parent event types
        handlers = self._get_handlers_for_event(event)

        if not handlers:
            logger.debug(f"No subscribers for event: {event.event_name}")
            # Execute middleware (after) even if no handlers
            for middleware in reversed(self._middleware):
                await middleware.after_publish(event)
            return

        logger.debug(f"Found {len(handlers)} handler(s) for event: {event.event_name}")

        # Execute all handlers
        tasks = []
        for subscriber_info in handlers:
            task = self._execute_handler(event, subscriber_info)
            tasks.append(task)

        # Wait for all handlers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for errors
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                handler_name = handlers[idx]['handler'].__name__
                logger.error(
                    f"Handler '{handler_name}' failed for event '{event.event_name}': {result}"
                )

        # Execute middleware (after)
        for middleware in reversed(self._middleware):
            await middleware.after_publish(event)

        logger.debug(f"Event published: {event.event_name} (id={event.event_id})")

    async def publish_many(self, events: List[Event]) -> None:
        """
        Publish multiple events.

        Events are published sequentially in order.

        Args:
            events: List of events to publish
        """
        for event in events:
            await self.publish(event)

    def _get_handlers_for_event(self, event: Event) -> List[Dict[str, Any]]:
        """
        Get all handlers that should receive this event.

        Includes handlers for the exact event type and all parent event types.
        """
        handlers = []
        event_type = type(event)

        # Get handlers for exact type
        if event_type in self._subscribers:
            handlers.extend(self._subscribers[event_type])

        # Get handlers for parent types (event inheritance)
        for base_type in event_type.__mro__[1:]:
            if base_type == Event or not issubclass(base_type, Event):
                continue
            if base_type in self._subscribers:
                handlers.extend(self._subscribers[base_type])

        return handlers

    async def _execute_handler(
        self,
        event: Event,
        subscriber_info: Dict[str, Any]
    ) -> None:
        """
        Execute a single event handler with retry logic.

        Args:
            event: Event to handle
            subscriber_info: Subscriber configuration
        """
        handler = subscriber_info['handler']
        retry_on_error = subscriber_info['retry_on_error']
        max_retries = subscriber_info['max_retries']

        attempt = 0
        last_exception = None

        while attempt <= (max_retries if retry_on_error else 0):
            try:
                # Execute handler
                result = handler(event)

                # Await if coroutine
                if asyncio.iscoroutine(result):
                    await result

                # Success - exit retry loop
                return

            except Exception as e:
                last_exception = e
                attempt += 1

                if attempt <= max_retries and retry_on_error:
                    logger.warning(
                        f"Handler '{handler.__name__}' failed (attempt {attempt}/{max_retries}): {e}"
                    )
                    # Exponential backoff
                    await asyncio.sleep(0.1 * (2 ** (attempt - 1)))
                else:
                    # All retries exhausted or retry disabled
                    logger.error(
                        f"Handler '{handler.__name__}' failed for event '{event.event_name}': {e}",
                        exc_info=True
                    )

                    # Call error handlers
                    for error_handler in self._error_handlers:
                        try:
                            result = error_handler(event, e, handler.__name__)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as err_ex:
                            logger.error(
                                f"Error handler failed: {err_ex}",
                                exc_info=True
                            )

                    # Re-raise exception
                    raise last_exception

    def clear_subscribers(self, event_type: Optional[Type[Event]] = None) -> None:
        """
        Clear all subscribers.

        Args:
            event_type: If provided, only clear subscribers for this event type.
                       If None, clear all subscribers.
        """
        if event_type is None:
            self._subscribers.clear()
            logger.debug("Cleared all subscribers")
        elif event_type in self._subscribers:
            del self._subscribers[event_type]
            logger.debug(f"Cleared subscribers for: {event_type.__name__}")

    def get_subscriber_count(self, event_type: Type[Event]) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: Event type

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Creates the instance on first call (singleton pattern).

    Returns:
        Global EventBus instance

    Example:
        from vega.events import get_event_bus

        bus = get_event_bus()
        await bus.publish(MyEvent())
    """
    global _global_event_bus

    if _global_event_bus is None:
        _global_event_bus = EventBus()
        logger.debug("Created global event bus")

    return _global_event_bus


def set_event_bus(bus: EventBus) -> None:
    """
    Set a custom event bus as the global instance.

    Useful for testing or custom configurations.

    Args:
        bus: EventBus instance to use globally
    """
    global _global_event_bus
    _global_event_bus = bus
    logger.debug("Set custom global event bus")
