import logging
import subprocess
from collections.abc import Iterable
from functools import cache
from hashlib import sha256
from pathlib import Path

import toml

from ._components import ComponentId, ComponentOperations
from ._container_images import ContainerImage

logger = logging.getLogger(__name__)


class ProjectTools:
    _path: Path

    def __init__(self, path: Path, image_registry: str) -> None:
        self._path = path
        self._image_registry = image_registry

    def build_component_images(self) -> None:
        for c in self.discover_components():
            self.build_component_image(c.name)

    def build_component_image(self, name: str) -> None:
        ops = self.get_component(name)
        file = ops.find_path("Containerfile")
        if not file.exists():
            raise RuntimeError(f"Containerfile not found in component {name}")

        image = ContainerImage(
            name=f"{self._image_registry}/{name}",
            tag=self.image_context_hash(),
        )

        print(image)
        ops.exe("docker", "build", "-t", image.full, "--file", str(file), "../")

        if image.name.split("/")[0].split(".")[1:3] == ["azurecr", "io"]:
            acr_registry = image.name.split(".")[0]
            ops.exe("az", "acr", "login", "--name", acr_registry)
            # for now only pushing automatically if the registry is ACR
            ops.exe("docker", "push", image.full)

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
        containerfile = self.get_component("rats-devtools").find_path(
            "src/resources/image-context-hash/Containerfile"
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

    def discover_components(self) -> Iterable[ComponentId]:
        valid_components = []
        for p in self.repo_root().iterdir():
            if not p.is_dir() or not (p / "pyproject.toml").is_file():
                continue

            component_info = toml.loads((p / "pyproject.toml").read_text())
            if not component_info.get("tool", {}).get("rats-devtools", {}).get("enabled", False):
                # we don't recognize components unless they enable rats-devtools
                logger.warning(f"detected unmanaged component: {p.name}")
                continue

            valid_components.append(ComponentId(component_info["tool"]["poetry"]["name"]))

        return tuple(valid_components)

    def get_component(self, name: str) -> ComponentOperations:
        p = self.repo_root() / name
        if not p.is_dir() or not (p / "pyproject.toml").is_file():
            raise ComponentNotFoundError(f"component {name} is not a valid python component")

        return ComponentOperations(p)

    def repo_root(self) -> Path:
        guess = self._path.resolve()
        while str(guess) != "/":
            if (guess / ".git").exists():
                return guess

            guess = guess.parent

        raise ProjectNotFoundError(
            "could not find the root of the repository. rats-devtools must be used from a repo."
        )


class ComponentNotFoundError(ValueError):
    pass


class ProjectNotFoundError(ValueError):
    pass
