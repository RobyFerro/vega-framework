"""Template loading and rendering utilities for Vega CLI"""
from __future__ import annotations

import importlib.resources
from typing import Any

from jinja2 import Environment, BaseLoader, TemplateNotFound


class ResourceLoader(BaseLoader):
    """Jinja2 loader that reads templates from package resources"""

    def __init__(self, package: str, subfolder: str = ""):
        self.package = package
        self.subfolder = subfolder

    def get_source(self, environment: Environment, template: str) -> tuple[str, str | None, Any]:
        """Load template from package resources"""
        try:
            # Try importlib.resources.files (Python 3.9+)
            files = getattr(importlib.resources, "files", None)
            if files:
                resource = files(self.package)
                if self.subfolder:
                    resource = resource.joinpath(self.subfolder)
                resource = resource.joinpath(template)

                if resource.is_file():
                    source = resource.read_text(encoding="utf-8")
                    # Return (source, filename, uptodate_function)
                    # filename is None, uptodate always returns True (templates don't change at runtime)
                    return source, None, lambda: True
            else:  # pragma: no cover - legacy Python fallback
                if self.subfolder:
                    template_path = f"{self.subfolder}/{template}"
                else:
                    template_path = template
                source = importlib.resources.read_text(self.package, template_path, encoding="utf-8")
                return source, None, lambda: True

        except Exception as e:
            raise TemplateNotFound(template) from e

        raise TemplateNotFound(template)


def render_template(template_name: str, subfolder: str = "project", **context: Any) -> str:
    """
    Render a Jinja2 template from vega.cli.templates

    Args:
        template_name: Name of the template file (e.g., 'config.py.j2')
        subfolder: Subfolder within templates directory (default: 'project')
        **context: Variables to pass to the template

    Returns:
        Rendered template content

    Raises:
        TemplateNotFound: If template doesn't exist
    """
    env = Environment(
        loader=ResourceLoader("vega.cli.templates", subfolder),
        autoescape=False,  # We're generating code, not HTML
        keep_trailing_newline=True,  # Preserve trailing newlines
        trim_blocks=True,  # Remove first newline after block
        lstrip_blocks=True,  # Strip leading spaces before blocks
    )

    template = env.get_template(template_name)
    return template.render(**context)
