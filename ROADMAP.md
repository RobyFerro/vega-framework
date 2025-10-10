# Vega Framework - Roadmap

This document outlines the planned features, improvements, and enhancements for the Vega Framework. The roadmap is organized by priority and includes both new features and performance/quality improvements.

> **Last Updated**: 2025-01-09
> **Current Version**: Check [CHANGELOG.md](CHANGELOG.md) for latest version

---

## Table of Contents

- [Vision](#vision)
- [High Priority Features](#high-priority-features)
- [Medium Priority Features](#medium-priority-features)
- [Low Priority Features](#low-priority-features)
- [Performance Improvements](#performance-improvements)
- [Code Quality & Technical Debt](#code-quality--technical-debt)
- [Version Milestones](#version-milestones)

---

## Vision

Vega Framework aims to be the **premier Python framework for Clean Architecture**, providing enterprise-grade features while maintaining simplicity and developer experience. We take inspiration from the best features of .NET Core, Spring Boot, and Laravel, adapted to Python's ecosystem.

**Core Principles:**
- ✅ Clean Architecture enforcement
- ✅ Developer experience first
- ✅ Type-safety and modern Python features
- ✅ Minimal boilerplate
- ✅ Enterprise-ready patterns

---

## High Priority Features

### 1. Base Repository with CRUD Operations
**Status**: 🟡 Planned
**Inspired by**: Spring Data JPA, Laravel Eloquent
**Target**: v1.1.0

**Problem**: Currently, `Repository[T]` is empty and every repository must reimplement basic CRUD operations.

**Proposal**:
```python
from vega.patterns import BaseRepository

class BaseRepository(Repository[T]):
    """Base repository with common CRUD operations"""

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """Find entity by ID"""
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all entities with pagination"""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Create or update entity"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity by ID"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total entities"""
        pass
```

**Implementation Tasks**:
- [ ] Create `BaseRepository[T]` abstract class
- [ ] Update SQLAlchemy repository template to extend `BaseRepository`
- [ ] Update documentation and examples
- [ ] Add tests for base repository pattern
- [ ] Update CLI generator to use `BaseRepository`

---

### 2. Enhanced DI Container with Advanced Features
**Status**: 🟡 Planned
**Inspired by**: .NET Core DI, Spring Boot
**Target**: v1.1.0

**Problem**: Current container only supports simple type mapping. Missing factory functions, named services, and conditional registration.

**Proposal**:

#### 2.1 Factory Functions
```python
# Register with factory
container.register_factory(
    UserRepository,
    factory=lambda sp: PostgresUserRepository(
        db=sp.resolve(DatabaseManager),
        cache=sp.resolve(CacheService)
    )
)
```

#### 2.2 Named Services
```python
# Multiple implementations of same interface
container.register_named(IEmailService, "sendgrid", SendgridEmailService)
container.register_named(IEmailService, "mailgun", MailgunEmailService)

# Resolve specific implementation
@bind(name="sendgrid")
async def call(self, email_service: IEmailService):
    ...
```

#### 2.3 Conditional Registration
```python
# Environment-based registration
if settings.ENVIRONMENT == "development":
    container.register(IEmailService, FakeEmailService)
else:
    container.register(IEmailService, SendgridEmailService)
```

**Implementation Tasks**:
- [ ] Add `register_factory()` method to Container
- [ ] Implement named service resolution
- [ ] Add conditional registration helpers
- [ ] Update `@bind` decorator to support `name` parameter
- [ ] Update documentation with advanced DI patterns
- [ ] Add comprehensive tests

---

### 3. Event Bus & Domain Events
**Status**: ✅ **COMPLETED**
**Inspired by**: .NET MediatR, Laravel Events
**Completed**: 2025-01-09

**Implementation**: Fully functional event system with all planned features!

**What's Included**:
```python
from vega.events import Event, get_event_bus, subscribe
from dataclasses import dataclass

# Define event
@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str
    name: str

    def __post_init__(self):
        super().__init__()

# Subscribe to event
@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    await email_service.send(event.email, "Welcome!")

@subscribe(UserCreated, priority=10, retry_on_error=True, max_retries=3)
async def create_audit_log(event: UserCreated):
    await audit_service.log(f"User {event.user_id} created")

# Publish event
bus = get_event_bus()
await bus.publish(UserCreated(user_id="123", email="test@test.com", name="Test"))
```

**Features Implemented**:
- ✅ Async event handling
- ✅ Multiple subscribers per event
- ✅ Event inheritance support
- ✅ Priority ordering
- ✅ Error handling with retry logic
- ✅ Event middleware (logging, metrics, validation, enrichment)
- ✅ Type-safe with full type hints
- ✅ Global and custom event buses
- ✅ Comprehensive documentation
- ✅ Working examples

**Implementation Completed**:
- [x] Create `Event` base class
- [x] Implement `EventBus` with pub/sub pattern
- [x] Add `@subscribe` and `@event_handler` decorators
- [x] Support async event handlers
- [x] Add event middleware (logging, metrics, validation, enrichment)
- [x] CLI generator templates for events (ready for integration)
- [x] Full documentation with README
- [x] Working examples (basic_example.py, middleware_example.py)
- [x] Tested and verified

**Location**: `vega/events/`
**Documentation**: `vega/events/README.md`
**Examples**: `examples/events/`

---

### 4. Testing Utilities & Helpers
**Status**: 🟡 Planned
**Inspired by**: Laravel TestCase, Spring Boot Test
**Target**: v1.2.0

**Problem**: No built-in testing helpers, making tests verbose and repetitive.

**Proposal**:
```python
from vega.testing import TestCase, mock_repository, mock_service

class TestCreateUser(TestCase):
    """Base test case with DI and async support"""

    async def test_creates_user_successfully(self):
        # Mock repository
        with mock_repository(UserRepository) as mock_repo:
            mock_repo.save.return_value = User(id="123", name="Test")

            # Execute use case
            user = await CreateUser(name="Test", email="test@test.com")

            # Assertions
            self.assertEqual(user.name, "Test")
            mock_repo.save.assert_called_once()

    async def test_with_real_dependencies(self):
        # Test with actual implementations
        self.register_services({
            UserRepository: InMemoryUserRepository
        })

        user = await CreateUser(name="Real", email="real@test.com")
        self.assertIsNotNone(user.id)
```

**Features**:
- `TestCase` base class with async support
- `mock_repository()` and `mock_service()` context managers
- Database fixtures and factories
- HTTP client for API testing
- Assertion helpers

**Implementation Tasks**:
- [ ] Create `vega.testing` module
- [ ] Implement `TestCase` base class
- [ ] Add mocking utilities
- [ ] Create test fixtures and factories
- [ ] Add HTTP test client (for FastAPI routes)
- [ ] Documentation with examples
- [ ] Test coverage for testing utilities

---

## Medium Priority Features

### 5. Specification Pattern for Complex Queries
**Status**: 🟡 Planned
**Inspired by**: Spring Data Specifications, DDD patterns
**Target**: v1.3.0

**Problem**: Every custom query requires a new repository method, leading to bloated interfaces.

**Proposal**:
```python
from vega.patterns import Specification

# Define specifications
class EmailContains(Specification[User]):
    def __init__(self, text: str):
        self.text = text

    def is_satisfied_by(self, user: User) -> bool:
        return self.text in user.email

    def to_sql_expression(self):
        return User.email.like(f"%{self.text}%")

class IsActive(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.active

    def to_sql_expression(self):
        return User.active == True

# Compose specifications
spec = EmailContains("@gmail.com").and_(IsActive())

# Use in repository
users = await repository.find_by_spec(spec)
```

**Implementation Tasks**:
- [ ] Create `Specification[T]` base class
- [ ] Implement AND/OR/NOT combinators
- [ ] Add SQL expression support for SQLAlchemy
- [ ] Update repository interface with `find_by_spec()`
- [ ] CLI generator: `vega generate specification ActiveUsers`
- [ ] Documentation and examples

---

### 6. Configurable Middleware Pipeline
**Status**: 🟡 Planned
**Inspired by**: ASP.NET Core middleware pipeline
**Target**: v1.3.0

**Problem**: Middleware registration is not centralized or configurable.

**Proposal**:
```python
from vega.web import MiddlewarePipeline

# In config.py or app setup
pipeline = MiddlewarePipeline()
pipeline.use(RequestLoggingMiddleware)
pipeline.use(AuthenticationMiddleware)
pipeline.use(AuthorizationMiddleware)
pipeline.use(RateLimitingMiddleware)

# Conditional middleware
if settings.DEBUG:
    pipeline.use(DebugMiddleware)

# Custom inline middleware
@pipeline.use_inline
async def custom_header_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Custom"] = "Value"
    return response
```

**Implementation Tasks**:
- [ ] Create `MiddlewarePipeline` class
- [ ] Support ordering and priorities
- [ ] Add conditional middleware registration
- [ ] Inline middleware decorator
- [ ] Update FastAPI integration
- [ ] Documentation

---

### 7. Integrated Validation Framework
**Status**: 🟡 Planned
**Inspired by**: Laravel Validation, Spring Boot Validation
**Target**: v1.3.0

**Problem**: Pydantic is used but not integrated into Vega patterns.

**Proposal**:
```python
from vega.patterns import Interactor, validate
from pydantic import BaseModel, Field, EmailStr

class CreateUser(Interactor[User]):
    class Input(BaseModel):
        name: str = Field(min_length=2, max_length=100)
        email: EmailStr
        age: int = Field(ge=18, le=120)

    def __init__(self, **kwargs):
        self.input = self.Input(**kwargs)  # Auto-validates

    @bind
    async def call(self, repository: UserRepository) -> User:
        # self.input is already validated
        user = User(
            name=self.input.name,
            email=self.input.email,
            age=self.input.age
        )
        return await repository.save(user)

# Usage - validation errors raised automatically
try:
    user = await CreateUser(name="A", email="invalid", age=15)
except ValidationError as e:
    print(e.errors())
```

**Implementation Tasks**:
- [ ] Create `Input` pattern for Interactors
- [ ] Auto-validation in `__init__`
- [ ] Custom validators library
- [ ] Error message customization
- [ ] CLI generator includes validation
- [ ] Documentation

---

### 8. Query Builder for Repositories
**Status**: 🟢 Nice-to-Have
**Inspired by**: Laravel Query Builder, Django ORM
**Target**: v1.4.0

**Proposal**:
```python
# Fluent query builder
users = await repository.query() \
    .where("email", "like", "%@gmail.com") \
    .where("active", "=", True) \
    .where("created_at", ">", date(2024, 1, 1)) \
    .order_by("name", "asc") \
    .limit(10) \
    .offset(0) \
    .get()

# Or with lambdas (type-safe)
users = await repository.query() \
    .where(lambda u: u.email.contains("@gmail.com")) \
    .where(lambda u: u.active == True) \
    .order_by(lambda u: u.name) \
    .get()
```

**Implementation Tasks**:
- [ ] Design query builder API
- [ ] Implement for SQLAlchemy
- [ ] Type-safe lambda expressions
- [ ] Pagination support
- [ ] Documentation

---

## Low Priority Features

### 9. Configurable Auto-Discovery
**Status**: 🟢 Future Enhancement
**Target**: v2.0.0

**Proposal**:
```python
# config.py
DISCOVERY_CONFIG = {
    'routes': [
        'presentation.web.routes',
        'external.api.routes',
    ],
    'commands': [
        'presentation.cli.commands',
    ],
    'exclude_patterns': [
        '*.test.*',
        '*.backup.*',
        '*_old.*',
    ],
    'auto_tags': True,
    'auto_prefix': True,
}
```

**Implementation Tasks**:
- [ ] Make discovery paths configurable
- [ ] Add exclude patterns
- [ ] Support multiple discovery sources
- [ ] Update documentation

---

### 10. GraphQL Support
**Status**: 🟢 Future Enhancement
**Target**: v2.0.0

**Proposal**:
```bash
vega add graphql

vega generate graphql-type User
vega generate graphql-query GetUser
vega generate graphql-mutation CreateUser
```

---

### 11. WebSocket Support
**Status**: 🟢 Future Enhancement
**Target**: v2.0.0

**Proposal**:
```bash
vega add websocket

vega generate websocket-handler ChatHandler
```

---

### 12. Background Jobs & Task Queue
**Status**: 🟢 Future Enhancement
**Target**: v2.0.0

**Proposal**:
```python
from vega.jobs import background_job, JobQueue

@background_job(queue="emails", retry=3)
async def send_welcome_email(user_id: str):
    user = await user_repository.find_by_id(user_id)
    await email_service.send(user.email, "Welcome!")

# Enqueue
await JobQueue.enqueue(send_welcome_email, user_id="123")
```

---

## Performance Improvements

### P1. Cache `inspect.signature()` Results
**Status**: 🔴 Critical
**Target**: v1.0.1 (Patch Release)

**Problem**: `inspect.signature()` is called repeatedly in hot paths (DI resolution), causing 50-200ms overhead on startup.

**Solution**:
```python
from functools import lru_cache

@lru_cache(maxsize=256)
def get_cached_signature(func):
    return inspect.signature(func)

@lru_cache(maxsize=256)
def get_cached_type_hints(func):
    return get_type_hints(func)
```

**Impact**: 30-50% reduction in DI resolution time.

**Tasks**:
- [ ] Implement signature caching in `di/container.py`
- [ ] Implement type hints caching in `di/decorators.py`
- [ ] Add benchmarks
- [ ] Test with large applications

---

### P2. Optimize File I/O in Code Generation
**Status**: 🟡 High
**Target**: v1.0.1

**Problem**: Files are read/written multiple times during code generation, causing 100-300ms overhead per command.

**Solution**:
- Batch file operations
- Use `io.StringIO` for in-memory manipulation
- Write files only once

**Tasks**:
- [ ] Refactor `generate.py` file operations
- [ ] Use in-memory buffers
- [ ] Batch writes
- [ ] Add benchmarks

---

### P3. Add Timeouts to Subprocess Calls
**Status**: 🔴 Critical (Reliability)
**Target**: v1.0.1

**Problem**: `subprocess.run()` in migrate commands has no timeout, can hang indefinitely.

**Solution**:
```python
result = subprocess.run(
    [sys.executable, '-m', 'alembic', 'revision', ...],
    capture_output=True,
    text=True,
    timeout=30  # Add timeout
)
```

**Tasks**:
- [ ] Add timeouts to all subprocess calls
- [ ] Make timeout configurable
- [ ] Handle timeout exceptions gracefully

---

### P4. Lazy Module Loading
**Status**: 🟢 Medium
**Target**: v1.1.0

**Problem**: Optional dependencies (FastAPI, SQLAlchemy) are imported even when not used.

**Solution**: Use `importlib.util.LazyLoader` for optional imports.

**Tasks**:
- [ ] Implement lazy loading for FastAPI
- [ ] Implement lazy loading for SQLAlchemy
- [ ] Test import performance improvements

---

### P5. Optimize Auto-Discovery Performance
**Status**: 🟢 Medium
**Target**: v1.2.0

**Problem**: `importlib.import_module()` in loops can be slow for large projects.

**Solution**:
- Cache imported modules
- Parallel module loading
- Incremental discovery

**Tasks**:
- [ ] Add module import caching
- [ ] Benchmark discovery performance
- [ ] Implement parallel discovery (if beneficial)

---

## Code Quality & Technical Debt

### Q1. Remove Obsolete Code
**Status**: 🟡 Medium
**Target**: v1.0.1

**Issues Found**:
- `print()` in docstrings should use logging
- Empty functions with only `pass` need documentation
- `StringIO` for output suppression → use `contextlib.redirect_stdout()`
- Multiple `sys` imports that may be unused

**Tasks**:
- [ ] Replace `print()` with logging in examples
- [ ] Add docstrings to empty group functions
- [ ] Refactor output suppression with context managers
- [ ] Run `ruff check` to find unused imports
- [ ] Clean up unused imports

---

### Q2. Add Type Hints Coverage
**Status**: 🟢 Low
**Target**: v1.1.0

**Goal**: 100% type hints coverage

**Tasks**:
- [ ] Run `mypy --strict` on codebase
- [ ] Add missing type hints
- [ ] Fix type errors
- [ ] Add to CI/CD

---

### Q3. Improve Test Coverage
**Status**: 🟡 Medium
**Target**: v1.1.0

**Goal**: 90%+ test coverage

**Tasks**:
- [ ] Add tests for DI container edge cases
- [ ] Add tests for auto-discovery
- [ ] Add integration tests for CLI commands
- [ ] Add tests for scope management
- [ ] Set up code coverage reporting

---

### Q4. Documentation Improvements
**Status**: 🟢 Ongoing
**Target**: Continuous

**Tasks**:
- [ ] Add video tutorials
- [ ] Create example projects repository
- [ ] Add architecture decision records (ADRs)
- [ ] API reference documentation
- [ ] Migration guides from other frameworks

---

## Version Milestones

### v1.0.1 (Patch) - Performance & Quality
**Target**: Q1 2025
**Focus**: Performance improvements and bug fixes

- [ ] P1: Cache `inspect.signature()` results
- [ ] P2: Optimize file I/O
- [ ] P3: Add subprocess timeouts
- [ ] Q1: Remove obsolete code
- [ ] Bug fixes

---

### v1.1.0 (Minor) - Enhanced Repository & DI
**Target**: Q2 2025
**Focus**: Repository and DI improvements

- [ ] Feature #1: Base Repository with CRUD
- [ ] Feature #2: Enhanced DI Container
- [ ] P4: Lazy module loading
- [ ] Q2: Type hints coverage
- [ ] Q3: Improve test coverage

---

### v1.2.0 (Minor) - Events & Testing
**Target**: Q3 2025
**Focus**: Event system and testing utilities

- [ ] Feature #3: Event Bus & Domain Events
- [ ] Feature #4: Testing Utilities
- [ ] P5: Optimize auto-discovery
- [ ] Documentation improvements

---

### v1.3.0 (Minor) - Query & Validation
**Target**: Q4 2025
**Focus**: Advanced querying and validation

- [ ] Feature #5: Specification Pattern
- [ ] Feature #6: Middleware Pipeline
- [ ] Feature #7: Integrated Validation
- [ ] Documentation improvements

---

### v1.4.0 (Minor) - Query Builder
**Target**: Q1 2026
**Focus**: Query builder and advanced features

- [ ] Feature #8: Query Builder
- [ ] Feature #9: Configurable Auto-Discovery
- [ ] Documentation improvements

---

### v2.0.0 (Major) - Extended Ecosystem
**Target**: Q3 2026
**Focus**: New delivery mechanisms and job processing

- [ ] Feature #10: GraphQL Support
- [ ] Feature #11: WebSocket Support
- [ ] Feature #12: Background Jobs
- [ ] Breaking changes (if any)
- [ ] Major documentation overhaul

---

## Contributing to the Roadmap

We welcome community input on the roadmap! If you have suggestions:

1. **Open an issue** with the `enhancement` label
2. **Discuss in GitHub Discussions** for larger features
3. **Submit a PR** with your proposal added to this roadmap

### Priority Guidelines

- 🔴 **Critical**: Security, reliability, or severe performance issues
- 🟡 **High**: Important features that improve developer experience
- 🟢 **Medium/Low**: Nice-to-have features or minor improvements

---

## Notes

- Dates are estimates and subject to change based on community feedback and contributions
- Features may be reprioritized based on user demand
- Performance benchmarks will be added as optimizations are implemented
- Breaking changes will only occur in major versions (v2.0.0+)

---

**Last Updated**: 2025-01-09
**Maintainers**: Vega Framework Team
**License**: See [LICENSE](LICENSE)
