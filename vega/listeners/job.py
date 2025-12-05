"""Job scheduling for async listeners"""
from typing import Any
from vega.listeners.driver import QueueDriver
from vega.di import Summon


class Job:
    """
    Simple job scheduling interface (Laravel-style).

    Schedule jobs to be processed asynchronously by listeners.

    Example:
        # Schedule a job
        await Job.schedule(
            queue="email-notifications",
            to="user@example.com",
            subject="Welcome!",
            template="welcome",
            context={"name": "John Doe"}
        )

        # Listener processes it
        @job_listener(queue="email-notifications")
        class EmailListener(JobListener):
            @bind
            async def handle(self, message: Message, email_service: EmailService):
                # message.body = {"to": "...", "subject": "...", "template": "...", "context": {...}}
                await email_service.send(**message.body)

    Usage:
        The kwargs passed to schedule() become the message body that the
        listener receives in message.body.
    """

    @staticmethod
    async def schedule(queue: str, **data: Any) -> None:
        """
        Schedule a job to be processed by a listener.

        Args:
            queue: Name of the queue to send the job to
            **data: Job data as keyword arguments (becomes message.body)

        Raises:
            Exception: If the queue driver is not configured or sending fails

        Example:
            await Job.schedule(
                queue="order-processing",
                order_id="12345",
                user_id="67890",
                items=[{"sku": "ABC", "qty": 2}]
            )
        """
        driver = Summon(QueueDriver)
        await driver.send_message(queue_name=queue, body=data)
