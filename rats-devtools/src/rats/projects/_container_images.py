from typing import NamedTuple


class ContainerImage(NamedTuple):
    """Simple data object to represent a container image."""

    name: str
    tag: str

    @property
    def full(self) -> str:
        return f"{self.name}:{self.tag}"
