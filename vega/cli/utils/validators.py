"""Validation utilities for CLI inputs"""
from pathlib import Path
from typing import Tuple


def validate_project_name(name: str) -> Tuple[bool, str | None]:
    """
    Validate project name format.

    Args:
        name: Project name to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None

    Examples:
        >>> validate_project_name("my-project")
        (True, None)
        >>> validate_project_name("my project")
        (False, "Project name must be alphanumeric (hyphens and underscores allowed)")
    """
    if not name:
        return False, "Project name cannot be empty"

    # Check if name contains only alphanumeric characters, hyphens, and underscores
    if not name.replace('-', '').replace('_', '').isalnum():
        return False, "Project name must be alphanumeric (hyphens and underscores allowed)"

    # Check if name starts with a number (not recommended)
    if name[0].isdigit():
        return False, "Project name should not start with a number"

    return True, None


def validate_path_exists(path: str | Path) -> Tuple[bool, str | None]:
    """
    Validate that a path exists.

    Args:
        path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    path_obj = Path(path)

    if not path_obj.exists():
        return False, f"Path does not exist: {path}"

    if not path_obj.is_dir():
        return False, f"Path is not a directory: {path}"

    return True, None


def validate_vega_project(path: Path) -> Tuple[bool, str | None]:
    """
    Validate that a path is a Vega project root.

    Args:
        path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    config_file = path / "config.py"

    if not config_file.exists():
        return False, (
            f"Not a Vega project: {path}\n"
            "Missing config.py. Run this command from your project root, "
            "or use the --path option"
        )

    return True, None


def validate_entity_exists(project_root: Path, entity_name: str, entity_file: str) -> bool:
    """
    Check if an entity file exists in the project.

    Args:
        project_root: Root directory of the project
        entity_name: Name of the entity class
        entity_file: Snake_case filename of the entity

    Returns:
        True if entity exists, False otherwise
    """
    entity_path = project_root / "domain" / "entities" / f"{entity_file}.py"
    return entity_path.exists()


def validate_component_name(name: str) -> Tuple[bool, str | None]:
    """
    Validate component name (entity, repository, etc.).

    Args:
        name: Component name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Component name cannot be empty"

    # Allow alphanumeric and underscores
    if not name.replace('_', '').isalnum():
        return False, "Component name must be alphanumeric (underscores allowed)"

    return True, None
