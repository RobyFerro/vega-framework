"""
Aggregate pattern for Domain-Driven Design

An aggregate is a cluster of domain objects that can be treated as a single unit.
The aggregate root is the only member of the aggregate that outside objects are
allowed to hold references to.

Key principles:
- All access goes through the root
- Identity: Each aggregate has a unique identifier
- Consistency boundary: Changes within an aggregate are atomic
- External references only to the root, never to internal members

Example:
    from dataclasses import dataclass
    from vega.patterns import AggregateRoot

    @dataclass
    class Order(AggregateRoot[str]):
        id: str
        customer_id: str
        total_amount: float

        def __post_init__(self):
            if not self.id:
                raise ValueError("Order must have an ID")
            if self.total_amount < 0:
                raise ValueError("Total amount cannot be negative")
"""

from abc import ABC
from typing import TypeVar, Generic

T = TypeVar('T')


class AggregateRoot(ABC, Generic[T]):
    """
    Base class for aggregate roots in Domain-Driven Design.

    An aggregate is a cluster of domain objects that can be treated as a single unit.
    The aggregate root is the entry point and ensures consistency.

    Type parameter T represents the type of the aggregate's ID (str, UUID, int, etc.)

    Example:
        @dataclass
        class Order(AggregateRoot[str]):
            id: str
            items: List[OrderItem]

            def add_item(self, item: OrderItem):
                self.items.append(item)
                # Validate invariants
                if len(self.items) > 100:
                    raise ValueError("Order cannot have more than 100 items")
    """
    pass
