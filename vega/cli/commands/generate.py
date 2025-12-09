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
    render_listener,
    render_template,
    # CQRS
    render_cqrs_handler,
    render_cqrs_command,
    render_cqrs_query,
    render_cqrs_response,
    # DDD
    render_aggregate,
    render_value_object,
)
from vega.cli.scaffolds import create_fastapi_scaffold
from vega.cli.utils import to_snake_case, to_pascal_case


def _has_bounded_context_root(project_root: Path) -> bool:
    """Return True if the project contains a bounded-context root (lib/ or <pkg_name>/)."""
    normalized_name = project_root.name.replace('-', '_')
    return (project_root / "lib").exists() or (project_root / normalized_name).exists()


def _find_project_root(start_path: Path) -> Path | None:
    """
    Walk upwards from start_path until a directory containing config.py is found.
    Returns None if not found.
    """
    current = start_path
    while True:
        if (current / "config.py").exists():
            return current
        if current.parent == current:
            # Reached filesystem root
            return None
        current = current.parent


def _detect_bounded_context(project_root: Path) -> str | None:
    """
    Detect which bounded context we're in based on current directory or by prompting the user.

    Supports both legacy lib/ structure and the new package-based layout
    (<project_name>/<context>/...). If no bounded-context root is present,
    returns None to allow legacy flat projects.
    """
    normalized_name = project_root.name.replace('-', '_')
    lib_path = project_root / "lib"
    package_path = project_root / normalized_name

    # Collect potential context roots (prefer package layout)
    context_roots: list[Path] = []
    if package_path.exists():
        context_roots.append(package_path)
    if lib_path.exists():
        context_roots.append(lib_path)

    if not context_roots:
        return None  # Legacy flat structure

    # Try to detect context from current working directory
    cwd = Path.cwd()
    for root in context_roots:
        try:
            relative = cwd.relative_to(root)
            if relative.parts:
                return relative.parts[0]
        except (ValueError, IndexError):
            continue

    # Build available contexts list (deduplicated, preserve order)
    contexts: list[str] = []
    for root in context_roots:
        for d in root.iterdir():
            if d.is_dir() and not d.name.startswith('_') and d.name != 'shared':
                if d.name not in contexts:
                    contexts.append(d.name)

    if not contexts:
        root_hint = package_path if package_path.exists() else lib_path
        click.echo(click.style(f"ERROR: No bounded contexts found in {root_hint.name}/", fg='red'))
        click.echo("Create a context first with: vega generate context <name>")
        return None

    if len(contexts) == 1:
        click.echo(f"Using context: {click.style(contexts[0], fg='cyan')}")
        return contexts[0]

    click.echo("\nAvailable contexts:")
    for i, ctx in enumerate(contexts, 1):
        click.echo(f"  {i}. {ctx}")

    try:
        choice = click.prompt("Select context", type=click.IntRange(1, len(contexts)))
        return contexts[choice - 1]
    except (click.Abort, KeyboardInterrupt):
        click.echo("\nCancelled.")
        return None


def _get_context_base_path(project_root: Path, context: str | None) -> Path:
    """
    Get base path for generating components.

    Args:
        project_root: Root of the project
        context: Bounded context name (None for legacy structure)

    Returns:
        Base path where components should be created
    """
    if context is None:
        return project_root  # Legacy structure

    normalized_name = project_root.name.replace('-', '_')
    package_path = project_root / normalized_name / context
    if package_path.exists():
        return package_path

    # Fallback to legacy lib/ structure
    return project_root / "lib" / context


def _get_module_base(project_root: Path, context: str | None, project_name: str | None = None) -> str:
    """
    Calculate the module base for imports based on the project structure.

    Args:
        project_root: Root of the project
        context: Bounded context name (None for legacy structure)
        project_name: Project name (if None, derived from project_root.name)

    Returns:
        Module base string for absolute imports (e.g., 'myproject.billing' or 'lib.billing'),
        or empty string for legacy structure (to use relative imports)
    """
    if context is None:
        return ""  # Legacy structure - use relative/legacy imports

    if project_name is None:
        project_name = project_root.name

    normalized_name = project_name.replace('-', '_')

    # Check if package structure exists
    package_path = project_root / normalized_name / context
    if package_path.exists():
        return f"{normalized_name}.{context}"

    # Fallback to lib/ structure
    lib_path = project_root / "lib" / context
    if lib_path.exists():
        return f"lib.{context}"

    # If neither exists, use package structure by default (for new contexts)
    return f"{normalized_name}.{context}"


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
    demo_router: bool = False,
):
    """Generate a component in the Vega project"""

    start_path = Path(project_path).resolve()
    project_root = _find_project_root(start_path)

    # Check if we're in a Vega project
    if project_root is None:
        click.echo(click.style("ERROR: Error: Not a Vega project (config.py not found)", fg='red'))
        click.echo(f"   Path checked: {start_path}")
        click.echo("   Run this command from your project root, or point --path to the project")
        return

    # Get project name from directory
    project_name = project_root.name

    class_name = to_pascal_case(name)
    implementation = implementation.strip() if implementation else None

    # Handle aliases
    if component_type == 'repo':
        component_type = 'repository'
    if component_type in {'event-handler', 'subscriber'}:
        component_type = 'event_handler'
    if component_type == 'value-object':
        component_type = 'value_object'
    if component_type == 'domain-event':
        component_type = 'event'

    suffixes = {
        "repository": "Repository",
        "service": "Service",
        "mediator": "Mediator",
    }

    if implementation and component_type not in {'repository', 'service', 'interactor'}:
        click.echo(
            click.style(
                "WARNING: Implementation option is only supported for repositories, services, and interactors (as CQRS type)",
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

    if demo_router and component_type != 'router':
        click.echo(
            click.style(
                "WARNING: --demo-router is ignored for component types other than 'router'",
                fg='yellow',
            )
        )

    # DDD generators (context-aware)
    if component_type == 'context':
        _generate_context(project_root, project_name, name)
    elif component_type == 'aggregate':
        _generate_aggregate(project_root, project_name, class_name, file_name)
    elif component_type == 'value_object':
        _generate_value_object(project_root, project_name, class_name, file_name)
    # CQRS generators
    elif component_type == 'command':
        # Default: CQRS command handler
        # With --impl=cli: CLI command
        if implementation and implementation.lower() == 'cli':
            _generate_command(project_root, project_name, name, None)
        else:
            _generate_interactor(project_root, project_name, class_name, file_name, 'command')
    elif component_type == 'query':
        _generate_interactor(project_root, project_name, class_name, file_name, 'query')
    # Existing generators
    elif component_type == 'entity':
        _generate_entity(project_root, project_name, class_name, file_name)
    elif component_type == 'repository':
        _generate_repository(project_root, project_name, class_name, file_name, implementation)
    elif component_type == 'service':
        _generate_service(project_root, project_name, class_name, file_name, implementation)
    elif component_type == 'interactor':
        _generate_interactor(project_root, project_name, class_name, file_name, implementation)
    elif component_type == 'mediator':
        _generate_mediator(project_root, project_name, class_name, file_name)
    elif component_type == 'router':
        _generate_router(project_root, project_name, name, demo_router=demo_router)
    elif component_type == 'middleware':
        _generate_middleware(project_root, project_name, class_name, file_name)
    elif component_type == 'model':
        _generate_sqlalchemy_model(project_root, project_name, class_name, file_name)
    elif component_type == 'webmodel':
        _generate_web_models(project_root, project_name, name, is_request, is_response)
    elif component_type == 'cli_command':
        _generate_command(project_root, project_name, name, implementation)
    elif component_type == 'event':
        _generate_event(project_root, project_name, class_name, file_name)
    elif component_type == 'event_handler':
        _generate_event_handler(project_root, project_name, class_name, file_name)
    elif component_type == 'listener':
        _generate_listener(project_root, project_name, class_name, file_name)
    else:
        click.echo(click.style(f"ERROR: Unknown component type: {component_type}", fg='red'))
        click.echo("Supported types: context, aggregate, value-object, command, query, entity, repository, service, etc.")


def _generate_entity(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate domain entity (context-aware)"""
    context = _detect_bounded_context(project_root)
    if context is None and _has_bounded_context_root(project_root):
        return  # Error already shown

    base_path = _get_context_base_path(project_root, context)
    file_path = base_path / "domain" / "entities" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)
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
    """Generate repository interface (context-aware)"""
    context = _detect_bounded_context(project_root)
    if context is None and _has_bounded_context_root(project_root):
        return  # Error already shown

    base_path = _get_context_base_path(project_root, context)

    # Remove 'Repository' suffix if present to get entity name
    entity_name = class_name[:-len('Repository')] if class_name.endswith('Repository') else class_name
    entity_file = to_snake_case(entity_name)

    file_path = base_path / "domain" / "repositories" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    # Check if entity or aggregate exists
    entity_path = base_path / "domain" / "entities" / f"{entity_file}.py"
    aggregate_path = base_path / "domain" / "aggregates" / f"{entity_file}.py"
    aggregate_exists = aggregate_path.exists()
    entity_exists = entity_path.exists()
    resource_folder = "aggregates" if aggregate_exists else "entities"

    if not entity_exists and not aggregate_exists:
        click.echo(
            click.style(
                f"⚠️  Warning: neither Entity nor Aggregate named {entity_name} exists "
                f"(checked {entity_path.relative_to(project_root)} and {aggregate_path.relative_to(project_root)})",
                fg='yellow',
            )
        )
        choice = click.prompt(
            "Create missing type",
            type=click.Choice(['entity', 'aggregate'], case_sensitive=False),
            default='entity'
        )
        if choice == 'entity':
            _generate_entity(project_root, project_name, entity_name, entity_file)
            resource_folder = "entities"
        else:
            _generate_aggregate(project_root, project_name, entity_name, entity_file)
            resource_folder = "aggregates"
        click.echo()  # spacing
    else:
        # Show what we found
        if entity_exists:
            click.echo(click.style(f"✔ Found entity at {entity_path.relative_to(project_root)}", fg='green'))
        if aggregate_exists:
            click.echo(click.style(f"✔ Found aggregate at {aggregate_path.relative_to(project_root)}", fg='green'))

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate module base for imports
    domain_module_base = _get_module_base(project_root, context, project_name)

    content = render_repository_interface(
        class_name=class_name,
        entity_name=entity_name,
        entity_file=entity_file,
        resource_folder=resource_folder,
        domain_module_base=domain_module_base,
    )
    file_path.write_text(content)

    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    # Suggest next steps
    infra_path = "lib/{context}/infrastructure/repositories/" if context else "infrastructure/repositories/"
    click.echo(f"\n💡 Next steps:")
    click.echo(f"   1. Create entity: vega generate entity {entity_name}")
    click.echo(f"   2. Implement repository in {infra_path}")
    click.echo(f"   3. Register in config.py SERVICES dict")

    if implementation:
        _generate_infrastructure_repository(
            project_root,
            project_name,
            class_name,
            file_name,
            entity_name,
            entity_file,
            implementation,
            context,
            resource_folder,
        )


def _generate_service(
    project_root: Path,
    project_name: str,
    class_name: str,
    file_name: str,
    implementation: str | None = None,
):
    """Generate service interface (context-aware)"""
    context = _detect_bounded_context(project_root)
    if context is None and _has_bounded_context_root(project_root):
        return  # Error already shown

    base_path = _get_context_base_path(project_root, context)

    # Services go in domain layer for DDD (domain services)
    # Or in application layer for application services
    # Default to domain for now
    file_path = base_path / "domain" / "services" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate module base for imports
    domain_module_base = _get_module_base(project_root, context, project_name)
    application_module_base = domain_module_base  # Same base for application layer

    content = render_service_interface(
        class_name,
        domain_module_base=domain_module_base,
        application_module_base=application_module_base,
    )
    file_path.write_text(content)

    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    click.echo(f"\n💡 Next steps:")
    click.echo(f"   1. Implement service in infrastructure/services/")
    click.echo(f"   2. Register in config.py SERVICES dict")

    if implementation:
        _generate_infrastructure_service(
            project_root,
            project_name,
            class_name,
            file_name,
            implementation,
            context,
        )


def _generate_interactor(project_root: Path, project_name: str, class_name: str, file_name: str, cqrs_type: str | None = None):
    """Generate interactor (use case) with CQRS pattern"""

    # Detect bounded context so generated files land in the right folder
    context = _detect_bounded_context(project_root)
    if context is None and _has_bounded_context_root(project_root):
        return  # Error already shown by detector
    base_path = _get_context_base_path(project_root, context)

    # If no CQRS type specified, ask the user
    if not cqrs_type:
        cqrs_type = click.prompt(
            "CQRS type",
            type=click.Choice(['command', 'query'], case_sensitive=False),
            default='command'
        ).lower()

    # Normalize type
    cqrs_type = cqrs_type.lower()

    # Determine layer folder (commands or queries)
    layer_folder = 'commands' if cqrs_type == 'command' else 'queries'
    handler_type = 'COMMAND' if cqrs_type == 'command' else 'QUERY'

    # Folder name for the interactor (snake_case)
    folder_name = file_name

    # Create the interactor directory
    interactor_dir = base_path / "application" / layer_folder / folder_name

    if interactor_dir.exists():
        click.echo(click.style(f"ERROR: Error: {interactor_dir.relative_to(project_root)} already exists", fg='red'))
        return

    interactor_dir.mkdir(parents=True, exist_ok=True)

    # Prepare file names and class names
    input_file = f"{file_name}_{cqrs_type}"  # e.g., create_user_command.py
    input_class = f"{class_name}{cqrs_type.capitalize()}"  # CreateUserCommand or GetUserQuery
    input_var = cqrs_type  # command or query
    response_file = f"{file_name}_response"
    response_class = f"{class_name}Result"

    # Ask for description
    description = click.prompt("Description", default=f"{class_name} {cqrs_type}")

    # Build import base module (handles bounded context)
    if base_path == project_root:
        app_module = "application"
        domain_module_base = ""
    else:
        app_module = f"{base_path.relative_to(project_root).as_posix().replace('/', '.')}.application"
        domain_module_base = _get_module_base(project_root, context, project_name)

    # Generate handler.py
    handler_content = render_cqrs_handler(
        class_name=class_name,
        handler_type=handler_type,
        layer_folder=layer_folder,
        folder_name=folder_name,
        app_module=app_module,
        input_file=input_file,
        input_class=input_class,
        input_var=input_var,
        response_file=response_file,
        response_class=response_class,
        description=description,
        domain_module_base=domain_module_base,
    )
    handler_file = interactor_dir / f"{file_name}_handler.py"
    handler_file.write_text(handler_content)
    click.echo(f"+ Created {click.style(str(handler_file.relative_to(project_root)), fg='green')}")

    # Generate command.py or query.py
    if cqrs_type == 'command':
        input_content = render_cqrs_command(class_name, description)
    else:
        input_content = render_cqrs_query(input_class, class_name, description)

    input_file_path = interactor_dir / f"{input_file}.py"
    input_file_path.write_text(input_content)
    click.echo(f"+ Created {click.style(str(input_file_path.relative_to(project_root)), fg='green')}")

    # Generate response.py
    response_content = render_cqrs_response(class_name, description)
    response_file_path = interactor_dir / f"{response_file}.py"
    response_file_path.write_text(response_content)
    click.echo(f"+ Created {click.style(str(response_file_path.relative_to(project_root)), fg='green')}")

    # Create __init__.py for easier imports
    init_content = f'''"""{ class_name} {cqrs_type} - CQRS Pattern"""
from .{file_name}_handler import {class_name}Handler
from .{input_file} import {input_class}
from .{response_file} import {response_class}

__all__ = [
    "{class_name}Handler",
    "{input_class}",
    "{response_class}",
]
'''
    init_file = interactor_dir / "__init__.py"
    init_file.write_text(init_content)
    click.echo(f"+ Created {click.style(str(init_file.relative_to(project_root)), fg='green')}")

    # Usage instructions
    click.echo(f"\nUsage:")
    click.echo(f"   from {app_module}.{layer_folder}.{folder_name} import {class_name}Handler, {input_class}")
    click.echo(f"   {input_var} = {input_class}(...)  # Add your parameters")
    click.echo(f"   result = await {class_name}Handler({input_var})")


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
    project_name: str,
    interface_class_name: str,
    interface_file_name: str,
    entity_name: str,
    entity_file: str,
    implementation: str,
    context: str | None = None,
    resource_folder: str = "entities",
) -> None:
    """Generate infrastructure repository implementation (context-aware)."""
    impl_class, impl_file = _resolve_implementation_names(interface_class_name, implementation)

    base_path = _get_context_base_path(project_root, context)
    file_path = base_path / "infrastructure" / "repositories" / f"{impl_file}.py"

    if file_path.exists():
        click.echo(click.style(f"WARNING: Implementation {file_path} already exists", fg='yellow'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate module base for imports
    domain_module_base = _get_module_base(project_root, context, project_name)

    content = render_infrastructure_repository(
        impl_class,
        interface_class_name,
        interface_file_name,
        entity_name,
        entity_file,
        resource_folder,
        domain_module_base=domain_module_base,
    )

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")


def _generate_infrastructure_service(
    project_root: Path,
    project_name: str,
    interface_class_name: str,
    interface_file_name: str,
    implementation: str,
    context: str | None = None,
) -> None:
    """Generate infrastructure service implementation extending the domain interface."""
    impl_class, impl_file = _resolve_implementation_names(interface_class_name, implementation)

    # Detect bounded context if not provided
    if context is None:
        context = _detect_bounded_context(project_root)

    base_path = _get_context_base_path(project_root, context)
    file_path = base_path / "infrastructure" / "services" / f"{impl_file}.py"

    if file_path.exists():
        click.echo(click.style(f"WARNING: Implementation {file_path} already exists", fg='yellow'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate module base for imports
    application_module_base = _get_module_base(project_root, context, project_name)

    content = render_infrastructure_service(
        impl_class,
        interface_class_name,
        interface_file_name,
        application_module_base=application_module_base,
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


def _generate_router(project_root: Path, project_name: str, name: str, demo_router: bool = False) -> None:
    """Generate a Vega Web router for a resource (context-aware)"""

    # Detect bounded context
    context = _detect_bounded_context(project_root)
    base_path = _get_context_base_path(project_root, context)

    # Check if web folder exists in context
    web_path = base_path / "presentation" / "web"
    if not web_path.exists():
        click.echo(click.style("ERROR: Web module not found", fg='red'))
        if context:
            click.echo(f"   Router generation requires web structure in context '{context}'")
            click.echo(f"   Create it: mkdir -p {web_path / 'routes'}")
        else:
            click.echo("   Router generation requires Vega Web module")
            click.echo("   Web support is included by default in new projects (vega init <name>)")
        return

    # Convert name to appropriate formats
    resource_name = to_pascal_case(name)
    resource_file = to_snake_case(resource_name)

    # Create routes directory if it doesn't exist
    routes_path = web_path / "routes"
    routes_path.mkdir(parents=True, exist_ok=True)

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

    content = render_fastapi_router(
        resource_name=resource_name,
        resource_file=resource_file,
        project_name=project_name,
        demo=demo_router,
    )
    router_file.write_text(content)

    click.echo(f"+ Created {click.style(str(router_file.relative_to(project_root)), fg='green')}")

    # Instructions for next steps
    click.echo(f"\nNext steps:")
    click.echo(f"   1. Create Pydantic models in presentation/web/models/{resource_file}_models.py")
    click.echo(f"   2. Implement domain interactors for {resource_name} operations")
    click.echo(f"   3. Replace in-memory storage with actual use cases")
    click.echo(click.style(f"   (Router auto-discovered from web/routes/)", fg='bright_black'))


def _generate_web_models(project_root: Path, project_name: str, name: str, is_request: bool, is_response: bool) -> None:
    """Generate Pydantic request or response model for Vega Web (context-aware)"""

    # Detect bounded context
    context = _detect_bounded_context(project_root)
    base_path = _get_context_base_path(project_root, context)

    # Check if web folder exists in context
    web_path = base_path / "presentation" / "web"
    if not web_path.exists():
        click.echo(click.style("ERROR: Web module not found", fg='red'))
        if context:
            click.echo(f"   Model generation requires web structure in context '{context}'")
        else:
            click.echo("   Model generation requires Vega Web module")
            click.echo("   Web support is included by default in new projects (vega init <name>)")
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
    models_path.mkdir(parents=True, exist_ok=True)

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
        click.echo("   Web support is included by default in new projects (vega init <name>)")
        return

    # Remove 'Middleware' suffix if present to avoid duplication
    if class_name.endswith('Middleware'):
        class_name = class_name[:-len('Middleware')]

    file_name = to_snake_case(class_name)

    # Create middleware directory if it doesn't exist
    middleware_path = web_path / "middleware"
    middleware_path.mkdir(exist_ok=True)

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
    # Detect bounded context to find correct base path
    context = _detect_bounded_context(project_root)
    base_path = _get_context_base_path(project_root, context)
    models_path = base_path / "infrastructure" / "models"
    models_path.mkdir(parents=True, exist_ok=True)

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
    """Generate a CLI command (context-aware)"""

    # Detect bounded context
    context = _detect_bounded_context(project_root)
    base_path = _get_context_base_path(project_root, context)

    # Check if presentation/cli exists in context
    cli_path = base_path / "presentation" / "cli"
    if not cli_path.exists():
        cli_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"+ Created {click.style(str(cli_path.relative_to(project_root)), fg='green')}")

    # Create commands directory if it doesn't exist
    commands_path = cli_path / "commands"
    commands_path.mkdir(parents=True, exist_ok=True)

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
    """Generate a domain event (context-aware)."""
    context = _detect_bounded_context(project_root)
    if context is None and _has_bounded_context_root(project_root):
        return  # Error already shown

    base_path = _get_context_base_path(project_root, context)
    events_path = base_path / "domain" / "events"
    events_path.mkdir(parents=True, exist_ok=True)

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


def _generate_listener(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate a job queue listener in infrastructure/listeners/"""

    listeners_path = project_root / "infrastructure" / "listeners"
    listeners_path.mkdir(parents=True, exist_ok=True)

    listener_file = listeners_path / f"{file_name}.py"
    if listener_file.exists():
        click.echo(click.style(f"ERROR: {listener_file.relative_to(project_root)} already exists", fg='red'))
        return

    # Prompt for listener configuration
    default_queue = to_snake_case(class_name.replace("Listener", ""))
    queue_name = click.prompt("Queue name", default=default_queue)
    workers = click.prompt("Number of workers", default=1, type=int)
    auto_ack = click.confirm("Auto-acknowledge messages?", default=True)
    visibility_timeout = click.prompt("Visibility timeout (seconds)", default=30, type=int)
    retry_on_error = click.confirm("Retry on failure?", default=False)
    max_retries = 3
    if retry_on_error:
        max_retries = click.prompt("Max retries", default=3, type=int)

    # Determine if context parameter is needed (only when auto_ack=False)
    has_context = not auto_ack

    content = render_listener(
        class_name=class_name,
        queue_name=queue_name,
        workers=workers,
        auto_ack=auto_ack,
        visibility_timeout=visibility_timeout,
        retry_on_error=retry_on_error,
        max_retries=max_retries,
        has_context=has_context,
    )

    listener_file.write_text(content)
    click.echo(f"+ Created {click.style(str(listener_file.relative_to(project_root)), fg='green')}")

    click.echo("\nNext steps:")
    click.echo(f"   1. Implement message handling logic in {listener_file.relative_to(project_root)}")
    click.echo("   2. Configure queue driver in config.py (e.g., SQSDriver)")
    click.echo(f"   3. Run: vega listener run")
    click.echo(f"\nQueue configuration:")
    click.echo(f"   - Queue: {queue_name}")
    click.echo(f"   - Workers: {workers}")
    click.echo(f"   - Auto-ack: {auto_ack}")
    click.echo(f"   - Visibility timeout: {visibility_timeout}s")
    if retry_on_error:
        click.echo(f"   - Retry on error: Yes (max {max_retries} retries)")


# DDD Generators


def _generate_context(project_root: Path, project_name: str, context_name: str):
    """Generate bounded context structure under package directory"""
    # Use normalized project name as package directory
    normalized_name = project_name.replace('-', '_')
    package_path = project_root / normalized_name

    if not package_path.exists():
        click.echo(click.style(f"ERROR: {normalized_name}/ directory not found. This project uses legacy structure.", fg='red'))
        click.echo("Create a new project with `vega init` to use DDD bounded contexts.")
        return

    context_path = package_path / context_name
    if context_path.exists():
        click.echo(click.style(f"ERROR: Context '{context_name}' already exists", fg='red'))
        return

    click.echo(f"\n[*] Creating bounded context: {click.style(context_name, fg='green')}")

    directories = [
        "domain/aggregates",
        "domain/entities",
        "domain/value_objects",
        "domain/events",
        "domain/repositories",
        "application/commands",
        "application/queries",
        "infrastructure/repositories",
        "infrastructure/services",
        "presentation/cli/commands",
        "presentation/web/routes",
        "presentation/web/models",
    ]

    for directory in directories:
        dir_path = context_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"  + Created {context_name}/{directory}/")

    # Create test scaffolding per bounded context to keep tests co-located
    tests_base = project_root / "tests" / normalized_name / context_name
    test_dirs = [
        "domain",
        "application",
        "infrastructure",
        "presentation",
    ]
    for test_dir in test_dirs:
        path = tests_base / test_dir
        path.mkdir(parents=True, exist_ok=True)
        # Note: __init__.py files are not required for namespace packages in Python 3.3+
        click.echo(f"  + Created tests/{normalized_name}/{context_name}/{test_dir}/")

    # Initialize web package files
    # Note: Only create __init__.py files that contain functional code
    # (Python 3.3+ namespace packages don't require empty __init__.py files)
    from vega.cli.templates import (
        render_vega_routes_init_context,
        render_pydantic_models_init
    )

    routes_init_path = context_path / "presentation" / "web" / "routes" / "__init__.py"
    routes_init_path.write_text(render_vega_routes_init_context(context_name, project_name))

    models_init_path = context_path / "presentation" / "web" / "models" / "__init__.py"
    models_init_path.write_text(render_pydantic_models_init())

    click.echo(f"  + Initialized web package in {context_name}")

    # Note: Context __init__.py with only documentation is omitted (Python 3.3+)

    click.echo(f"\n{click.style('SUCCESS!', fg='green')} Bounded context '{context_name}' created")
    click.echo(f"\nNext steps:")
    click.echo(f"  vega generate aggregate Order          # In {context_name} context")
    click.echo(f"  vega generate value-object Money")
    click.echo(f"  vega generate command CreateOrder")


def _generate_aggregate(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate aggregate root in domain/aggregates/"""
    context = _detect_bounded_context(project_root)
    if context is None and _has_bounded_context_root(project_root):
        return  # Error already shown by _detect_bounded_context

    base_path = _get_context_base_path(project_root, context)

    # Determine path based on structure
    if context:
        file_path = base_path / "domain" / "aggregates" / f"{file_name}.py"
    else:
        # Legacy: create in domain/entities (no aggregates folder in legacy)
        file_path = base_path / "domain" / "entities" / f"{file_name}.py"
        click.echo(
            click.style(
                "WARNING: Using legacy structure. Consider migrating to bounded contexts (project_name/<context>/...).",
                fg='yellow'
            )
        )

    if file_path.exists():
        click.echo(click.style(f"ERROR: {file_path} already exists", fg='red'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_aggregate(class_name)
    file_path.write_text(content)

    relative_path = file_path.relative_to(project_root)
    click.echo(f"+ Created {click.style(str(relative_path), fg='green')}")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Add fields to {class_name}")
    click.echo(f"  2. Implement business methods")
    click.echo(f"  3. Add validation in __post_init__")


def _generate_value_object(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate value object in domain/value_objects/"""
    context = _detect_bounded_context(project_root)
    if context is None and _has_bounded_context_root(project_root):
        return  # Error already shown

    base_path = _get_context_base_path(project_root, context)

    if context:
        file_path = base_path / "domain" / "value_objects" / f"{file_name}.py"
    else:
        # Legacy: create in domain/entities
        file_path = base_path / "domain" / "entities" / f"{file_name}.py"
        click.echo(click.style("WARNING: Using legacy structure. Value objects created in domain/entities/", fg='yellow'))

    if file_path.exists():
        click.echo(click.style(f"ERROR: {file_path} already exists", fg='red'))
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_value_object(class_name)
    file_path.write_text(content)

    relative_path = file_path.relative_to(project_root)
    click.echo(f"+ Created {click.style(str(relative_path), fg='green')}")
    click.echo(f"\nValue object characteristics:")
    click.echo(f"  - Immutable (frozen=True)")
    click.echo(f"  - Equality by value, not identity")
    click.echo(f"  - Self-validating (__post_init__)")
