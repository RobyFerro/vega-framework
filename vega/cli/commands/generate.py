"""Generate command - Create components in Vega project"""
import os
import click
import re
from pathlib import Path


def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def to_pascal_case(name: str) -> str:
    """Convert to PascalCase"""
    return ''.join(word.capitalize() for word in name.replace('_', ' ').replace('-', ' ').split())


def generate_component(component_type: str, name: str, project_path: str):
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
    file_name = to_snake_case(name)

    if component_type == 'entity':
        _generate_entity(project_root, project_name, class_name, file_name)
    elif component_type == 'repository':
        _generate_repository(project_root, project_name, class_name, file_name)
    elif component_type == 'service':
        _generate_service(project_root, project_name, class_name, file_name)
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

    content = f'''"""{class_name} entity"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class {class_name}:
    """{class_name} domain entity"""
    id: str
    # Add your fields here

    # Add your business logic methods here
    def is_valid(self) -> bool:
        """Validate entity"""
        return bool(self.id)
'''

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")


def _generate_repository(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate repository interface"""

    # Remove 'Repository' suffix if present to get entity name
    entity_name = class_name.replace('Repository', '')
    entity_file = to_snake_case(entity_name)

    file_path = project_root / "domain" / "repositories" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    content = f'''"""{class_name} interface"""
from abc import abstractmethod
from typing import List, Optional

from vega.patterns import Repository
from {project_name}.domain.entities.{entity_file} import {entity_name}


class {class_name}(Repository[{entity_name}]):
    """{class_name} interface"""

    @abstractmethod
    async def find_all(self) -> List[{entity_name}]:
        """Find all {entity_name.lower()}s"""
        pass

    # Add your custom methods here
    # @abstractmethod
    # async def find_by_name(self, name: str) -> Optional[{entity_name}]:
    #     pass
'''

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    # Suggest next steps
    click.echo(f"\n💡 Next steps:")
    click.echo(f"   1. Create entity: vega generate entity {entity_name}")
    click.echo(f"   2. Implement repository in infrastructure/repositories/")
    click.echo(f"   3. Register in config.py SERVICES dict")


def _generate_service(project_root: Path, project_name: str, class_name: str, file_name: str):
    """Generate service interface"""

    file_path = project_root / "domain" / "services" / f"{file_name}.py"

    if file_path.exists():
        click.echo(click.style(f"ERROR: Error: {file_path} already exists", fg='red'))
        return

    content = f'''"""{class_name} interface"""
from abc import abstractmethod

from vega.patterns import Service


class {class_name}(Service):
    """{class_name} interface"""

    @abstractmethod
    async def execute(self, data: dict) -> dict:
        """Execute service operation"""
        pass

    # Add your custom methods here
'''

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    click.echo(f"\n💡 Next steps:")
    click.echo(f"   1. Implement service in infrastructure/services/")
    click.echo(f"   2. Register in config.py SERVICES dict")


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

    content = f'''"""{class_name} use case"""
from vega.patterns import Interactor
from vega.di import bind

# Import your dependencies
# from {project_name}.domain.entities.{entity_file} import {entity_name}
# from {project_name}.domain.repositories.{entity_file}_repository import {entity_name}Repository


class {class_name}(Interactor[dict]):  # Replace dict with your return type
    """{class_name} use case"""

    def __init__(self, **kwargs):
        # Store input parameters
        pass

    @bind
    async def call(self) -> dict:  # Add dependencies as parameters
        """Execute the use case"""
        # TODO: Implement use case logic
        raise NotImplementedError("Implement this use case")
'''

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

    content = f'''"""{class_name} workflow"""
from vega.patterns import Mediator

# Import your use cases
# from {project_name}.domain.interactors.create_user import CreateUser


class {class_name}(Mediator[dict]):  # Replace dict with your return type
    """{class_name} workflow - orchestrates multiple use cases"""

    def __init__(self, **kwargs):
        # Store input parameters
        pass

    async def call(self) -> dict:
        """Execute the workflow"""
        # TODO: Orchestrate multiple use cases
        # Example:
        # user = await CreateUser(name="John")
        # await SendWelcomeEmail(user.email)
        # return user

        raise NotImplementedError("Implement this workflow")
'''

    file_path.write_text(content)
    click.echo(f"+ Created {click.style(str(file_path.relative_to(project_root)), fg='green')}")

    click.echo(f"\n💡 Usage:")
    click.echo(f"   result = await {class_name}(param=value)")
