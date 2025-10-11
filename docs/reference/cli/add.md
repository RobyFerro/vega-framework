# vega add

Add optional scaffolds to an existing Vega project.

## Usage

```bash
vega add <feature> [OPTIONS]
```

Valid features:

| Feature | Purpose |
|---------|---------|
| `web` | Adds FastAPI scaffold under `presentation/web/` |
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

## FastAPI Scaffold (`web`)

```bash
vega add web
```

Creates FastAPI boilerplate:

- `presentation/web/app.py`
- `presentation/web/main.py`
- `presentation/web/routes/__init__.py`
- `presentation/web/routes/health.py`
- Auto-discovery support for new routers

**Next steps**

1. `poetry add fastapi uvicorn[standard]`
2. `vega web run --reload`
3. Hit `http://localhost:8000/api/health/status`

## SQLAlchemy Support (`sqlalchemy` / `db`)

```bash
vega add sqlalchemy
```

Creates SQLAlchemy helpers and Alembic configuration:

- `infrastructure/database_manager.py`
- `alembic.ini` and `alembic/` folder
- Base SQLAlchemy model template
- Optional example repository (entity, interface, implementation, model)

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

Update `config.py` to bind repositories (e.g., `SQLAlchemyUserRepository`) to their interfaces.

## Example Workflow

```bash
vega init store --template fastapi
cd store
poetry install
vega add sqlalchemy
poetry add sqlalchemy aiosqlite alembic
vega migrate init
```

You now have FastAPI endpoints, CLI commands, and database scaffolding ready for your application.
