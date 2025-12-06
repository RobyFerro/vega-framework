"""
Base patterns for Clean Architecture and Domain-Driven Design

Provides foundational classes for implementing Clean Architecture and DDD:

Clean Architecture Patterns:
- Interactor: Single-purpose use cases
- Mediator: Complex workflows that coordinate multiple use cases
- Repository: Data persistence abstraction
- Service: External service abstraction

Domain-Driven Design Patterns:
- AggregateRoot: Aggregate root entity with identity
- CommandHandler: CQRS command handler (write operations)
- QueryHandler: CQRS query handler (read operations)

Example:
    from vega.patterns import Interactor, Repository, AggregateRoot
    from vega.di import bind
    from dataclasses import dataclass

    @dataclass
    class Order(AggregateRoot[str]):
        id: str
        total: float

    class UserRepository(Repository[User]):
        @abstractmethod
        async def find_by_email(self, email: str) -> Optional[User]:
            pass

    class CreateUser(Interactor[User]):
        def __init__(self, name: str, email: str):
            self.name = name
            self.email = email

        @bind
        async def call(self, repository: UserRepository) -> User:
            user = User(name=self.name, email=self.email)
            return await repository.save(user)
"""

from vega.patterns.interactor import Interactor
from vega.patterns.mediator import Mediator
from vega.patterns.repository import Repository
from vega.patterns.service import Service
from vega.patterns.aggregate import AggregateRoot
from vega.patterns.command import CommandHandler
from vega.patterns.query import QueryHandler

__all__ = [
    "Interactor",
    "Mediator",
    "Repository",
    "Service",
    "AggregateRoot",
    "CommandHandler",
    "QueryHandler",
]
