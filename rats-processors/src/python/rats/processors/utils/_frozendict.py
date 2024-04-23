"""frozendict class and MappingProtocol."""

from __future__ import annotations

from collections.abc import ItemsView, Iterable, Iterator, Mapping, ValuesView
from functools import reduce
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
    get_args,
    overload,
)

from typing_extensions import Self

if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_VT_co = TypeVar("_VT_co", covariant=True)
_VS_co = TypeVar("_VS_co", covariant=True)


class frozendict(Mapping[_KT, _VT_co], Generic[_KT, _VT_co]):
    """Dictionary like class with private storage."""

    _hash: int | None = None
    _type_T: Any

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, **kwargs: _VT_co) -> None: ...

    @overload
    def __init__(self, __map: SupportsKeysAndGetItem[_KT, _VT_co]) -> None: ...

    @overload
    def __init__(self, __map: SupportsKeysAndGetItem[str, _VT_co], **kwargs: _VT_co) -> None: ...

    @overload
    def __init__(self, __iterable: Iterable[tuple[_KT, _VT_co]]) -> None: ...

    @overload
    def __init__(self, __iterable: Iterable[tuple[str, _VT_co]], **kwargs: _VT_co) -> None: ...

    @overload
    def __init__(self: frozendict[str, str], __iterable: Iterable[list[str]]) -> None: ...

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __getstate__(self) -> dict[str, Any]:
        # our implementation of __getattr__ messes with pickle, so we need to implement
        # __getstate__ and __setstate__
        return dict(
            _d=self._d,
            _hash=self._hash,
        )

    def __setstate__(self, d: Mapping[str, Any]) -> None:
        # our implementation of __getattr__ messes with pickle, so we need to implement
        # __getstate__ and __setstate__
        self._d = d["_d"]
        self._hash = d["_hash"]

    def __init_subclass__(cls) -> None:
        cls._type_T = get_args(cls.__orig_bases__[0])  # type: ignore

    def __iter__(self) -> Iterator[_KT]:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __getitem__(self, key: _KT) -> _VT_co:
        """Gets item from storage."""
        return self._d[key]

    def __getattr__(self, key: str) -> _VT_co:
        try:  # https://stackoverflow.com/a/16237698
            return self._d[key]
        except KeyError:
            raise AttributeError(key) from None

    def __contains__(self, __o: object) -> bool:
        return __o in self._d

    def __hash__(self) -> int:
        """Computes hash of object."""
        if self._hash is None:
            _hash = 0
            for pair in self.items():
                _hash ^= hash(pair)
            return _hash
        return self._hash

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._d!r})"

    def delete(self: Self, key: _KT) -> Self:
        new_d = self._d.copy()
        del new_d[key]
        return self.__class__(new_d)

    def items(self, **kwargs: _VT) -> ItemsView[_KT, _VT_co | _VT]:
        new_d = self._d.copy()
        new_d.update(kwargs)
        return new_d.items()

    def set(self: Self, key: _KT, value: object) -> Self:
        new_d = self._d.copy()
        new_d[key] = value
        return self.__class__(new_d)

    def values(self, **kwargs: _VT) -> ValuesView[_VT_co | _VT]:
        new_d = self._d.copy()
        new_d.update(kwargs)
        return new_d.values()

    def __or__(self: Self, other: Mapping[_KT, _VS_co]) -> Self:
        new_d = self._d.copy()  # pipe operator | available in python 3.9
        new_d.update(dict(other))
        return self.__class__(new_d)

    def __and__(self: Self, other: Mapping[_KT, _VS_co]) -> Self:
        new_d = {k: v for k, v in self._d.items() if k in other}
        if new_d and any(v != self._d[k] for k, v in new_d.items()):
            raise ValueError("Intersection only supported if common keys have same values.")
        return self.__class__(new_d)

    def __sub__(self: Self, other: Iterable[_KT]) -> Self:
        other_keys = set(other)
        new_d = {k: v for k, v in self._d.items() if k not in other_keys}
        return self.__class__(new_d)

    def intersection(self: Self, *s: Mapping[_KT, _VS_co]) -> Self:
        return reduce(lambda xi, si: xi.__and__(si), s, self)

    @overload
    def union(self: Self, *s: Mapping[_KT, _VT_co]) -> Self:
        return reduce(lambda xi, si: xi.__or__(si), s, self)

    @overload
    def union(self, *s: Mapping[_KT, _VS_co]) -> frozendict[_KT, _VT_co | _VS_co]:
        return reduce(lambda xi, si: xi.__or__(si), s, self)

    def union(self, *s: Mapping[_KT, _VS_co]) -> frozendict[_KT, _VT_co | _VS_co]:
        return reduce(lambda xi, si: xi.__or__(si), s, self)


fdict = frozendict
