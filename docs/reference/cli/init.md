# vega init

Scaffold a new Vega project with a Clean Architecture layout.

## Usage

```bash
vega init <project_name> [OPTIONS]
```

Run the command in the directory where you want the project folder to be created.

## Options

### --template <basic|web|ai-rag>

```bash
vega init my-service --template web
```

- `basic` (default) - CLI-first layout with a ready-to-use `main.py`.
- `web` - Adds the Vega Web scaffold under `presentation/web/` and writes a Vega Web-specific `main.py`. Run `vega web run` to start the server.
- `fastapi` - Legacy alias for `web` kept for backward compatibility.
- `ai-rag` - Reserved template name for future AI/RAG tooling. For now it produces the same structure as `basic` so you can migrate seamlessly when the dedicated scaffold lands.

### --path PATH

```bash
vega init billing --path ./apps
```

Creates the project under `PATH/project_name` instead of the current working directory.

## Generated Structure

```
project_name/
├── domain/
│   ├── entities/
│   ├── repositories/
│   ├── services/
│   └── interactors/
├── application/mediators/
├── infrastructure/
│   ├── repositories/
│   └── services/
├── presentation/
│   └── cli/commands/__init__.py  # auto-discovers CLI commands
├── events/__init__.py            # auto-registers event handlers
├── tests/(domain|application|infrastructure|presentation)/
├── config.py                     # dependency injection container
├── settings.py                   # pydantic-based settings
├── .env.example                  # starter environment variables
├── .gitignore
├── pyproject.toml                # Poetry configuration (pinning current vega version)
├── README.md                     # project overview
├── ARCHITECTURE.md               # layer responsibilities
└── main.py                       # CLI entry point (Vega Web-specific when template=web)
```

When the web template is selected (`--template web` or the legacy `--template fastapi`), the command also runs `vega add web` internally to create:

- `presentation/web/app.py`
- `presentation/web/main.py`
- `presentation/web/routes/{__init__.py,health.py,users.py}`
- `presentation/web/models/{__init__.py,user_models.py}`

## Next Steps

```bash
cd project_name
poetry install
cp .env.example .env
```

- Add infrastructure implementations and bind them in `config.py`.
- Generate new components with `vega generate ...`.
- When using the web template:
  ```bash
  vega web run --reload
  ```
- For database support run `vega add sqlalchemy` and follow the prompts.

The generated `README.md` contains a quick reference tailored to the chosen template, so keep it handy for onboarding teammates.
