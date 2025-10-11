# CLI Overview

Vega Framework provides a comprehensive CLI for scaffolding and managing Clean Architecture projects.

## Installation

```bash
pip install vega-framework
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `vega init <name>` | Create new project |
| `vega generate <type> <name>` | Generate component |
| `vega add <feature>` | Add feature to project |
| `vega migrate <command>` | Manage database migrations |
| `vega doctor` | Validate project architecture |
| `vega update` | Update framework |

## Common Workflows

### Create New Project

```bash
# Basic project
vega init my-app
cd my-app
poetry install

# Web project with FastAPI
vega init my-api --template fastapi
cd my-api
poetry install
```

### Generate Components

```bash
# Domain layer
vega generate entity User
vega generate repository UserRepository
vega generate interactor CreateUser

# Presentation layer
vega generate command create-user
vega generate router User  # Requires web
```

### Add Features

```bash
# Add web support
vega add web

# Add database support
vega add sqlalchemy

# Then generate database models
vega generate model User
```

### Database Management

```bash
# Initialize database
vega migrate init

# Create migration
vega migrate create -m "add users table"

# Apply migrations
vega migrate upgrade

# Rollback
vega migrate downgrade
```

### Validate Project

```bash
# Check architecture compliance
vega doctor

# Check if project is a valid Vega project
vega doctor --path ./my-project
```

## Command Categories

### Project Management
- [vega init](init.md) - Initialize new project
- [vega doctor](doctor.md) - Validate project
- [vega update](update.md) - Update framework

### Code Generation
- [vega generate](generate.md) - Generate components

### Feature Management
- [vega add](add.md) - Add features

### Database Management
- [vega migrate](migrate.md) - Database migrations

## Help

Get help for any command:

```bash
vega --help
vega init --help
vega generate --help
vega migrate --help
```

## Next Steps

- [vega init](init.md) - Create your first project
- [vega generate](generate.md) - Learn all component types
- [vega add](add.md) - Add features to existing projects
