# Project Structure

Vega Framework enforces a standard 4-layer Clean Architecture structure.

## Overview

```
my-app/
├── domain/                       # 🔵 DOMAIN LAYER
│   ├── entities/                # Business objects
│   ├── repositories/            # Data persistence interfaces
│   ├── services/                # External service interfaces
│   └── interactors/             # Use cases
│
├── application/                  # 🟢 APPLICATION LAYER
│   └── mediators/               # Complex workflows
│
├── infrastructure/               # 🟡 INFRASTRUCTURE LAYER
│   ├── repositories/            # Repository implementations
│   ├── services/                # Service implementations
│   ├── models/                  # Database models (optional)
│   └── database_manager.py      # Database connection (optional)
│
├── presentation/                 # 🟠 PRESENTATION LAYER
│   ├── cli/                     # CLI interface
│   │   └── commands/
│   └── web/                     # Web interface (optional)
│       ├── routes/
│       ├── middleware/
│       └── app.py
│
├── config.py                    # Dependency injection setup
├── settings.py                  # Application settings
├── main.py                      # Application entry point
└── pyproject.toml              # Dependencies
```

## Layer Responsibilities

### Domain Layer (Core Business Logic)

**Purpose**: Contains pure business logic, independent of any framework or infrastructure.

**Contains**:
- **Entities**: Business data structures
- **Repository Interfaces**: Abstract data persistence contracts
- **Service Interfaces**: Abstract external service contracts
- **Interactors**: Single-purpose use cases

**Rules**:
- ✅ NO dependencies on other layers
- ✅ NO framework-specific code
- ✅ Pure Python only
- ✅ Only defines interfaces, never implementations

**Example**:
```python
# domain/entities/user.py
@dataclass
class User:
    id: str
    name: str
    email: str

# domain/repositories/user_repository.py
class UserRepository(Repository[User]):
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

# domain/interactors/create_user.py
class CreateUser(Interactor[User]):
    @bind
    async def call(self, repository: UserRepository) -> User:
        # Business logic here
        pass
```

### Application Layer (Workflows)

**Purpose**: Orchestrates multiple domain use cases into complex workflows.

**Contains**:
- **Mediators**: Multi-step business workflows

**Rules**:
- ✅ Depends ONLY on domain layer
- ✅ NO infrastructure dependencies
- ✅ Coordinates multiple interactors

**Example**:
```python
# application/mediators/user_registration_flow.py
class UserRegistrationFlow(Mediator[User]):
    async def call(self) -> User:
        user = await CreateUser(self.name, self.email)
        await SendWelcomeEmail(user.email)
        await CreateAuditLog(user.id)
        return user
```

### Infrastructure Layer (Implementations)

**Purpose**: Provides concrete implementations of domain interfaces using specific technologies.

**Contains**:
- **Repository Implementations**: Database-specific code
- **Service Implementations**: External API integrations
- **Database Models**: ORM models (SQLAlchemy, etc.)
- **Adapters**: Technology-specific integrations

**Rules**:
- ✅ Implements domain interfaces
- ✅ Contains ALL technology-specific code
- ✅ Should be easily replaceable

**Example**:
```python
# infrastructure/repositories/postgres_user_repository.py
@injectable(scope=Scope.SINGLETON)
class PostgresUserRepository(UserRepository):
    async def find_by_email(self, email: str) -> Optional[User]:
        # PostgreSQL-specific implementation
        pass
```

### Presentation Layer (Delivery Mechanisms)

**Purpose**: Handles user interaction through different interfaces (CLI, Web, etc.).

**Contains**:
- **CLI Commands**: Command-line interface
- **Web Routes**: HTTP API endpoints (Vega Web)
- **Middleware**: Request/response processing

**Rules**:
- ✅ Depends on application and domain layers
- ✅ Handles input validation and formatting
- ✅ NO business logic

**Example**:
```python
# presentation/cli/commands/user_commands.py
@click.command()
@click.option('--name', required=True)
@click.option('--email', required=True)
@async_command
async def create_user(name: str, email: str):
    import config  # Initialize DI
    user = await CreateUser(name=name, email=email)
    click.echo(f"Created: {user.name}")

# presentation/web/routes/user_routes.py
from vega.web import Router

router = Router()

@router.post("/users")
async def create_user(request: CreateUserRequest):
    user = await CreateUser(name=request.name, email=request.email)
    return {"user": user}
```

## Dependency Flow

The **Dependency Rule** ensures dependencies point inward:

```
Presentation → Application → Domain ← Infrastructure
    ↓              ↓                      ↓
  (CLI/Web)    (Mediators)           (Implements)
```

- **Domain** has NO dependencies
- **Application** depends only on Domain
- **Infrastructure** implements Domain interfaces
- **Presentation** depends on Application and Domain

## Configuration Files

### config.py (DI Container)

Maps interfaces to implementations:

```python
from vega.di import Container, set_container
from domain.repositories.user_repository import UserRepository
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository

container = Container({
    UserRepository: PostgresUserRepository,
})

set_container(container)
```

### settings.py (Application Settings)

Centralized configuration using Pydantic:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost/myapp"
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### main.py (Entry Point)

Application entry point:

```python
import asyncio
from presentation.cli.commands import get_commands
import config  # Initialize DI

def main():
    # CLI entry point
    cli = click.Group()
    for command in get_commands():
        cli.add_command(command)
    cli()

if __name__ == "__main__":
    main()
```

## Optional Directories

### Database Support (SQLAlchemy)

When you add database support with `vega add sqlalchemy`:

```
infrastructure/
├── models/              # SQLAlchemy models
├── database_manager.py  # Database connection
└── alembic/            # Database migrations
    └── versions/
```

### Vega Web Support

When you add web support with `vega add web`:

```
presentation/
└── web/
    ├── app.py          # Vega Web app factory
    ├── routes/         # API endpoints
    ├── middleware/     # Request/response middleware
    └── models/         # Request/response DTOs
```

## Next Steps

- [Clean Architecture](../architecture/clean-architecture.md) - Understand architectural principles
- [Dependency Injection](../core/dependency-injection.md) - Learn DI system
- [Patterns](../patterns/interactor.md) - Deep dive into patterns
