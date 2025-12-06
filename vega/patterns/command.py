"""
Command pattern for CQRS (Command Query Responsibility Segregation)

Commands represent write operations that modify state. They are the "write" side
of CQRS, as opposed to queries which are the "read" side.

A CommandHandler is responsible for:
- Validating command input
- Executing business logic
- Modifying aggregate state
- Persisting changes
- Publishing domain events (if applicable)

Note: CommandHandler is a type alias to Interactor, maintaining the same
metaclass auto-call behavior and dependency injection support.

Example:
    from dataclasses import dataclass
    from vega.patterns import CommandHandler
    from vega.di import bind

    @dataclass(frozen=True)
    class CreateOrderCommand:
        customer_id: str
        items: List[OrderItem]

    @dataclass
    class CreateOrderResult:
        order_id: str
        total: float

    class CreateOrderHandler(CommandHandler[CreateOrderResult]):
        def __init__(self, command: CreateOrderCommand):
            self.command = command

        @bind
        async def call(
            self,
            repository: OrderRepository
        ) -> CreateOrderResult:
            order = Order.create(
                customer_id=self.command.customer_id,
                items=self.command.items
            )
            saved = await repository.save(order)
            return CreateOrderResult(
                order_id=saved.id,
                total=saved.total_amount
            )

    # Usage (metaclass auto-calls call() method):
    command = CreateOrderCommand(customer_id="123", items=[...])
    result = await CreateOrderHandler(command)
"""

from typing import TypeAlias
from vega.patterns.interactor import Interactor

# CommandHandler is a semantic alias to Interactor
# This maintains the metaclass auto-call behavior and DI support
# while providing clear CQRS semantics
CommandHandler: TypeAlias = Interactor

__all__ = ["CommandHandler"]
