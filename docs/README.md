# Vega Framework Documentation

Welcome to the Vega Framework documentation set. The content now follows the Diátaxis model so you can pick the type of material you need—tutorials for learning, how-to guides for specific goals, reference for precise lookups, and explanations for background knowledge.

## Quick Links
- Tutorials: [Project quickstart](tutorials/quickstart.md), [Getting started with events](tutorials/events/getting-started.md)
- How-to guides: [Install Vega](how-to/install.md), [Build the domain layer](how-to/build-domain-layer.md), [Publish events](how-to/events/publish-events.md)
- Reference: [CLI overview](reference/cli/overview.md), [CLI generate command](reference/cli/generate.md), [Events API](reference/events/api.md), [Changelog](reference/CHANGELOG.md)
- Explanations: [Philosophy](explanation/philosophy.md), [Project structure](explanation/project-structure.md), [Architecture](explanation/architecture/clean-architecture.md), [Patterns](explanation/patterns/interactor.md), [Event concepts](explanation/events/overview.md)

## Tutorials
- [Project quickstart](tutorials/quickstart.md) – scaffold your first Vega application and run an interactor.
- [Getting started with events](tutorials/events/getting-started.md) – define events, subscribe handlers, and publish them end-to-end.

## How-to Guides
- [Install Vega](how-to/install.md) – installation using pip or Poetry.
- [Build the domain layer](how-to/build-domain-layer.md) – craft entities, interactors, and repositories.
- [Publish events](how-to/events/publish-events.md) – choose between auto-publish and manual publishing patterns.

## Reference
- [CLI overview](reference/cli/overview.md) – available commands and workflows.
- [CLI generate command](reference/cli/generate.md) – supported component generators and options.
- [Events API](reference/events/api.md) – classes, decorators, and middleware exposed by `vega.events`.
- [Changelog](reference/CHANGELOG.md) – release history.
- [Roadmap](reference/ROADMAP.md) – planned capabilities.

## Explanation
- [Philosophy](explanation/philosophy.md) – guiding principles and when to reach for Vega.
- [Project structure](explanation/project-structure.md) – layered layout and responsibilities.
- Architecture
  - [Clean architecture](explanation/architecture/clean-architecture.md)
  - [Layers](explanation/architecture/layers.md)
  - [Dependency rule](explanation/architecture/dependency-rule.md)
- Core concepts
  - [Dependency injection](explanation/core/dependency-injection.md)
- Patterns
  - [Interactor](explanation/patterns/interactor.md)
  - [Mediator](explanation/patterns/mediator.md)
  - [Repository](explanation/patterns/repository.md)
  - [Service](explanation/patterns/service.md)
- Events
  - [Event concepts](explanation/events/overview.md)

## Examples
Browse the `examples/` directory in the repository for runnable demonstrations of domains, patterns, and the events system.

## Getting Help
- Open a GitHub issue for bugs and feature requests.
- Join GitHub Discussions for questions or to share ideas.
- Refer back to this documentation when you need guidance.

## Contributing
Contributions are welcome! Check the repository guidelines for details on proposing changes or submitting pull requests.
