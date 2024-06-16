import logging
from pathlib import Path

from ._component_operations import ComponentOperations

logger = logging.getLogger(__name__)


class ProjectTools:
    _path: Path

    def __init__(self, path: Path) -> None:
        self._path = path

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

        raise ValueError(
            "could not find the root of the repository. rats-devtools must be used from a repo."
        )


class ComponentNotFoundError(ValueError):
    pass
