# vega generate

Create Clean Architecture components for an existing Vega project.

## Usage

```bash
vega generate <component_type> <name> [OPTIONS]
```

The command must run from the project root (where `config.py` lives) unless you pass `--path`.

## Component Matrix

| Type | Aliases | Output location | Requirements |
|------|---------|-----------------|--------------|
| `entity` | – | `domain/entities/` | – |
| `repository` | `repo` | `domain/repositories/` (+ optional infrastructure) | – |
| `service` | – | `domain/services/` (+ optional infrastructure) | – |
| `interactor` | – | `domain/interactors/` | – |
| `mediator` | – | `application/mediators/` | – |
| `model` | – | `infrastructure/models/` | `vega add sqlalchemy` |
| `router` | – | `presentation/web/routes/` | `vega add web` |
| `middleware` | – | `presentation/web/middleware/` | `vega add web` |
| `webmodel` | – | `presentation/web/models/` | `vega add web`; `--request` or `--response` |
| `command` | – | `presentation/cli/commands/` | – |
| `event` | – | `domain/events/` | – |
| `event-handler` | `subscriber` | `events/` | – |

## Domain Layer Generators

### Entities (`entity`)

```bash
vega generate entity User
```

Produces a dataclass under `domain/entities/user.py`. The generator scaffolds the class and leaves placeholders for your fields.

### Repositories (`repository`, `repo`)

```bash
vega generate repository UserRepository
vega generate repository User --impl memory
```

Creates an abstract repository in `domain/repositories/`. If the corresponding entity does not exist, the CLI offers to create it automatically.

Use `--impl <name>` to also scaffold an infrastructure implementation in `infrastructure/repositories/`. Vega derives PascalCase and snake_case names for the implementation (e.g., `SqlUserRepository` → `sql_user_repository.py`).

### Services (`service`)

```bash
vega generate service EmailService
vega generate service Email --impl sendgrid
```

Similar to repositories, services live in `domain/services/`. The optional `--impl` flag creates an implementation under `infrastructure/services/`.

### Interactors (`interactor`)

```bash
vega generate interactor CreateUser
```

Interactors go to `domain/interactors/` and follow the Vega `Interactor` base class. The generator infers the target entity from common prefixes such as `Create`, `Update`, or `Get`.

## Application Layer Generators

### Mediators (`mediator`)

```bash
vega generate mediator CheckoutWorkflow
```

Creates a skeleton under `application/mediators/` for orchestrating multiple interactors.

## Events

### Domain Events (`event`)

```bash
vega generate event UserCreated
```

Outputs an immutable dataclass in `domain/events/`. The CLI prompts you for payload fields (name, type hint, description) and fills in the base `Event` plumbing.

### Event Handlers (`event-handler`, `subscriber`)

```bash
vega generate subscriber SendWelcomeEmail
```

Writes an async handler in the top-level `events/` package so auto-discovery can import it. You will be prompted for the event class/module, handler priority, and retry configuration. Remember to call `events.register_all_handlers()` during application startup so Vega loads every subscriber.

## Presentation Layer Generators

### FastAPI Router (`router`)

```bash
vega add web
vega generate router User
```

Requires the FastAPI scaffold. Generates `presentation/web/routes/user.py`, adds the router to `routes/__init__.py`, and reminds you to build request/response models and interactors.

### FastAPI Middleware (`middleware`)

```bash
vega generate middleware Logging
```

Creates `presentation/web/middleware/logging.py` and registers the import in the middleware package if it exists.

### Pydantic Models (`webmodel`)

```bash
vega generate webmodel CreateUserRequest --request
vega generate webmodel UserResponse --response
```

Also requires the FastAPI scaffold. Generates (or appends to) files under `presentation/web/models/`. You must specify one of `--request` or `--response`. If the target file already exists, Vega appends the new class instead of overwriting the file.

## Infrastructure Layer Generators

### SQLAlchemy Models (`model`)

```bash
vega add sqlalchemy
vega generate model Order
```

Places a SQLAlchemy model under `infrastructure/models/order.py`, auto-pluralises the table name, and attempts to import the model in `alembic/env.py` so Alembic can discover it. If the env file could not be updated automatically, the CLI prints the import snippet you need to add manually.

## CLI Command Generators

### Commands (`command`)

```bash
vega generate command CreateUser
vega generate command ReportMetrics --impl sync
```

Creates an interactive command generator under `presentation/cli/commands/`. By default the command is async and wraps the function with `@async_command`. Passing `--impl sync` (or `--impl simple`) produces a synchronous template.

During generation Vega asks for:

- Description text (used as the docstring/help).
- Optional options/arguments (name, type, requirement).
- Whether the command will call an interactor.

The generator also lays down `presentation/cli/commands/__init__.py` with auto-discovery utilities if it does not already exist.

## Options

- `--path PATH` – Run the generator against a project located somewhere else.
- `--impl NAME` – Valid for `repository`, `service`, and `command`. Adds an infrastructure implementation or switches the command template to synchronous mode.
- `--request`, `--response` – Required flags for `webmodel` to pick the correct template.

Attempting to use `--impl` on unsupported component types results in a warning and the flag is ignored.

## Auto-Discovery Highlights

- **Routers** are auto-imported from `presentation/web/routes/` via `routes/__init__.py`.
- **CLI commands** are auto-registered by iterating over `presentation/cli/commands/`.
- **Event handlers** are loaded when `events.register_all_handlers()` runs, which imports every module in the `events/` package.
- **SQLAlchemy models** receive an import in `alembic/env.py` so autogeneration sees them.

## Examples

```bash
# Full user flow
vega generate entity User
vega generate repository User --impl sql
vega generate interactor CreateUser
vega generate interactor GetUser
vega generate mediator UserLifecycle
vega add web
vega generate webmodel CreateUserRequest --request
vega generate webmodel UserResponse --response
vega generate router User
vega generate command create-user
```
