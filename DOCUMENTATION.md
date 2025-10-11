# Vega Framework - Documentation Overview

## 📚 Documentation Structure

The documentation has been completely reorganized for clarity and ease of use.

### Root Files (Gateway)

**[README.md](README.md)** - Main entry point
- Quick overview of the framework
- Installation and quick start
- Key concepts summary
- Links to full documentation

### Complete Documentation (docs/)

All detailed documentation is now in the `docs/` directory:

**[docs/README.md](docs/README.md)** - Documentation index
- Complete table of contents
- Quick links to all sections

## 🎯 Key Documents

### Start Here

1. **[Philosophy](docs/philosophy.md)** ⭐ **NEW!**
   - Why Vega exists
   - Core principles explained with examples
   - When to use (and when not to use) Vega
   - The Vega way of working
   - **Read this first to understand the "why" behind everything**

2. **[Quick Start](docs/getting-started/quick-start.md)**
   - Create your first project in 5 minutes
   - Hands-on tutorial with code examples

### Core Concepts

3. **[Clean Architecture](docs/architecture/clean-architecture.md)**
   - What is Clean Architecture and why it matters
   - Real-world examples comparing good vs bad
   - Benefits and trade-offs

4. **[Dependency Injection](docs/core/dependency-injection.md)**
   - How DI works in Vega
   - @bind and @injectable decorators
   - Scopes (Singleton, Scoped, Transient)
   - Complete examples

5. **[Interactor Pattern](docs/patterns/interactor.md)**
   - The heart of business logic
   - Real-world use cases
   - Testing strategies
   - Best practices and common mistakes

### Practical Guides

6. **[Building Domain Layer](docs/guides/building-domain-layer.md)**
   - Step-by-step guide
   - Philosophy: Business logic first
   - Business vs technical logic
   - Real e-commerce example

7. **[CLI Commands](docs/cli/generate.md)**
   - All vega generate commands
   - Component types explained
   - Practical workflows
   - Examples for complete features

### Events System

8. **[Events Overview](docs/events/overview.md)**
   - Complete event system guide (from vega/events/)
   - Pub/sub pattern
   - Middleware and best practices

9. **[Event Publishing Syntax](docs/events/publishing.md)**
   - Three publishing syntaxes
   - When to use each
   - Auto-publish feature

## 📂 File Organization

```
vega-framework-release/
├── README.md                          # Gateway (overview + links)
├── DOCUMENTATION.md                   # This file
├── LICENSE
├── pyproject.toml
│
├── docs/                              # All documentation
│   ├── README.md                     # Documentation index
│   ├── philosophy.md                 # Framework philosophy ⭐
│   │
│   ├── getting-started/              # Getting started guides
│   │   ├── installation.md
│   │   ├── quick-start.md
│   │   └── project-structure.md
│   │
│   ├── architecture/                 # Architecture concepts
│   │   ├── clean-architecture.md
│   │   ├── layers.md
│   │   └── dependency-rule.md
│   │
│   ├── core/                         # Core concepts
│   │   └── dependency-injection.md
│   │
│   ├── patterns/                     # Design patterns
│   │   └── interactor.md
│   │
│   ├── events/                       # Event system
│   │   ├── overview.md
│   │   └── publishing.md
│   │
│   ├── cli/                          # CLI reference
│   │   ├── overview.md
│   │   └── generate.md
│   │
│   ├── guides/                       # Practical guides
│   │   └── building-domain-layer.md
│   │
│   └── reference/                    # Reference materials
│       ├── CHANGELOG.md
│       └── ROADMAP.md
│
├── vega/                             # Framework code
└── examples/                         # Code examples
```

## 🔄 What Changed

### Removed from Root

- ❌ `ARCHITECTURE.md` - Now in `docs/architecture/`
- ❌ `ROADMAP.md` - Now in `docs/reference/`
- ❌ `CHANGELOG.md` - Now in `docs/reference/`

These files were creating duplication and confusion.

### Added

- ✅ **`docs/philosophy.md`** - NEW! Core principles and philosophy
- ✅ Streamlined `README.md` - Now a clean gateway
- ✅ Well-organized `docs/` directory structure
- ✅ Consistent linking between documents

## 🎓 Recommended Reading Order

### For New Users

1. [README.md](README.md) - Get the overview
2. [Philosophy](docs/philosophy.md) - Understand why Vega exists
3. [Quick Start](docs/getting-started/quick-start.md) - Build your first project
4. [Clean Architecture](docs/architecture/clean-architecture.md) - Learn the principles
5. [Interactor Pattern](docs/patterns/interactor.md) - Write your first use case

### For Experienced Developers

1. [Philosophy](docs/philosophy.md) - Understand the approach
2. [Dependency Rule](docs/architecture/dependency-rule.md) - Learn the key principle
3. [Building Domain Layer](docs/guides/building-domain-layer.md) - Start coding
4. [CLI Generate](docs/cli/generate.md) - Speed up development
5. [Events System](docs/events/overview.md) - Event-driven architecture

### For Architects

1. [Philosophy](docs/philosophy.md) - Understand design decisions
2. [Clean Architecture](docs/architecture/clean-architecture.md) - Architecture principles
3. [Layers](docs/architecture/layers.md) - Layer responsibilities
4. [Dependency Rule](docs/architecture/dependency-rule.md) - Dependency management
5. [Roadmap](docs/reference/ROADMAP.md) - Future direction

## 🌟 Key Features of the Documentation

### Philosophy First

The new `philosophy.md` explains the **why** before the **how**:
- Why Clean Architecture matters
- Why business logic should be pure
- When to use Vega and when not to
- Real-world examples comparing approaches

### Real Examples

Every concept includes:
- ✅ Good examples
- ❌ Bad examples
- Real-world scenarios
- Common mistakes to avoid

### Practical Focus

- Step-by-step guides
- Complete code examples
- Testing strategies
- Best practices

### Clear Navigation

- Table of contents in every section
- Cross-references between related topics
- Quick links to important documents
- Consistent structure

## 📝 Documentation by Use Case

### "I want to understand if Vega is right for me"

1. [Philosophy](docs/philosophy.md) - Core principles
2. [README.md](README.md) - Quick overview
3. "Perfect For" and "When NOT to Use" sections in Philosophy

### "I want to get started quickly"

1. [Installation](docs/getting-started/installation.md)
2. [Quick Start](docs/getting-started/quick-start.md)
3. [CLI Overview](docs/cli/overview.md)

### "I want to understand Clean Architecture"

1. [Philosophy](docs/philosophy.md) - Why it matters
2. [Clean Architecture](docs/architecture/clean-architecture.md) - Principles
3. [Layers](docs/architecture/layers.md) - Layer details
4. [Dependency Rule](docs/architecture/dependency-rule.md) - Key principle

### "I want to build an application"

1. [Building Domain Layer](docs/guides/building-domain-layer.md)
2. [Interactor Pattern](docs/patterns/interactor.md)
3. [Dependency Injection](docs/core/dependency-injection.md)
4. [CLI Generate](docs/cli/generate.md)

### "I want to use the event system"

1. [Events Overview](docs/events/overview.md)
2. [Event Publishing](docs/events/publishing.md)

## 🚀 Next Steps

### For Documentation Contributors

If you want to add more documentation:

1. **Core Concepts** - Add to `docs/core/`:
   - `scopes.md` - Deep dive on scopes
   - `container.md` - Advanced container configuration

2. **Patterns** - Add to `docs/patterns/`:
   - `mediator.md` - Mediator pattern
   - `repository.md` - Repository pattern
   - `service.md` - Service pattern

3. **CLI** - Add to `docs/cli/`:
   - `init.md` - vega init details
   - `add.md` - vega add details
   - `migrate.md` - Database migrations

4. **Guides** - Add to `docs/guides/`:
   - `building-application-layer.md` - Mediators and workflows
   - `building-infrastructure.md` - Repository implementations
   - `building-web-api.md` - FastAPI integration
   - `testing.md` - Testing strategies

### Maintain Consistency

When adding documentation:
- Include real code examples
- Show both ✅ DO and ❌ DON'T
- Link to related documents
- Add to table of contents in `docs/README.md`
- Follow the established structure

## 📧 Feedback

The documentation has been completely restructured. If you find:
- Missing information
- Unclear explanations
- Broken links
- Areas that need more examples

Please open an issue or submit a PR!

---

**Remember**: The [Philosophy](docs/philosophy.md) document is the key to understanding everything else. Start there! ⭐
