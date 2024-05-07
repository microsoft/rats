# type: ignore[reportUntypedFunctionDecorator]
import subprocess
import sys
from pathlib import Path

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli


class RatsCiCommands(cli.CommandContainer):
    @cli.command(cli.CommandId.auto())
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def poetry_install(self, component_path: str) -> None:
        """Build the documentation site for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "install"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @cli.command(cli.CommandId.auto())
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def test(self, component_path: str) -> None:
        """Build the python wheel for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "run", "pytest"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @cli.command(cli.CommandId.auto())
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def check_all(self, component_path: str) -> None:
        """
        If this command passes, ci should pass.

        I hope.
        """
        pyproject_path = Path(f"{component_path}/pyproject.toml")

        if not pyproject_path.is_file():
            raise ValueError("does not seem to be running within repo root")

        poetry_commands = [
            ["ruff", "check", "--fix", "--unsafe-fixes"],
            ["ruff", "format"],
            ["pyright"],
            ["pytest"],
        ]

        try:
            for cmd in poetry_commands:
                subprocess.run(
                    ["poetry", "run", *cmd],
                    check=True,
                    cwd=component_path,
                )
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @cli.command(cli.CommandId.auto())
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def build_wheel(self, component_path: str) -> None:
        """Build the python wheel for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "build", "-f", "wheel"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @cli.command(cli.CommandId.auto())
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    @click.argument("repository_name", type=str)
    def publish_wheel(self, component_path: str, repository_name: str) -> None:
        """Publish the python wheel for one of the components in this project."""
        p = Path(component_path)
        pyproject_path = p / "pyproject.toml"

        if not p.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(
                [
                    "poetry",
                    "publish",
                    "--repository",
                    repository_name,
                    "--no-interaction",
                    # temporarily skip existing during testing
                    "--skip-existing",
                ],
                cwd=component_path,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
