import logging
import os
import subprocess
from collections.abc import Iterable
from functools import cache
from hashlib import sha256
from pathlib import Path
from typing import NamedTuple

import toml

from rats import apps

from ._component_tools import ComponentId, ComponentTools
from ._container_images import ContainerImage

logger = logging.getLogger(__name__)


class ProjectConfig(NamedTuple):
    name: str
    path: str
    # this one doesn't seem to belong here
    image_registry: str
    image_push_on_build: bool


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
            raise RuntimeError(f"Containerfile not found in component {name}")

        image = ContainerImage(
            name=f"{self._config().image_registry}/{name}",
            tag=self.image_context_hash(),
        )

        print(f"building docker image: {image.full}")
        component_tools.exe("docker", "build", "-t", image.full, "--file", str(file), "../")

        if image.name.split("/")[0].split(".")[1:3] == ["azurecr", "io"]:
            acr_registry = image.name.split(".")[0]
            if os.environ.get("DEVTOOLS_K8S_SKIP_LOGIN", "0") == "0":
                component_tools.exe("az", "acr", "login", "--name", acr_registry)

        if self._config().image_push_on_build:
            component_tools.exe("docker", "push", image.full)

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
        containerfile = self.get_component(self.devtools_component().name).find_path(
            "resources/image-context-hash/Containerfile"
        )
        if not containerfile.exists():
            raise FileNotFoundError(
                f"Containerfile not found in devtools component: {containerfile}"
            )

        subprocess.run(
            ["docker", "build", "-t", "image-context-hasher", "--file", str(containerfile), "."],
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
            return toml.loads((root / "pyproject.toml").read_text())["tool"]["poetry"]["name"]

        # this is a monorepo so i'm not quite sure what to use to detect the project name
        return self.repo_root().name

    def devtools_component(self) -> ComponentId:
        for c in self.discover_components():
            tool_info = self._extract_tool_info(self.repo_root() / c.name / "pyproject.toml")
            if tool_info["devtools-component"]:
                return c

        raise ComponentNotFoundError("was not able to find a devtools component in the project")

    @cache  # noqa: B019
    def discover_components(self) -> Iterable[ComponentId]:
        valid_components = []
        # limited to 1 level of nesting for now (i think)
        for p in self.repo_root().iterdir():
            if not p.is_dir() or not (p / "pyproject.toml").is_file():
                continue

            component_info = toml.loads((p / "pyproject.toml").read_text())
            tool_info = self._extract_tool_info(p / "pyproject.toml")

            if not tool_info["enabled"]:
                # we don't recognize components unless they enable rats-devtools
                # play nice and don't surprise people
                logger.info(f"detected unmanaged component: {p.name}")
                continue

            # how do we stop depending on poetry here?
            # looks like we wait: https://github.com/python-poetry/poetry/pull/9135
            valid_components.append(ComponentId(component_info["tool"]["poetry"]["name"]))

        return tuple(valid_components)

    def _extract_tool_info(self, pyproject: Path) -> dict[str, bool]:
        config = toml.loads(pyproject.read_text())["tool"].get("rats-devtools", {})
        return {
            "enabled": config.get("enabled", False),
            "devtools-component": config.get("devtools-component", False),
        }

    def get_component(self, name: str) -> ComponentTools:
        p = self.repo_root() / name
        if not p.is_dir() or not (p / "pyproject.toml").is_file():
            raise ComponentNotFoundError(f"component {name} is not a valid python component")

        return ComponentTools(p)

    def repo_root(self) -> Path:
        p = Path(self._config().path).resolve()
        if not (p / ".git").exists():
            raise ProjectNotFoundError(
                f"repo root not found: {p}. devtools must be used on a project in a git repo."
            )

        return p


class ComponentNotFoundError(ValueError):
    pass


class ProjectNotFoundError(ValueError):
    pass
