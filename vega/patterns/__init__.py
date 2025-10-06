"""
Base patterns for Clean Architecture

Provides foundational classes for implementing Clean Architecture:
- Interactor: Single-purpose use cases
- Mediator: Complex workflows that coordinate multiple use cases
- Repository: Data persistence abstraction
- Service: External service abstraction

Example:
    from vega.patterns import Interactor, Repository
    from vega.di import bind

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

__all__ = [
    "Interactor",
    "Mediator",
    "Repository",
    "Service",
]
