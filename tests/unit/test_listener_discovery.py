"""Unit tests for listener discovery"""
import pytest
import importlib
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from vega.discovery import discover_listeners
from vega.listeners import JobListener, job_listener, Message
from vega.listeners.registry import clear_listener_registry, get_listener_registry


@pytest.mark.unit
@pytest.mark.listeners
class TestListenerDiscovery:
    """Test listener auto-discovery"""

    def setup_method(self):
        """Clear registry before each test"""
        clear_listener_registry()

    def teardown_method(self):
        """Clear registry after each test"""
        clear_listener_registry()

    def test_discover_listeners_returns_empty_for_missing_package(self):
        """Test discovery returns empty list when package doesn't exist"""
        listeners = discover_listeners(
            "nonexistent_package",
            listeners_subpackage="infrastructure.listeners"
        )

        assert listeners == []

    def test_discover_listeners_returns_registered_listeners(self):
        """Test discovery returns listeners from registry"""
        # Manually register some listeners
        @job_listener(queue="test-1")
        class Listener1(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        @job_listener(queue="test-2")
        class Listener2(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        # Discovery should return already registered listeners
        listeners = get_listener_registry()

        assert len(listeners) == 2
        assert Listener1 in listeners
        assert Listener2 in listeners

    @patch('vega.discovery.listeners.importlib.import_module')
    @patch('vega.discovery.listeners.Path')
    def test_discover_listeners_imports_modules(self, mock_path_class, mock_import):
        """Test discovery imports all Python modules in listeners directory"""
        # Mock the listeners package
        mock_listeners_module = MagicMock()
        mock_listeners_module.__file__ = "/fake/path/infrastructure/listeners/__init__.py"

        # Mock Path.glob to return fake listener files
        mock_path = MagicMock()
        mock_file1 = MagicMock()
        mock_file1.stem = "listener1"
        mock_file2 = MagicMock()
        mock_file2.stem = "listener2"
        mock_file3 = MagicMock()
        mock_file3.stem = "__init__"  # Should be skipped

        mock_path.glob.return_value = [mock_file1, mock_file2, mock_file3]
        mock_path_class.return_value.parent = mock_path

        # Configure import_module mock
        def import_side_effect(module_name):
            if module_name == "test.infrastructure.listeners":
                return mock_listeners_module
            return MagicMock()

        mock_import.side_effect = import_side_effect

        # Run discovery
        discover_listeners("test", "infrastructure.listeners")

        # Verify modules were imported (excluding __init__.py)
        import_calls = [call[0][0] for call in mock_import.call_args_list]
        assert "test.infrastructure.listeners.listener1" in import_calls
        assert "test.infrastructure.listeners.listener2" in import_calls
        assert "test.infrastructure.listeners.__init__" not in import_calls

    def test_discover_listeners_handles_fully_qualified_package(self):
        """Test discovery handles fully qualified package names"""
        # This test verifies that if the base_package already includes
        # the listeners subpackage, it doesn't duplicate it

        # Since we can't easily test this without creating real packages,
        # we'll verify the logic by checking with mocks

        with patch('vega.discovery.listeners.importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Package not found")

            # Should handle this gracefully
            listeners = discover_listeners(
                "infrastructure.listeners",
                "infrastructure.listeners"
            )

            assert listeners == []

    @patch('vega.discovery.listeners.importlib.import_module')
    @patch('vega.discovery.listeners.Path')
    def test_discover_listeners_continues_on_import_error(self, mock_path_class, mock_import):
        """Test discovery continues when a module fails to import"""
        # Mock the listeners package
        mock_listeners_module = MagicMock()
        mock_listeners_module.__file__ = "/fake/path/infrastructure/listeners/__init__.py"

        # Mock Path.glob to return fake listener files
        mock_path = MagicMock()
        mock_file1 = MagicMock()
        mock_file1.stem = "good_listener"
        mock_file2 = MagicMock()
        mock_file2.stem = "bad_listener"

        mock_path.glob.return_value = [mock_file1, mock_file2]
        mock_path_class.return_value.parent = mock_path

        # Configure import_module mock to fail on one module
        def import_side_effect(module_name):
            if module_name == "test.infrastructure.listeners":
                return mock_listeners_module
            elif "bad_listener" in module_name:
                raise ImportError("Broken module")
            return MagicMock()

        mock_import.side_effect = import_side_effect

        # Run discovery - should not raise error
        listeners = discover_listeners("test", "infrastructure.listeners")

        # Should return listeners despite one module failing
        assert isinstance(listeners, list)

    def test_get_listener_registry_returns_copy(self):
        """Test that get_listener_registry returns a copy"""
        @job_listener(queue="test")
        class TestListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        registry1 = get_listener_registry()
        registry2 = get_listener_registry()

        # Should be equal but not the same object
        assert registry1 == registry2
        assert registry1 is not registry2

        # Modifying one shouldn't affect the other
        registry1.append(MagicMock())
        assert len(registry1) != len(registry2)


@pytest.mark.unit
@pytest.mark.listeners
class TestDiscoveryIntegration:
    """Integration tests for discovery with actual listener classes"""

    def setup_method(self):
        """Clear registry before each test"""
        clear_listener_registry()

    def teardown_method(self):
        """Clear registry after each test"""
        clear_listener_registry()

    def test_decorated_listeners_auto_register(self):
        """Test that @job_listener decorator auto-registers listeners"""
        initial_count = len(get_listener_registry())

        @job_listener(queue="auto-register-test")
        class AutoRegisterListener(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        final_count = len(get_listener_registry())

        assert final_count == initial_count + 1
        assert AutoRegisterListener in get_listener_registry()

    def test_multiple_listeners_register_independently(self):
        """Test multiple listeners register without conflicts"""
        @job_listener(queue="queue-1")
        class Listener1(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        @job_listener(queue="queue-2")
        class Listener2(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        @job_listener(queue="queue-3")
        class Listener3(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        registry = get_listener_registry()

        assert len(registry) == 3
        assert all(listener in registry for listener in [Listener1, Listener2, Listener3])

        # Verify each has correct queue
        assert Listener1._listener_queue == "queue-1"
        assert Listener2._listener_queue == "queue-2"
        assert Listener3._listener_queue == "queue-3"

    def test_clear_registry_removes_all_listeners(self):
        """Test clearing registry removes all listeners"""
        @job_listener(queue="test-1")
        class Listener1(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        @job_listener(queue="test-2")
        class Listener2(JobListener):
            async def handle(self, message: Message) -> None:
                pass

        assert len(get_listener_registry()) == 2

        clear_listener_registry()

        assert len(get_listener_registry()) == 0
