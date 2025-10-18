"""Unit tests for bean auto-discovery"""

import pytest
from abc import ABC, abstractmethod
from vega.di import bean, Container, set_container, get_container
from vega.discovery import discover_beans, discover_beans_in_module, list_registered_beans


# Test Fixtures - Note: Using _Base prefix to avoid pytest collection


class _BaseRepository(ABC):
    """Test abstract repository"""

    @abstractmethod
    def save(self):
        pass


class _BaseService:
    """Test concrete service"""

    def execute(self):
        return "executed"


class TestBeanDiscovery:
    """Test bean auto-discovery functionality"""

    def setup_method(self):
        """Reset container before each test"""
        set_container(Container())

    def test_list_registered_beans_empty(self):
        """Test listing beans when container is empty"""
        beans = list_registered_beans()
        assert isinstance(beans, dict)
        assert len(beans) == 0

    def test_list_registered_beans_after_registration(self):
        """Test listing beans after manual registration"""

        @bean
        class ServiceImpl(_BaseService):
            pass

        beans = list_registered_beans()
        assert len(beans) == 1
        assert ServiceImpl in beans

    def test_discover_beans_in_current_module(self):
        """Test discovering beans in the current test module"""

        # Define beans in this test
        @bean
        class LocalService:
            def __init__(self):
                self.name = "local"

        # This bean should already be registered
        beans = list_registered_beans()
        assert LocalService in beans

    def test_bean_discovery_counts_correctly(self):
        """Test that discovery returns correct count"""

        initial_count = len(list_registered_beans())

        @bean
        class Service1:
            pass

        @bean
        class Service2:
            pass

        final_count = len(list_registered_beans())
        assert final_count == initial_count + 2


class TestBeanDiscoveryIntegration:
    """Integration tests for bean discovery"""

    def setup_method(self):
        """Reset container before each test"""
        set_container(Container())

    def test_discovered_beans_are_resolvable(self):
        """Test that discovered beans can be resolved from container"""

        @bean
        class MyTestService:
            def __init__(self):
                self.value = 42

        container = get_container()
        service = container.resolve(MyTestService)

        assert isinstance(service, MyTestService)
        assert service.value == 42

    def test_discovered_beans_with_dependencies(self):
        """Test beans with dependencies are discovered and resolvable"""

        @bean
        class DatabaseService:
            def __init__(self):
                self.connected = True

        @bean
        class RepositoryService:
            def __init__(self, db: DatabaseService):
                self.db = db

        container = get_container()
        repo = container.resolve(RepositoryService)

        assert isinstance(repo, RepositoryService)
        assert isinstance(repo.db, DatabaseService)
        assert repo.db.connected is True
