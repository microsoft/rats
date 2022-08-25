"""FrozenDict class.

Original source from https://stackoverflow.com/a/25332884 (MIT License)

"""
from __future__ import annotations

from typing import Any, Dict, Generic, Iterator, Mapping, Optional, TypeVar, overload

T = TypeVar("T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class FrozenDict(Mapping[_KT, _VT], Generic[_KT, _VT]):
    """Dictionary like class with private storage."""

    _hash: Optional[int]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self) -> Iterator[_KT]:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __getitem__(self, key: _KT) -> _VT:
        """Gets item from storage."""
        return self._d[key]

    def __contains__(self, __o: object) -> bool:
        return self._d.__contains__(__o)

    def __hash__(self) -> int:
        """Computes hash of object."""
        if self._hash is None:
            hash_ = 0
            for pair in self.items():
                hash_ ^= hash(pair)
            self._hash = hash_
        return self._hash

    def __repr__(self) -> str:
        return f"FrozenDict({repr(self._d)})"

    def copy(self) -> FrozenDict[_KT, _VT]:
        return self.__class__(self._d.copy())

    def set(self, key: _KT, value: _VT) -> FrozenDict[_KT, _VT]:
        new_d = self._d.copy()
        new_d[key] = value
        return self.__class__(new_d)

    def delete(self, key: _KT) -> FrozenDict[_KT, _VT]:
        new_d = self._d.copy()
        del new_d[key]
        return self.__class__(new_d)

    @overload
    def __or__(self, other: Dict[_KT, _VT]) -> FrozenDict[_KT, _VT]:
        ...

    @overload
    def __or__(self, other: FrozenDict[_KT, _VT]) -> FrozenDict[_KT, _VT]:
        ...

    def __or__(self, other: Dict[_KT, _VT] | FrozenDict[_KT, _VT]) -> FrozenDict[_KT, _VT]:
        new_d = self._d.copy()  # pipe operator | available in python 3.9
        new_d.update(dict(other))
        return self.__class__(new_d)
