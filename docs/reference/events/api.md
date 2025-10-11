# Vega Events API Reference

Lookup the primary types, decorators, and middleware available in the Vega Events module.

## Event

Base class for all events.

**Properties**:
- `event_id: str` - Unique identifier (auto-generated UUID)
- `timestamp: datetime` - When event was created (auto-generated)
- `event_name: str` - Event class name
- `metadata: Dict[str, Any]` - Additional metadata

**Methods**:
- `add_metadata(key: str, value: Any)` - Add metadata to event

## EventBus

Central event bus for pub/sub.

**Methods**:
- `subscribe(event_type, handler, priority=0, retry_on_error=False, max_retries=3)` - Subscribe handler
- `unsubscribe(event_type, handler)` - Unsubscribe handler
- `publish(event)` - Publish event to all subscribers
- `publish_many(events)` - Publish multiple events
- `add_middleware(middleware)` - Add middleware
- `on_error(handler)` - Register error handler
- `clear_subscribers(event_type=None)` - Clear subscribers
- `get_subscriber_count(event_type)` - Get subscriber count

## Decorators

**`@subscribe(event_type, priority=0, retry_on_error=False, max_retries=3)`**

Subscribe function to event on global bus.

**`@event_handler(event_type, bus=None, priority=0, retry_on_error=False, max_retries=3)`**

Mark method as event handler with optional custom bus.

**`@trigger(event_class)`**

Decorator for Interactor classes to automatically trigger an event after call() completes. The event is constructed with the return value of call() and auto-published.

## Discovery Functions

**`discover_event_handlers(base_package, events_subpackage="events")`**

Auto-discover and register event handlers from a package. Scans the specified package for Python modules containing event handlers decorated with @subscribe() and automatically imports them to trigger registration.

## Middleware

**Built-in Middleware**:
- `LoggingEventMiddleware` - Log all events
- `MetricsEventMiddleware` - Collect event metrics
- `ValidationEventMiddleware` - Validate events before publishing
- `EnrichmentEventMiddleware` - Auto-add metadata to events

**Custom Middleware**:

Extend `EventMiddleware` and implement:
- `async def before_publish(event: Event)` - Called before event is published
- `async def after_publish(event: Event)` - Called after handlers complete

## Performance Considerations

- **Async Handlers**: All handlers run concurrently (not sequentially)
- **Error Isolation**: Failed handlers don't block other handlers
- **Retry Overhead**: Use retry sparingly - exponential backoff adds delay
- **Middleware Order**: Middleware runs in order added - keep it lightweight

