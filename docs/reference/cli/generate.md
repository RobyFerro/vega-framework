# vega generate

Generate Clean Architecture components in your project.

## Usage

```bash
vega generate <component_type> <name> [OPTIONS]
```

## Component Types

### Domain Layer

#### entity - Domain Entity

```bash
vega generate entity User
vega generate entity Product
```

Creates a domain entity (dataclass) in `domain/entities/`.

**Generated file**:
```python
from dataclasses import dataclass

@dataclass
class User:
    id: str
    # Add your fields here
```

#### repository - Repository Interface

```bash
vega generate repository UserRepository
vega generate repository Product  # Auto-adds "Repository" suffix
```

Creates repository interface in `domain/repositories/`.

**With implementation**:
```bash
vega generate repository User --impl memory    # In-memory
vega generate repository User --impl sql       # SQL implementation
```

Creates both interface and implementation.

#### service - Service Interface

```bash
vega generate service EmailService
vega generate service Email --impl smtp
```

Creates service interface in `domain/services/`.

**With implementation**:
```bash
vega generate service Email --impl sendgrid
```

#### interactor - Use Case

```bash
vega generate interactor CreateUser
vega generate interactor GetUserById
vega generate interactor UpdateUserEmail
```

Creates interactor in `domain/interactors/`.

**Generated file**:
```python
from vega.patterns import Interactor
from vega.di import bind

class CreateUser(Interactor[Result]):
    def __init__(self):
        pass

    @bind
    async def call(self) -> Result:
        # Implement your use case here
        pass
```

### Events

#### event - Domain Event

```bash
vega generate event UserCreated
```

Creates immutable domain event in `domain/events/`.

**Generated file**:
```python
from dataclasses import dataclass
from vega.events import Event

@dataclass(frozen=True)
class UserCreated(Event):
    user_id: str
    email: str

    def __post_init__(self):
        super().__init__()
```

#### subscriber - Event Handler

```bash
vega generate subscriber SendWelcomeEmail --name UserCreated
```

Creates async event handler in `events/` (project root) so auto-discovery can import it.

**Generated file**:
```python
from vega.events import subscribe
from domain.events.user_created import UserCreated

@subscribe(UserCreated)
async def send_welcome_email(event: UserCreated):
    # Implement handling logic
    raise NotImplementedError("Implement SendWelcomeEmail handler")
```

Call `events.register_all_handlers()` during startup to load every module in `events/` automatically.

> Tip: Projects generated with newer versions of Vega invoke `register_all_handlers()` from `config.py`. If you created your project before this change, add:
> ```python
> try:
>     from events import register_all_handlers
> except ImportError:
>     pass
> else:
>     register_all_handlers()
> ```
> near the bottom of your `config.py`.

### Application Layer

#### mediator - Workflow

```bash
vega generate mediator UserRegistrationFlow
vega generate mediator CheckoutWorkflow
```

Creates mediator in `application/mediators/`.

**Generated file**:
```python
from vega.patterns import Mediator

class UserRegistrationFlow(Mediator[Result]):
    def __init__(self):
        pass

    async def call(self) -> Result:
        # Orchestrate multiple interactors here
        pass
```

### Infrastructure Layer

#### model - SQLAlchemy Model

```bash
vega generate model User
vega generate model Product
```

**Requires**: SQLAlchemy support (`vega add sqlalchemy`)

Creates SQLAlchemy model in `infrastructure/models/` and registers it with Alembic.

### Presentation Layer

#### router - FastAPI Router

```bash
vega generate router User
vega generate router Product
```

**Requires**: Web support (`vega add web`)

Creates FastAPI router in `presentation/web/routes/` and auto-registers it.

**Generated file**:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_users():
    return {"users": []}

@router.get("/{id}")
async def get_user(id: str):
    return {"user": {}}
```

#### middleware - FastAPI Middleware

```bash
vega generate middleware Logging
vega generate middleware Authentication
```

**Requires**: Web support (`vega add web`)

Creates middleware in `presentation/web/middleware/` and auto-registers it.

#### command - CLI Command

```bash
vega generate command CreateUser                # Async (default)
vega generate command ListUsers --impl sync     # Synchronous
```

Creates CLI command in `presentation/cli/commands/`.

The generator will prompt for:
- Command description
- Options and arguments
- Whether it uses interactors

**Generated async command**:
```python
import click
from vega.cli.utils import async_command

@click.command()
@click.option('--name', required=True)
@async_command
async def create_user(name: str):
    """Create a user"""
    import config  # Initialize DI
    # Your logic here
    click.echo(f"Created user: {name}")
```

## Options

### --path

Specify project path (default: current directory):

```bash
vega generate entity User --path ./my-project
```

### --impl

Generate implementation along with interface:

```bash
# Repository implementations
vega generate repository User --impl memory
vega generate repository User --impl sql
vega generate repository User --impl postgres

# Service implementations
vega generate service Email --impl sendgrid
vega generate service Payment --impl stripe

# Command types
vega generate command MyCommand --impl sync    # Synchronous
vega generate command MyCommand --impl async   # Asynchronous (default)
```

## Examples

### Complete Feature Generation

```bash
# 1. Generate entity
vega generate entity Product

# 2. Generate repository with implementation
vega generate repository Product --impl memory

# 3. Generate interactors
vega generate interactor CreateProduct
vega generate interactor GetProductById
vega generate interactor UpdateProduct
vega generate interactor DeleteProduct

# 4. Generate mediator for complex workflow
vega generate mediator ProductCatalogSync

# 5. Generate API endpoints
vega generate router Product

# 6. Generate CLI commands
vega generate command create-product
vega generate command list-products
```

### E-commerce Example

```bash
# Entities
vega generate entity User
vega generate entity Product
vega generate entity Order

# Repositories
vega generate repository User --impl sql
vega generate repository Product --impl sql
vega generate repository Order --impl sql

# Use cases
vega generate interactor CreateUser
vega generate interactor PurchaseProduct
vega generate interactor CreateOrder
vega generate interactor ProcessPayment

# Workflows
vega generate mediator CheckoutWorkflow
vega generate mediator OrderFulfillment

# API
vega generate router User
vega generate router Product
vega generate router Order

# CLI
vega generate command create-user
vega generate command list-orders
```

## Auto-Registration

Some components are auto-discovered:

### Routers (FastAPI)

```python
# presentation/web/routes/user_routes.py
router = APIRouter()  # Must be named 'router'

# Automatically registered at /api/user
```

### Commands (CLI)

```python
# presentation/cli/commands/user_commands.py
@click.command()
def create_user():
    pass

# Automatically discovered and registered
```

### Event Subscribers

```python
# events/__init__.py
from events import register_all_handlers

def bootstrap():
    register_all_handlers()  # Loads every @subscribe handler in events/
```

Handlers live in `events/` and are imported automatically once `register_all_handlers()` runs.

## Tips

### Naming Conventions

```bash
# Entity: Singular, PascalCase
vega generate entity User
vega generate entity Product

# Repository: EntityName + Repository
vega generate repository UserRepository
vega generate repository User  # Auto-adds Repository

# Interactor: Verb + Entity
vega generate interactor CreateUser
vega generate interactor UpdateProduct

# Mediator: Workflow name + Flow/Workflow
vega generate mediator UserRegistrationFlow
vega generate mediator CheckoutWorkflow

# Router: Entity name (creates /entity routes)
vega generate router User  # Creates /user endpoints

# Command: Verb + noun (kebab-case)
vega generate command create-user
vega generate command list-products
```

### Order of Generation

1. **Entities** first (domain objects)
2. **Repositories** (data access)
3. **Services** (external dependencies)
4. **Interactors** (use cases)
5. **Mediators** (workflows)
6. **Routers/Commands** (presentation)

### Batch Generation

```bash
# Use shell loop for multiple similar components
for entity in User Product Order; do
    vega generate entity $entity
    vega generate repository $entity --impl sql
done
```

## Next Steps

- [vega add](add.md) - Add features before generating components
- [vega doctor](doctor.md) - Validate generated code
- [Patterns](../patterns/interactor.md) - Understand the patterns
