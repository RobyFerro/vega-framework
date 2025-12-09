# vega add

Add optional scaffolds to an existing Vega project.

## Usage

```bash
vega add <feature> [OPTIONS]
```

Valid features:

| Feature | Purpose |
|---------|---------|
| `web` | Adds Vega Web scaffold under `presentation/web/` |
| `sqlalchemy` | Adds SQLAlchemy database support |
| `db` | Alias for `sqlalchemy` |

## Requirements

- Run the command from your project root or provide `--path`.
- `config.py` must exist in the target folder (created by `vega init`).

## Options

### --path

```bash
vega add sqlalchemy --path ./my-project
```

Allows enabling features for a project located elsewhere.

## Vega Web Scaffold (`web`)

```bash
vega add web
```

Creates Vega Web boilerplate:

- `presentation/web/__init__.py`
- `presentation/web/app.py`
- `presentation/web/main.py`
- `presentation/web/routes/__init__.py`
- `presentation/web/routes/users.py`
- `presentation/web/models/__init__.py`
- `presentation/web/models/user_models.py`
- Auto-discovery support for new routers

**Next steps**

1. `poetry install` *(or `poetry update` to refresh dependencies)*
2. `vega web run --reload`
3. Visita `http://localhost:8000/docs`

## SQLAlchemy Support (`sqlalchemy` / `db`)

```bash
vega add sqlalchemy
```

Creates SQLAlchemy helpers and Alembic configuration:

- `infrastructure/database_manager.py`
- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/.gitkeep`
- Updates `config.py` to expose a `DatabaseManager` instance if missing
- Injects `sqlalchemy`, `alembic`, and `aiosqlite` into `pyproject.toml`
- Optional example repository (entity, interface, SQLAlchemy implementation, model)

**Next steps**

1. Define `DATABASE_URL` in `settings.py`.
2. Install dependencies:
   ```bash
   poetry add sqlalchemy aiosqlite alembic
   ```
3. Initialize database tables:
   ```bash
   vega migrate init
   ```
4. Autogenerate your first migration:
   ```bash
   vega migrate create -m "Initial migration"
   ```
5. Apply migrations:
   ```bash
   vega migrate upgrade
   ```

6. Wire infrastructure into `config.py` (e.g., bind `SQLAlchemyUserRepository` to `UserRepository`).

If you accept the example repository prompt, the CLI also generates:

- `domain/entities/user.py`
- `domain/repositories/user_repository.py`
- `infrastructure/models/user.py`
- `infrastructure/repositories/sqlalchemy_user_repository.py`

## Example Workflow

```bash
vega init store --template web
cd store
poetry install
vega add sqlalchemy
poetry add sqlalchemy aiosqlite alembic
vega migrate init
```

You now have Vega Web endpoints, CLI commands, and database scaffolding ready for your application.
