"""Generate command - Create components in Vega project"""
import click
from pathlib import Path

from vega.cli.templates import (
    render_entity,
    render_infrastructure_repository,
    render_infrastructure_service,
    render_interactor,
    render_mediator,
    render_repository_interface,
    render_service_interface,
    render_fastapi_router,
    render_fastapi_middleware,
    render_sqlalchemy_model,
    render_cli_command,
    render_cli_command_simple,
    render_event,
    render_event_handler,
    render_template,
)
from vega.cli.scaffolds import create_fastapi_scaffold
from vega.cli.utils import to_snake_case, to_pascal_case


def _resolve_implementation_names(class_name: str, implementation: str) -> tuple[str, str]:
    """Derive implementation class and file names from flag input."""
    impl_pascal = to_pascal_case(implementation) or "Impl"
    base = class_name

    if impl_pascal.lower() in {"impl", "implementation"}:
        impl_class = f"{base}{impl_pascal}"
    elif base.lower().startswith(impl_pascal.lower()):
        impl_class = base
    else:
        impl_class = f"{impl_pascal}{base}"

    impl_file = to_snake_case(impl_class)
    return impl_class, impl_file


def generate_component(
    component_type: str,
    name: str,
    project_path: str,
    implementation: str | None = None,
    is_request: bool = False,
    is_response: bool = False,
):
    """Generate a component in the Vega project"""

    project_root = Path(project_path).resolve()

    # Check if we're in a Vega project
    if not (project_root / "config.py").exists():
        click.echo(click.style("ERROR: Error: Not a Vega project (config.py not found)", fg='red'))
        click.echo("   Run this command from your project root, or use --path option")
        return

    # Get project name from directory
    project_name = project_root.name

    class_name = to_pascal_case(name)
    implementation = implementation.strip() if implementation else None

    if component_type == 'repo':
        component_type = 'repository'
    if component_type in {'event-handler', 'subscriber'}:
        component_type = 'event_handler'

    suffixes = {
        "repository": "Repository",
        "service": "Service",
        "mediator": "Mediator",
    }

    if implementation and component_type not in {'repository', 'service'}:
        click.echo(
            click.style(
                "WARNING: Implementation option is only supported for repositories and services",
                fg='yellow',
            )
        )
        implementation = None

    if component_type in suffixes:
        suffix = suffixes[component_type]
        if class_name.lower().endswith(suffix.lower()):
            class_name = f"{class_name[:-len(suffix)]}{suffix}"
        else:
            class_name = f"{class_name}{suffix}"

    file_name = to_snake_case(class_name)

    if component_type == 'entity':
        _generate_entity(project_root, project_name, class_name, file_name)
    elif component_type == 'repository':
        _generate_repository(project_root, project_name, class_name, file_name, implementation)
    elif component_type == 'service':
        _generate_service(project_root, project_name, class_name, file_name, implementation)
    elif component_type == 'interactor':
        _generate_interactor(project_root, project_name, class_name, file_name)
    elif component_type == 'mediator':
        _generate_mediator(project_root, project_name, class_name, file_name)
    elif component_type == 'router':
        _generate_router(project_root, project_name, name)
    elif component_type == 'middleware':
        _generate_middleware(project_root, project_name, class_name, file_name)
    elif component_type == 'model':
        _generate_sqlalchemy_model(project_root, project_name, class_name, file_name)
    elif component_type == 'webmodel':
        _generate_web_models(project_root, project_name, name, is_request, is_response)
    elif component_type == 'command':
        _generate_command(project_root, project_name, name, implementation)
    elif component_type == 'event':
        _generate_event(project_root, project_name, class_name, file_name)
    elif component_type == 'event_handler':
        _generate_event_handler(project_root, project_name, class_name, file_name)


def _generate_entity(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate domain entity"""

    file_path = project_root / "domain" / "entities" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    content = render_entity(class_name)

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")


def _generate_repository(
    project_root: Path,
    project_name: str,
    class_name: str,
    file_name: str,
    implementation: str | None = None,
):
    """Generate repository interface"""

    # Remove 'Repository' suffix if present to get entity name
    entity_name = class_name[:-len('Repository')] if class_name.endswith('Repository') else class_name
    entity_file = to_snake_case(entity_name)

    file_path = project_root / "domain" / "repositories" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    # Check if entity exists
    entity_path = project_root / "domain" / "entities" / f"{entity_file}.py"
    if not entity_path.exists():
        click.echo(
            click.style(
                f"⚠️  Warning: Entity {entity_name} does not exist at {entity_path.relative_to(project_root)}",
                fg='yellow',
            )
        )

        if click.confirm(f"Do you want to create the entity {entity_name}?", default=True):
            _generate_entity(project_root, project_name, entity_name, entity_file)
            click.echo()  # Empty line for readability
        else:
            click.echo(click.style(f"ERROR: Cannot create repository without entity {entity_name}", fg='red'))
            return

    content = render_repository_interface(class_name, entity_name, entity_file)

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    # Suggest next steps
    click.echo(f"\n💡 Next steps:")
    click.echo(f"   1. Create entity: vega generate entity {entity_name}")
    click.echo(f"   2. Implement repository in infrastructure/repositories/")
    click.echo(f"   3. Register in config.py SERVICES dict")

    if implementation:
        _generate_infrastructure_repository(
            project_root,
            class_name,
            file_name,
            entity_name,
            entity_file,
            implementation,
        )


def _generate_service(
    project_root: Path,
    project_name: str,
    class_name: str,
    file_name: str,
    implementation: str | None = None,
):
    """Generate service interface"""

    file_path = project_root / "domain" / "services" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    content = render_service_interface(class_name)

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    click.echo(f"\n💡 Next steps:")
    click.echo(f"   1. Implement service in infrastructure/services/")
    click.echo(f"   2. Register in config.py SERVICES dict")

    if implementation:
        _generate_infrastructure_service(
            project_root,
            class_name,
            file_name,
            implementation,
        )


def _generate_interactor(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate interactor (use case)"""

    # Try to infer entity from name (e.g., CreateUser -> User)
    entity_name = class_name
    for prefix in ['Create', 'Update', 'Delete', 'Get', 'List', 'Find']:
        if class_name.startswith(prefix):
            entity_name = class_name[len(prefix):]
            break

    entity_file = to_snake_case(entity_name)

    file_path = project_root / "domain" / "interactors" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    content = render_interactor(class_name, entity_name, entity_file)

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    click.echo(f"\n💡 Usage:")
    click.echo(f"   result = await {class_name}(param=value)")


def _generate_mediator(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate mediator (workflow)"""

    file_path = project_root / "application" / "mediators" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    content = render_mediator(class_name)

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    click.echo(f"\n💡 Usage:")
    click.echo(f"   result = await {class_name}(param=value)")


def _generate_infrastructure_repository(
    project_root: Path,
    interface_class_name: str,
    interface_file_name: str,
    entity_name: str,
    entity_file: str,
    implementation: str,
) -> None:
    """Generate infrastructure repository implementation extending the domain interface."""
    impl_class, impl_file = _resolve_implementation_names(interface_class_name, implementation)
    file_path = project_root / "infrastructure" / "repositories" / f"{impl_file}.py"

    if file_path.exists():
        click.echo(click.style(f"WARNING: Implementation {file_path} already exists", fg='yellow'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = render_infrastructure_repository(
        impl_class,
        interface_class_name,
        interface_file_name,
        entity_name,
        entity_file,
    )

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")


def _generate_infrastructure_service(
    project_root: Path,
    interface_class_name: str,
    interface_file_name: str,
    implementation: str,
) -> None:
    """Generate infrastructure service implementation extending the domain interface."""
    impl_class, impl_file = _resolve_implementation_names(interface_class_name, implementation)
    file_path = project_root / "infrastructure" / "services" / f"{impl_file}.py"

    if file_path.exists():
        click.echo(click.style(f"WARNING: Implementation {file_path} already exists", fg='yellow'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = render_infrastructure_service(
        impl_class,
        interface_class_name,
        interface_file_name,
    )

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

def _generate_fastapi_web(project_root: Path, project_name: str, name: str) -> None:
    """Generate FastAPI web scaffold"""
    if name.lower() not in {"fastapi", "fast-api"}:
        click.echo(click.style("ERROR: Unsupported web scaffold. Use: vega generate web fastapi", fg='red'))
        return

    create_fastapi_scaffold(project_root, project_name)


def _register_router_in_init(project_root: Path, resource_file: str, resource_name: str) -> None:
    """Register a new router in routes/__init__.py"""
    routes_init = project_root / "presentation" / "web" / "routes" / "__init__.py"

    if not routes_init.exists():
        click.echo(click.style("WARNING: routes/__init__.py not found", fg='yellow'))
        return

    content = routes_init.read_text()
    lines = content.split('\n')

    # Check if already registered
    router_call = f"{resource_file}.router"
    if any(router_call in line for line in lines):
        click.echo(click.style(f"WARNING: Router {resource_file} already registered in routes/__init__.py", fg='yellow'))
        return

    # Find and update the import line
    import_updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith('from . import') and 'health' in line:
            # Parse existing imports
            imports_part = line.split('from . import')[1].strip()
            existing_imports = [imp.strip() for imp in imports_part.split(',')]

            # Check if already in imports (shouldn't happen, but just in case)
            if resource_file in existing_imports:
                break

            # Add new import alphabetically
            existing_imports.append(resource_file)
            existing_imports.sort()

            lines[i] = f"from . import {', '.join(existing_imports)}"
            import_updated = True
            break

    if not import_updated:
        # Fallback: add import line
        for i, line in enumerate(lines):
            if line.startswith('from fastapi import'):
                lines.insert(i + 2, f"from . import {resource_file}")
                break

    # Find the function and add the router registration
    last_include_idx = -1
    for i, line in enumerate(lines):
        if 'router.include_router' in line:
            last_include_idx = i

    if last_include_idx != -1:
        # Add the new router after the last include_router
        plural = f"{resource_file}s" if not resource_file.endswith('s') else resource_file
        new_line = f'    router.include_router({resource_file}.router, tags=["{resource_name}s"], prefix="/{plural}")'
        lines.insert(last_include_idx + 1, new_line)

    routes_init.write_text('\n'.join(lines))
    click.echo(f"+ Updated {click.style(str(routes_init.relative_to(project_root)), fg='green')}")


def _generate_router(project_root: Path, project_name: str, name: str) -> None:
    """Generate a Vega Web router for a resource"""

    # Check if web folder exists
    web_path = project_root / "presentation" / "web"
    if not web_path.exists():
        click.echo(click.style("ERROR: Web module not found", fg='red'))
        click.echo("   Router generation requires Vega Web module")
        click.echo("   Install it with: vega add web")
        return

    # Convert name to appropriate formats
    resource_name = to_pascal_case(name)
    resource_file = to_snake_case(resource_name)

    # Create routes directory if it doesn't exist
    routes_path = web_path / "routes"
    routes_path.mkdir(exist_ok=True)

    # Check if __init__.py exists, create with auto-discovery if not
    init_file = routes_path / "__init__.py"
    if not init_file.exists():
        from vega.cli.templates import render_fastapi_routes_init_autodiscovery
        init_file.write_text(render_fastapi_routes_init_autodiscovery())
        click.echo(f"+ Created {click.style(str(init_file.relative_to(project_root)), fg='green')}")

    # Generate router file
    router_file = routes_path / f"{resource_file}.py"

    if router_file.exists():
        click.echo(click.style(f"ERROR: Error: {router_file.relative_to(project_root)} already exists", fg='red'))
        return

    content = render_fastapi_router(resource_name, resource_file, project_name)
    router_file.write_text(content)

    click.echo(f"+ Created {click.style(str(router_file.relative_to(project_root)), fg='green')}")

    # Instructions for next steps
    click.echo(f"\nNext steps:")
    click.echo(f"   1. Create Pydantic models in presentation/web/models/{resource_file}_models.py")
    click.echo(f"   2. Implement domain interactors for {resource_name} operations")
    click.echo(f"   3. Replace in-memory storage with actual use cases")
    click.echo(click.style(f"   (Router auto-discovered from web/routes/)", fg='bright_black'))


def _generate_web_models(project_root: Path, project_name: str, name: str, is_request: bool, is_response: bool) -> None:
    """Generate Pydantic request or response model for Vega Web"""

    # Check if web folder exists
    web_path = project_root / "presentation" / "web"
    if not web_path.exists():
        click.echo(click.style("ERROR: Web module not found", fg='red'))
        click.echo("   Model generation requires Vega Web module")
        click.echo("   Install it with: vega add web")
        return

    # Validate flags
    if not is_request and not is_response:
        click.echo(click.style("ERROR: Must specify either --request or --response", fg='red'))
        click.echo("   Examples:")
        click.echo("      vega generate webmodel CreateUserRequest --request")
        click.echo("      vega generate webmodel UserResponse --response")
        return

    if is_request and is_response:
        click.echo(click.style("ERROR: Cannot specify both --request and --response", fg='red'))
        click.echo("   Use separate commands to generate both types")
        return

    # Ensure models directory exists
    models_path = web_path / "models"
    models_path.mkdir(exist_ok=True)

    # Ensure __init__.py exists
    init_file = models_path / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Pydantic models for API validation"""\n')

    # Convert name to PascalCase for class names
    model_name = to_pascal_case(name)
    model_file = to_snake_case(model_name)

    # Determine model type
    if is_request:
        template_file = "request_model.py.j2"
        description = "Request model for API validation"
        model_type = "request"
    else:
        template_file = "response_model.py.j2"
        description = "Response model for API data"
        model_type = "response"

    # Generate model file
    file_path = models_path / f"{model_file}.py"

    if file_path.exists():
        # Append to existing file
        click.echo(click.style(f"WARNING: {file_path.relative_to(project_root)} already exists", fg='yellow'))
        click.echo(f"   Appending {model_name} to existing file...")

        content = render_template(
            template_file,
            subfolder="web",
            model_name=model_name,
            description=description
        )

        # Remove imports from template since they're already in the file
        lines = content.split('\n')
        class_start = next((i for i, line in enumerate(lines) if line.startswith('class ')), 0)
        content_to_append = '\n\n' + '\n'.join(lines[class_start:])

        with file_path.open('a', encoding='utf-8') as f:
            f.write(content_to_append)

        click.echo(click.style("+ ", fg='green', bold=True) + f"Added {model_name} to {file_path.relative_to(project_root)}")
    else:
        # Create new file
        content = render_template(
            template_file,
            subfolder="web",
            model_name=model_name,
            description=description
        )
        file_path.write_text(content, encoding='utf-8')

        click.echo(click.style("+ ", fg='green', bold=True) + f"Created {file_path.relative_to(project_root)}")

    # Instructions for next steps
    click.echo(f"\nNext steps:")
    click.echo(f"   1. Add fields to {model_name} in {file_path.relative_to(project_root)}")
    click.echo(f"   2. Update the Config.json_schema_extra with example values")
    click.echo(f"   3. Import in your router:")
    click.echo(f"      from presentation.web.models.{model_file} import {model_name}")


def _generate_middleware(project_root: Path, project_name: str, class_name: str, file_name: str) -> None:
    """Generate a Vega Web middleware"""

    # Check if web folder exists
    web_path = project_root / "presentation" / "web"
    if not web_path.exists():
        click.echo(click.style("ERROR: Web module not found", fg='red'))
        click.echo("   Middleware generation requires Vega Web module")
        click.echo("   Install it with: vega add web")
        return

    # Remove 'Middleware' suffix if present to avoid duplication
    if class_name.endswith('Middleware'):
        class_name = class_name[:-len('Middleware')]

    file_name = to_snake_case(class_name)

    # Create middleware directory if it doesn't exist
    middleware_path = web_path / "middleware"
    middleware_path.mkdir(exist_ok=True)

    # Check if __init__.py exists
    init_file = middleware_path / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Vega Web Middlewares"""\n')
        click.echo(f"+ Created {click.style(str(init_file.relative_to(project_root)), fg='green')}")

    # Generate middleware file
    middleware_file = middleware_path / f"{file_name}.py"

    if middleware_file.exists():
        click.echo(click.style(f"ERROR: Error: {middleware_file.relative_to(project_root)} already exists", fg='red'))
        return

    content = render_fastapi_middleware(class_name, file_name)
    middleware_file.write_text(content)

    click.echo(f"+ Created {click.style(str(middleware_file.relative_to(project_root)), fg='green')}")

    # Warn if legacy app-level registration is present
    app_file = project_root / "presentation" / "web" / "app.py"
    if app_file.exists():
        app_content = app_file.read_text()
        legacy_call = f"app.add_middleware({class_name}Middleware"
        if legacy_call in app_content:
            click.echo(click.style(
                f"WARNING: Detected legacy app-level registration for {class_name}Middleware in presentation/web/app.py.",
                fg='yellow'
            ))
            click.echo(click.style(
                "         Route middleware should be applied with the @middleware decorator per route.",
                fg='yellow'
            ))

    # Instructions for next steps
    click.echo(f"\nNext steps:")
    click.echo(f"   1. Implement your middleware logic in {class_name}Middleware.before/after().")
    click.echo(f"   2. Apply it to routes using the @middleware decorator, for example:")
    click.echo(click.style(f'''      from vega.web import middleware
      from .middleware.{file_name} import {class_name}Middleware

      @router.get("/example")
      @middleware({class_name}Middleware())
      async def example():
          return {{"status": "ok"}}''', fg='cyan'))
    click.echo(f"   3. Restart your server to load the updated route middleware.")




def _generate_sqlalchemy_model(project_root: Path, project_name: str, class_name: str, file_name: str) -> None:
    """Generate a SQLAlchemy model"""

    # Check if infrastructure/database_manager.py exists
    db_manager_path = project_root / "infrastructure" / "database_manager.py"
    if not db_manager_path.exists():
        click.echo(click.style("ERROR: SQLAlchemy not configured", fg='red'))
        click.echo("   Model generation requires SQLAlchemy support")
        click.echo("   Install it with: vega add sqlalchemy")
        return

    # Create models directory if it doesn't exist
    models_path = project_root / "infrastructure" / "models"
    models_path.mkdir(exist_ok=True)

    # Check if __init__.py exists in models directory
    init_file = models_path / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""SQLAlchemy models"""\n')
        click.echo(f"+ Created {click.style(str(init_file.relative_to(project_root)), fg='green')}")

    # Generate model file
    model_file = models_path / f"{file_name}.py"

    if model_file.exists():
        click.echo(click.style(f"ERROR: Error: {model_file.relative_to(project_root)} already exists", fg='red'))
        return

    # Convert class name to table name (e.g., User -> users, ProductCategory -> product_categories)
    table_name = to_snake_case(class_name)
    if not table_name.endswith('s'):
        table_name = f"{table_name}s"

    content = render_sqlalchemy_model(class_name, table_name)
    model_file.write_text(content)

    click.echo(f"+ Created {click.style(str(model_file.relative_to(project_root)), fg='green')}")

    # Update alembic/env.py to import the model
    _register_model_in_alembic(project_root, class_name, file_name)

    # Instructions for next steps
    click.echo(f"\nNext steps:")
    click.echo(f"   1. Add columns to your model in {model_file.relative_to(project_root)}")
    click.echo(f"   2. Create migration: vega migrate create -m \"Add {table_name} table\"")
    click.echo(f"   3. Apply migration: vega migrate upgrade")


def _register_model_in_alembic(project_root: Path, class_name: str, file_name: str) -> None:
    """Register a new model in alembic/env.py"""
    env_file = project_root / "alembic" / "env.py"

    if not env_file.exists():
        click.echo(click.style("WARNING: alembic/env.py not found", fg='yellow'))
        click.echo(f"\nTo register manually, add to alembic/env.py:")
        click.echo(click.style(f'''
from infrastructure.models.{file_name} import {class_name}Model  # noqa: F401
''', fg='cyan'))
        return

    content = env_file.read_text()
    lines = content.split('\n')

    # Check if already registered
    model_import = f"from infrastructure.models.{file_name} import {class_name}Model"
    if any(model_import in line for line in lines):
        click.echo(click.style(f"WARNING: Model {class_name} already imported in alembic/env.py", fg='yellow'))
        return

    # Find the import section for models and add the new import
    import_added = False
    for i, line in enumerate(lines):
        # Look for existing model imports or the Base import
        if "from infrastructure.database_manager import Base" in line:
            # Add import after Base import
            lines.insert(i + 1, f"from infrastructure.models.{file_name} import {class_name}Model  # noqa: F401")
            import_added = True
            break
        elif "from infrastructure.models." in line or "from domain.entities." in line:
            # Add after other model imports
            lines.insert(i + 1, f"from infrastructure.models.{file_name} import {class_name}Model  # noqa: F401")
            import_added = True
            break

    if import_added:
        env_file.write_text('\n'.join(lines))
        click.echo(f"+ Updated {click.style('alembic/env.py', fg='green')} with model import")
    else:
        click.echo(click.style("WARNING: Could not auto-register model in alembic/env.py", fg='yellow'))
        click.echo(f"\nTo register manually, add to alembic/env.py:")
        click.echo(click.style(f'''
from infrastructure.models.{file_name} import {class_name}Model  # noqa: F401
''', fg='cyan'))


def _generate_command(project_root: Path, project_name: str, name: str, is_async: str | None = None) -> None:
    """Generate a CLI command"""
    
    # Check if presentation/cli exists
    cli_path = project_root / "presentation" / "cli"
    if not cli_path.exists():
        cli_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"+ Created {click.style(str(cli_path.relative_to(project_root)), fg='green')}")
    
    # Create commands directory if it doesn't exist
    commands_path = cli_path / "commands"
    commands_path.mkdir(exist_ok=True)

    # Check if __init__.py exists, create with auto-discovery if not
    init_file = commands_path / "__init__.py"
    if not init_file.exists():
        from vega.cli.templates import render_cli_commands_init
        init_file.write_text(render_cli_commands_init())
        click.echo(f"+ Created {click.style(str(init_file.relative_to(project_root)), fg='green')}")
    
    # Convert name to snake_case for command and file
    command_name = to_snake_case(name).replace('_', '-')
    file_name = to_snake_case(name)
    
    # Generate command file
    command_file = commands_path / f"{file_name}.py"
    
    if command_file.exists():
        click.echo(click.style(f"ERROR: Error: {command_file.relative_to(project_root)} already exists", fg='red'))
        return
    
    # Determine if async (default is async unless explicitly set to 'sync' or 'simple')
    use_async = is_async not in ['sync', 'simple', 'false', 'no'] if is_async else True
    
    # Prompt for command details
    description = click.prompt("Command description", default=f"{name} command")
    
    # Ask if user wants to add options/arguments
    add_params = click.confirm("Add options or arguments?", default=False)
    
    options = []
    arguments = []
    params_list = []
    
    if add_params:
        click.echo("\nAdd options (e.g., --name, --email). Press Enter when done.")
        while True:
            opt_name = click.prompt("Option name (without --)", default="", show_default=False)
            if not opt_name:
                break
            opt_type = click.prompt("Type", default="str", type=click.Choice(['str', 'int', 'bool']))
            opt_required = click.confirm("Required?", default=False)
            opt_help = click.prompt("Help text", default=f"{opt_name.replace('-', ' ').replace('_', ' ')}")
            
            params_list.append(opt_name.replace('-', '_'))
            
            opt_params = f"help='{opt_help}'"
            if opt_required:
                opt_params += ", required=True"
            if opt_type != 'str':
                if opt_type == 'bool':
                    opt_params += ", is_flag=True"
                else:
                    opt_params += f", type={opt_type}"
            
            options.append({
                "flag": f"--{opt_name}",
                "params": opt_params
            })
        
        click.echo("\nAdd arguments (positional). Press Enter when done.")
        while True:
            arg_name = click.prompt("Argument name", default="", show_default=False)
            if not arg_name:
                break
            arg_required = click.confirm("Required?", default=True)
            
            params_list.append(arg_name)
            
            arg_params = "" if arg_required else ", required=False"
            arguments.append({
                "name": arg_name,
                "params": arg_params
            })
    
    params_signature = ", ".join(params_list) if params_list else ""
    
    # Ask about interactor usage
    with_interactor = False
    interactor_name = ""
    if use_async:
        with_interactor = click.confirm("Will this command use an interactor?", default=True)
        if with_interactor:
            interactor_name = click.prompt("Interactor name", default=f"{to_pascal_case(name)}")
    
    usage_example = f"python main.py {command_name}"
    if params_list:
        usage_example += " " + " ".join([f"--{p.replace('_', '-')}=value" if f"--{p.replace('_', '-')}" in str(options) else p for p in params_list])
    
    # Generate content
    if use_async:
        content = render_cli_command(
            command_name=file_name,
            description=description,
            options=options,
            arguments=arguments,
            params_signature=params_signature,
            params_list=params_list,
            with_interactor=with_interactor,
            usage_example=usage_example,
            interactor_name=interactor_name,
        )
    else:
        content = render_cli_command_simple(
            command_name=file_name,
            description=description,
            options=options,
            arguments=arguments,
            params_signature=params_signature,
            params_list=params_list,
        )
    
    command_file.write_text(content)
    click.echo(f"+ Created {click.style(str(command_file.relative_to(project_root)), fg='green')}")
    
    # Instructions for next steps
    click.echo(f"\nNext steps:")
    click.echo(f"   1. Implement your command logic in {command_file.relative_to(project_root)}")
    click.echo(f"   2. Run your command: python main.py {command_name}")
    click.echo(click.style(f"      (Commands are auto-discovered from cli/commands/)", fg='bright_black'))
    if with_interactor:
        click.echo(f"   3. Create interactor: vega generate interactor {interactor_name}")


def _generate_event(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate a domain event."""

    events_path = project_root / "domain" / "events"
    events_path.mkdir(parents=True, exist_ok=True)

    init_file = events_path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    file_path = events_path / f"{file_name}.py"
    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path.relative_to(project_root)} already exists", fg='red'))
        return

    click.echo("\nDefine event payload fields (press Enter to skip):")
    fields: list[dict[str, str]] = []
    while True:
        field_name = click.prompt("Field name", default="", show_default=False)
        if not field_name:
            break
        snake_name = to_snake_case(field_name)
        type_hint = click.prompt("Type hint", default="str")
        description = click.prompt(
            "Description",
            default=f"{snake_name.replace('_', ' ').capitalize()} value",
        )
        fields.append(
            {
                "name": snake_name,
                "type_hint": type_hint,
                "description": description,
            }
        )

    content = render_event(class_name, fields)
    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    click.echo("\nNext steps:")
    click.echo("   1. Publish the event from your domain logic.")
    click.echo("   2. Generate subscribers: vega generate subscriber <HandlerName>")


def _generate_event_handler(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate an application-level event handler/subscriber in events/ for auto-discovery."""

    handlers_path = project_root / "events"
    handlers_path.mkdir(parents=True, exist_ok=True)

    init_file = handlers_path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    handler_file = handlers_path / f"{file_name}.py"
    if handler_file.exists():
        click.echo(click.style(f"ERROR: Error: {handler_file.relative_to(project_root)} already exists", fg='red'))
        return

    default_event_class = class_name
    if default_event_class.lower().endswith("handler"):
        default_event_class = default_event_class[:-7] or class_name

    event_class = click.prompt("Event class name", default=default_event_class)
    event_module_default = f"domain.events.{to_snake_case(event_class)}"
    event_module = click.prompt("Event module path", default=event_module_default)

    priority = click.prompt("Handler priority (higher runs first)", default=0, type=int)
    retry_on_error = click.confirm("Retry on failure?", default=False)
    max_retries = None
    if retry_on_error:
        max_retries = click.prompt("Max retries", default=3, type=int)

    decorator_args = event_class
    options: list[str] = []
    if priority:
        options.append(f"priority={priority}")
    if retry_on_error:
        options.append("retry_on_error=True")
        if max_retries is not None:
            options.append(f"max_retries={max_retries}")
    if options:
        decorator_args = f"{event_class}, " + ", ".join(options)

    handler_func_name = to_snake_case(class_name)

    content = render_event_handler(
        class_name=class_name,
        handler_func_name=handler_func_name,
        event_name=event_class,
        event_module=event_module,
        decorator_args=decorator_args,
    )

    handler_file.write_text(content)
    click.echo(f"+ Created {click.style(str(handler_file.relative_to(project_root)), fg='green')}")

    click.echo("\nNext steps:")
    click.echo(f"   1. Implement your handler in {handler_file.relative_to(project_root)}")
    click.echo("   2. Call events.register_all_handlers() during startup so auto-discovery loads it.")
    click.echo("   3. Run your workflow and verify the subscriber reacts to the event.")
