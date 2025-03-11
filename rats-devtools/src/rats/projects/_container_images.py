from typing import NamedTuple


class ContainerImage(NamedTuple):
    name: str
    tag: str

    @property
    def full(self) -> str:
        return f"{self.name}:{self.tag}"
