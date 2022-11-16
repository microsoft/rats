"""frozendict class and MappingProtocol.

Original source of frozendict from https://stackoverflow.com/a/25332884 (MIT License)

"""
from __future__ import annotations

from typing import (
    AbstractSet,
    Any,
    Generic,
    ItemsView,
    Iterator,
    KeysView,
    Mapping,
    Optional,
    Protocol,
    TypeVar,
    ValuesView,
    overload,
)

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT", covariant=True)

Self = TypeVar("Self", bound="frozendict[Any, Any]")


class frozendict(Mapping[_KT, _VT], Generic[_KT, _VT]):
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

    def __getattr__(self, key: str) -> _VT:
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
        return f"{self.__class__.__name__}({repr(self._d)})"

    def copy(self: Self) -> Self:
        return self.__class__(self._d.copy())

    def delete(self: Self, key: _KT) -> Self:
        new_d = self._d.copy()
        del new_d[key]
        return self.__class__(new_d)

    def items(self, **kwargs: _T) -> ItemsView[_KT, _VT | _T]:
        new_d = self._d.copy()
        new_d.update(kwargs)
        return new_d.items()

    def set(self: Self, key: _KT, value: _T) -> Self:
        new_d = self._d.copy()
        new_d[key] = value
        return self.__class__(new_d)

    def values(self, **kwargs: _T) -> ValuesView[_VT | _T]:
        new_d = self._d.copy()
        new_d.update(kwargs)
        return new_d.values()

    @overload
    def __or__(self: Self, other: dict[_KT, _VT]) -> Self:
        ...

    @overload
    def __or__(self: Self, other: Self) -> Self:
        ...

    def __or__(self: Self, other: dict[_KT, _VT] | Self) -> Self:
        new_d = self._d.copy()  # pipe operator | available in python 3.9
        new_d.update(dict(other))
        return self.__class__(new_d)

    @overload
    def __and__(self: Self, other: dict[_KT, _VT]) -> Self:
        ...

    @overload
    def __and__(self: Self, other: Self) -> Self:
        ...

    def __and__(self: Self, other: dict[_KT, _VT] | Self) -> Self:
        new_d = {k: v for k, v in self._d.items() if k in other}
        if new_d and any(v != self._d[k] for k, v in new_d.items()):
            raise ValueError("Intersection only supported if common keys have same values.")
        return self.__class__(new_d)

    @overload
    def __sub__(self: Self, other: KeysView[_KT]) -> Self:
        ...

    @overload
    def __sub__(self: Self, other: AbstractSet[_KT]) -> Self:
        ...

    @overload
    def __sub__(self: Self, other: Mapping[_KT, _VT]) -> Self:
        ...

    def __sub__(self: Self, other: Any) -> Self:
        new_d = {k: v for k, v in self._d.items() if k not in other}
        return self.__class__(new_d)


fdict = frozendict


class MappingProtocol(Protocol[_KT, _VT]):
    """Mapping as a protocol."""

    def __contains__(self, __o: object) -> bool:
        ...

    def __eq__(self, __o: object) -> bool:
        ...

    def __getitem__(self, key: _KT) -> _VT:
        ...

    def __iter__(self) -> Iterator[_KT]:
        ...

    def __len__(self) -> int:
        ...

    def __ne__(self, __o: object) -> bool:
        ...

    def keys(self) -> KeysView[_KT]:
        ...

    @overload
    def get(self, __key: _KT) -> _VT | None:
        ...

    @overload
    def get(self, __key: _KT, __default: _VT | _T) -> _VT | _T:
        ...

    @overload
    def items(self) -> ItemsView[_KT, _VT]:
        ...

    @overload
    def items(self, **kwargs: _T) -> ItemsView[_KT | str, _VT | _T]:
        ...

    @overload
    def values(self) -> ValuesView[_VT]:
        ...

    @overload
    def values(self, **kwargs: _T) -> ValuesView[_VT | _T]:
        ...
