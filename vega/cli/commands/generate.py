"""Generate command - Create components in Vega project"""
import click
import re
from pathlib import Path

from vega.cli.templates import (
    render_entity,
    render_infrastructure_repository,
    render_infrastructure_service,
    render_interactor,
    render_mediator,
    render_repository_interface,
    render_service_interface,
)
from vega.cli.scaffolds import create_fastapi_scaffold



def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def to_pascal_case(name: str) -> str:
    """Convert strings to PascalCase, handling separators and camelCase input"""
    cleaned = name.strip()
    if not cleaned:
        return ""

    # Normalize common separators to spaces
    normalized = cleaned.replace('-', ' ').replace('_', ' ')
    if ' ' in normalized:
        parts = normalized.split()
    else:
        parts = re.findall(r'[A-Z]+(?=$|[A-Z][a-z0-9])|[A-Z]?[a-z0-9]+|[0-9]+', cleaned)
        if not parts:
            parts = [cleaned]

    def _pascal_piece(piece: str) -> str:
        return piece if piece.isupper() else piece[:1].upper() + piece[1:].lower()

    return ''.join(_pascal_piece(part) for part in parts if part)


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

