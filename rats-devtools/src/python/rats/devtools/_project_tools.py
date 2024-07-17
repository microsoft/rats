import logging
import subprocess
from functools import cache
from pathlib import Path

from ._component_operations import ComponentOperations

logger = logging.getLogger(__name__)


class ProjectTools:
    _path: Path

    def __init__(self, path: Path) -> None:
        self._path = path

    @cache
    def image_context_hash(self) -> str:
        manifest = self.image_context_manifest()
        return subprocess.run(
            ["git", "hash-object", "--stdin"],
            input=manifest,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    @cache
    def image_context_manifest(self) -> str:
        """
        Use `git ls-tree` to create a manifest of the files in the image context.

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
            capture_output=True,
            text=True,
        ).stdout
        lines = sorted(output.strip().split("\n"))

        return subprocess.run(
            ["git", "ls-tree", "-r", "--full-tree", "HEAD", *lines],
            check=True,
            cwd=self.repo_root(),
            capture_output=True,
            text=True,
        ).stdout.strip()

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
