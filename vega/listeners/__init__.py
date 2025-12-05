"""
Job queue listeners for background processing.

This module provides infrastructure for building background job processors
that listen to queues (SQS, RabbitMQ, Redis, etc.) and execute tasks asynchronously.

Quick Start:
    1. Define a listener:
        from vega.listeners import JobListener, job_listener, Message
        from vega.di import bind

        @job_listener(queue="email-queue", workers=3)
        class SendEmailListener(JobListener):
            @bind
            async def handle(self, message: Message, email_service: EmailService):
                await email_service.send(**message.body)

    2. Configure queue driver in config.py:
        from vega.listeners.drivers.sqs import SQSDriver
        from vega.listeners.driver import QueueDriver

        container = Container({
            QueueDriver: SQSDriver,
        })

    3. Run listeners:
        vega listener run

Core Components:
    - JobListener: Base class for listeners
    - @job_listener: Decorator to register listeners
    - QueueDriver: Abstract interface for queue backends
    - Message: Queue message data structure
    - MessageContext: Manual acknowledgment control

Available Drivers:
    - SQSDriver: AWS SQS (requires aioboto3)
    - More drivers coming soon (RabbitMQ, Redis, etc.)

See Also:
    - Discovery: vega.discovery.discover_listeners()
    - CLI: vega listener run, vega listener list
    - Generator: vega generate listener <name>
"""

from vega.listeners.listener import JobListener
from vega.listeners.decorators import job_listener
from vega.listeners.driver import QueueDriver
from vega.listeners.message import Message, MessageContext
from vega.listeners.manager import ListenerManager
from vega.listeners.job import Job
from vega.listeners.registry import (
    register_listener,
    get_listener_registry,
    clear_listener_registry
)

__all__ = [
    # Core classes
    'JobListener',
    'QueueDriver',
    'Message',
    'MessageContext',
    'ListenerManager',
    'Job',
    # Decorators
    'job_listener',
    # Registry functions
    'register_listener',
    'get_listener_registry',
    'clear_listener_registry',
]
