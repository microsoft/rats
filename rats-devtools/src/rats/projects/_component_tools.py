import logging
import subprocess
import sys
import warnings
from collections.abc import Mapping
from os import symlink
from pathlib import Path
from shutil import copy, copytree, rmtree
from typing import Any, NamedTuple

import toml

logger = logging.getLogger(__name__)


class ComponentId(NamedTuple):
    """A simple wrapper around the name of a component, for typing convenience."""

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
        """The component's name, as defined by `[project.name]` in `pyproject.toml`."""
        return self._load_pyproject()["project"]["name"]

    def symlink(self, src: Path, dst: Path) -> None:
        """
        Create a symlink in the component directory.

        The destination path must be relative to the component directory.

        Args:
            src: the existing file or directory to link to
            dst: the symlink path to be created
        """
        self._validate_component_path(dst)

        symlink(src, dst)

    def copy(self, src: Path, dst: Path) -> None:
        """
        Copy a file into the component.

        The destination path must be relative to the component directory.

        Args:
            src: the existing file to copy
            dst: the destination of the copied file
        """
        # we expect this instance to create files in the matching component
        self._validate_component_path(dst)

        copy(src, dst)

    def copy_tree(self, src: Path, dst: Path) -> None:
        """
        Copy a directory into the component.

        The destination path must be relative to the component directory.

        Args:
            src: the existing directory to copy
            dst: the destination of the copied directory
        """
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
        Given a path, relative to the root of the component, return the full path.

        All paths are expected to be within the directory of the component.
        """
        path = (self._path / name).resolve()
        self._validate_component_path(path)
        return path

    def _validate_component_path(self, path: Path) -> None:
        """Ensure a path is relative to the component this instance is tied to."""
        if not path.is_relative_to(self._path):
            raise ValueError(f"component path must be relative to component: {path}")

    def pytest(self) -> None:
        self.run("pytest")

    def ruff(self, *args: str) -> None:
        self.run("ruff", *args)

    def pyright(self) -> None:
        self.run("pyright")

    def poetry(self, *args: str) -> None:
        warnings.warn(
            "The ComponentTools.poetry() method is deprecated. Use ComponentTools.run() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.is_poetry_detected():
            raise RuntimeError(f"cannot run poetry commands in component: {self.component_name()}")

        self.exe("env", "-u", "POETRY_ACTIVE", "-u", "VIRTUAL_ENV", "poetry", *args)

    def run(self, *args: str) -> None:
        """Tries to run a command within the component's venv."""
        # generally try to unset any package manager venv specific details
        if self.is_poetry_detected():
            self.exe("env", "-u", "POETRY_ACTIVE", "-u", "VIRTUAL_ENV", "poetry", "run", *args)
        elif self._is_uv_detected():
            self.exe("env", "-u", "UV_ACTIVE", "-u", "VIRTUAL_ENV", "uv", "run", *args)
        else:
            self.exe(*args)

    def exe(self, *cmd: str) -> None:
        """Run a command from the root of a component."""
        logger.debug(f"executing in {self._path}/: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, cwd=self._path, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"failure detected: {' '.join(cmd)}")
            sys.exit(e.returncode)

    def is_poetry_detected(self) -> bool:
        """
        Returns true if we think this component might be managed by poetry.

        Since PEP 621 is gaining adoption, including by poetry, we should be able to remove most of
        the complexity in trying to parse details out of pyproject.toml. This method is here until
        we can fully delete any non PEP 621 code since we initially started as poetry-specific.
        """
        data = self._load_pyproject()
        if "tool" in data and "poetry" in data["tool"]:
            # we found some poetry values in the toml file
            return True

        # make double sure by checking if we see a lockfile for poetry
        return self.find_path("poetry.lock").is_file()

    def _is_uv_detected(self) -> bool:
        """
        Returns true if we think this component might be managed by uv.

        Keeping this private because the hope is to remove all coupling to specific packaging
        tools,
        """
        data = self._load_pyproject()
        if "tool" in data and "uv" in data["tool"]:
            # we found some uv values in the toml file
            return True

        # make double sure by checking if we see a lockfile for poetry
        return self.find_path("uv.lock").is_file()

    def _load_pyproject(self) -> Mapping[str, Any]:
        return toml.loads((self.find_path("pyproject.toml")).read_text())


class UnsetComponentTools(ComponentTools):
    """
    A stub component tools without any implemented operations.

    All methods within this class raise a `NotImplementedError`.
    """

    def copy_tree(self, src: Path, dst: Path) -> None:
        raise NotImplementedError("no component selected")

    def create_or_empty(self, directory: Path) -> None:
        raise NotImplementedError("no component selected")

    def find_path(self, name: str) -> Path:
        raise NotImplementedError("no component selected")

    def exe(self, *cmd: str) -> None:
        raise NotImplementedError("no component selected")
