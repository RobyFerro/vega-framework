# Vega Framework

An enterprise-ready Python framework that enforces Clean Architecture for building maintainable and scalable applications.

## Features

- ✅ **Automatic Dependency Injection** - Zero boilerplate, type-safe DI
- ✅ **Clean Architecture Patterns** - Interactor, Mediator, Repository, Service
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

### Initialize Project

```bash
vega init <project_name> [--template basic|fastapi|ai-rag] [--path .]
```

Creates a new Vega project with Clean Architecture structure:

- `domain/` - Entities, repositories, services, interactors
- `application/` - Mediators and workflows
- `infrastructure/` - Repository and service implementations
- `config.py` - DI container setup
- `settings.py` - Application configuration

### Generate Components

```bash
vega generate entity <Name>
vega generate repository <Name> [--impl memory|sql]
vega generate service <Name>
vega generate interactor <Name>
vega generate mediator <Name>
vega generate router <Name>          # Requires FastAPI
vega generate middleware <Name>      # Requires FastAPI
vega generate model <Name>           # Requires SQLAlchemy
```

### Add Features

```bash
# Add FastAPI web scaffold
vega add web

# Add SQLAlchemy database support
vega add sqlalchemy
# or
vega add db
```

### Database Migrations (SQLAlchemy)

```bash
# Initialize database
vega migrate init

# Create a new migration
vega migrate create -m "migration message"

# Apply migrations
vega migrate upgrade [--revision head]

# Rollback migrations
vega migrate downgrade [--revision -1]

# Show current revision
vega migrate current

# Show migration history
vega migrate history
```

### Validate Project

```bash
vega doctor [--path .]
```

Validates project structure, DI configuration, and architecture compliance.

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
