# CLI Overview

Vega Framework ships with a CLI for scaffolding, extending, and maintaining Clean Architecture projects.

## Installation

```bash
pip install vega-framework
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `vega init <name>` | Scaffold a new project (templates: `basic`, `web`, `ai-rag`) |
| `vega generate <type> <name>` | Create domain, application, infrastructure, or presentation components |
| `vega add <feature>` | Enable optional scaffolds such as Vega Web (`web`) or SQLAlchemy (`sqlalchemy`/`db`) |
| `vega web <command>` | Run or manage the Vega Web server once the web scaffold is present |
| `vega migrate <command>` | Proxy Alembic to manage database migrations |
| `vega update` | Check for and install CLI/framework updates |
| `vega doctor` | Planned architecture diagnostics (command reserved; implementation pending) |

Use `--help` on any command to inspect options.

## Common Workflows

### Create New Project

```bash
# Basic project
vega init my-app
cd my-app
poetry install

# Vega Web project
vega init my-api --template web
cd my-api
poetry install
vega web run --reload
```

### Generate Components

```bash
# Domain layer
vega generate entity User
vega generate repository UserRepository --impl memory
vega generate interactor CreateUser

# Application layer
vega generate mediator CheckoutFlow

# Presentation layer
vega add web
vega generate router User
vega generate webmodel CreateUserRequest --request

# Infrastructure layer
vega add sqlalchemy
vega generate model User
vega generate repository UserRepository --impl sql
```

### Add Features

```bash
vega add web            # Vega Web scaffold
vega add sqlalchemy     # SQLAlchemy + Alembic
vega add db             # Alias for sqlalchemy
```

### Database Management

```bash
vega migrate init                        # Create tables from current models
vega migrate create -m "add users table" # Generate Alembic revision
vega migrate upgrade                     # Apply migrations
vega migrate downgrade                   # Roll back
vega migrate history                     # Inspect revision log
```

## Command Categories

### Project Management
- [vega init](init.md) – Bootstrap a new project structure.
- [vega update](update.md) – Keep the CLI and framework up to date.
- [vega doctor](doctor.md) – Track roadmap status and planned checks.

### Code Generation
- [vega generate](generate.md) – Create components across all layers.

### Feature Management
- [vega add](add.md) - Add Vega Web or database scaffolds.
- [vega web](web.md) - Run the Vega Web app after adding the web scaffold.

### Database Management
- [vega migrate](migrate.md) – Run Alembic commands through the Vega CLI.

## Help

```bash
vega --help
vega init --help
vega generate --help
vega migrate --help
vega web --help
```

## Next Steps

- [vega init](init.md) – Create your first project.
- [vega add](add.md) – Add web or database capabilities.
- [vega generate](generate.md) – Explore every generator and option.
- [vega migrate](migrate.md) – Manage your schema once SQLAlchemy is enabled.
