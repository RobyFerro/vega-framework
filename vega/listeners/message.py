"""Message models for job listeners"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Message:
    """
    Represents a queue message.

    Attributes:
        id: Unique message identifier
        body: Message payload (parsed from JSON)
        attributes: Message metadata
        receipt_handle: Driver-specific handle for acknowledgment
        received_count: Number of times this message has been received
        timestamp: When the message was received
    """
    id: str
    body: Dict[str, Any]
    attributes: Dict[str, Any]
    receipt_handle: str
    received_count: int
    timestamp: datetime

    @property
    def data(self) -> Dict[str, Any]:
        """Alias for body."""
        return self.body


@dataclass
class MessageContext:
    """
    Context for message handling with acknowledgment controls.

    Provides methods to acknowledge, reject, or extend visibility timeout
    for messages when using manual acknowledgment mode.

    Example:
        @job_listener(queue="orders", auto_ack=False)
        class ProcessOrderListener(JobListener):
            @bind
            async def handle(self, message: Message, context: MessageContext):
                try:
                    await self.process(message.body)
                    await context.ack()  # Acknowledge success
                except TemporaryError:
                    await context.reject(requeue=True)  # Retry later
                except ValidationError:
                    await context.reject(requeue=False)  # Send to DLQ
    """
    message: Message
    driver: 'QueueDriver'
    queue_name: str

    async def ack(self) -> None:
        """
        Acknowledge successful processing.

        Removes the message from the queue.
        """
        await self.driver.acknowledge(self.message)

    async def reject(
        self,
        requeue: bool = True,
        visibility_timeout: Optional[int] = None
    ) -> None:
        """
        Reject a message.

        Args:
            requeue: If True, makes message available for retry.
                    If False, removes from queue (sends to DLQ if configured).
            visibility_timeout: Custom visibility timeout for requeued messages.
                              If None, uses default behavior.
        """
        await self.driver.reject(
            self.message,
            requeue=requeue,
            visibility_timeout=visibility_timeout
        )

    async def extend_visibility(self, seconds: int) -> None:
        """
        Extend message visibility timeout.

        Useful for long-running jobs that need more processing time.

        Args:
            seconds: Additional seconds to extend visibility

        Example:
            # Process large file that takes 5 minutes
            await context.extend_visibility(300)
            await process_large_file(message.body['file_url'])
            await context.ack()
        """
        await self.driver.extend_visibility(self.message, seconds)
