import logging
import subprocess
import sys
from collections.abc import Iterator
from os import symlink
from pathlib import Path
from shutil import copy, copytree, rmtree
from typing import NamedTuple

import toml

logger = logging.getLogger(__name__)


class ComponentId(NamedTuple):
    name: str


class ComponentTools:
    """
    A small collection of operations commonly done on components.

    This class might contain unrelated things like poetry and docker specific methods that we can
    hopefully move to better components in the future.
    """

    _path: Path

    def __init__(self, path: Path) -> None:
        self._path = path

    def component_name(self) -> str:
        # for now only supporting poetry components :(
        return toml.loads((self.find_path("pyproject.toml")).read_text())["tool"]["poetry"]["name"]

    def root_package_dirs(self) -> Iterator[str]:
        # currently assuming packages have been specified in poetry pyproject.toml settings
        pkgs = toml.loads(
            (self.find_path("pyproject.toml")).read_text(),
        )["tool"]["poetry"]["packages"]
        for pkg in pkgs:
            yield f"{pkg['from']}/{pkg['include']}"

    def symlink(self, src: Path, dst: Path) -> None:
        """
        Create a symlink in the component directory.

        The source path must be relative to the project directory. And the destination path must be
        relative to the component directory.
        """
        self._validate_project_path(src)
        self._validate_component_path(dst)

        symlink(src, dst)

    def copy(self, src: Path, dst: Path) -> None:
        """
        Copy a file or directory into the component.

        The source path must be relative to the project directory. And the destination path must be
        relative to the component directory.
        """
        self._validate_project_path(src)
        # we expect this instance to create files in the matching component
        self._validate_component_path(dst)

        copy(src, dst)

    def copy_tree(self, src: Path, dst: Path) -> None:
        # we want to allow copying files from anywhere in the project.
        self._validate_project_path(src)
        # we expect this instance to create files in the matching component
        self._validate_component_path(dst)

        copytree(src, dst, dirs_exist_ok=True)

    def create_or_empty(self, directory: Path) -> None:
        """Ensure a directory in the component exists and is empty."""
        self._validate_component_path(directory)
        if directory.exists():
            rmtree(directory)

        directory.mkdir(parents=True)

    def find_path(self, name: str) -> Path:
        """
        Given a directory path, relative to the root of the component, return the full path.

        All paths are expected to be within the directory of the repository.
        """
        path = (self._path / name).resolve()
        self._validate_component_path(path)
        return path

    def _validate_component_path(self, path: Path) -> None:
        """Ensure a path is relative to the component this instance is tied to."""
        if not path.is_relative_to(self._path):
            raise ValueError(f"component path must be relative to component: {path}")

    def _validate_project_path(self, path: Path) -> None:
        """
        Ensure a path is relative to the project.

        Mostly to prevent accidentally messing with external files. This library is specifically
        designed to work with files in the repository.
        """
        # For now, we assume the project is one directory up from the component.
        # We can move this to configs later if we need to.
        project = self._path.parent
        if not path.is_relative_to(project):
            raise ValueError(f"component path must be relative to project: {path}")

    def install(self) -> None:
        """Install the dependencies of the component."""
        self.poetry("install")

    def pytest(self) -> None:
        self.run("pytest")

    def ruff(self, *args: str) -> None:
        self.run("ruff", *args)

    def pyright(self) -> None:
        self.run("pyright")

    def run(self, *args: str) -> None:
        self.poetry("run", *args)

    def poetry(self, *args: str) -> None:
        # when running a poetry command, we want to ignore any env we might be in.
        # i'm not sure yet how reliable this is.
        self.exe("env", "-u", "POETRY_ACTIVE", "-u", "VIRTUAL_ENV", "poetry", *args)

    def exe(self, *cmd: str) -> None:
        logger.debug(f"executing in {self._path}/: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, cwd=self._path, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"failure detected: {' '.join(cmd)}")
            sys.exit(e.returncode)


class UnsetComponentTools(ComponentTools):
    def copy_tree(self, src: Path, dst: Path) -> None:
        raise NotImplementedError("no component selected")

    def create_or_empty(self, directory: Path) -> None:
        raise NotImplementedError("no component selected")

    def find_path(self, name: str) -> Path:
        raise NotImplementedError("no component selected")

    def exe(self, *cmd: str) -> None:
        raise NotImplementedError("no component selected")
