"""Listener manager for lifecycle and orchestration"""
import asyncio
import logging
import signal
from typing import List, Type, Optional
from vega.listeners.listener import JobListener
from vega.listeners.driver import QueueDriver
from vega.listeners.message import Message, MessageContext
from vega.di import Summon, scope_context

logger = logging.getLogger(__name__)


class ListenerManager:
    """
    Manages lifecycle of all job listeners.

    Responsibilities:
    - Initialize queue driver connection
    - Start worker tasks for each listener
    - Handle graceful shutdown (SIGTERM, SIGINT)
    - Manage message polling and processing
    - Retry logic and error handling
    - Call lifecycle hooks (on_startup, on_shutdown, on_error)

    Example:
        from vega.discovery import discover_listeners
        from vega.listeners.manager import ListenerManager

        # Discover all listeners
        listener_classes = discover_listeners("infrastructure.listeners")

        # Create and start manager
        manager = ListenerManager(listener_classes)
        await manager.start()  # Blocks until shutdown signal
    """

    def __init__(self, listener_classes: List[Type[JobListener]]):
        """
        Initialize the listener manager.

        Args:
            listener_classes: List of listener classes to manage
        """
        self._listener_classes = listener_classes
        self._driver: Optional[QueueDriver] = None
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """
        Start all listeners.

        This method:
        1. Resolves QueueDriver from DI container
        2. Connects to queue service
        3. Sets up signal handlers for graceful shutdown
        4. Instantiates each listener
        5. Calls on_startup() hooks
        6. Creates worker tasks for each listener
        7. Waits for all tasks to complete or cancellation

        Blocks until shutdown signal is received.
        """
        # Resolve queue driver from DI container
        self._driver = Summon(QueueDriver)
        await self._driver.connect()

        logger.info(f"Starting {len(self._listener_classes)} listener(s)")

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Start all listener workers
        self._running = True
        tasks = []

        for listener_cls in self._listener_classes:
            # Instantiate listener (dependencies injected via DI if class uses @injectable)
            listener = listener_cls()

            # Get listener metadata
            queue = getattr(listener_cls, '_listener_queue')
            workers = getattr(listener_cls, '_listener_workers', 1)

            # Call startup hook
            try:
                await listener.on_startup()
            except Exception as e:
                logger.error(f"Error in on_startup hook for {listener_cls.__name__}: {e}")

            # Create worker tasks
            for worker_id in range(workers):
                task = asyncio.create_task(
                    self._run_worker(listener, listener_cls, worker_id)
                )
                tasks.append(task)
                logger.info(
                    f"Started worker {worker_id + 1}/{workers} "
                    f"for {listener_cls.__name__} (queue: {queue})"
                )

        self._tasks = tasks

        try:
            # Wait for all tasks
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Received cancellation signal")
        finally:
            await self.shutdown()

    async def _run_worker(
        self,
        listener: JobListener,
        listener_cls: Type[JobListener],
        worker_id: int
    ) -> None:
        """
        Run a single listener worker (poll loop).

        Args:
            listener: Listener instance
            listener_cls: Listener class (for metadata access)
            worker_id: Worker identifier
        """
        queue = getattr(listener_cls, '_listener_queue')
        auto_ack = getattr(listener_cls, '_listener_auto_ack', True)
        visibility_timeout = getattr(listener_cls, '_listener_visibility_timeout', 30)
        max_messages = getattr(listener_cls, '_listener_max_messages', 1)
        retry_on_error = getattr(listener_cls, '_listener_retry_on_error', False)
        max_retries = getattr(listener_cls, '_listener_max_retries', 3)

        logger.debug(
            f"Worker {worker_id} polling queue '{queue}' "
            f"(auto_ack={auto_ack}, visibility={visibility_timeout}s)"
        )

        while self._running:
            try:
                # Poll for messages (long polling with 10s wait for efficiency)
                messages = await self._driver.receive_messages(
                    queue_name=queue,
                    max_messages=max_messages,
                    visibility_timeout=visibility_timeout,
                    wait_time=10  # Long polling reduces API calls
                )

                if not messages:
                    continue  # No messages, continue polling

                # Process each message
                for message in messages:
                    await self._process_message(
                        listener,
                        listener_cls,
                        message,
                        queue,
                        auto_ack,
                        retry_on_error,
                        max_retries
                    )

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(
                    f"Worker {worker_id} error in poll loop: {e}",
                    exc_info=True
                )
                # Backoff on error to avoid tight error loops
                await asyncio.sleep(1)

    async def _process_message(
        self,
        listener: JobListener,
        listener_cls: Type[JobListener],
        message: Message,
        queue: str,
        auto_ack: bool,
        retry_on_error: bool,
        max_retries: int
    ) -> None:
        """
        Process a single message with retry logic.

        Args:
            listener: Listener instance
            listener_cls: Listener class
            message: Message to process
            queue: Queue name
            auto_ack: Auto-acknowledgment enabled
            retry_on_error: Retry on failure
            max_retries: Maximum retry attempts
        """
        context = MessageContext(
            message=message,
            driver=self._driver,
            queue_name=queue
        )

        # Store queue name in message attributes for driver
        message.attributes['queue_name'] = queue

        attempt = 0
        last_error = None

        while attempt <= (max_retries if retry_on_error else 0):
            try:
                # Use scope context for scoped dependencies
                with scope_context():
                    # Call handler with DI
                    if auto_ack:
                        # Auto-ack mode: only pass message
                        await listener.handle(message)
                    else:
                        # Manual mode: pass message and context
                        await listener.handle(message, context)

                # Success - acknowledge if auto-ack
                if auto_ack:
                    await context.ack()

                logger.debug(
                    f"Processed message {message.id} from queue '{queue}'"
                )
                return

            except Exception as e:
                last_error = e
                attempt += 1

                # Call error hook (don't let it break processing)
                try:
                    await listener.on_error(message, e)
                except Exception as hook_error:
                    logger.error(
                        f"Error in on_error hook: {hook_error}",
                        exc_info=True
                    )

                if attempt <= max_retries and retry_on_error:
                    # Retry with exponential backoff
                    backoff_time = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        f"Handler failed (attempt {attempt}/{max_retries + 1}): {e}. "
                        f"Retrying in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    # All retries exhausted or no retry enabled
                    logger.error(
                        f"Handler failed for message {message.id}: {e}",
                        exc_info=True
                    )

                    # Auto-reject on failure if auto-ack enabled
                    if auto_ack:
                        # Requeue if received count is low, else send to DLQ
                        requeue = message.received_count < 3
                        try:
                            await context.reject(requeue=requeue)
                            logger.debug(
                                f"Auto-rejected message {message.id} "
                                f"(requeue={requeue})"
                            )
                        except Exception as reject_error:
                            logger.error(
                                f"Failed to reject message: {reject_error}",
                                exc_info=True
                            )

                    break

    def _setup_signal_handlers(self) -> None:
        """
        Setup graceful shutdown on SIGTERM/SIGINT.

        Registers signal handlers that:
        1. Stop the running flag
        2. Cancel all worker tasks
        """
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating graceful shutdown")
            self.stop()

        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except (ValueError, OSError, RuntimeError, AttributeError) as e:
            # Windows / restricted environments may not support signal handling
            logger.debug(f"Signal handlers not installed: {e}")

    async def shutdown(self) -> None:
        """
        Gracefully shutdown all listeners.

        This method:
        1. Stops the running flag
        2. Calls on_shutdown() hooks for all listeners
        3. Disconnects from queue driver
        """
        logger.info("Shutting down listeners...")
        self._running = False

        # Call shutdown hooks
        for listener_cls in self._listener_classes:
            try:
                listener = listener_cls()
                await listener.on_shutdown()
            except Exception as e:
                logger.error(
                    f"Error in shutdown hook for {listener_cls.__name__}: {e}",
                    exc_info=True
                )

        # Disconnect driver
        if self._driver:
            try:
                await self._driver.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting driver: {e}", exc_info=True)

        logger.info("All listeners stopped")

    def stop(self) -> None:
        """
        Stop polling loop and cancel worker tasks.
        Safe to call multiple times.
        """
        self._running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()
