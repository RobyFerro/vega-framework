# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vega Framework is an enterprise-ready Python framework that enforces Clean Architecture for building maintainable and scalable applications. It provides automatic dependency injection, type-safe patterns (Interactor, Mediator, Repository, Service), and CLI scaffolding tools.

## Core Architecture Principles

### Clean Architecture Layers (Dependency Rule)

Dependencies flow **inward only**. Outer layers depend on inner layers, never the reverse:

```
Presentation (CLI, Web) → Application (Workflows) → Domain (Business Logic) → (abstractions)
                                                    ← Infrastructure (Implementations)
```

- **Domain Layer**: Pure business logic, framework-independent
  - `domain/entities/`: Business objects (dataclasses)
  - `domain/repositories/`: Abstract interfaces for data access
  - `domain/services/`: Abstract interfaces for external services
  - `domain/interactors/`: Use cases (single-purpose business operations)

- **Application Layer**: Complex workflows
  - `application/mediators/`: Orchestrate multiple interactors

- **Infrastructure Layer**: Technical implementations
  - `infrastructure/repositories/`: Database implementations (PostgreSQL, Memory, etc.)
  - `infrastructure/services/`: External API integrations

- **Presentation Layer**: User interfaces
  - `presentation/cli/`: CLI commands
  - `presentation/web/`: Vega Web routes (Starlette-based)

### Key Patterns

**Interactor**: Single-purpose use case. The metaclass auto-calls `call()` on instantiation.
```python
class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        user = User(name=self.name, email=self.email)
        return await repository.save(user)

# Usage: result = await CreateUser(name="John", email="john@example.com")
```

**Mediator**: Orchestrates multiple interactors for complex workflows (no business logic).

**Repository**: Abstract interface for data persistence. Inherit from `Repository[T]`.

**Service**: Abstract interface for external services. Inherit from `Service`.

### Dependency Injection System

**Three scopes**:
- `Scope.SINGLETON`: One instance for entire application
- `Scope.SCOPED`: One instance per operation/request (default for `@bind`)
- `Scope.TRANSIENT`: New instance every time

**@injectable decorator**: For classes (decorates `__init__`)
```python
@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    pass
```

**@bind decorator**: For methods (typically on `call()` methods)
```python
@bind
async def call(self, repository: UserRepository, service: EmailService) -> User:
    # Dependencies auto-injected
```

**@bean decorator**: Auto-registers classes in DI container
- Auto-detects interfaces (ABC, Repository, Service)
- Supports constructor parameters: `@bean(url=settings.db_url, scope=Scope.SINGLETON)`
- Use explicit interface if multiple: `@bean(interface=UserRepository)`

**Container**: Wire implementations to interfaces in `config.py`
```python
from vega.di import Container
container = Container({
    UserRepository: PostgresUserRepository,
    EmailService: SendgridEmailService,
})
```

**Auto-discovery**: Use discovery utilities to automatically register beans, routes, and event handlers
```python
from vega.discovery import discover_beans, discover_routers, discover_event_handlers

# Auto-register all @bean-decorated classes
discover_beans("infrastructure")

# Auto-discover all routers
discover_routers(app, "presentation.web.routes")
```

**Summon()**: Manual dependency resolution (Service Locator pattern)
```python
from vega.di import Summon

# Resolve dependencies anywhere in your code
def my_function():
    repository = Summon(UserRepository)
    return repository.find_all()

# In event handlers
@subscribe(UserCreated)
async def on_user_created(event: UserCreated):
    email_service = Summon(EmailService)
    await email_service.send_welcome(event.email)

# Type-safe resolution
user_repo: UserRepository = Summon(UserRepository)
```

### Event System

Built-in event-driven architecture:
```python
from vega.events import Event, subscribe

@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str

@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    await email_service.send(event.email, "Welcome!")

# Publish: await UserCreated(user_id="123", email="test@test.com").publish()
```

## Development Commands

### Environment Setup
```bash
poetry install              # Install dependencies
poetry install --with dev   # Install with dev dependencies
```

### Testing (pytest with async support)
```bash
# Run all tests
poetry run pytest
make test

# Run by category
make test-unit          # Unit tests only
make test-functional    # Functional tests only
make test-integration   # Integration tests only

# Run by marker
make test-web           # Web-related tests
make test-di            # DI-related tests
make test-events        # Event system tests
make test-fast          # Exclude slow tests

# Coverage
make test-cov           # Run tests with coverage report
make show-cov           # Open coverage report in browser

# Other test commands
make test-failed        # Rerun failed tests
```

Test markers: `unit`, `functional`, `integration`, `slow`, `web`, `di`, `events`

### Linting and Formatting
```bash
make lint               # Check code quality (black, isort, ruff)
make format             # Format code (black, isort)
make check              # Run lint + test
```

Code style configuration:
- Black: line-length 100, target Python 3.10+
- isort: profile "black"
- mypy: strict typing enabled
- ruff: line-length 100

### CLI Tool (`vega` command)

**Project Management**:
```bash
vega init my-app                    # Create new project (includes web by default)
vega init my-api --path ./projects  # Create in specific directory
vega doctor                         # Validate architecture (not implemented yet)
vega update                         # Update framework
vega update --check                 # Check for updates
```

**Code Generation**:
```bash
# Domain layer
vega generate entity Product
vega generate repository ProductRepository
vega generate repository Product --impl memory     # With memory implementation
vega generate repository Product --impl sql        # With SQL implementation
vega generate service EmailService
vega generate interactor CreateProduct

# Application layer
vega generate mediator CheckoutWorkflow

# Presentation layer
vega generate router Product                       # Vega Web router
vega generate command create-product               # CLI command (async by default)
vega generate command list-users --impl sync       # Sync CLI command
vega generate middleware Logging
vega generate webmodel CreateUserRequest --request
vega generate webmodel UserResponse --response

# Infrastructure
vega generate model Product                        # SQLAlchemy model

# Events
vega generate event UserCreated
vega generate subscriber SendWelcomeEmail          # Event handler
```

Aliases: `repo` = `repository`, `event-handler` = `subscriber`

**Feature Management**:
```bash
vega add sqlalchemy  # Add database support (alias: db)
```

Note: Web support (Vega Web with Swagger UI) is integrated by default in all new projects

**Database Migrations**:
```bash
vega migrate init                    # Initialize database
vega migrate create -m "add users"   # Create migration
vega migrate upgrade                 # Apply migrations
vega migrate downgrade               # Rollback
```

**Web Development**:
```bash
vega web run                         # Run development server
```

## Framework Components

### Vega Web (Starlette-based)

**VegaApp**: ASGI application built on Starlette with FastAPI-like API
- OpenAPI schema auto-generation
- Built-in Swagger UI (`/docs`) and ReDoc (`/redoc`)
- Automatic dependency injection in routes

**Router**: Similar to FastAPI routers
```python
from vega.web import Router

router = Router(prefix="/api/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: str):
    return {"id": user_id}

app.include_router(router)
```

**Route Middleware**: Apply middleware to specific routes
**Built-in Middlewares**: CORS, authentication, logging, etc.

### Discovery System

Located in `vega/discovery/`:
- `discover_routers()`: Auto-discover web routes
- `discover_commands()`: Auto-discover CLI commands
- `discover_event_handlers()`: Auto-discover event subscribers
- `discover_beans()`: Auto-discover @bean-decorated classes

### Settings Management

Uses Pydantic v2 BaseSettings with python-dotenv support for configuration.

## Important Implementation Details

### Interactor Metaclass Behavior

The `InteractorMeta` metaclass automatically calls the `call()` method when an Interactor is instantiated. This enables the clean syntax:
```python
result = await CreateUser(name="John", email="john@test.com")
```

Instead of:
```python
interactor = CreateUser(name="John", email="john@test.com")
result = await interactor.call()
```

The metaclass also supports `@trigger` decorator for automatic event publishing after `call()` completes.

### DI Container Resolution

The Container resolves dependencies recursively:
1. Check if service is an abstract interface with a mapping
2. Check if service is a concrete implementation
3. For `@injectable` classes, use ScopeManager for caching based on scope
4. Inspect constructor signature and resolve dependencies
5. Instantiate with resolved dependencies

### Scope Context

Use `scope_context()` for scoped dependencies:
```python
from vega.di import scope_context

async with scope_context():
    # All SCOPED dependencies share instances within this context
    result = await MyInteractor()
```

## Project Structure Conventions

Generated projects follow this structure:
```
my-app/
├── domain/
│   ├── entities/          # Business objects
│   ├── repositories/      # Data interfaces
│   ├── services/          # External service interfaces
│   └── interactors/       # Use cases
├── application/
│   └── mediators/         # Workflows
├── infrastructure/
│   ├── repositories/      # Database implementations
│   └── services/          # API integrations
├── presentation/
│   ├── cli/              # CLI commands
│   └── web/              # Vega Web routes
├── config.py             # DI container setup
├── settings.py           # Configuration
└── main.py               # Entry point
```

## Development Workflow

1. **Start with Domain**: Define entities, repository/service interfaces, and interactors
2. **Define Interfaces**: Create abstract interfaces for external dependencies
3. **Implement Use Cases**: Create interactors for business operations
4. **Build Infrastructure**: Implement repositories and services with actual tech
5. **Wire Dependencies**: Configure Container in `config.py` or use `@bean` with auto-discovery
6. **Add Presentation**: Create routes or CLI commands
7. **Test**: Domain tests use mocks, infrastructure tests use real dependencies

## Critical Rules

- **Never import infrastructure in domain layer**
- **Business logic only in domain/interactors**, not in routes or repositories
- **Repository/Service implementations in infrastructure**, not domain
- **Routes/commands are thin wrappers** - just call interactors
- **One interactor = one use case** (single responsibility)
- **Use @bind for dependency injection** in `call()` methods
- **All entities are dataclasses** or Pydantic models
- **Async by default** for I/O operations

## Testing Conventions

- Unit tests: Mock all dependencies, test business logic in isolation
- Functional tests: Test features end-to-end with test doubles
- Integration tests: Test with real infrastructure (databases, APIs)
- Use `pytest.mark.asyncio` for async tests (configured via `asyncio_mode = "auto"`)
