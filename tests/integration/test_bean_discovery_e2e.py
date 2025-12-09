"""End-to-end integration tests for bean discovery in DDD structure"""
import sys
import tempfile
from pathlib import Path
from abc import ABC, abstractmethod

import pytest

from vega.di import Container, set_container, get_container
from vega.di.bean import bean
from vega.discovery import discover_beans, list_registered_beans
from vega.patterns import Repository


# Note: Class names don't start with "Test" to avoid pytest collection


@pytest.fixture
def temp_project():
    """Create a temporary project structure like vega init"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()
        
        # Normalized package name (like vega init does)
        normalized_name = "test_project"
        package_path = project_path / normalized_name
        package_path.mkdir()
        
        # Create shared kernel structure
        shared_path = package_path / "shared"
        (shared_path / "domain" / "repositories").mkdir(parents=True)
        (shared_path / "infrastructure" / "repositories").mkdir(parents=True)
        (shared_path / "infrastructure" / "services").mkdir(parents=True)
        
        # Create bounded context structure (for future contexts)
        context_path = package_path / "sales"
        (context_path / "domain" / "repositories").mkdir(parents=True)
        (context_path / "infrastructure" / "repositories").mkdir(parents=True)
        
        # Create config.py
        config_content = f'''"""Test config"""
import sys
from pathlib import Path

from vega.di import Container, set_container
from vega.discovery import discover_beans

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

container = Container({{}})
set_container(container)

discovered = discover_beans("{normalized_name}")
'''
        (project_path / "config.py").write_text(config_content)
        
        yield {
            'project_path': project_path,
            'package_path': package_path,
            'normalized_name': normalized_name,
            'shared_path': shared_path,
            'context_path': context_path,
        }


@pytest.fixture
def reset_container():
    """Reset container before each test"""
    set_container(Container())
    yield
    # Cleanup after test
    set_container(Container())


class TestBeanDiscoveryDDDSharedKernel:
    """Test discovery in shared kernel (DDD structure)"""
    
    def test_discover_beans_shared_kernel_with_abc_interface(self, temp_project, reset_container):
        """Test discovery of bean with ABC interface in shared kernel"""
        # Create interface in domain
        interface_file = temp_project['shared_path'] / "domain" / "repositories" / "user_repository.py"
        interface_file.write_text('''
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def find_all(self):
        pass
''')
        
        # Create implementation in infrastructure with @bean
        impl_file = temp_project['shared_path'] / "infrastructure" / "repositories" / "memory_user_repository.py"
        impl_file.write_text(f'''
from vega.di.bean import bean
from {temp_project['normalized_name']}.shared.domain.repositories.user_repository import UserRepository

@bean
class MemoryUserRepository(UserRepository):
    def __init__(self):
        self.users = []
    
    def find_all(self):
        return self.users
''')
        
        # Add project to sys.path
        if str(temp_project['project_path']) not in sys.path:
            sys.path.insert(0, str(temp_project['project_path']))
        
        try:
            # Discover beans
            discovered = discover_beans(temp_project['normalized_name'])
            
            # Verify discovery
            assert discovered >= 1, f"Expected at least 1 bean, got {discovered}"
            
            # Verify bean is registered
            container = get_container()
            beans = list_registered_beans()
            
            # Import the interface to check registration
            import importlib
            interface_module = importlib.import_module(
                f"{temp_project['normalized_name']}.shared.domain.repositories.user_repository"
            )
            UserRepository = interface_module.UserRepository
            
            # Check if registered
            assert UserRepository in beans or any(
                'MemoryUserRepository' in str(impl) for impl in beans.values()
            ), f"Bean not registered. Found: {list(beans.keys())}"
            
            # Verify can resolve
            repo = container.resolve(UserRepository)
            assert repo is not None
            assert hasattr(repo, 'find_all')
            
        finally:
            # Cleanup sys.path
            if str(temp_project['project_path']) in sys.path:
                sys.path.remove(str(temp_project['project_path']))


    def test_discover_beans_shared_kernel_with_repository_pattern(self, temp_project, reset_container):
        """Test discovery of bean with Repository pattern in shared kernel"""
        # Create interface using Repository pattern
        interface_file = temp_project['shared_path'] / "domain" / "repositories" / "email_service.py"
        interface_file.write_text(f'''
from vega.patterns import Repository

class EmailService(Repository):
    pass
''')
        
        # Create implementation with @bean
        impl_file = temp_project['shared_path'] / "infrastructure" / "services" / "smtp_email_service.py"
        impl_file.write_text(f'''
from vega.di.bean import bean
from {temp_project['normalized_name']}.shared.domain.repositories.email_service import EmailService

@bean
class SmtpEmailService(EmailService):
    def __init__(self):
        self.sent_messages = []
    
    def send(self, message: str):
        self.sent_messages.append(message)
        return True
''')
        
        # Add project to sys.path
        if str(temp_project['project_path']) not in sys.path:
            sys.path.insert(0, str(temp_project['project_path']))
        
        try:
            # Discover beans
            discovered = discover_beans(temp_project['normalized_name'])
            
            # Verify discovery
            assert discovered >= 1
            
            # Verify bean is registered and resolvable
            container = get_container()
            
            # Import interface
            import importlib
            interface_module = importlib.import_module(
                f"{temp_project['normalized_name']}.shared.domain.repositories.email_service"
            )
            EmailService = interface_module.EmailService
            
            # Resolve
            service = container.resolve(EmailService)
            assert service is not None
            assert hasattr(service, 'send')
            
        finally:
            # Cleanup sys.path
            if str(temp_project['project_path']) in sys.path:
                sys.path.remove(str(temp_project['project_path']))


class TestBeanDiscoveryDDDBoundedContext:
    """Test discovery in bounded contexts (DDD structure)"""
    
    def test_discover_beans_bounded_context(self, temp_project, reset_container):
        """Test discovery of beans in bounded context"""
        # Create interface in bounded context domain
        interface_file = temp_project['context_path'] / "domain" / "repositories" / "order_repository.py"
        interface_file.write_text('''
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def find_all(self):
        pass
''')
        
        # Create implementation in bounded context infrastructure
        impl_file = temp_project['context_path'] / "infrastructure" / "repositories" / "memory_order_repository.py"
        impl_file.write_text(f'''
from vega.di.bean import bean
from {temp_project['normalized_name']}.sales.domain.repositories.order_repository import OrderRepository

@bean
class MemoryOrderRepository(OrderRepository):
    def __init__(self):
        self.orders = []
    
    def find_all(self):
        return self.orders
''')
        
        # Add project to sys.path
        if str(temp_project['project_path']) not in sys.path:
            sys.path.insert(0, str(temp_project['project_path']))
        
        try:
            # Discover beans
            discovered = discover_beans(temp_project['normalized_name'])
            
            # Verify discovery found the bean in bounded context
            assert discovered >= 1
            
            # Verify bean is registered
            container = get_container()
            
            # Import interface
            import importlib
            interface_module = importlib.import_module(
                f"{temp_project['normalized_name']}.sales.domain.repositories.order_repository"
            )
            OrderRepository = interface_module.OrderRepository
            
            # Resolve
            repo = container.resolve(OrderRepository)
            assert repo is not None
            assert hasattr(repo, 'find_all')
            
        finally:
            # Cleanup sys.path
            if str(temp_project['project_path']) in sys.path:
                sys.path.remove(str(temp_project['project_path']))


class TestBeanDiscoveryIntegrationConfig:
    """Test discovery integration with config.py simulation"""
    
    def test_discover_beans_integration_with_config_py(self, temp_project, reset_container):
        """Test complete discovery flow as in real projects with config.py"""
        # Create interface and implementation in shared kernel
        interface_file = temp_project['shared_path'] / "domain" / "repositories" / "product_repository.py"
        interface_file.write_text('''
from abc import ABC, abstractmethod

class ProductRepository(ABC):
    @abstractmethod
    def find_all(self):
        pass
''')
        
        impl_file = temp_project['shared_path'] / "infrastructure" / "repositories" / "memory_product_repository.py"
        impl_file.write_text(f'''
from vega.di.bean import bean
from {temp_project['normalized_name']}.shared.domain.repositories.product_repository import ProductRepository

@bean
class MemoryProductRepository(ProductRepository):
    def __init__(self):
        self.products = []
    
    def find_all(self):
        return self.products
''')
        
        # Simulate config.py execution
        # Add project to sys.path (as config.py does)
        if str(temp_project['project_path']) not in sys.path:
            sys.path.insert(0, str(temp_project['project_path']))
        
        try:
            # Simulate config.py: create container and discover
            from vega.di import Container, set_container
            from vega.discovery import discover_beans
            
            container = Container({})
            set_container(container)
            
            # Discover beans (as config.py does)
            discovered = discover_beans(temp_project['normalized_name'])
            
            # Verify discovery
            assert discovered >= 1, f"Expected at least 1 bean, got {discovered}"
            
            # Verify bean is registered and can be resolved
            import importlib
            interface_module = importlib.import_module(
                f"{temp_project['normalized_name']}.shared.domain.repositories.product_repository"
            )
            ProductRepository = interface_module.ProductRepository
            
            # Resolve from container
            repo = container.resolve(ProductRepository)
            assert repo is not None
            assert hasattr(repo, 'find_all')
            assert isinstance(repo.find_all(), list)
            
        finally:
            # Cleanup sys.path
            if str(temp_project['project_path']) in sys.path:
                sys.path.remove(str(temp_project['project_path']))

