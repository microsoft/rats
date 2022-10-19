from typing import TypeVar

from ._frozendict import frozendict

T = TypeVar("T")


class FrozenDictWithAttrAccess(frozendict[str, T]):
    def __getattr__(self, param: str) -> T:
        return self[param]
