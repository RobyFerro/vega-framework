# vega web

Manage the FastAPI server that lives inside a Vega project.

## Usage

```bash
vega web <command> [OPTIONS]
```

The `web` command group is available after you add the FastAPI scaffold (`vega add web` or `vega init --template fastapi`).

## Commands

### run

```bash
vega web run [--host HOST] [--port PORT] [--reload] [--path PATH]
```

Starts `uvicorn` with the application defined in `presentation/web/main.py`.

Options:

- `--host` – Host interface (default `0.0.0.0`).
- `--port` – TCP port (default `8000`).
- `--reload` – Enable code reload on file changes (development only).
- `--path` – Use this project directory instead of the current working directory.

## Requirements

- The project must contain `config.py` and `presentation/web/main.py`. If they are missing, run `vega add web`.
- Install FastAPI dependencies:
  ```bash
  poetry add fastapi uvicorn[standard]
  ```
- Ensure your DI container (`config.py`) and any modules imported by `presentation/web/main.py` can be loaded without errors.

When the command runs, Vega:

1. Adds the project root to `sys.path` so imports resolve.
2. Imports `config` to bootstrap the dependency injection container.
3. Imports `presentation.web.main:app`.
4. Invokes `uvicorn.run()` with the supplied options.

Any import failures or missing packages are surfaced with actionable messages (for example, missing `uvicorn` or the web scaffold). Fix the highlighted issue and rerun the command.
