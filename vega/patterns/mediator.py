"""Mediator pattern for complex workflows"""
from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')


class MediatorMeta(ABCMeta):
    """
    Metaclass for Mediator that automatically calls call() method on instantiation.

    This allows for clean syntax:
        result = await CheckoutWorkflow(cart_id="123")

    Instead of:
        mediator = CheckoutWorkflow(cart_id="123")
        result = await mediator.call()
    """

    async def __call__(cls, *args, **kwargs):
        """
        Create instance and call the call() method.

        Returns the result of call() method (coroutine).
        """
        instance = super().__call__(*args, **kwargs)
        return await instance.call()


class Mediator(Generic[T], metaclass=MediatorMeta):
    """
    Base class for complex workflows that coordinate multiple use cases.

    A Mediator orchestrates multiple Interactors to accomplish a complex
    business operation. It represents a workflow or process.

    Key differences from Interactor:
    - Mediator: Orchestrates multiple use cases
    - Interactor: Single, focused business operation

    Example:
        from vega.patterns import Mediator

        class CheckoutWorkflow(Mediator[Order]):
            def __init__(self, cart_id: str, payment_method: str):
                self.cart_id = cart_id
                self.payment_method = payment_method

            async def call(self) -> Order:
                # Orchestrate multiple interactors
                cart = await GetCart(self.cart_id)
                order = await CreateOrder(cart.items)
                await ProcessPayment(order.id, self.payment_method)
                await SendConfirmationEmail(order.customer_email)
                return order

        # Usage (metaclass auto-calls call())
        order = await CheckoutWorkflow(cart_id="123", payment_method="stripe")

    Returns:
        T: Generic type that represents the return type of the mediator.
    """

    @abstractmethod
    async def call(self) -> T:
        """
        Execute the workflow logic.

        This method orchestrates multiple Interactors to accomplish
        a complex business operation.

        Returns:
            T: Result of the workflow
        """
        raise NotImplementedError
