import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import click

from rats import apps

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import command_tree as command_tree

from ._ids import PluginServices


@dataclass(frozen=True)
class ComponentArgs:
    component_path: Annotated[str, command_tree.ClickConversion(argument=True)]
    """The path to the component to operate on."""


@dataclass(frozen=True)
class PublishWheelsArgs:
    repository_name: Annotated[str, command_tree.ClickConversion(argument=True)]
    """The name of the repository to publish to."""


class RatsCiCommands(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools ci"))
    def poetry_install_command_tree(self) -> command_tree.CommandTree:
        def handler(component_args: ComponentArgs) -> None:
            p = Path(component_args.component_path)
            if not p.exists() and p.is_dir():
                raise ValueError(f"component {component_args.component_path} does not exist")

            pyproject_path = p / "pyproject.toml"

            if not p.is_dir() or not pyproject_path.is_file():
                raise ValueError(f"component {component_args.component_path} does not exist")

            try:
                subprocess.run(
                    ["poetry", "install"], cwd=component_args.component_path, check=True
                )
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return command_tree.CommandTree(
            name="poetry-install",
            description="Install the dependencies for a component using poetry.",
            handler=handler,
        )

    @apps.service(PluginServices.command("poetry-install"))
    def poetry_install_command(self) -> click.Command:
        @click.command()
        @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
        def poetry_install(component_path: str) -> None:
            """Build the documentation site for one of the components in this project."""
            p = Path(component_path)
            pyproject_path = p / "pyproject.toml"

            if not p.is_dir() or not pyproject_path.is_file():
                raise ValueError(f"component {component_path} does not exist")

            try:
                subprocess.run(["poetry", "install"], cwd=component_path, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return poetry_install

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools ci"))
    def test_command_tree(self) -> command_tree.CommandTree:
        def handler(component_args: ComponentArgs) -> None:
            p = Path(component_args.component_path)
            pyproject_path = p / "pyproject.toml"

            if not p.is_dir() or not pyproject_path.is_file():
                raise ValueError(f"component {component_args.component_path} does not exist")

            try:
                subprocess.run(
                    ["poetry", "run", "pytest"], cwd=component_args.component_path, check=True
                )
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return command_tree.CommandTree(
            name="test",
            description="Build the python wheel for one of the components in this project.",
            handler=handler,
        )

    @apps.service(PluginServices.command("test"))
    def test_command(self) -> click.Command:
        @click.command()
        @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
        def test(component_path: str) -> None:
            """Build the python wheel for one of the components in this project."""
            p = Path(component_path)
            pyproject_path = p / "pyproject.toml"

            if not p.is_dir() or not pyproject_path.is_file():
                raise ValueError(f"component {component_path} does not exist")

            try:
                subprocess.run(["poetry", "run", "pytest"], cwd=component_path, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return test

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools ci"))
    def check_all_command_tree(self) -> command_tree.CommandTree:
        def handler(component_args: ComponentArgs) -> None:
            pyproject_path = Path(f"{component_args.component_path}/pyproject.toml")

            if not pyproject_path.is_file():
                raise ValueError("does not seem to be running within repo root")

            poetry_commands = [
                ["ruff", "check", "--fix", "--unsafe-fixes"],
                ["ruff", "format", "--check"],
                ["pyright"],
                ["pytest"],
            ]

            try:
                for cmd in poetry_commands:
                    subprocess.run(
                        ["poetry", "run", *cmd],
                        check=True,
                        cwd=component_args.component_path,
                    )
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return command_tree.CommandTree(
            name="check-all",
            description="""
            If this command passes, ci should pass.

            I hope.
            """,
            handler=handler,
        )

    @apps.service(PluginServices.command("check-all"))
    def check_all_command(self) -> click.Command:
        @click.command()
        @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
        def check_all(component_path: str) -> None:
            """
            If this command passes, ci should pass.

            I hope.
            """
            pyproject_path = Path(f"{component_path}/pyproject.toml")

            if not pyproject_path.is_file():
                raise ValueError("does not seem to be running within repo root")

            poetry_commands = [
                ["ruff", "check", "--fix", "--unsafe-fixes"],
                ["ruff", "format", "--check"],
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

        return check_all

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools ci"))
    def build_wheel_command_tree(self) -> command_tree.CommandTree:
        def handler(component_args: ComponentArgs) -> None:
            p = Path(component_args.component_path)
            pyproject_path = p / "pyproject.toml"

            if not p.is_dir() or not pyproject_path.is_file():
                raise ValueError(f"component {component_args.component_path} does not exist")

            try:
                subprocess.run(
                    ["poetry", "build", "-f", "wheel"],
                    cwd=component_args.component_path,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return command_tree.CommandTree(
            name="build-wheel",
            description="Build the python wheel for one of the components in this project.",
            handler=handler,
        )

    @apps.service(PluginServices.command("build-wheel"))
    def build_wheel_command(self) -> click.Command:
        @click.command()
        @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
        def build_wheel(component_path: str) -> None:
            """Build the python wheel for one of the components in this project."""
            p = Path(component_path)
            pyproject_path = p / "pyproject.toml"

            if not p.is_dir() or not pyproject_path.is_file():
                raise ValueError(f"component {component_path} does not exist")

            try:
                subprocess.run(["poetry", "build", "-f", "wheel"], cwd=component_path, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return build_wheel

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools ci"))
    def publish_wheels_command_tree(self) -> command_tree.CommandTree:
        def handler(component_args: ComponentArgs, publish_wheels_args: PublishWheelsArgs) -> None:
            p = Path(component_args.component_path)
            pyproject_path = p / "pyproject.toml"

            if not p.is_dir() or not pyproject_path.is_file():
                raise ValueError(f"component {component_args.component_path} does not exist")

            try:
                subprocess.run(
                    [
                        "poetry",
                        "publish",
                        "--repository",
                        publish_wheels_args.repository_name,
                        "--no-interaction",
                        # temporarily skip existing during testing
                        "--skip-existing",
                    ],
                    cwd=component_args.component_path,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)

        return command_tree.CommandTree(
            name="publish-wheel",
            description="Publish the python wheel for one of the components in this project.",
            kwargs_class=PublishWheelsArgs,
            handler=handler,
        )

    @apps.service(PluginServices.command("publish-wheel"))
    def publish_wheel_command(self) -> click.Command:
        @click.command()
        @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
        @click.argument("repository_name", type=str)
        def publish_wheel(component_path: str, repository_name: str) -> None:
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

        return publish_wheel
