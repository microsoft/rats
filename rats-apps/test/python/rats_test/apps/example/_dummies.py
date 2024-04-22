from abc import abstractmethod
from typing import Protocol


class ITag(Protocol):
    @abstractmethod
    def get_tag(self) -> str:
        """Get the tag."""


class Tag1:
    def __init__(self, ns: str) -> None:
        self._ns = ns

    def get_tag(self) -> str:
        return f"{self._ns}:t1"


class Tag2:
    def __init__(self, ns: str) -> None:
        self._ns = ns

    def get_tag(self) -> str:
        return f"{self._ns}:t2"
