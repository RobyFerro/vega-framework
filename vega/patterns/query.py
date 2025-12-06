"""
Query pattern for CQRS (Command Query Responsibility Segregation)

Queries represent read operations that do NOT modify state. They are the "read" side
of CQRS, as opposed to commands which are the "write" side.

A QueryHandler is responsible for:
- Validating query parameters
- Fetching data from repositories or read models
- Transforming data into the desired output format
- Returning results WITHOUT side effects

Key principles:
- Queries should be idempotent (can be called multiple times with same result)
- Queries should NOT modify state
- Queries can bypass domain model for performance (read from denormalized views)

Note: QueryHandler is a type alias to Interactor, maintaining the same
metaclass auto-call behavior and dependency injection support.

Example:
    from dataclasses import dataclass
    from vega.patterns import QueryHandler
    from vega.di import bind

    @dataclass(frozen=True)
    class GetOrderByIdQuery:
        order_id: str

    @dataclass
    class OrderDetails:
        id: str
        customer_name: str
        items: List[OrderItemView]
        total: float

    class GetOrderByIdHandler(QueryHandler[OrderDetails]):
        def __init__(self, query: GetOrderByIdQuery):
            self.query = query

        @bind
        async def call(
            self,
            repository: OrderRepository
        ) -> OrderDetails:
            order = await repository.get_by_id(self.query.order_id)
            if not order:
                raise NotFoundException(f"Order {self.query.order_id} not found")

            return OrderDetails(
                id=order.id,
                customer_name=order.customer.name,
                items=[...],
                total=order.total_amount
            )

    # Usage (metaclass auto-calls call() method):
    query = GetOrderByIdQuery(order_id="123")
    result = await GetOrderByIdHandler(query)
"""

from typing import TypeAlias
from vega.patterns.interactor import Interactor

# QueryHandler is a semantic alias to Interactor
# This maintains the metaclass auto-call behavior and DI support
# while providing clear CQRS semantics
QueryHandler: TypeAlias = Interactor

__all__ = ["QueryHandler"]
