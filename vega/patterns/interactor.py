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
    """

    def __call__(cls, *args, **kwargs):
        """
        Create instance and call the call() method.

        Returns the result of call() method (usually a coroutine).
        """
        instance = super(InteractorMeta, cls).__call__(*args, **kwargs)
        return instance.call()


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
