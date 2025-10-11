# vega update

Update the Vega Framework package (and CLI) to the latest release.

## Usage

```bash
vega update [OPTIONS]
```

The command checks PyPI for a newer version and installs it via the appropriate tool (`pipx` or `pip`).

## Options

### --check

```bash
vega update --check
```

Performs a version check without installing anything. Displays the current and latest versions and exits.

### --force

```bash
vega update --force
```

Reinstalls Vega even if you are already on the latest version. Useful when local files became corrupted.

## Behaviour Details

1. **Version lookup** – Contacts PyPI for the `vega-framework` metadata. If PyPI is unreachable you can choose whether to proceed (unless `--check` was used).
2. **pipx-aware** – If Vega was installed with `pipx`, the command runs `pipx upgrade vega-framework` (or `pipx reinstall` when `--force` is set). Otherwise it falls back to `python -m pip install --upgrade`.
3. **Error reporting** – Any installation failure prints the captured stderr so you can diagnose permission problems, virtual environments, or network hiccups. On failure the command exits with a non-zero status.

## Tips

- Run `vega update --check` regularly in CI to alert when a new release is available.
- If you manage Vega inside a Poetry project, upgrade the dependency in `pyproject.toml` instead of running this command inside the virtual environment.
- On Windows, `pipx` detection uses the `where` command. Ensure `pipx` is in `PATH` so the CLI can locate it. If detection fails, the command transparently falls back to `pip`.
