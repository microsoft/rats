from abc import abstractmethod
from typing import Protocol


class ITag(Protocol):
    @abstractmethod
    def get_tag(self) -> str:
        """Get the tag."""


class Tag:
    def __init__(self, ns: str) -> None:
        self._ns = ns

    def get_tag(self) -> str:
        return self._ns
