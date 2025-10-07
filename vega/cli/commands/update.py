"""Update command - Update Vega Framework"""
import click
import subprocess
import sys
import urllib.request
import json
from typing import Optional

from vega import __version__


CURRENT_VERSION = __version__
PYPI_URL = "https://pypi.org/pypi/vega-framework/json"


def get_latest_version() -> Optional[str]:
    """Get the latest version from PyPI"""
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data['info']['version']
    except Exception:
        return None


def compare_versions(current: str, latest: str) -> bool:
    """Compare version strings. Returns True if latest > current"""
    def version_tuple(v):
        return tuple(map(int, v.split('.')))

    try:
        return version_tuple(latest) > version_tuple(current)
    except Exception:
        return False


def update_vega(force: bool = False) -> None:
    """Update Vega Framework to the latest version"""

    click.echo("Checking for updates...")

    latest_version = get_latest_version()

    if latest_version is None:
        click.echo(click.style("WARNING: Could not check for updates (PyPI unreachable or package not published)", fg='yellow'))
        click.echo(f"   Current version: {CURRENT_VERSION}")

        if not force:
            if not click.confirm("\nDo you want to try updating anyway?", default=False):
                return
    elif not compare_versions(CURRENT_VERSION, latest_version):
        click.echo(click.style(f"+ You already have the latest version ({CURRENT_VERSION})", fg='green'))

        if not force:
            return

        click.echo(click.style("\nWARNING: Force update enabled, reinstalling...", fg='yellow'))
    else:
        click.echo(f"Current version: {CURRENT_VERSION}")
        click.echo(f"Latest version:  {latest_version}")
        click.echo()

        if not force and not click.confirm("Do you want to update?", default=True):
            click.echo("Update cancelled.")
            return

    click.echo("\nUpdating Vega Framework...")

    try:
        # Try to update via pip
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]

        if force:
            cmd.append("--force-reinstall")

        # Try PyPI first
        result = subprocess.run(
            cmd + ["vega-framework"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # If PyPI fails, try local installation (for development)
            click.echo(click.style("⚠️  PyPI installation failed, trying local installation...", fg='yellow'))

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "--editable", "."],
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            click.echo(click.style("\n+ Vega Framework updated successfully!", fg='green'))
            click.echo(f"\n   Run 'vega --version' to verify the installation")
        else:
            click.echo(click.style("\nERROR: Update failed", fg='red'))
            click.echo(f"\n{result.stderr}")
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"\nERROR: Update failed: {e}", fg='red'))
        sys.exit(1)


def check_version() -> None:
    """Check for available updates without installing"""

    click.echo("Checking for updates...")

    latest_version = get_latest_version()

    if latest_version is None:
        click.echo(click.style("WARNING: Could not check for updates (PyPI unreachable or package not published)", fg='yellow'))
        click.echo(f"   Current version: {CURRENT_VERSION}")
        return

    click.echo(f"Current version: {CURRENT_VERSION}")
    click.echo(f"Latest version:  {latest_version}")

    if compare_versions(CURRENT_VERSION, latest_version):
        click.echo(click.style(f"\nUpdate available!", fg='yellow'))
        click.echo(f"   Run 'vega update' to upgrade to version {latest_version}")
    else:
        click.echo(click.style("\n+ You have the latest version!", fg='green'))
