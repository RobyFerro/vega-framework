"""Unit tests for job listener system"""
import pytest
from datetime import datetime
from typing import Optional
from vega.listeners import JobListener, job_listener, Message, MessageContext
from vega.listeners.registry import (
    register_listener,
    get_listener_registry,
    clear_listener_registry
)


@pytest.mark.unit
@pytest.mark.listeners
class TestJobListenerDecorator:
    """Test @job_listener decorator"""

    def setup_method(self):
        """Clear registry before each test"""
        clear_listener_registry()

    def teardown_method(self):
        """Clear registry after each test"""
        clear_listener_registry()

    def test_decorator_registers_listener(self):
        """Test that decorator registers listener in global registry"""
        @job_listener(queue="test-queue")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        registry = get_listener_registry()
        assert len(registry) == 1
        assert TestListener in registry

    def test_decorator_stores_metadata(self):
        """Test that decorator stores configuration metadata on class"""
        @job_listener(
            queue="my-queue",
            workers=5,
            auto_ack=False,
            visibility_timeout=60,
            max_messages=10,
            retry_on_error=True,
            max_retries=3
        )
        class TestListener(JobListener):
            async def handle(self, message: Message, context: MessageContext) -> None:
                pass

        assert TestListener._listener_queue == "my-queue"
        assert TestListener._listener_workers == 5
        assert TestListener._listener_auto_ack is False
        assert TestListener._listener_visibility_timeout == 60
        assert TestListener._listener_max_messages == 10
        assert TestListener._listener_retry_on_error is True
        assert TestListener._listener_max_retries == 3
        assert TestListener._is_job_listener is True

    def test_decorator_default_values(self):
        """Test decorator default configuration values"""
        @job_listener(queue="test-queue")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        assert TestListener._listener_queue == "test-queue"
        assert TestListener._listener_workers == 1
        assert TestListener._listener_auto_ack is True
        assert TestListener._listener_visibility_timeout == 30
        assert TestListener._listener_max_messages == 1
        assert TestListener._listener_retry_on_error is False
        assert TestListener._listener_max_retries == 3

    def test_decorator_validates_base_class(self):
        """Test that decorator raises error if class doesn't inherit from JobListener"""
        with pytest.raises(TypeError, match="must inherit from JobListener"):
            @job_listener(queue="test-queue")
            class NotAListener:
                async def handle(self, message: Message) -> None:
                    pass

    def test_multiple_listeners_registered(self):
        """Test registering multiple listeners"""
        @job_listener(queue="queue-1")
        class Listener1(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        @job_listener(queue="queue-2")
        class Listener2(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        @job_listener(queue="queue-3")
        class Listener3(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        registry = get_listener_registry()
        assert len(registry) == 3
        assert Listener1 in registry
        assert Listener2 in registry
        assert Listener3 in registry


@pytest.mark.unit
@pytest.mark.listeners
class TestListenerRegistry:
    """Test listener registry functions"""

    def setup_method(self):
        """Clear registry before each test"""
        clear_listener_registry()

    def teardown_method(self):
        """Clear registry after each test"""
        clear_listener_registry()

    def test_register_listener(self):
        """Test manual listener registration"""
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        register_listener(TestListener)
        registry = get_listener_registry()
        assert TestListener in registry

    def test_get_empty_registry(self):
        """Test getting empty registry"""
        registry = get_listener_registry()
        assert len(registry) == 0
        assert isinstance(registry, list)

    def test_clear_registry(self):
        """Test clearing registry"""
        @job_listener(queue="test")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        assert len(get_listener_registry()) == 1
        clear_listener_registry()
        assert len(get_listener_registry()) == 0

    def test_registry_returns_copy(self):
        """Test that registry returns a copy, not the original list"""
        @job_listener(queue="test")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        registry1 = get_listener_registry()
        registry2 = get_listener_registry()

        # Should be different objects
        assert registry1 is not registry2
        # But same content
        assert registry1 == registry2


@pytest.mark.unit
@pytest.mark.listeners
class TestMessage:
    """Test Message data structure"""

    def test_message_creation(self):
        """Test creating a Message instance"""
        timestamp = datetime.now()
        message = Message(
            id="msg-123",
            body={"key": "value", "number": 42},
            attributes={"attr1": "val1"},
            receipt_handle="receipt-456",
            received_count=1,
            timestamp=timestamp
        )

        assert message.id == "msg-123"
        assert message.body == {"key": "value", "number": 42}
        assert message.attributes == {"attr1": "val1"}
        assert message.receipt_handle == "receipt-456"
        assert message.received_count == 1
        assert message.timestamp == timestamp

    def test_message_data_property(self):
        """Test that message.data is an alias for message.body"""
        message = Message(
            id="msg-123",
            body={"test": "data"},
            attributes={},
            receipt_handle="receipt-456",
            received_count=1,
            timestamp=datetime.now()
        )

        assert message.data == message.body
        assert message.data == {"test": "data"}


@pytest.mark.unit
@pytest.mark.listeners
class TestMessageContext:
    """Test MessageContext acknowledgment controls"""

    @pytest.fixture
    def mock_driver(self):
        """Create a mock QueueDriver"""
        from unittest.mock import AsyncMock, MagicMock

        driver = MagicMock()
        driver.acknowledge = AsyncMock()
        driver.reject = AsyncMock()
        driver.extend_visibility = AsyncMock()
        return driver

    @pytest.fixture
    def sample_message(self):
        """Create a sample message"""
        return Message(
            id="msg-123",
            body={"test": "data"},
            attributes={},
            receipt_handle="receipt-456",
            received_count=1,
            timestamp=datetime.now()
        )

    async def test_ack(self, mock_driver, sample_message):
        """Test message acknowledgment"""
        context = MessageContext(
            message=sample_message,
            driver=mock_driver,
            queue_name="test-queue"
        )

        await context.ack()

        mock_driver.acknowledge.assert_called_once_with(sample_message)

    async def test_reject_with_requeue(self, mock_driver, sample_message):
        """Test message rejection with requeue"""
        context = MessageContext(
            message=sample_message,
            driver=mock_driver,
            queue_name="test-queue"
        )

        await context.reject(requeue=True)

        mock_driver.reject.assert_called_once_with(
            sample_message,
            requeue=True,
            visibility_timeout=None
        )

    async def test_reject_without_requeue(self, mock_driver, sample_message):
        """Test message rejection without requeue (send to DLQ)"""
        context = MessageContext(
            message=sample_message,
            driver=mock_driver,
            queue_name="test-queue"
        )

        await context.reject(requeue=False)

        mock_driver.reject.assert_called_once_with(
            sample_message,
            requeue=False,
            visibility_timeout=None
        )

    async def test_reject_with_custom_visibility(self, mock_driver, sample_message):
        """Test message rejection with custom visibility timeout"""
        context = MessageContext(
            message=sample_message,
            driver=mock_driver,
            queue_name="test-queue"
        )

        await context.reject(requeue=True, visibility_timeout=60)

        mock_driver.reject.assert_called_once_with(
            sample_message,
            requeue=True,
            visibility_timeout=60
        )

    async def test_extend_visibility(self, mock_driver, sample_message):
        """Test extending message visibility timeout"""
        context = MessageContext(
            message=sample_message,
            driver=mock_driver,
            queue_name="test-queue"
        )

        await context.extend_visibility(300)

        mock_driver.extend_visibility.assert_called_once_with(sample_message, 300)


@pytest.mark.unit
@pytest.mark.listeners
class TestJobListener:
    """Test JobListener base class"""

    def test_listener_is_abstract(self):
        """Test that JobListener cannot be instantiated directly"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            JobListener()

    def test_listener_requires_handle_implementation(self):
        """Test that subclasses must implement handle() method"""
        class IncompleteListener(JobListener):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteListener()

    async def test_listener_lifecycle_hooks_are_optional(self):
        """Test that lifecycle hooks have default implementations"""
        @job_listener(queue="test")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        listener = TestListener()

        # Should not raise errors
        await listener.on_startup()
        await listener.on_shutdown()
        await listener.on_error(
            Message(
                id="test",
                body={},
                attributes={},
                receipt_handle="test",
                received_count=1,
                timestamp=datetime.now()
            ),
            Exception("test error")
        )

    async def test_listener_handle_signature(self):
        """Test that handle method can be called with message"""
        @job_listener(queue="test")
        class TestListener(JobListener):
            def __init__(self):
                self.messages_handled = []

            async def handle(self, message: Message) -> None:
                self.messages_handled.append(message)

        listener = TestListener()
        message = Message(
            id="msg-123",
            body={"test": "data"},
            attributes={},
            receipt_handle="receipt-456",
            received_count=1,
            timestamp=datetime.now()
        )

        await listener.handle(message)

        assert len(listener.messages_handled) == 1
        assert listener.messages_handled[0] == message
