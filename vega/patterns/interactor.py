"""Interactor pattern for use cases"""
from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')


class InteractorMeta(ABCMeta):
    """
    Metaclass for Interactor that automatically calls call() method on instantiation.

    This allows for clean syntax:
        result = await CreateUser(name="John", email="john@example.com")

    Instead of:
        interactor = CreateUser(name="John", email="john@example.com")
        result = await interactor.call()

    Also supports @trigger decorator to automatically publish events after call() completes.
    """

    def __call__(cls, *args, **kwargs):
        """
        Create instance and call the call() method.

        If @trigger decorator is used, wraps call() to publish event after completion.

        Returns the result of call() method (usually a coroutine).
        """
        instance = super(InteractorMeta, cls).__call__(*args, **kwargs)
        call_result = instance.call()

        # Check if @trigger decorator was used
        if hasattr(cls, '_trigger_event'):
            # Wrap the coroutine to trigger event after completion
            return cls._wrap_with_event_trigger(call_result, cls._trigger_event)

        return call_result

    @staticmethod
    async def _wrap_with_event_trigger(call_coroutine, event_class):
        """
        Wrap call() coroutine to trigger event after it completes.

        Args:
            call_coroutine: The coroutine returned by call()
            event_class: The event class to instantiate and publish

        Returns:
            The result of call()
        """
        # Execute the call() method
        result = await call_coroutine

        # Trigger the event with the result
        try:
            # If result is a dict, unpack as kwargs
            if isinstance(result, dict):
                await event_class(**result)
            # If result is None, create event with no args
            elif result is None:
                await event_class()
            # Otherwise, pass result as first argument
            else:
                await event_class(result)
        except Exception as e:
            # Log but don't fail the interactor if event publishing fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to trigger event {event_class.__name__}: {e}")

        # Return the original result
        return result


class Interactor(Generic[T], metaclass=InteractorMeta):
    """
    Base class for use cases (business logic operations).

    An Interactor represents a single, focused business operation.
    It encapsulates the logic for one specific use case.

    Key principles:
    - Single responsibility: One interactor = one use case
    - Dependencies injected via @bind decorator on call() method
    - Constructor receives input parameters
    - call() method executes the logic and returns result

    Example:
        from vega.patterns import Interactor
        from vega.di import bind

        class CreateUser(Interactor[User]):
            def __init__(self, name: str, email: str):
                self.name = name
                self.email = email

            @bind
            async def call(self, repository: UserRepository) -> User:
                # Dependencies auto-injected by @bind
                user = User(name=self.name, email=self.email)
                return await repository.save(user)

        # Usage (metaclass auto-calls call())
        user = await CreateUser(name="John", email="john@example.com")
    """

    @abstractmethod
    async def call(self, **kwargs) -> T:
        """
        Execute the use case logic.

        Declare dependencies as type-hinted parameters for auto-injection.
        Use the @bind decorator to enable dependency injection.

        Args:
            **kwargs: Dependencies auto-injected by @bind decorator

        Returns:
            T: Result of the use case
        """
        raise NotImplementedError
