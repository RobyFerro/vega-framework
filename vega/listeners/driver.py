"""Queue driver abstraction for job listeners"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from vega.patterns import Service
from vega.listeners.message import Message


class QueueDriver(Service, ABC):
    """
    Abstract interface for queue service drivers.

    Provides a contract for implementing queue backends like SQS, RabbitMQ,
    Redis Streams, etc. All methods are async for non-blocking I/O.

    Implementations should be registered in the DI container:
        from vega.di import Container
        from vega.listeners.drivers.sqs import SQSDriver

        container = Container({
            QueueDriver: SQSDriver,
        })

    Example implementation:
        @bean(scope=Scope.SINGLETON)
        class RabbitMQDriver(QueueDriver):
            async def receive_messages(self, queue_name: str, ...) -> List[Message]:
                # Implementation
                pass
    """

    @abstractmethod
    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        visibility_timeout: int = 30,
        wait_time: int = 0
    ) -> List[Message]:
        """
        Receive messages from a queue.

        Args:
            queue_name: Name of the queue to poll
            max_messages: Maximum number of messages to receive (driver may have limits)
            visibility_timeout: How long (seconds) to hide message from other consumers
            wait_time: Long polling wait time in seconds (0 = short polling)

        Returns:
            List of received messages (may be empty)

        Note:
            Use wait_time > 0 for long polling to reduce API calls and improve efficiency.
        """
        pass

    @abstractmethod
    async def acknowledge(self, message: Message) -> None:
        """
        Acknowledge successful message processing.

        Removes the message from the queue permanently.

        Args:
            message: The message to acknowledge
        """
        pass

    @abstractmethod
    async def reject(
        self,
        message: Message,
        requeue: bool = True,
        visibility_timeout: Optional[int] = None
    ) -> None:
        """
        Reject a message (nack).

        Args:
            message: The message to reject
            requeue: If True, makes message available for retry.
                    If False, removes from queue (may send to DLQ if configured).
            visibility_timeout: Custom visibility timeout for requeued messages.
                              If None, uses default behavior (typically immediate requeue).
        """
        pass

    @abstractmethod
    async def extend_visibility(self, message: Message, seconds: int) -> None:
        """
        Extend the visibility timeout for a message.

        Useful for long-running jobs that need more processing time.

        Args:
            message: The message to extend
            seconds: Additional seconds to extend visibility
        """
        pass

    @abstractmethod
    async def get_queue_attributes(self, queue_name: str) -> Dict[str, Any]:
        """
        Get queue metadata and attributes.

        Returns implementation-specific queue information like:
        - Approximate message count
        - DLQ configuration
        - Queue ARN/URL
        - etc.

        Args:
            queue_name: Name of the queue

        Returns:
            Dictionary of queue attributes
        """
        pass

    @abstractmethod
    async def send_message(self, queue_name: str, body: Dict[str, Any]) -> None:
        """
        Send a message to a queue.

        Used for scheduling jobs to be processed by listeners.

        Args:
            queue_name: Name of the queue to send to
            body: Message body as dictionary (will be JSON serialized)

        Example:
            await driver.send_message(
                queue_name="email-notifications",
                body={"to": "user@example.com", "subject": "Welcome"}
            )
        """
        pass

    async def connect(self) -> None:
        """
        Initialize connection to queue service.

        Override this method if your driver needs to establish connections,
        create clients, or perform initialization.

        Called once when ListenerManager starts.
        """
        pass

    async def disconnect(self) -> None:
        """
        Close connection to queue service.

        Override this method if your driver needs to clean up resources,
        close connections, or perform shutdown tasks.

        Called once when ListenerManager stops.
        """
        pass
