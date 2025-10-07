"""Update command - Update Vega Framework"""
import click
import subprocess
import sys
import urllib.request
import json
import os
from pathlib import Path
from typing import Optional

from vega import __version__


CURRENT_VERSION = __version__
PYPI_URL = "https://pypi.org/pypi/vega-framework/json"


def is_pipx_install() -> bool:
    """Check if vega was installed via pipx"""
    vega_path = Path(sys.executable)
    return 'pipx' in str(vega_path).lower()


def get_pipx_command() -> Optional[str]:
    """Get the pipx executable path"""
    # Try common locations
    if os.name == 'nt':  # Windows
        # Check if pipx is in PATH
        result = subprocess.run(
            ['where', 'pipx'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    else:  # Unix-like
        result = subprocess.run(
            ['which', 'pipx'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()

    return None


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
        # Check if installed via pipx
        if is_pipx_install():
            pipx_cmd = get_pipx_command()
            if pipx_cmd:
                click.echo(click.style("Detected pipx installation, using pipx upgrade...", fg='cyan'))
                cmd = [pipx_cmd, 'upgrade', 'vega-framework']
                if force:
                    # For pipx, we need to reinstall to force
                    cmd = [pipx_cmd, 'reinstall', 'vega-framework']

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    click.echo(click.style("\n+ Vega Framework updated successfully!", fg='green'))
                    click.echo(f"\n   Run 'vega --version' to verify the installation")
                    return
                else:
                    click.echo(click.style("\nERROR: pipx update failed", fg='red'))
                    click.echo(f"\n{result.stderr}")
                    sys.exit(1)
            else:
                click.echo(click.style("⚠️  pipx detected but command not found, falling back to pip...", fg='yellow'))

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

        if result.returncode == 0:
            click.echo(click.style("\n+ Vega Framework updated successfully!", fg='green'))
            click.echo(f"\n   Run 'vega --version' to verify the installation")
        else:
            click.echo(click.style("\nERROR: Update failed", fg='red'))
            click.echo(f"\n{result.stderr}")
            click.echo(click.style("\nTIP: If you installed vega with pipx, use: pipx upgrade vega-framework", fg='yellow'))
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
