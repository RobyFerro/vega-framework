"""Dependency Injection configuration for test-router-project"""
from vega.di import Container, set_container

# Domain interfaces (Abstract)
# Example:
# from test-router-project.domain.repositories.user_repository import UserRepository

# Infrastructure implementations (Concrete)
# Example:
# from test-router-project.infrastructure.repositories.memory_user_repository import MemoryUserRepository

# DI Registry: Map interfaces to implementations
SERVICES = {
    # Example:
    # UserRepository: MemoryUserRepository,
}

# Create and set container
container = Container(SERVICES)
set_container(container)
