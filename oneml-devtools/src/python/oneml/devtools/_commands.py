import sys

import os

import subprocess

from pathlib import Path

from typing import Iterable

import click

from ._click import ClickCommandRegistry, command
from oneml.services import IExecutable, ServiceProvider


class OnemlDevtoolsCli(IExecutable):

    _registries_group_provider: ServiceProvider[Iterable[ClickCommandRegistry]]

    def __init__(self, registries_group_provider: ServiceProvider[Iterable[ClickCommandRegistry]]) -> None:
        self._registries_group_provider = registries_group_provider

    def execute(self) -> None:
        cli = click.Group()
        for registry in self._registries_group_provider():
            registry.register(cli)

        cli()


class OnemlDevtoolsCommands(ClickCommandRegistry):

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def build_docs(self, component_path: str) -> None:
        """build the documentation site for one of the components in this project"""
        component_path = Path(component_path)
        pyproject_path = component_path / "pyproject.toml"
        site_dir_path = component_path / "dist/site"

        if not component_path.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run([
                "mkdocs", "build",
                "--site-dir", str(site_dir_path.resolve()),
            ], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def build_wheel(self, component_path: str) -> None:
        """build the python wheel for one of the components in this project"""
        component_path = Path(component_path)
        pyproject_path = component_path / "pyproject.toml"

        if not component_path.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "build", "-f", "wheel"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    @click.argument("repository_name", type=str)
    def publish_wheel(self, component_path: str, repository_name: str) -> None:
        """publish the python wheel for one of the components in this project"""
        component_path = Path(component_path)
        pyproject_path = component_path / "pyproject.toml"

        if not component_path.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run([
                "poetry", "publish",
                "--repository", repository_name,
                "--no-interaction",
                # temporarily skip existing during testing
                "--skip-existing",
            ], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    @click.argument("component_path", type=click.Path(exists=True, file_okay=False))
    def test(self, component_path: str) -> None:
        """build the python wheel for one of the components in this project"""
        component_path = Path(component_path)
        pyproject_path = component_path / "pyproject.toml"

        if not component_path.is_dir() or not pyproject_path.is_file():
            raise ValueError(f"component {component_path} does not exist")

        try:
            subprocess.run(["poetry", "run", "pytest"], cwd=component_path, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

    @command
    def ping(self) -> None:
        """no-op used for testing"""
        print("pong")
