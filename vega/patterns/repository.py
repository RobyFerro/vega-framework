"""Repository pattern for data persistence"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    Base repository interface for data persistence.

    Repository pattern provides abstraction over data persistence,
    allowing domain layer to remain independent of infrastructure.

    Key principles:
    - Abstract interface defined in domain layer
    - Concrete implementations in infrastructure layer
    - Generic type T represents the entity type

    Example:
        from vega.patterns import Repository

        # Domain layer: Abstract interface
        class UserRepository(Repository[User]):
            @abstractmethod
            async def find_by_email(self, email: str) -> Optional[User]:
                pass

            @abstractmethod
            async def find_active_users(self) -> List[User]:
                pass

        # Infrastructure layer: Concrete implementation
        class PostgresUserRepository(UserRepository):
            async def get(self, id: str) -> Optional[User]:
                # PostgreSQL specific implementation
                pass

            async def save(self, user: User) -> User:
                # PostgreSQL specific implementation
                pass

            async def find_by_email(self, email: str) -> Optional[User]:
                # PostgreSQL specific implementation
                pass
    """
    pass
