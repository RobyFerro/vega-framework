"""Base class for job queue listeners"""
from abc import ABC, abstractmethod
from typing import Optional
from vega.listeners.message import Message, MessageContext


class JobListener(ABC):
    """
    Base class for job queue listeners.

    Similar to Interactor pattern but designed for background job processing.
    Listeners continuously poll queues and process messages asynchronously.

    Key features:
    - Automatic dependency injection via @bind decorator
    - Lifecycle hooks (on_startup, on_shutdown, on_error)
    - Auto-acknowledgment or manual control
    - Integration with Vega DI system

    Example (auto-acknowledgment):
        from vega.listeners import JobListener, job_listener, Message
        from vega.di import bind
        from domain.services import EmailService

        @job_listener(queue="email-notifications", workers=3)
        class SendEmailListener(JobListener):
            @bind
            async def handle(self, message: Message, email_service: EmailService):
                data = message.body
                await email_service.send(to=data['to'], subject=data['subject'])
                # Automatically acknowledged on success

    Example (manual acknowledgment):
        @job_listener(queue="orders", auto_ack=False, workers=5)
        class ProcessOrderListener(JobListener):
            @bind
            async def handle(
                self,
                message: Message,
                context: MessageContext,
                order_repo: OrderRepository
            ):
                try:
                    order = await order_repo.get(message.body['order_id'])
                    await self.process(order)
                    await context.ack()  # Explicit acknowledgment
                except TemporaryError:
                    await context.reject(requeue=True)  # Retry later
                except ValidationError:
                    await context.reject(requeue=False)  # Send to DLQ

    Example (long-running job):
        @job_listener(queue="file-processing", visibility_timeout=300)
        class ProcessFileListener(JobListener):
            @bind
            async def handle(
                self,
                message: Message,
                context: MessageContext,
                storage: StorageService
            ):
                # Extend visibility for long processing
                await context.extend_visibility(600)  # Add 10 more minutes

                file_url = message.body['file_url']
                await storage.process_large_file(file_url)

                await context.ack()
    """

    @abstractmethod
    async def handle(
        self,
        message: Message,
        context: Optional[MessageContext] = None
    ) -> None:
        """
        Process a queue message.

        Use @bind decorator for automatic dependency injection.

        Args:
            message: The queue message to process
            context: Message context for manual ack/reject (only when auto_ack=False)

        Raises:
            Exception: Any exception will trigger retry logic if enabled,
                      or auto-reject if auto_ack=True
        """
        raise NotImplementedError

    async def on_error(self, message: Message, error: Exception) -> None:
        """
        Hook called when message processing fails.

        Called after all retry attempts are exhausted. Use this for:
        - Logging errors to monitoring systems (Sentry, DataDog, etc.)
        - Sending notifications
        - Custom error handling logic

        Args:
            message: The message that failed processing
            error: The exception that was raised

        Note:
            Exceptions raised in this hook are logged but don't affect message handling.
        """
        pass

    async def on_startup(self) -> None:
        """
        Hook called when the listener starts.

        Use this for initialization tasks like:
        - Opening connections
        - Loading configuration
        - Warming up caches

        Called once per listener instance before workers start polling.
        """
        pass

    async def on_shutdown(self) -> None:
        """
        Hook called when the listener stops.

        Use this for cleanup tasks like:
        - Closing connections
        - Flushing buffers
        - Saving state

        Called once per listener instance after all workers stop.
        """
        pass
