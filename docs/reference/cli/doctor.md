# vega doctor

Validate your project's structure and configuration (feature planned).

## Status

The `vega doctor` command is reserved for an upcoming diagnostic tool. Running it today prints a placeholder message:

```
🏥 Running Vega Doctor...
⚠️  Feature not implemented yet. Coming soon!
```

## Planned Checks

According to the roadmap, the doctor will eventually verify:

- Folder layout matches the expected Clean Architecture structure.
- `config.py` bootstraps the dependency injection container correctly.
- Modules respect layer boundaries (no forbidden imports).
- Optional scaffolds (FastAPI, SQLAlchemy) are wired consistently.

Follow the [roadmap](../ROADMAP.md) for updates or contribute ideas if you have specific validations that would help your team.
