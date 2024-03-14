from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator, Sequence, Set
from functools import reduce
from itertools import chain
from typing import Any, SupportsIndex, TypeVar, overload

_T_co = TypeVar("_T_co", covariant=True)
_S = TypeVar("_S")
Self = TypeVar("Self", bound="orderedset[Any]")


class orderedset(Hashable, Set[_T_co], Sequence[_T_co]):
    _d: dict[_T_co, None]

    @overload
    def __init__(self, /) -> None: ...

    @overload
    def __init__(self, __iterable: Iterable[_T_co] = ()) -> None: ...

    def __init__(self, __iterable: Iterable[_T_co] = ()) -> None:
        self._d = dict.fromkeys(__iterable, None)

    @overload
    def __and__(self: Self, other: Set[_S]) -> Self: ...

    @overload
    def __and__(self: Self, other: Any) -> Self: ...

    def __and__(self: Self, other: Iterable[_S]) -> Self:
        other_set = set(other)
        return self.__class__(k for k in self._d if k in other_set)

    def __contains__(self, x: object) -> bool:
        return x in self._d

    def __eq__(self, __o: Any) -> bool:
        return self.__class__ == __o.__class__ and tuple(self._d.keys()) == tuple(__o._d.keys())

    @overload
    def __getitem__(self, __x: SupportsIndex) -> _T_co: ...

    @overload
    def __getitem__(self: Self, __x: slice) -> Self: ...

    def __getitem__(self: Self, __x: SupportsIndex | slice) -> _T_co | Self:
        t = self.as_tuple()
        return self.__class__(t[__x]) if isinstance(__x, slice) else t[__x]

    def __hash__(self) -> int:
        return hash(tuple(self._d.keys()))

    def __iter__(self) -> Iterator[_T_co]:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __or__(self: Self, __T_co: Iterable[_S]) -> Self:
        return self.__class__(chain(self._d, __T_co))

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + ", ".join(repr(k) for k in self._d) + ")"

    def __sub__(self: Self, other: Iterable[_T_co]) -> Self:
        return self.__class__(k for k in self._d if k not in other)

    def as_tuple(self) -> tuple[_T_co, ...]:
        return tuple(self)

    def intersection(self: Self, *s: Iterable[_S]) -> Self:
        return reduce(lambda xi, si: xi.__and__(si), s, self)

    def union(self: Self, *s: Iterable[_S]) -> Self:
        return reduce(lambda xi, si: xi.__or__(si), s, self)


oset = orderedset
