"""Unit tests for @bean decorator"""

import pytest
from abc import ABC, abstractmethod
from vega.di import (
    bean,
    is_bean,
    get_bean_metadata,
    Container,
    get_container,
    set_container,
    Scope,
    DependencyInjectionError,
    Summon,
    clear_singletons,
    clear_scoped,
)
from vega.patterns import Repository, Service
from typing import Optional


# Test Fixtures: Abstract Interfaces (ABC-based)


class UserRepository(ABC):
    """Abstract user repository interface"""

    @abstractmethod
    def find_all(self):
        pass


class AuditableRepository(ABC):
    """Abstract auditable repository interface"""

    @abstractmethod
    def audit_log(self):
        pass


class ProductRepository(ABC):
    """Abstract product repository interface"""

    @abstractmethod
    def find_by_id(self, product_id: str):
        pass


# Test Fixtures: Pattern-based Interfaces (Repository and Service)


class User:
    """Simple User entity"""
    def __init__(self, id: str, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email


class UserPatternRepository(Repository[User]):
    """Abstract user repository using Repository pattern"""

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass


class EmailService(Service):
    """Abstract email service using Service pattern"""

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> bool:
        pass


# Test Fixtures: Concrete Classes


class DatabaseManager:
    """Concrete database manager"""

    def __init__(self, url: str = "sqlite:///:memory:"):
        self.url = url
        self.connected = True


class ConfigService:
    """Concrete configuration service"""

    def __init__(self):
        self.config = {"app": "test"}


class CacheService:
    """Concrete cache service"""

    def __init__(self, ttl: int = 300):
        self.ttl = ttl


# Test Fixtures: Implementations


class SqlUserRepository(UserRepository):
    """SQL implementation of UserRepository"""

    def __init__(self, db: DatabaseManager):
        self._db = db

    def find_all(self):
        return []


class MemoryUserRepository(UserRepository):
    """Memory implementation of UserRepository"""

    def __init__(self):
        self._users = []

    def find_all(self):
        return self._users


class MultiInterfaceRepository(UserRepository, AuditableRepository):
    """Repository implementing multiple interfaces"""

    def __init__(self):
        self._data = []

    def find_all(self):
        return self._data

    def audit_log(self):
        return []


# Test Classes


class TestBeanBasicRegistration:
    """Test basic @bean registration functionality"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_bean_with_abc_interface(self):
        """Test @bean registers class with ABC interface"""

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self):
                pass

            def find_all(self):
                return []

        container = get_container()
        assert UserRepository in container._services
        assert container._services[UserRepository] == TestUserRepo

    def test_bean_concrete_class_no_interface(self):
        """Test @bean registers concrete class without interface"""

        @bean
        class TestConfigService:
            def __init__(self):
                self.config = {}

        container = get_container()
        assert TestConfigService in container._services
        assert container._services[TestConfigService] == TestConfigService

    def test_bean_metadata_stored(self):
        """Test @bean stores metadata on the class"""

        @bean
        class TestService:
            pass

        assert is_bean(TestService)
        metadata = get_bean_metadata(TestService)
        assert metadata is not None
        assert metadata['registered'] is True
        assert metadata['interface'] == TestService
        assert metadata['scope'] == Scope.SCOPED

    def test_non_bean_class_metadata(self):
        """Test non-bean class has no metadata"""

        class RegularClass:
            pass

        assert not is_bean(RegularClass)
        assert get_bean_metadata(RegularClass) is None


class TestBeanScopeConfiguration:
    """Test @bean scope configuration"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_default_scope_is_scoped(self):
        """Test default scope is SCOPED"""

        @bean
        class TestService:
            pass

        metadata = get_bean_metadata(TestService)
        assert metadata['scope'] == Scope.SCOPED

    def test_singleton_scope_override(self):
        """Test @bean with SINGLETON scope"""

        @bean(scope=Scope.SINGLETON)
        class SingletonService:
            pass

        metadata = get_bean_metadata(SingletonService)
        assert metadata['scope'] == Scope.SINGLETON

    def test_transient_scope_override(self):
        """Test @bean with TRANSIENT scope"""

        @bean(scope=Scope.TRANSIENT)
        class TransientService:
            pass

        metadata = get_bean_metadata(TransientService)
        assert metadata['scope'] == Scope.TRANSIENT


class TestBeanConstructorParameters:
    """Test @bean with constructor parameters"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_bean_with_constructor_params(self):
        """Test @bean with constructor parameters"""

        @bean(url="postgresql://localhost/test")
        class TestDatabaseManager:
            def __init__(self, url: str):
                self.url = url

        container = get_container()
        assert TestDatabaseManager in container._services

        # Verify the factory is registered
        factory = container._services[TestDatabaseManager]
        assert factory is not None

    def test_bean_with_multiple_constructor_params(self):
        """Test @bean with multiple constructor parameters"""

        @bean(host="localhost", port=5432, timeout=30)
        class DatabaseConnection:
            def __init__(self, host: str, port: int, timeout: int):
                self.host = host
                self.port = port
                self.timeout = timeout

        container = get_container()
        assert DatabaseConnection in container._services


class TestBeanMultipleInterfaces:
    """Test @bean with multiple interfaces"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_multiple_interfaces_without_explicit_raises_error(self):
        """Test @bean with multiple interfaces raises error without explicit interface"""

        with pytest.raises(DependencyInjectionError) as exc_info:

            @bean
            class TestMultiRepo(UserRepository, AuditableRepository):
                def find_all(self):
                    return []

                def audit_log(self):
                    return []

        assert "multiple interfaces" in str(exc_info.value).lower()
        assert "UserRepository" in str(exc_info.value)
        assert "AuditableRepository" in str(exc_info.value)

    def test_multiple_interfaces_with_explicit_interface(self):
        """Test @bean with explicit interface parameter for multiple interfaces"""

        @bean(interface=UserRepository)
        class TestMultiRepo(UserRepository, AuditableRepository):
            def find_all(self):
                return []

            def audit_log(self):
                return []

        container = get_container()
        assert UserRepository in container._services
        assert container._services[UserRepository] == TestMultiRepo

    def test_explicit_interface_with_single_interface(self):
        """Test @bean with explicit interface parameter even with single interface"""

        @bean(interface=UserRepository)
        class TestUserRepo(UserRepository):
            def find_all(self):
                return []

        container = get_container()
        assert UserRepository in container._services
        metadata = get_bean_metadata(TestUserRepo)
        assert metadata['interface'] == UserRepository


class TestBeanInterfaceDetection:
    """Test interface detection logic"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_abc_interface_detected(self):
        """Test ABC-based interface is detected"""

        @bean
        class TestRepo(UserRepository):
            def find_all(self):
                return []

        metadata = get_bean_metadata(TestRepo)
        assert metadata['interface'] == UserRepository

    def test_non_abc_base_class_ignored(self):
        """Test non-ABC base class is ignored"""

        class BaseEntity:
            """Regular base class (not ABC)"""
            pass

        @bean
        class TestEntity(BaseEntity):
            pass

        metadata = get_bean_metadata(TestEntity)
        # Should register as itself since BaseEntity is not ABC
        assert metadata['interface'] == TestEntity

    def test_mixed_abc_and_regular_base_classes(self):
        """Test mixed ABC and regular base classes"""

        class BaseEntity:
            """Regular base class"""
            pass

        @bean
        class TestRepo(UserRepository, BaseEntity):
            def find_all(self):
                return []

        metadata = get_bean_metadata(TestRepo)
        # Should detect only the ABC interface
        assert metadata['interface'] == UserRepository


class TestBeanDependencyInjection:
    """Test @bean integration with dependency injection"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_bean_dependency_resolution(self):
        """Test @bean classes can be resolved with dependencies"""

        @bean
        class TestDatabaseManager:
            def __init__(self):
                self.connected = True

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self, db: TestDatabaseManager):
                self._db = db

            def find_all(self):
                return []

        container = get_container()

        # Resolve UserRepository - should get SqlUserRepository with injected db
        repo = container.resolve(UserRepository)
        assert isinstance(repo, TestUserRepo)
        assert hasattr(repo, '_db')
        assert isinstance(repo._db, TestDatabaseManager)
        assert repo._db.connected is True

    def test_bean_nested_dependencies(self):
        """Test @bean with nested dependency chain"""

        @bean
        class ConfigService:
            def __init__(self):
                self.settings = {"db": "test"}

        @bean
        class DatabaseManager:
            def __init__(self, config: ConfigService):
                self.config = config

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self, db: DatabaseManager):
                self._db = db

            def find_all(self):
                return []

        container = get_container()
        repo = container.resolve(UserRepository)

        assert isinstance(repo, TestUserRepo)
        assert isinstance(repo._db, DatabaseManager)
        assert isinstance(repo._db.config, ConfigService)
        assert repo._db.config.settings == {"db": "test"}


class TestBeanDecoratorSyntax:
    """Test different @bean decorator syntax options"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_bean_without_parentheses(self):
        """Test @bean decorator without parentheses"""

        @bean
        class TestService:
            pass

        assert is_bean(TestService)

    def test_bean_with_empty_parentheses(self):
        """Test @bean() decorator with empty parentheses"""

        @bean()
        class TestService:
            pass

        assert is_bean(TestService)

    def test_bean_with_scope_only(self):
        """Test @bean(scope=...) decorator"""

        @bean(scope=Scope.SINGLETON)
        class TestService:
            pass

        assert is_bean(TestService)
        metadata = get_bean_metadata(TestService)
        assert metadata['scope'] == Scope.SINGLETON

    def test_bean_with_interface_only(self):
        """Test @bean(interface=...) decorator"""

        @bean(interface=UserRepository)
        class TestRepo(UserRepository):
            def find_all(self):
                return []

        assert is_bean(TestRepo)
        metadata = get_bean_metadata(TestRepo)
        assert metadata['interface'] == UserRepository

    def test_bean_with_all_parameters(self):
        """Test @bean with all possible parameters"""

        @bean(scope=Scope.SINGLETON, interface=UserRepository, url="test://db")
        class TestRepo(UserRepository):
            def __init__(self, url: str):
                self.url = url

            def find_all(self):
                return []

        assert is_bean(TestRepo)
        metadata = get_bean_metadata(TestRepo)
        assert metadata['scope'] == Scope.SINGLETON
        assert metadata['interface'] == UserRepository


class TestBeanPatternInterfaces:
    """Test @bean with Repository and Service pattern interfaces"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_repository_pattern_interface_detected(self):
        """Test Repository pattern interface is auto-detected"""

        @bean
        class PostgresUserRepository(UserPatternRepository):
            async def find_by_email(self, email: str) -> Optional[User]:
                return None

        metadata = get_bean_metadata(PostgresUserRepository)
        assert metadata['interface'] == UserPatternRepository

    def test_service_pattern_interface_detected(self):
        """Test Service pattern interface is auto-detected"""

        @bean
        class SendgridEmailService(EmailService):
            async def send(self, to: str, subject: str, body: str) -> bool:
                return True

        metadata = get_bean_metadata(SendgridEmailService)
        assert metadata['interface'] == EmailService

    def test_repository_pattern_registration(self):
        """Test Repository pattern class is registered correctly"""

        @bean
        class PostgresUserRepository(UserPatternRepository):
            async def find_by_email(self, email: str) -> Optional[User]:
                return None

        container = get_container()
        assert UserPatternRepository in container._services
        assert container._services[UserPatternRepository] == PostgresUserRepository

    def test_service_pattern_registration(self):
        """Test Service pattern class is registered correctly"""

        @bean
        class SendgridEmailService(EmailService):
            async def send(self, to: str, subject: str, body: str) -> bool:
                return True

        container = get_container()
        assert EmailService in container._services
        assert container._services[EmailService] == SendgridEmailService

    def test_repository_pattern_with_scope(self):
        """Test Repository pattern with custom scope"""

        @bean(scope=Scope.SINGLETON)
        class PostgresUserRepository(UserPatternRepository):
            async def find_by_email(self, email: str) -> Optional[User]:
                return None

        metadata = get_bean_metadata(PostgresUserRepository)
        assert metadata['scope'] == Scope.SINGLETON
        assert metadata['interface'] == UserPatternRepository

    def test_service_pattern_with_scope(self):
        """Test Service pattern with custom scope"""

        @bean(scope=Scope.SINGLETON)
        class SendgridEmailService(EmailService):
            async def send(self, to: str, subject: str, body: str) -> bool:
                return True

        metadata = get_bean_metadata(SendgridEmailService)
        assert metadata['scope'] == Scope.SINGLETON
        assert metadata['interface'] == EmailService


class TestBeanRealWorldScenarios:
    """Test real-world usage scenarios"""

    def setup_method(self):
        """Reset container and caches before each test"""
        set_container(Container())  # Reset first to clear mappings
        clear_singletons()  # Then clear caches
        clear_scoped()

    def test_repository_pattern(self):
        """Test @bean with repository pattern"""

        @bean(scope=Scope.SINGLETON, url="sqlite:///:memory:")
        class TestDatabaseManager:
            def __init__(self, url: str):
                self.url = url

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self, db: TestDatabaseManager):
                self._db = db

            def find_all(self):
                return []

        @bean
        class TestProductRepo(ProductRepository):
            def __init__(self, db: TestDatabaseManager):
                self._db = db

            def find_by_id(self, product_id: str):
                return None

        container = get_container()

        user_repo = container.resolve(UserRepository)
        product_repo = container.resolve(ProductRepository)

        # Both repositories should share the same DatabaseManager (singleton)
        assert isinstance(user_repo, TestUserRepo)
        assert isinstance(product_repo, TestProductRepo)

    def test_service_layer_pattern(self):
        """Test @bean with service layer pattern"""

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self):
                self._users = []

            def find_all(self):
                return self._users

        @bean
        class UserService:
            def __init__(self, user_repo: UserRepository):
                self._repo = user_repo

            def get_all_users(self):
                return self._repo.find_all()

        container = get_container()
        service = container.resolve(UserService)

        assert isinstance(service, UserService)
        assert isinstance(service._repo, TestUserRepo)
        assert service.get_all_users() == []


class TestSummonFunction:
    """Test Summon() function for manual DI resolution"""

    def setup_method(self):
        """Reset container and singletons before each test"""
        clear_singletons()
        set_container(Container())

    def test_summon_registered_interface(self):
        """Test Summon() resolves registered interface"""

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self):
                self._users = []

            def find_all(self):
                return self._users

        # Summon the repository using the interface
        repo = Summon(UserRepository)

        assert isinstance(repo, TestUserRepo)
        assert repo.find_all() == []

    def test_summon_concrete_class(self):
        """Test Summon() resolves concrete class"""

        @bean
        class TestDatabaseManager:
            def __init__(self):
                self.connected = True

        # Summon concrete class
        db = Summon(TestDatabaseManager)

        assert isinstance(db, TestDatabaseManager)
        assert db.connected is True

    def test_summon_with_dependencies(self):
        """Test Summon() resolves dependencies recursively"""

        @bean
        class TestDatabaseManager:
            def __init__(self):
                self.connected = True

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self, db: TestDatabaseManager):
                self._db = db

            def find_all(self):
                return []

        # Summon should resolve UserRepository with TestDatabaseManager injected
        repo = Summon(UserRepository)

        assert isinstance(repo, TestUserRepo)
        assert hasattr(repo, '_db')
        assert isinstance(repo._db, TestDatabaseManager)
        assert repo._db.connected is True

    def test_summon_nested_dependencies(self):
        """Test Summon() resolves nested dependency chain"""

        @bean
        class ConfigService:
            def __init__(self):
                self.settings = {"db": "test"}

        @bean
        class DatabaseManager:
            def __init__(self, config: ConfigService):
                self.config = config

        @bean
        class TestUserRepo(UserRepository):
            def __init__(self, db: DatabaseManager):
                self._db = db

            def find_all(self):
                return []

        # Summon with deep dependency chain
        repo = Summon(UserRepository)

        assert isinstance(repo, TestUserRepo)
        assert isinstance(repo._db, DatabaseManager)
        assert isinstance(repo._db.config, ConfigService)
        assert repo._db.config.settings == {"db": "test"}

    def test_summon_unregistered_service_raises_error(self):
        """Test Summon() raises error for unregistered service"""

        class UnregisteredService:
            pass

        with pytest.raises(ValueError) as exc_info:
            Summon(UnregisteredService)

        assert "not registered" in str(exc_info.value).lower()

    def test_summon_in_event_handler(self):
        """Test Summon() usage in event handler (real-world scenario)"""

        @bean(scope=Scope.SINGLETON)  # Use singleton so instances are shared
        class TestEmailService:
            def __init__(self):
                self.sent_emails = []

            def send(self, to: str, message: str):
                self.sent_emails.append((to, message))
                return True

        # Simulate event handler using Summon
        def handle_user_created_event(user_email: str):
            email_service = Summon(TestEmailService)
            email_service.send(user_email, "Welcome!")

        handle_user_created_event("test@example.com")

        # Verify the email was sent
        email_service = Summon(TestEmailService)
        assert len(email_service.sent_emails) > 0

    def test_summon_in_regular_function(self):
        """Test Summon() usage in regular function (service locator pattern)"""

        @bean
        class TestProductRepo(ProductRepository):
            def __init__(self):
                self._products = ["Product A", "Product B"]

            def find_by_id(self, product_id: str):
                return None

        # Regular function using Summon
        def get_all_products():
            repo = Summon(ProductRepository)
            return repo._products

        products = get_all_products()
        assert products == ["Product A", "Product B"]

    def test_summon_type_safety(self):
        """Test Summon() maintains type safety"""

        @bean
        class TestUserRepo(UserRepository):
            def find_all(self):
                return []

        # Summon returns the correct type
        repo: UserRepository = Summon(UserRepository)

        # Should have the interface methods
        assert hasattr(repo, 'find_all')
        assert callable(repo.find_all)

    def test_summon_with_constructor_params(self):
        """Test Summon() with @bean constructor parameters"""

        @bean(url="postgresql://localhost/test")
        class TestDatabaseManager:
            def __init__(self, url: str):
                self.url = url

        db = Summon(TestDatabaseManager)

        assert isinstance(db, TestDatabaseManager)
        assert db.url == "postgresql://localhost/test"

    def test_summon_singleton_scope(self):
        """Test Summon() respects SINGLETON scope"""

        @bean(scope=Scope.SINGLETON)
        class SingletonService:
            def __init__(self):
                self.id = id(self)

        # Summon multiple times - should return same instance
        service1 = Summon(SingletonService)
        service2 = Summon(SingletonService)

        assert service1.id == service2.id
        assert service1 is service2

    def test_summon_pattern_interfaces(self):
        """Test Summon() with Repository and Service pattern interfaces"""

        @bean
        class PostgresUserRepository(UserPatternRepository):
            async def find_by_email(self, email: str) -> Optional[User]:
                return User("1", "Test", email)

        @bean
        class SendgridEmailService(EmailService):
            async def send(self, to: str, subject: str, body: str) -> bool:
                return True

        # Summon Repository pattern
        user_repo = Summon(UserPatternRepository)
        assert isinstance(user_repo, PostgresUserRepository)

        # Summon Service pattern
        email_service = Summon(EmailService)
        assert isinstance(email_service, SendgridEmailService)
