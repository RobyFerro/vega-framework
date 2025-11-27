"""Listener command - Manage job queue listeners"""
import sys
import asyncio
from pathlib import Path
import click


@click.group()
def listener():
    """Manage job queue listeners

    Commands to run and manage job queue listeners for your Vega project.
    Listeners process messages from queues (SQS, RabbitMQ, Redis, etc.).

    Example:
        vega listener run              # Start all listeners
        vega listener list             # List registered listeners
    """
    pass


@listener.command()
@click.option('--path', default='.', help='Path to Vega project (default: current directory)')
def run(path: str):
    """Start all discovered job listeners

    This command:
    1. Validates the Vega project structure
    2. Initializes the DI container
    3. Auto-discovers listeners from infrastructure/listeners/
    4. Starts all listener workers
    5. Runs until SIGTERM/SIGINT (Ctrl+C)

    The queue driver (SQS, RabbitMQ, etc.) must be registered in config.py:

        from vega.listeners.drivers.sqs import SQSDriver
        from vega.listeners.driver import QueueDriver

        container = Container({
            QueueDriver: SQSDriver,
        })

    Examples:
        vega listener run
        vega listener run --path ./my-project

    Note:
        - Graceful shutdown on SIGTERM/SIGINT
        - Long polling for efficiency
        - Concurrent workers per listener
        - Auto-acknowledgment or manual control
    """
    project_path = Path(path).resolve()

    # Validate Vega project
    if not (project_path / "config.py").exists():
        click.echo(click.style("ERROR: Not a Vega project (config.py not found)", fg='red'))
        click.echo(f"Path checked: {project_path}")
        click.echo("\nRun 'vega init <project-name>' to create a new Vega project.")
        sys.exit(1)

    # Add project to sys.path
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))

    # Initialize DI container
    try:
        import config  # noqa: F401
        click.echo(click.style("✓ DI container initialized", fg='green'))
    except ImportError as e:
        click.echo(click.style(f"ERROR: Failed to load config.py: {e}", fg='red'))
        click.echo("\nMake sure config.py exists in the project root")
        sys.exit(1)

    # Import discovery utilities
    try:
        from vega.discovery import discover_listeners
        from vega.listeners.manager import ListenerManager
        from vega.listeners.driver import QueueDriver
        from vega.di import Summon
    except ImportError as e:
        click.echo(click.style(f"ERROR: Failed to import Vega listeners: {e}", fg='red'))
        click.echo("\nMake sure vega-framework is properly installed")
        sys.exit(1)

    # Check if QueueDriver is registered
    try:
        driver = Summon(QueueDriver)
        click.echo(click.style(f"✓ Queue driver configured: {driver.__class__.__name__}", fg='green'))
    except Exception as e:
        click.echo(click.style("ERROR: QueueDriver not registered in DI container", fg='red'))
        click.echo("\nRegister a queue driver in config.py:")
        click.echo(click.style("""
    from vega.listeners.drivers.sqs import SQSDriver
    from vega.listeners.driver import QueueDriver

    container = Container({
        QueueDriver: SQSDriver,
    })
        """, fg='cyan'))
        click.echo(f"\nDetails: {e}")
        sys.exit(1)

    # Discover listeners
    try:
        listener_classes = discover_listeners(
            "infrastructure",
            listeners_subpackage="listeners"
        )

        if not listener_classes:
            click.echo(click.style("WARNING: No listeners found", fg='yellow'))
            click.echo("\nCreate listeners in infrastructure/listeners/")
            click.echo("Example:")
            click.echo(click.style("  vega generate listener SendEmail", fg='cyan'))
            sys.exit(0)

        click.echo(click.style(
            f"✓ Discovered {len(listener_classes)} listener(s)",
            fg='green'
        ))

        for listener_cls in listener_classes:
            queue = getattr(listener_cls, '_listener_queue', 'unknown')
            workers = getattr(listener_cls, '_listener_workers', 1)
            auto_ack = getattr(listener_cls, '_listener_auto_ack', True)
            click.echo(
                f"  - {listener_cls.__name__} "
                f"(queue: {queue}, workers: {workers}, auto_ack: {auto_ack})"
            )

    except Exception as e:
        click.echo(click.style(f"ERROR: Failed to discover listeners: {e}", fg='red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Create and start manager
    click.echo(f"\nStarting job listeners...")
    click.echo(click.style("Press Ctrl+C to stop", fg='yellow'))

    try:
        manager = ListenerManager(listener_classes)
        asyncio.run(manager.start())
    except KeyboardInterrupt:
        click.echo(click.style("\n\nShutdown initiated by user", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\nERROR: {e}", fg='red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)


@listener.command()
@click.option('--path', default='.', help='Path to Vega project (default: current directory)')
def list(path: str):
    """List all registered listeners

    Displays information about discovered listeners including:
    - Listener class name
    - Queue name
    - Number of workers
    - Auto-acknowledgment setting
    - Module location

    Example:
        vega listener list
        vega listener list --path ./my-project

    Output example:
        Registered Listeners (3):
        ------------------------------------------------------------

        SendEmailListener
          Queue: email-notifications
          Workers: 3
          Auto-ack: True
          Module: infrastructure.listeners.send_email_listener

        ProcessOrderListener
          Queue: order-processing
          Workers: 5
          Auto-ack: False
          Module: infrastructure.listeners.process_order_listener
    """
    project_path = Path(path).resolve()

    # Validate Vega project
    if not (project_path / "config.py").exists():
        click.echo(click.style("ERROR: Not a Vega project", fg='red'))
        sys.exit(1)

    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))

    try:
        import config  # noqa: F401
        from vega.discovery import discover_listeners

        listener_classes = discover_listeners(
            "infrastructure",
            listeners_subpackage="listeners"
        )

        if not listener_classes:
            click.echo("No listeners registered")
            click.echo("\nCreate listeners with:")
            click.echo(click.style("  vega generate listener <name>", fg='cyan'))
            return

        click.echo(f"\nRegistered Listeners ({len(listener_classes)}):")
        click.echo("-" * 60)

        for listener_cls in listener_classes:
            queue = getattr(listener_cls, '_listener_queue', 'unknown')
            workers = getattr(listener_cls, '_listener_workers', 1)
            auto_ack = getattr(listener_cls, '_listener_auto_ack', True)
            visibility_timeout = getattr(listener_cls, '_listener_visibility_timeout', 30)
            retry = getattr(listener_cls, '_listener_retry_on_error', False)
            max_retries = getattr(listener_cls, '_listener_max_retries', 3)

            click.echo(f"\n{listener_cls.__name__}")
            click.echo(f"  Queue: {queue}")
            click.echo(f"  Workers: {workers}")
            click.echo(f"  Auto-ack: {auto_ack}")
            click.echo(f"  Visibility timeout: {visibility_timeout}s")
            click.echo(f"  Retry on error: {retry}")
            if retry:
                click.echo(f"  Max retries: {max_retries}")
            click.echo(f"  Module: {listener_cls.__module__}")

        click.echo()

    except Exception as e:
        click.echo(click.style(f"ERROR: {e}", fg='red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)
