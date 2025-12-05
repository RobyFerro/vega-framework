"""Functional tests for listener workflows"""
import pytest
import asyncio
from datetime import datetime
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from vega.listeners import JobListener, job_listener, Message, MessageContext
from vega.listeners.manager import ListenerManager
from vega.listeners.driver import QueueDriver
from vega.listeners.registry import clear_listener_registry, get_listener_registry
from vega.di import Container, bind, Scope, injectable, set_container


class MockQueueDriver(QueueDriver):
    """Mock queue driver for testing"""

    def __init__(self):
        self.messages: List[Message] = []
        self.acknowledged: List[str] = []
        self.rejected: List[tuple] = []
        self.extended: List[tuple] = []
        self.connected = False
        self.disconnected = False
        self._poll_count = 0

    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 1,
        visibility_timeout: int = 30,
        wait_time: int = 0
    ) -> List[Message]:
        """Return messages for the queue"""
        self._poll_count += 1

        # Return messages once, then empty list to prevent infinite loops
        if self._poll_count == 1 and self.messages:
            # Filter by queue if needed
            queue_messages = [m for m in self.messages if m.attributes.get('queue_name') == queue_name]
            return queue_messages[:max_messages]

        # Small delay to prevent tight loops in tests
        await asyncio.sleep(0.01)
        return []

    async def acknowledge(self, message: Message) -> None:
        """Record acknowledged message"""
        self.acknowledged.append(message.id)

    async def reject(
        self,
        message: Message,
        requeue: bool = True,
        visibility_timeout: Optional[int] = None
    ) -> None:
        """Record rejected message"""
        self.rejected.append((message.id, requeue, visibility_timeout))

    async def extend_visibility(self, message: Message, seconds: int) -> None:
        """Record visibility extension"""
        self.extended.append((message.id, seconds))

    async def get_queue_attributes(self, queue_name: str) -> dict:
        """Return mock queue attributes"""
        return {
            "ApproximateNumberOfMessages": len(self.messages),
            "QueueArn": f"arn:aws:sqs:us-east-1:123456789012:{queue_name}"
        }

    async def connect(self) -> None:
        """Mark as connected"""
        self.connected = True

    async def disconnect(self) -> None:
        """Mark as disconnected"""
        self.disconnected = True

    def add_message(self, queue_name: str, body: dict, message_id: str = "msg-123") -> Message:
        """Helper to add messages to the mock driver"""
        message = Message(
            id=message_id,
            body=body,
            attributes={"queue_name": queue_name},
            receipt_handle=f"receipt-{message_id}",
            received_count=1,
            timestamp=datetime.now()
        )
        self.messages.append(message)
        return message


@pytest.mark.functional
@pytest.mark.listeners
class TestListenerAutoAckWorkflow:
    """Test auto-acknowledgment workflow"""

    def setup_method(self):
        """Setup for each test"""
        clear_listener_registry()
        self.driver = MockQueueDriver()
        self.container = Container({QueueDriver: lambda: self.driver})
        set_container(self.container)

    def teardown_method(self):
        """Cleanup after each test"""
        clear_listener_registry()

    async def test_auto_ack_on_success(self):
        """Test message is auto-acknowledged on successful processing"""
        processed_messages = []

        @job_listener(queue="test-queue", auto_ack=True)
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                processed_messages.append(message.body)

        # Add message to driver
        self.driver.add_message("test-queue", {"data": "test"}, "msg-1")

        # Create and start manager
        manager = ListenerManager([TestListener])

        # Run for a short time
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.1)

        # Stop manager
        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify message was processed and acknowledged
        assert len(processed_messages) == 1
        assert processed_messages[0] == {"data": "test"}
        assert "msg-1" in self.driver.acknowledged

    async def test_auto_reject_on_error(self):
        """Test message is auto-rejected on processing error"""
        @job_listener(queue="test-queue", auto_ack=True)
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                raise ValueError("Processing failed")

        # Add message to driver
        self.driver.add_message("test-queue", {"data": "test"}, "msg-1")

        # Create and start manager
        manager = ListenerManager([TestListener])

        # Run for a short time
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.1)

        # Stop manager
        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify message was rejected
        assert len(self.driver.rejected) == 1
        assert self.driver.rejected[0][0] == "msg-1"
        assert self.driver.rejected[0][1] is True  # requeue=True (first attempt)


@pytest.mark.functional
@pytest.mark.listeners
class TestListenerManualAckWorkflow:
    """Test manual acknowledgment workflow"""

    def setup_method(self):
        """Setup for each test"""
        clear_listener_registry()
        self.driver = MockQueueDriver()
        self.container = Container({QueueDriver: lambda: self.driver})
        set_container(self.container)

    def teardown_method(self):
        """Cleanup after each test"""
        clear_listener_registry()

    async def test_manual_ack(self):
        """Test manual message acknowledgment"""
        @job_listener(queue="test-queue", auto_ack=False)
        class TestListener(JobListener):
            async def handle(self, message: Message, context: MessageContext) -> None:
                # Process and manually acknowledge
                await context.ack()

        # Add message to driver
        self.driver.add_message("test-queue", {"data": "test"}, "msg-1")

        # Create and start manager
        manager = ListenerManager([TestListener])

        # Run for a short time
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.1)

        # Stop manager
        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify manual acknowledgment
        assert "msg-1" in self.driver.acknowledged

    async def test_manual_reject_with_requeue(self):
        """Test manual rejection with requeue"""
        @job_listener(queue="test-queue", auto_ack=False)
        class TestListener(JobListener):
            async def handle(self, message: Message, context: MessageContext) -> None:
                # Simulate temporary error
                await context.reject(requeue=True)

        # Add message to driver
        self.driver.add_message("test-queue", {"data": "test"}, "msg-1")

        # Create and start manager
        manager = ListenerManager([TestListener])

        # Run for a short time
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.1)

        # Stop manager
        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify rejection with requeue
        assert len(self.driver.rejected) == 1
        assert self.driver.rejected[0] == ("msg-1", True, None)

    async def test_manual_reject_to_dlq(self):
        """Test manual rejection without requeue (send to DLQ)"""
        @job_listener(queue="test-queue", auto_ack=False)
        class TestListener(JobListener):
            async def handle(self, message: Message, context: MessageContext) -> None:
                # Simulate permanent error
                await context.reject(requeue=False)

        # Add message to driver
        self.driver.add_message("test-queue", {"data": "test"}, "msg-1")

        # Create and start manager
        manager = ListenerManager([TestListener])

        # Run for a short time
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.1)

        # Stop manager
        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify rejection without requeue
        assert len(self.driver.rejected) == 1
        assert self.driver.rejected[0] == ("msg-1", False, None)


@pytest.mark.functional
@pytest.mark.listeners
class TestListenerLifecycleHooks:
    """Test listener lifecycle hooks"""

    def setup_method(self):
        """Setup for each test"""
        clear_listener_registry()
        self.driver = MockQueueDriver()
        self.container = Container({QueueDriver: lambda: self.driver})
        set_container(self.container)

    def teardown_method(self):
        """Cleanup after each test"""
        clear_listener_registry()

    async def test_on_startup_hook(self):
        """Test on_startup hook is called"""
        startup_called = []

        @job_listener(queue="test-queue")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

            async def on_startup(self) -> None:
                startup_called.append(True)

        # Create and start manager
        manager = ListenerManager([TestListener])

        # Start and immediately stop
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.05)

        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify startup hook was called
        assert len(startup_called) == 1

    async def test_on_error_hook(self):
        """Test on_error hook is called on processing failure"""
        error_calls = []

        @job_listener(queue="test-queue", auto_ack=True)
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                raise ValueError("Test error")

            async def on_error(self, message: Message, error: Exception) -> None:
                error_calls.append((message.id, str(error)))

        # Add message to driver
        self.driver.add_message("test-queue", {"data": "test"}, "msg-1")

        # Create and start manager
        manager = ListenerManager([TestListener])

        # Run for a short time
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.1)

        # Stop manager
        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify error hook was called
        assert len(error_calls) == 1
        assert error_calls[0][0] == "msg-1"
        assert "Test error" in error_calls[0][1]


@pytest.mark.functional
@pytest.mark.listeners
class TestListenerWithDependencyInjection:
    """Test listener with dependency injection"""

    def setup_method(self):
        """Setup for each test"""
        clear_listener_registry()
        self.driver = MockQueueDriver()

    def teardown_method(self):
        """Cleanup after each test"""
        clear_listener_registry()

    async def test_listener_with_injected_dependencies(self):
        """Test listener with @bind decorator for dependency injection"""
        processed_data = []

        # Mock service
        @injectable(scope=Scope.SINGLETON)
        class EmailService:
            async def send(self, email: str, subject: str):
                processed_data.append({"email": email, "subject": subject})

        # Configure container
        container = Container({
            QueueDriver: lambda: self.driver,
            EmailService: EmailService
        })
        set_container(container)

        @job_listener(queue="email-queue")
        class SendEmailListener(JobListener):
            @bind
            async def handle(self, message: Message, email_service: EmailService) -> None:
                await email_service.send(**message.body)

        # Add message to driver
        self.driver.add_message("email-queue", {
            "email": "test@example.com",
            "subject": "Test"
        }, "msg-1")

        # Create and start manager
        manager = ListenerManager([SendEmailListener])

        # Run for a short time
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.1)

        # Stop manager
        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify dependency was injected and used
        assert len(processed_data) == 1
        assert processed_data[0]["email"] == "test@example.com"
        assert processed_data[0]["subject"] == "Test"


@pytest.mark.functional
@pytest.mark.listeners
class TestListenerManager:
    """Test ListenerManager orchestration"""

    def setup_method(self):
        """Setup for each test"""
        clear_listener_registry()
        self.driver = MockQueueDriver()
        self.container = Container({QueueDriver: lambda: self.driver})
        set_container(self.container)

    def teardown_method(self):
        """Cleanup after each test"""
        clear_listener_registry()

    async def test_manager_connects_driver(self):
        """Test manager connects to driver on start"""
        @job_listener(queue="test-queue")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        manager = ListenerManager([TestListener])

        # Start and immediately stop
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.05)

        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass

        # Verify driver was connected and disconnected
        assert self.driver.connected is True
        assert self.driver.disconnected is True

    async def test_manager_creates_multiple_workers(self):
        """Test manager creates multiple worker tasks"""
        workers_active = []

        @job_listener(queue="test-queue", workers=3)
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                workers_active.append(asyncio.current_task().get_name())

        # Add messages for workers
        for i in range(3):
            self.driver.add_message("test-queue", {"data": f"test-{i}"}, f"msg-{i}")

        manager = ListenerManager([TestListener])

        # Start and run briefly
        task = asyncio.create_task(manager.start())
        await asyncio.sleep(0.15)

        # Verify multiple tasks were created
        assert len(manager._tasks) == 3

        manager._running = False
        for t in manager._tasks:
            t.cancel()

        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.CancelledError:
            pass
