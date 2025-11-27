"""Decorators for job listeners"""
from typing import Type, TypeVar
from vega.listeners.registry import register_listener
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)


def job_listener(
    queue: str,
    workers: int = 1,
    auto_ack: bool = True,
    visibility_timeout: int = 30,
    max_messages: int = 1,
    retry_on_error: bool = False,
    max_retries: int = 3
):
    """
    Decorator to register a job listener.

    Registers the listener class in the global registry when the module
    is imported (similar to @subscribe for events).

    The decorated class must inherit from JobListener and implement the
    handle() method.

    Args:
        queue: Queue name to listen to
        workers: Number of concurrent workers for this listener (default: 1)
        auto_ack: Automatically acknowledge messages on success (default: True)
        visibility_timeout: Message visibility timeout in seconds (default: 30)
        max_messages: Max messages to fetch per poll (default: 1, driver may limit)
        retry_on_error: Retry failed messages with exponential backoff (default: False)
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        Decorated listener class

    Example (simple auto-ack):
        from vega.listeners import JobListener, job_listener, Message
        from vega.di import bind

        @job_listener(queue="email-queue", workers=3)
        class SendEmailListener(JobListener):
            @bind
            async def handle(self, message: Message, email_service: EmailService):
                await email_service.send(**message.body)
                # Auto-acknowledged on success

    Example (manual acknowledgment):
        @job_listener(queue="orders", auto_ack=False, workers=5)
        class ProcessOrderListener(JobListener):
            @bind
            async def handle(
                self,
                message: Message,
                context: MessageContext,
                repo: OrderRepository
            ):
                order = await repo.get(message.body['order_id'])
                await self.process(order)
                await context.ack()  # Manual acknowledgment

    Example (with retries):
        @job_listener(
            queue="api-calls",
            retry_on_error=True,
            max_retries=5,
            workers=10
        )
        class CallExternalAPIListener(JobListener):
            @bind
            async def handle(self, message: Message, api_client: APIClient):
                # Will retry up to 5 times with exponential backoff
                await api_client.call(message.body['endpoint'])

    Example (batch processing):
        @job_listener(
            queue="batch-jobs",
            max_messages=10,  # Process up to 10 messages at once
            workers=2
        )
        class BatchProcessListener(JobListener):
            async def handle(self, message: Message):
                # Each message still processed individually
                await self.process(message.body)
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Validate that class inherits from JobListener
        from vega.listeners.listener import JobListener
        if not issubclass(cls, JobListener):
            raise TypeError(
                f"{cls.__name__} must inherit from JobListener to use @job_listener decorator"
            )

        # Store metadata on class for runtime access
        cls._listener_queue = queue
        cls._listener_workers = workers
        cls._listener_auto_ack = auto_ack
        cls._listener_visibility_timeout = visibility_timeout
        cls._listener_max_messages = max_messages
        cls._listener_retry_on_error = retry_on_error
        cls._listener_max_retries = max_retries

        # Mark as listener for introspection
        cls._is_job_listener = True

        # Register in global registry (happens on import)
        register_listener(cls)

        logger.info(
            f"Registered listener '{cls.__name__}' -> queue '{queue}' "
            f"(workers={workers}, auto_ack={auto_ack})"
        )

        return cls

    return decorator
