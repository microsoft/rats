from __future__ import annotations

from itertools import chain
from typing import AbstractSet, Any, Generic, Hashable, Iterable, Iterator, TypeVar, overload

_T_co = TypeVar("_T_co", covariant=True)
_S_co = TypeVar("_S_co", covariant=True)
_S = TypeVar("_S")
Self = TypeVar("Self", bound="orderedset[Any]")


class orderedset(Hashable, AbstractSet[_T_co], Generic[_T_co]):
    _d: dict[_T_co, None]

    def __init__(self, __iterable: Iterable[_T_co] = ()) -> None:
        self._d = dict.fromkeys(__iterable, None)

    @overload
    def __and__(self: Self, other: AbstractSet[_T_co]) -> Self:
        ...

    @overload
    def __and__(self: Self, other: Any) -> Self:
        ...

    def __and__(self: Self, other: AbstractSet[_T_co]) -> Self:
        return self.__class__(k for k in self._d if k in other)

    def __contains__(self, x: object) -> bool:
        return x in self._d

    @overload
    def __eq__(self, __o: orderedset[_T_co]) -> bool:
        ...

    @overload
    def __eq__(self, __o: Any) -> bool:
        ...

    def __eq__(self, __o: Any) -> bool:
        assert isinstance(__o, self.__class__)
        return self.__class__ == __o.__class__ and tuple(self._d.keys()) == tuple(__o._d.keys())

    def __hash__(self) -> int:
        return hash(tuple(self._d.keys()))

    def __iter__(self) -> Iterator[_T_co]:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __or__(self: Self, __t: Iterable[_S_co]) -> Self:
        if isinstance(__t, Iterable):
            return self.__class__(chain(self._d, __t))
        else:
            raise ValueError("Argument is not an iterable.")

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + ", ".join(repr(k) for k in self._d) + ")"

    def __sub__(self: Self, other: AbstractSet[_T_co]) -> Self:
        return self.__class__(k for k in self._d if k not in other)

    def intersection(self: Self, *s: Iterable[_S]) -> Self:
        return self.__class__(k for k in self for si in s if k in si)

    def union(self: Self, *s: Iterable[_S]) -> Self:
        return self.__class__(chain(self._d, *s))


oset = orderedset
