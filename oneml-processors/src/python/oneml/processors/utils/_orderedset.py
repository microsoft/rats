from __future__ import annotations

from functools import reduce
from itertools import chain
from typing import AbstractSet, Any, Hashable, Iterable, Iterator, TypeAlias, TypeVar, overload

_T_co = TypeVar("_T_co", covariant=True)
_S = TypeVar("_S")
Self = TypeVar("Self", bound="orderedset[Any]")


class orderedset(Hashable, AbstractSet[_T_co]):
    _d: dict[_T_co, None]

    @overload
    def __init__(self) -> None:
        ...

    @overload
    def __init__(self, __iterable: Iterable[_T_co] = ()) -> None:
        ...

    def __init__(self, __iterable: Iterable[_T_co] = ()) -> None:
        self._d = dict.fromkeys(__iterable, None)

    @overload
    def __and__(self: Self, other: AbstractSet[_S]) -> Self:
        ...

    @overload
    def __and__(self: Self, other: Any) -> Self:
        ...

    def __and__(self: Self, other: Iterable[_S]) -> Self:
        return self.__class__(k for k in self._d if k in other)

    def __contains__(self, x: object) -> bool:
        return x in self._d

    def __eq__(self, __o: Any) -> bool:
        return self.__class__ == __o.__class__ and tuple(self._d.keys()) == tuple(__o._d.keys())

    def __hash__(self) -> int:
        return hash(tuple(self._d.keys()))

    def __iter__(self) -> Iterator[_T_co]:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __or__(self, __T_co: Iterable[_S]) -> orderedset[_T_co | _S]:
        return self.__class__(chain(self._d, __T_co))

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + ", ".join(repr(k) for k in self._d) + ")"

    def __sub__(self: Self, other: Iterable[_T_co]) -> Self:
        return self.__class__(k for k in self._d if k not in other)

    def intersection(self: Self, *s: Iterable[_S]) -> Self:
        return reduce(lambda xi, si: xi.__and__(si), s, self)

    @overload
    def union(self: Self, *s: Iterable[_S]) -> Self:
        ...

    @overload
    def union(self: orderedset[_T_co | _S], *s: Iterable[_S]) -> orderedset[_T_co | _S]:
        ...

    def union(self: orderedset[_T_co | _S], *s: Iterable[_S]) -> orderedset[_T_co | _S]:
        return reduce(lambda xi, si: xi.__or__(si), s, self)


oset: TypeAlias = orderedset[_T_co]
