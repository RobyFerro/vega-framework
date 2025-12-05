"""AWS SQS driver implementation

This driver requires aioboto3 to be installed.
Install it with: pip install vega-framework[sqs]
"""
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime
from vega.listeners.driver import QueueDriver
from vega.listeners.message import Message
from vega.di import Scope, injectable

logger = logging.getLogger(__name__)


@injectable(scope=Scope.SINGLETON)
class SQSDriver(QueueDriver):
    """
    AWS SQS implementation of QueueDriver.

    Supports both AWS SQS and LocalStack for local development.

    Configuration:
        Register in config.py:

        from vega.listeners.drivers.sqs import SQSDriver
        from vega.listeners.driver import QueueDriver
        from settings import settings

        container = Container({
            QueueDriver: lambda: SQSDriver(
                region=settings.aws_region,
                access_key=settings.aws_access_key,
                secret_key=settings.aws_secret_key,
                endpoint_url=settings.sqs_endpoint  # For LocalStack
            )
        })

    LocalStack Example:
        # Use LocalStack for local development
        driver = SQSDriver(
            region="us-east-1",
            endpoint_url="http://localhost:4566"  # LocalStack
        )

    Features:
        - Long polling support (reduces API calls)
        - Batch message receiving (up to 10 messages)
        - Visibility timeout management
        - DLQ support (configure on AWS side)
        - Queue URL caching for performance

    Note:
        - DLQ configuration should be done on AWS side
        - Message retention and DLQ redrive policies managed by AWS
        - Supports standard and FIFO queues
    """

    def __init__(
        self,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize SQS driver.

        Args:
            region: AWS region (default: us-east-1)
            access_key: AWS access key ID (uses default credentials if None)
            secret_key: AWS secret access key (uses default credentials if None)
            endpoint_url: Custom endpoint URL (for LocalStack, default: None)
        """
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self._client = None
        self._client_context = None
        self._queue_urls: Dict[str, str] = {}

    async def connect(self) -> None:
        """Initialize aioboto3 SQS client."""
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 is required for SQS driver. "
                "Install it with: pip install vega-framework[sqs]"
            )

        session_kwargs = {"region_name": self.region}
        if self.access_key and self.secret_key:
            session_kwargs["aws_access_key_id"] = self.access_key
            session_kwargs["aws_secret_access_key"] = self.secret_key

        self._session = aioboto3.Session(**session_kwargs)

        client_kwargs = {}
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        # Create async context manager for SQS client
        self._client_context = self._session.client('sqs', **client_kwargs)
        self._client = await self._client_context.__aenter__()

        logger.info(
            f"Connected to SQS (region={self.region}, "
            f"endpoint={self.endpoint_url or 'AWS'})"
        )

    async def disconnect(self) -> None:
        """Close SQS client."""
        if self._client and self._client_context:
            await self._client_context.__aexit__(None, None, None)
            logger.info("Disconnected from SQS")

    async def _get_queue_url(self, queue_name: str) -> str:
        """
        Get queue URL (cached for performance).

        Args:
            queue_name: Name of the queue

        Returns:
            Queue URL

        Raises:
            ClientError: If queue doesn't exist
        """
        if queue_name not in self._queue_urls:
            try:
                response = await self._client.get_queue_url(QueueName=queue_name)
                self._queue_urls[queue_name] = response['QueueUrl']
                logger.debug(f"Cached queue URL for '{queue_name}'")
            except Exception as e:
                logger.error(f"Failed to get queue URL for '{queue_name}': {e}")
                raise

        return self._queue_urls[queue_name]

    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        visibility_timeout: int = 30,
        wait_time: int = 0
    ) -> List[Message]:
        """
        Receive messages from SQS queue.

        Args:
            queue_name: Name of the queue
            max_messages: Max messages to receive (1-10, SQS limit)
            visibility_timeout: Visibility timeout in seconds
            wait_time: Long polling wait time (0-20 seconds)

        Returns:
            List of received messages
        """
        queue_url = await self._get_queue_url(queue_name)

        # SQS has a limit of 10 messages per request
        max_messages = min(max_messages, 10)

        try:
            response = await self._client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                VisibilityTimeout=visibility_timeout,
                WaitTimeSeconds=min(wait_time, 20),  # SQS max is 20s
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )

            messages = []
            for msg in response.get('Messages', []):
                # Parse message body (try JSON, fallback to raw)
                body = msg['Body']
                try:
                    body_data = json.loads(body)
                except json.JSONDecodeError:
                    body_data = {"raw": body}

                messages.append(Message(
                    id=msg['MessageId'],
                    body=body_data,
                    attributes=msg.get('Attributes', {}),
                    receipt_handle=msg['ReceiptHandle'],
                    received_count=int(
                        msg.get('Attributes', {}).get('ApproximateReceiveCount', 1)
                    ),
                    timestamp=datetime.utcnow()
                ))

            if messages:
                logger.debug(
                    f"Received {len(messages)} message(s) from queue '{queue_name}'"
                )

            return messages

        except Exception as e:
            logger.error(f"Failed to receive messages from '{queue_name}': {e}")
            raise

    async def acknowledge(self, message: Message) -> None:
        """
        Delete message from SQS queue.

        Args:
            message: Message to acknowledge
        """
        queue_name = message.attributes.get('queue_name')
        if not queue_name:
            raise ValueError("Message missing 'queue_name' in attributes")

        queue_url = await self._get_queue_url(queue_name)

        try:
            await self._client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message.receipt_handle
            )
            logger.debug(f"Acknowledged message {message.id}")
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message.id}: {e}")
            raise

    async def reject(
        self,
        message: Message,
        requeue: bool = True,
        visibility_timeout: Optional[int] = None
    ) -> None:
        """
        Reject message (change visibility or delete).

        Args:
            message: Message to reject
            requeue: If True, makes available immediately.
                    If False, deletes (sends to DLQ if configured)
            visibility_timeout: Custom visibility timeout (only if requeue=True)
        """
        queue_name = message.attributes.get('queue_name')
        if not queue_name:
            raise ValueError("Message missing 'queue_name' in attributes")

        queue_url = await self._get_queue_url(queue_name)

        try:
            if requeue:
                # Change visibility to make available for retry
                timeout = visibility_timeout if visibility_timeout is not None else 0
                await self._client.change_message_visibility(
                    QueueUrl=queue_url,
                    ReceiptHandle=message.receipt_handle,
                    VisibilityTimeout=timeout
                )
                logger.debug(
                    f"Rejected message {message.id} "
                    f"(requeue=True, visibility={timeout}s)"
                )
            else:
                # Delete message (will go to DLQ if configured)
                await self.acknowledge(message)
                logger.debug(f"Rejected message {message.id} (sent to DLQ)")

        except Exception as e:
            logger.error(f"Failed to reject message {message.id}: {e}")
            raise

    async def extend_visibility(self, message: Message, seconds: int) -> None:
        """
        Extend visibility timeout for a message.

        Args:
            message: Message to extend
            seconds: New visibility timeout in seconds
        """
        queue_name = message.attributes.get('queue_name')
        if not queue_name:
            raise ValueError("Message missing 'queue_name' in attributes")

        queue_url = await self._get_queue_url(queue_name)

        try:
            await self._client.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=message.receipt_handle,
                VisibilityTimeout=seconds
            )
            logger.debug(f"Extended visibility for message {message.id} to {seconds}s")
        except Exception as e:
            logger.error(
                f"Failed to extend visibility for message {message.id}: {e}"
            )
            raise

    async def get_queue_attributes(self, queue_name: str) -> Dict[str, Any]:
        """
        Get SQS queue attributes.

        Returns attributes like:
        - ApproximateNumberOfMessages
        - ApproximateNumberOfMessagesNotVisible
        - RedrivePolicy (DLQ configuration)
        - etc.

        Args:
            queue_name: Name of the queue

        Returns:
            Dictionary of queue attributes
        """
        queue_url = await self._get_queue_url(queue_name)

        try:
            response = await self._client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['All']
            )
            return response.get('Attributes', {})
        except Exception as e:
            logger.error(f"Failed to get attributes for '{queue_name}': {e}")
            raise

    async def send_message(self, queue_name: str, body: Dict[str, Any]) -> None:
        """
        Send a message to SQS queue.

        Args:
            queue_name: Name of the queue
            body: Message body as dictionary (will be JSON serialized)

        Example:
            await driver.send_message(
                queue_name="email-notifications",
                body={"to": "user@example.com", "subject": "Welcome"}
            )
        """
        queue_url = await self._get_queue_url(queue_name)

        try:
            message_body = json.dumps(body)
            response = await self._client.send_message(
                QueueUrl=queue_url,
                MessageBody=message_body
            )
            logger.debug(
                f"Sent message to queue '{queue_name}' "
                f"(MessageId: {response.get('MessageId')})"
            )
        except Exception as e:
            logger.error(f"Failed to send message to '{queue_name}': {e}")
            raise
