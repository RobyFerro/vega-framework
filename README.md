# Vega Framework

An enterprise-ready Python framework that enforces Clean Architecture for building maintainable and scalable applications.

## Features

- ✅ **Automatic Dependency Injection** - Zero boilerplate, type-safe DI
- ✅ **Clean Architecture Patterns** - Interactor, Mediator, Repository, Service
- ✅ **Async/Await Support** - Full async support for CLI and web
- ✅ **Scope Management** - Singleton, Scoped, Transient lifetimes
- ✅ **Type-Safe** - Full type hints support
- ✅ **Framework-Agnostic** - Works with any domain (web, AI, IoT, fintech, etc.)
- ✅ **CLI Scaffolding** - Generate projects and components instantly
- ✅ **FastAPI Integration** - Built-in web scaffold with routing and middleware
- ✅ **SQLAlchemy Support** - Database management with async support and migrations
- ✅ **Lightweight** - No unnecessary dependencies

## Installation

```bash
pip install vega-framework
```

## Quick Start

```bash
# Create new project
vega init my-app

# Generate components
vega generate entity User
vega generate repository UserRepository
vega generate interactor CreateUser

# Create FastAPI project
vega init my-api --template fastapi
```

## CLI Commands

Vega Framework provides a comprehensive CLI for scaffolding and managing Clean Architecture projects.

### Project Management

#### `vega init` - Initialize New Project

Create a new Vega project with Clean Architecture structure.

```bash
vega init <project_name> [OPTIONS]
```

**Options:**
- `--template <type>` - Project template (default: `basic`)
  - `basic` - Standard Clean Architecture project with CLI support
  - `fastapi` - Project with FastAPI web scaffold included
  - `ai-rag` - AI/RAG application template (coming soon)
- `--path <directory>` - Parent directory for project (default: current directory)

**Examples:**
```bash
vega init my-app
vega init my-api --template fastapi
vega init my-ai --template ai-rag --path ./projects
```

**Creates:**
- `domain/` - Entities, repositories, services, interactors
- `application/` - Mediators and workflows
- `infrastructure/` - Repository and service implementations
- `presentation/` - CLI and web interfaces
- `config.py` - DI container configuration
- `settings.py` - Application settings
- `pyproject.toml` - Dependencies and project metadata

---

#### `vega doctor` - Validate Project

Validate your Vega project structure and architecture compliance.

```bash
vega doctor [--path .]
```

**Options:**
- `--path <directory>` - Project path to validate (default: current directory)

**Checks:**
- Correct folder structure
- DI container configuration
- Import dependencies
- Architecture violations

**Example:**
```bash
vega doctor
vega doctor --path ./my-app
```

---

#### `vega update` - Update Framework

Update Vega Framework to the latest version.

```bash
vega update [OPTIONS]
```

**Options:**
- `--check` - Check for updates without installing
- `--force` - Force reinstall even if up to date

**Examples:**
```bash
vega update              # Update to latest version
vega update --check      # Check for updates only
vega update --force      # Force reinstall
```

---

### Code Generation

#### `vega generate` - Generate Components

Generate Clean Architecture components in your project.

```bash
vega generate <component_type> <name> [OPTIONS]
```

**Component Types:**

##### Domain Layer

**`entity`** - Domain Entity (dataclass)
```bash
vega generate entity Product
```
Creates a domain entity in `domain/entities/`

**`repository`** - Repository Interface
```bash
vega generate repository ProductRepository
vega generate repository Product --impl memory    # With in-memory implementation
vega generate repository Product --impl sql       # With SQL implementation
```
Creates repository interface in `domain/repositories/` and optionally an implementation in `infrastructure/repositories/`

**Alias:** `repo` can be used instead of `repository`

**`service`** - Service Interface
```bash
vega generate service EmailService
vega generate service Email --impl smtp          # With SMTP implementation
```
Creates service interface in `domain/services/` and optionally an implementation in `infrastructure/services/`

**`interactor`** - Use Case / Interactor
```bash
vega generate interactor CreateProduct
vega generate interactor GetUserById
```
Creates interactor (use case) in `domain/interactors/`

##### Application Layer

**`mediator`** - Workflow / Mediator
```bash
vega generate mediator CheckoutFlow
vega generate mediator OrderProcessing
```
Creates mediator (workflow orchestrator) in `application/mediators/`

##### Infrastructure Layer

**`model`** - SQLAlchemy Model *(requires SQLAlchemy)*
```bash
vega generate model User
vega generate model ProductCategory
```
Creates SQLAlchemy model in `infrastructure/models/` and registers it in Alembic

##### Presentation Layer

**`router`** - FastAPI Router *(requires FastAPI)*
```bash
vega generate router Product
vega generate router User
```
Creates FastAPI router in `presentation/web/routes/` and auto-registers it

**`middleware`** - FastAPI Middleware *(requires FastAPI)*
```bash
vega generate middleware Logging
vega generate middleware Authentication
```
Creates FastAPI middleware in `presentation/web/middleware/` and auto-registers it

**`command`** - CLI Command
```bash
vega generate command CreateUser                 # Async command (default)
vega generate command ListUsers --impl sync      # Synchronous command
```
Creates CLI command in `presentation/cli/commands/`

The generator will prompt for:
- Command description
- Options and arguments
- Whether it will use interactors

**Options:**
- `--path <directory>` - Project root path (default: current directory)
- `--impl <type>` - Generate infrastructure implementation
  - For `repository`: `memory`, `sql`, or custom name
  - For `service`: custom implementation name
  - For `command`: `sync` or `async` (default: async)

**Examples:**
```bash
# Domain layer
vega generate entity Product
vega generate repository ProductRepository --impl memory
vega generate service EmailService --impl smtp
vega generate interactor CreateProduct

# Application layer
vega generate mediator CheckoutFlow

# Presentation layer (web)
vega generate router Product
vega generate middleware Logging

# Presentation layer (CLI)
vega generate command CreateUser
vega generate command ListUsers --impl sync

# Infrastructure layer
vega generate model User
```

---

### Feature Management

#### `vega add` - Add Features to Project

Add additional features to an existing Vega project.

```bash
vega add <feature> [OPTIONS]
```

**Features:**

**`web`** - Add FastAPI Web Scaffold
```bash
vega add web
```
Adds FastAPI web scaffold to your project:
- `presentation/web/` - Web application structure
- `presentation/web/routes/` - API routes
- `presentation/web/middleware/` - Middleware components
- `presentation/web/app.py` - FastAPI app factory

**`sqlalchemy` / `db`** - Add SQLAlchemy Database Support
```bash
vega add sqlalchemy
vega add db              # Alias
```
Adds SQLAlchemy database support:
- `infrastructure/database_manager.py` - Database connection manager
- `infrastructure/models/` - SQLAlchemy models directory
- `alembic/` - Database migration system
- `alembic.ini` - Alembic configuration

**Options:**
- `--path <directory>` - Path to Vega project (default: current directory)

**Examples:**
```bash
vega add web
vega add sqlalchemy
vega add db --path ./my-project
```

---

### Database Management

#### `vega migrate` - Database Migration Commands

Manage database schema migrations with Alembic *(requires SQLAlchemy)*.

**`init`** - Initialize Database
```bash
vega migrate init
```
Creates all database tables based on current models. Use this for initial setup.

**`create`** - Create New Migration
```bash
vega migrate create -m "migration message"
```
Generates a new migration file by auto-detecting model changes.

**Options:**
- `-m, --message <text>` - Migration description (required)

**`upgrade`** - Apply Migrations
```bash
vega migrate upgrade [--revision head]
```
Apply pending migrations to the database.

**Options:**
- `--revision <id>` - Target revision (default: `head` - latest)

**`downgrade`** - Rollback Migrations
```bash
vega migrate downgrade [--revision -1]
```
Rollback database migrations.

**Options:**
- `--revision <id>` - Target revision (default: `-1` - previous)

**`current`** - Show Current Revision
```bash
vega migrate current
```
Display the current database migration revision.

**`history`** - Show Migration History
```bash
vega migrate history
```
Display complete migration history with details.

**Examples:**
```bash
# Initialize database
vega migrate init

# Create migration after changing models
vega migrate create -m "Add user table"
vega migrate create -m "Add email field to users"

# Apply all pending migrations
vega migrate upgrade

# Apply migrations up to specific revision
vega migrate upgrade --revision abc123

# Rollback last migration
vega migrate downgrade

# Rollback to specific revision
vega migrate downgrade --revision xyz789

# Check current status
vega migrate current

# View history
vega migrate history
```

---

### Getting Help

**Show Version:**
```bash
vega --version
```

**Show Help:**
```bash
vega --help                    # Main help
vega <command> --help          # Command-specific help
vega generate --help           # Generate command help
vega migrate --help            # Migrate command help
```

**Examples:**
```bash
vega init --help
vega generate --help
vega add --help
vega migrate upgrade --help
```

## Async CLI Commands

Vega provides seamless async/await support in CLI commands, allowing you to execute interactors directly.

### Generate a CLI Command

```bash
# Generate an async command (default)
vega generate command CreateUser

# Generate a synchronous command
vega generate command ListUsers --impl sync
```

The generator will prompt you for:
- Command description
- Options and arguments
- Whether it will use interactors

### Manual Command Example

```python
import click
from vega.cli.utils import async_command

@click.command()
@click.option('--name', required=True)
@async_command
async def create_user(name: str):
    """Create a user using an interactor"""
    import config  # Initialize DI container
    from domain.interactors.create_user import CreateUser

    user = await CreateUser(name=name)
    click.echo(f"Created: {user.name}")
```

This enables the same async business logic to work in both CLI and web (FastAPI) contexts.

## Use Cases

Perfect for:

- AI/RAG applications
- E-commerce platforms
- Fintech systems
- Mobile backends
- Microservices
- CLI tools
- Any Python application requiring clean architecture

## License

MIT

## Contributing

Contributions welcome! This framework is extracted from production code and battle-tested.
