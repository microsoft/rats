import logging
import os
import subprocess
from functools import cache
from hashlib import sha256
from pathlib import Path
from textwrap import dedent
from typing import NamedTuple

import toml

from rats import apps

from ._component_tools import ComponentId, ComponentTools
from ._container_images import ContainerImage

logger = logging.getLogger(__name__)


class ProjectConfig(NamedTuple):
    """Settings used by the [rats.projects.ProjectTools][] libraries."""

    name: str
    """
    The name of your project.

    In monorepos, this is typically the name of the repository. In single-component repositories,
    we generally expect the name of the repo to match the name of the component/package.
    """
    path: str
    """The path to the root of the project."""
    image_registry: str
    """The name of the container image registry built images will be tagged with."""
    image_push_on_build: bool
    """When enabled, images are automatically pushed to the defined registry when built."""
    image_tag: str | None = None
    """The version tag of the container image built images will be tagged with."""


class ProjectTools:
    """Small collection of methods to operate on the project and access component tools."""

    _config: apps.Provider[ProjectConfig]

    def __init__(self, config: apps.Provider[ProjectConfig]) -> None:
        """
        A config is required to specify the behavior of this instance.

        Args:
            config: the configuration of the project we are operating within.
        """
        self._config = config

    def build_component_images(self) -> None:
        """Sequentially builds container images for every component in the project."""
        for c in self.discover_components():
            self.build_component_image(c.name)

    def build_component_image(self, name: str) -> None:
        """
        Builds the container image for a given component in the project.

        Args:
            name: the name of the component to be built.
        """
        component_tools = self.get_component(name)
        file = component_tools.find_path("Containerfile")
        if not file.exists():
            file = component_tools.find_path("Dockerfile")

        if not file.exists():
            raise RuntimeError(f"Containerfile/Dockerfile not found in component {name}")

        config = self._config()
        image = self.container_image(name)

        print(f"building docker image: {image.full}")
        component_tools.exe(
            "docker",
            "build",
            "-t",
            image.full,
            "--file",
            str(file),
            str(self.repo_root()),
        )

        if image.name.split("/")[0].split(".")[1:3] == ["azurecr", "io"]:
            acr_registry = image.name.split(".")[0]
            if os.environ.get("DEVTOOLS_K8S_SKIP_LOGIN", "0") == "0":
                component_tools.exe("az", "acr", "login", "--name", acr_registry)

        if config.image_push_on_build:
            component_tools.exe("docker", "push", image.full)

    def container_image(self, name: str) -> ContainerImage:
        """
        Get the calculated container image for the given component.

        If a tag is not present in the [rats.projects.ProjectConfig][], one is calculated using
        [rats.projects.ProjectTools.image_context_hash][].

        Args:
            name: the name of the component for which we want the image.
        """
        config = self._config()
        return ContainerImage(
            name=f"{config.image_registry}/{name}",
            tag=config.image_tag or self.image_context_hash(),
        )

    @cache  # noqa: B019
    def image_context_hash(self) -> str:
        """
        Calculates a hash based on all the files available to the container build context.

        The hash is calculated by ignoring all files selected by `.gitignore` configs, and hashing
        all remaining files from the root of the project, giving us a unique hash of all possible
        contents that can be copied into an image.
        """
        manifest = self.image_context_manifest()
        return sha256(manifest.encode()).hexdigest()

    @cache  # noqa: B019
    def image_context_manifest(self) -> str:
        """
        Calculates a manifest of the files in the image context.

        When building container images, this hash can be used to determine if any of the files in
        the image might have changed. This manifest is used by methods like
        [rats.projects.ProjectTools.image_context_hash][].

        Inspired by https://github.com/5monkeys/docker-image-context-hash-action
        """
        containerfile = dedent("""
            FROM mcr.microsoft.com/mirror/docker/library/ubuntu:24.04
            COPY . /image-context
            WORKDIR /image-context

            CMD ["bash", "-c", "find . -type f | sort"]
        """)

        subprocess.run(
            ["docker", "build", "-t", "image-context-hasher", "-f-", "."],
            input=containerfile,
            check=True,
            cwd=self.repo_root(),
            capture_output=True,
            text=True,
        )

        output = subprocess.run(
            [
                "docker",
                "run",
                "--pull",
                "never",
                "--rm",
                "image-context-hasher",
            ],
            check=True,
            cwd=self.repo_root(),
            capture_output=True,
            text=True,
        ).stdout

        def _file_hash(p: str) -> str:
            contents = (self.repo_root() / p).read_bytes()
            return f"{sha256(contents).hexdigest()}\t{p}"

        lines = [f"{_file_hash(line[2:])}" for line in sorted(output.strip().split("\n"))]

        return "\n".join(lines)

    def project_name(self) -> str:
        """The name of the project, as defined by the provided [rats.projects.ProjectConfig][]."""
        return self._config().name

    @cache  # noqa: B019
    def discover_components(self) -> tuple[ComponentId, ...]:
        """Looks through the code base for any components containing a `pyproject.toml` file."""
        return tuple(self._component_paths().keys())

    def get_component(self, name: str) -> ComponentTools:
        """
        Get the component tools for a given component.

        Args:
            name: the name of the component within the project.
        """
        cid = ComponentId(name)
        if cid not in self._component_paths():
            raise ComponentNotFoundError(f"component {name} is not a valid python component")

        return ComponentTools(self._component_paths()[cid])

    def repo_root(self) -> Path:
        """The path to the root of the repository."""
        p = Path(self._config().path).resolve()
        # 99% of the time we just want the root of the repo
        # but in tests we use sub-projects to create fake scenarios
        # better test tooling can probably help us remove this later
        if not (p / ".git").exists() and not (p / ".rats-root").exists():
            raise ProjectNotFoundError(
                f"repo root not found: {p}. devtools must be used on a project in a git repo."
            )

        return p

    @cache  # noqa: B019
    def _component_paths(self) -> dict[ComponentId, Path]:
        results: dict[ComponentId, Path] = {}

        tomls: list[Path] = []
        # limit the search to 4 levels of directories
        for x in range(4):
            tomls.extend(self.repo_root().glob(f"{'*/' * x}pyproject.toml"))

        for t in tomls:
            p = t.parent
            if not p.is_dir() or not (p / "pyproject.toml").is_file():
                continue

            component_info = toml.loads((p / "pyproject.toml").read_text())
            tool_info = self._extract_tool_info(p / "pyproject.toml")

            if not tool_info["enabled"]:
                # we don't recognize components unless they enable rats-devtools
                # play nice and don't surprise people
                logger.debug(f"detected unmanaged component: {p.name}")
                continue

            poetry_name = component_info.get("tool", {}).get("poetry", {}).get("name")
            # fall back to assuming PEP 621 compliance
            name = poetry_name or component_info["project"]["name"]

            # poetry code paths can be dropped once 2.x is released
            # looks like we wait: https://github.com/python-poetry/poetry/pull/9135
            results[ComponentId(name)] = p

        return results

    def _extract_tool_info(self, pyproject: Path) -> dict[str, bool]:
        config = toml.loads(pyproject.read_text()).get("tool", {}).get("rats-devtools", {})

        return {
            "enabled": config.get("enabled", False),
            "devtools-component": config.get("devtools-component", False),
        }


class ComponentNotFoundError(ValueError):
    pass


class ProjectNotFoundError(ValueError):
    pass
