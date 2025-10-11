# Vega Framework Documentation

Complete documentation for Vega Framework - an enterprise-ready Python framework enforcing Clean Architecture.

## Quick Links

- **[Philosophy](philosophy.md)** - Why Vega exists and core principles ⭐
- [Installation](getting-started/installation.md) - Get started in minutes
- [Quick Start](getting-started/quick-start.md) - Build your first project
- [Architecture](architecture/clean-architecture.md) - Understand Clean Architecture
- [CLI Commands](cli/overview.md) - Master the CLI
- [Events System](events/overview.md) - Event-driven architecture

## Documentation Structure

### Philosophy & Concepts
- **[Philosophy](philosophy.md)** - Why Vega exists, core principles, when to use it

### Getting Started
- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)
- [Project Structure](getting-started/project-structure.md)

### Architecture
- [Clean Architecture](architecture/clean-architecture.md) - Core principles
- [Layers](architecture/layers.md) - The 4 layers explained
- [Dependency Rule](architecture/dependency-rule.md) - Why dependencies matter

### Core Concepts
- [Dependency Injection](core/dependency-injection.md) - DI system
- [Scopes](core/scopes.md) - Singleton, Scoped, Transient
- [Container](core/container.md) - Container configuration

### Patterns
- [Interactor](patterns/interactor.md) - Single-purpose use cases
- [Mediator](patterns/mediator.md) - Complex workflows
- [Repository](patterns/repository.md) - Data persistence abstraction
- [Service](patterns/service.md) - External service abstraction

### Events
- [Overview](events/overview.md) - Event system complete guide
- [Publishing](events/publishing.md) - Event publishing syntax
- [Handlers](events/handlers.md) - Event handlers
- [Middleware](events/middleware.md) - Event middleware
- [Best Practices](events/best-practices.md) - Events best practices

### CLI
- [Overview](cli/overview.md) - CLI introduction
- [init](cli/init.md) - Create projects
- [generate](cli/generate.md) - Generate components
- [add](cli/add.md) - Add features
- [migrate](cli/migrate.md) - Database migrations
- [doctor](cli/doctor.md) - Validate architecture
- [update](cli/update.md) - Update framework

### Features
- [FastAPI Integration](features/web-fastapi.md) - Web API support
- [SQLAlchemy & Alembic](features/database-sqlalchemy.md) - Database support
- [Async Support](features/async-support.md) - Async/await everywhere
- [Auto-Discovery](features/auto-discovery.md) - Component auto-discovery

### Guides
- [Building Domain Layer](guides/building-domain-layer.md)
- [Building Application Layer](guides/building-application-layer.md)
- [Building Infrastructure](guides/building-infrastructure.md)
- [Building Web API](guides/building-web-api.md)
- [Building CLI](guides/building-cli.md)
- [Testing](guides/testing.md)

### Reference
- [Changelog](reference/CHANGELOG.md)
- [Roadmap](reference/ROADMAP.md)

## Examples

Check the `examples/` directory in the repository for working examples:
- Event system examples
- Complete application examples
- Pattern usage examples

## Getting Help

- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and share ideas
- Documentation: This documentation

## Contributing

Contributions are welcome! See the contributing guidelines in the repository.
