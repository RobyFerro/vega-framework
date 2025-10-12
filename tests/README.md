# Vega Framework Test Suite

Comprehensive test suite for the Vega Framework, organized into unit tests, functional tests, and integration tests.

## 📁 Directory Structure

```
tests/
├── conftest.py              # Shared pytest configuration and fixtures
├── fixtures/                # Shared test data and fixtures
├── unit/                    # Unit tests (test individual components)
│   ├── test_di_container.py
│   ├── test_event_bus.py
│   └── test_router.py
├── functional/              # Functional tests (test features and workflows)
│   ├── test_web_endpoints.py
│   └── test_web_middleware.py
└── integration/             # Integration tests (test component interactions)
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)
Test individual components in isolation:
- Dependency Injection Container
- Event Bus
- Router
- Middleware
- Request/Response objects

**Run unit tests:**
```bash
pytest tests/unit -m unit
```

### Functional Tests (`tests/functional/`)
Test complete features and workflows:
- Web endpoints
- Middleware system
- Routing behavior
- Error handling

**Run functional tests:**
```bash
pytest tests/functional -m functional
```

### Integration Tests (`tests/integration/`)
Test interactions between multiple components:
- Full application workflows
- Database integration
- External service integration

**Run integration tests:**
```bash
pytest tests/integration -m integration
```

## 🚀 Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Functional tests only
pytest -m functional

# Integration tests only
pytest -m integration

# Web-related tests
pytest -m web

# Dependency injection tests
pytest -m di

# Event system tests
pytest -m events
```

### Run Tests with Coverage
```bash
# Generate coverage report
pytest --cov=vega --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Run Specific Test File
```bash
pytest tests/unit/test_di_container.py
```

### Run Specific Test Class or Function
```bash
pytest tests/unit/test_di_container.py::TestContainerBasics
pytest tests/unit/test_di_container.py::TestContainerBasics::test_container_initialization
```

### Run Tests in Parallel
```bash
# Install pytest-xdist first
poetry add --group dev pytest-xdist

# Run tests in parallel
pytest -n auto
```

## 📊 Test Markers

Tests are automatically marked based on their location and can be filtered:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.functional` - Functional tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.web` - Web framework tests
- `@pytest.mark.di` - Dependency injection tests
- `@pytest.mark.events` - Event system tests

### Example: Skip Slow Tests
```bash
pytest -m "not slow"
```

### Example: Run Only Web Tests
```bash
pytest -m web
```

## 🔧 Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

## 🛠️ Writing Tests

### Basic Test Structure

```python
import pytest
from vega.web import VegaApp

class TestMyFeature:
    """Test my feature"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        app = VegaApp()

        # Act
        result = app.do_something()

        # Assert
        assert result == expected_value
```

### Using Fixtures

```python
def test_with_container(container):
    """Test using the container fixture"""
    container.register(MyService)
    service = container.resolve(MyService)
    assert service is not None
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation(event_bus):
    """Test async operations"""
    await event_bus.publish(MyEvent())
    # assertions...
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_uppercase(input, expected):
    """Test with multiple inputs"""
    assert input.upper() == expected
```

## 📝 Available Fixtures

Defined in `conftest.py`:

- `container` - Fresh DI container
- `event_bus` - Fresh event bus
- `vega_app` - Basic Vega application
- `async_container` - Async-compatible DI container
- `async_event_bus` - Async-compatible event bus

## 🐛 Debugging Tests

### Run with verbose output
```bash
pytest -v
```

### Show print statements
```bash
pytest -s
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Run last failed tests
```bash
pytest --lf
```

### Run tests that failed first
```bash
pytest --ff
```

## 📈 Coverage Goals

- **Unit Tests**: Aim for >90% coverage of core components
- **Functional Tests**: Cover all major user workflows
- **Integration Tests**: Cover critical integration points

## 🔍 Test Quality Guidelines

1. **Naming**: Use descriptive test names that explain what is being tested
2. **Arrange-Act-Assert**: Follow the AAA pattern for clarity
3. **Independence**: Tests should not depend on each other
4. **Speed**: Keep unit tests fast; mark slow tests with `@pytest.mark.slow`
5. **Documentation**: Add docstrings to test classes and complex tests

## 🚨 Common Issues

### Import Errors
Make sure Vega is installed in development mode:
```bash
poetry install
```

### Async Test Errors
Ensure `pytest-asyncio` is installed and `asyncio_mode = "auto"` is set in `pyproject.toml`

### Coverage Not Working
Install coverage dependencies:
```bash
poetry add --group dev pytest-cov
```

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Vega Framework Documentation](https://vega-framework.readthedocs.io/)
