# Changelog

All notable changes to Vega Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.7] - 2025-01-06

### Added

- Added new project template for web applications
- Added `web` command to CLI for generating web application scaffolding
- Updated documentation to include web architecture guidelines

## [0.1.0] - 2025-01-06

### Added

- Initial release
- Dependency Injection system with automatic resolution
- Scope management (SINGLETON, SCOPED, TRANSIENT)
- Clean Architecture patterns (Interactor, Mediator, Repository, Service)
- Settings management with Pydantic
- CLI tool with `init` and `generate` commands
- Project scaffolding support
- Component generation (entity, repository, service, interactor, mediator)

### Features

- `@bind` decorator for method-level dependency injection
- `@injectable` decorator for class-level dependency injection
- IOC Container with recursive dependency resolution
- Thread-safe scoped instances
- Type-safe with full Python type hints support
- CLI commands:
  - `vega init <project>` - Initialize new project
  - `vega generate <component> <name>` - Generate components

[0.1.0]: https://github.com/your-org/vega-framework/releases/tag/v0.1.0
