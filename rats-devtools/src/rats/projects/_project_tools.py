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
    name: str
    path: str
    # these don't seem to belong here
    image_registry: str
    image_push_on_build: bool
    image_tag: str | None = None


class ProjectTools:
    _config: apps.Provider[ProjectConfig]

    def __init__(self, config: apps.Provider[ProjectConfig]) -> None:
        self._config = config

    def build_component_images(self) -> None:
        for c in self.discover_components():
            self.build_component_image(c.name)

    def build_component_image(self, name: str) -> None:
        component_tools = self.get_component(name)
        file = component_tools.find_path("Containerfile")
        if not file.exists():
            file = component_tools.find_path("Dockerfile")

        if not file.exists():
            raise RuntimeError(f"Containerfile not found in component {name}")

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
        config = self._config()
        return ContainerImage(
            name=f"{config.image_registry}/{name}",
            tag=config.image_tag or self.image_context_hash(),
        )

    @cache  # noqa: B019
    def image_context_hash(self) -> str:
        manifest = self.image_context_manifest()
        return sha256(manifest.encode()).hexdigest()

    @cache  # noqa: B019
    def image_context_manifest(self) -> str:
        """
        Use a container image to create a manifest of the files in the image context.

        When building container images, this hash can be used to determine if any of the files in
        the image might have changed.

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
        root = self.repo_root()
        if (root / "pyproject.toml").exists():
            # this is a single component project and the project name is the component name
            return toml.loads((root / "pyproject.toml").read_text())["project"]["name"]

        # this is a monorepo so i'm not quite sure what to use to detect the project name
        return self.repo_root().name

    @cache  # noqa: B019
    def discover_components(self) -> tuple[ComponentId, ...]:
        valid_components = []
        if self._is_single_component_project():
            p = self.repo_root() / "pyproject.toml"

            component_info = toml.loads(p.read_text())
            tool_info = self._extract_tool_info(p)

            if not tool_info["enabled"]:
                # we don't recognize components unless they enable rats-devtools
                # play nice and don't surprise people
                logger.info(f"detected unmanaged component: {p.name}")
                raise RuntimeError("detected single component repo but not managed by rats")

            return (ComponentId(component_info["project"]["name"]),)

        # limited to 1 level of nesting for now (i think)
        for p in self.repo_root().iterdir():
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
            valid_components.append(ComponentId(name))

        return tuple(valid_components)

    def get_component(self, name: str) -> ComponentTools:
        if self._is_single_component_project():
            return ComponentTools(self.repo_root())

        p = self.repo_root() / name
        if not p.is_dir() or not (p / "pyproject.toml").is_file():
            raise ComponentNotFoundError(f"component {name} is not a valid python component")

        return ComponentTools(p)

    def repo_root(self) -> Path:
        p = Path(self._config().path).resolve()
        # 99% of the time we just want the root of the repo
        # but in tests we use sub-projects to create fake scenarios
        # better test tooling can probably help us remove this later
        if not (p / ".git").exists() and not (p / ".rats-root").exists():
            raise ProjectNotFoundError(
                f"repo root not found: {p}. devtools must be used on a project in a git repo."
            )

        return p

    def _extract_tool_info(self, pyproject: Path) -> dict[str, bool]:
        config = toml.loads(pyproject.read_text()).get("tool", {}).get("rats-devtools", {})

        return {
            "enabled": config.get("enabled", False),
            "devtools-component": config.get("devtools-component", False),
        }

    def _is_single_component_project(self) -> bool:
        return (self.repo_root() / "pyproject.toml").exists()


class ComponentNotFoundError(ValueError):
    pass


class ProjectNotFoundError(ValueError):
    pass
