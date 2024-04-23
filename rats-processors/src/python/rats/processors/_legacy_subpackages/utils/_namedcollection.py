from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from functools import cached_property, reduce
from typing import TYPE_CHECKING, Any, Generic, Protocol, overload, runtime_checkable

from typing_extensions import Self, TypeVar

if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class SupportsAsDict(Protocol[T]):
    def _asdict(self) -> dict[str, T]: ...


class namedcollection(Generic[T_co]):
    """Ordered, immutable set of names and mapped attributes supporting recursive operations.

    Initialization and access of attributes is supported via dot notation and bracket notation.

    Examples:
        >>> from rats.processors._legacy_subpackages.utils import namedcollection

        >>> n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
        >>> n1.foo
        1
        >>> n1.bar
        2
        >>> n1["bar"]
        2

        >>> n2 = namedcollection(foo=1, bar=2, hey=3)
        >>> n2.foo
        1

        >>> n3 = namedcollection((("foo", 1), ("bar", 2), ("hey", 3)))
        >>> n3.bar
        2

        >>> n4 = namedcollection([("foo", 1), ("bar", 2), ("hey", 3)], boo=4)
        >>> n4.hey
        3

        >>> n5 = namedcollection([("foo.foo", 1), ("foo.bar", 2), ("bar.bar", 2)], boo=4)
        >>> n5.foo.foo
        1
        >>> n5["foo.foo"]
        1
        >>> n5.foo.bar
        2
        >>> n5["foo.bar"]
        2

        >>> n6 = namedcollection({"foo": 1, "bar": 2, "hey": n1}, boo=4)
        >>> n6.hey
        namedcollection(foo=1, bar=2, hey=3)
        >>> n6.boo
        4

        >>> n7 = namedcollection({"foo.foo": 1, "foo.bar": 2, "bar.bar": 2, "hey": 3}, boo=4)
        >>> assert n7.foo.foo == 1 and n7.bar.bar == 2 and n7.hey == 3 and n7.boo == 4

    Initialization of namedcollections is supported via `collections.abc.Mapping`,
    `rats.processors.utils.SupportsAsDict` (e.g., `collections.namedtuple` or subclasses of
    `rats.processors.utils.namedcollection`), iterable of tuples of name and value, and keyword
    arguments. Keys may contain dots to construct nested values.

    Supported operators:
        __eq__: equality of keys and values.
        __len__: number of keys.
        __iter__: iterator over keys.
        __or__: union of keys and recursive union of values across nested levels.
        __sub__: subtract keys using dot notation for subtracting nested namesets.
        __and__: NotImplemented.
        __repr__: string representation in the form of `namedcollection(X=..., shift=..., scale=...)`.

    Supported methods:
        _asdict: return a new dict which maps field names to their values.
        _replace: return a new instance of the namedcollection replacing specified fields with new values.
        _find: find locations of values in namedcollection and nested namesets.
        _rename: rename namedcollection names recursively splitting on dots (cannot rename across levels).
        _union: union of namedcollections.

    Properties:
        _depth: maximum number of levels of nested namedcollections.

    """

    _d: dict[str, T_co | Self]
    _hash: int | None = None

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, **kwargs: T_co) -> None: ...

    @overload
    def __init__(self, __map: SupportsKeysAndGetItem[str, T_co], **kwargs: T_co) -> None: ...

    @overload
    def __init__(self, __iterable: Iterable[tuple[str, T_co]], **kwargs: T_co) -> None: ...

    @overload
    def __init__(self, __asdict: SupportsAsDict[T_co], **kwargs: T_co) -> None: ...

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if len(args) == 1 and isinstance(args[0], Mapping):
            d = self._mapping_to_nested_collection(args[0])
        elif len(args) == 1 and isinstance(args[0], SupportsAsDict):
            d = self._mapping_to_nested_collection(args[0]._asdict())
        else:
            d = self._mapping_to_nested_collection(dict(*args))

        self._d = dict(d, **kwargs)
        self._hash = None
        if not all(isinstance(k, str) for k in self._d):
            raise ValueError("Input keys need to be `str` types.")
        if any(k.count(".") > 0 for k in self._d):
            raise ValueError("Input keys cannot contain dots.")

    def _mapping_to_nested_collection(self, __map: Mapping[str, T_co]) -> dict[str, T_co | Self]:
        d: dict[str, T_co | Self] = {}
        for k, v in __map.items():
            assert isinstance(k, str)
            k0, k1 = k.split(".", maxsplit=1) if "." in k else (k, "")
            if k1:
                d[k0] = self.__class__({k1: v}) if k0 not in d else d[k0] | self.__class__({k1: v})  # type: ignore[operator]
            else:
                d[k0] = v if k0 not in d else d[k0] | v  # type: ignore[operator]
        return d

    def __eq__(self, __o: Any) -> bool:
        return self.__class__ == __o.__class__ and self._d == __o._d

    def __len__(self) -> int:
        return len(self._d)

    def __iter__(self) -> Iterator[str]:
        return iter(self._d)

    def __contains__(self, o: object) -> bool:
        return o in self._d

    def __getitem__(self, key: str) -> Self | T_co:
        """Access attributes via bracket notation supporting keys with dots."""
        k0, k1 = key.split(".", maxsplit=1) if "." in key else (key, "")
        return self._d[k0] if not k1 else self._d[k0][k1]  # type: ignore[operator]

    def __getattr__(self, key: str) -> Self | T_co:
        try:  # https://stackoverflow.com/a/16237698
            return self._d[key]
        except KeyError:
            raise AttributeError(key) from None

    def __getstate__(self) -> dict[str, Any]:
        # our implementation of __getattr__ messes with pickle
        return dict(_d=self._d, _hash=self._hash)

    def __setstate__(self, d: Mapping[str, Any]) -> None:
        # our implementation of __getattr__ messes with pickle
        self._d = d["_d"]
        self._hash = d["_hash"]

    def __hash__(self) -> int:
        """Computes hash of object."""
        if self._hash is None:
            _hash = 0
            for pair in self._d.items():
                _hash ^= hash(pair)
            self._hash = _hash
        return self._hash

    def __or__(self, other: SupportsAsDict[T_co] | Mapping[str, T_co]) -> Self:
        """Union of keys and recursive union of values."""
        if not (isinstance(other, Mapping) or isinstance(other, SupportsAsDict)):
            raise TypeError("Input needs to be a Mapping or SupportsAsDict.")

        self_d = self._asdict()
        other_d = other._asdict() if isinstance(other, SupportsAsDict) else dict(other)
        ix = set(self_d) & set(other_d)
        values = self_d | other_d | {k: self_d[k] | other_d[k] for k in ix}  # type: ignore[operator]
        return self.__class__(values)

    def __and__(self, other: Any) -> Self:
        """Compute intersection of keys and values recursively.

        Args:
            other (Any): namedcollection or Mapping.

        Returns:
            Self: intersecting keys and values recursively.
        """
        raise NotImplementedError

    def __sub__(self, other: Iterable[str]) -> Self:
        """Subtract keys. Supports dot notation for nested namesets.

        Example:
            inputs - ("X", "shift", "scale")
            inputs - ("X.train", "X.eval", "scale")

        """
        d = self._asdict()
        for o in other:
            for k in tuple(d):
                ksplit, osplit = k.split("."), o.split(".")
                if k.startswith(o) and ksplit[: len(osplit)] == osplit:
                    d.pop(k)
        return self.__class__(d)

    def __repr__(self) -> str:
        d = self._asdict()
        repr_fmt = "(" + ", ".join(f"{name}=%r" for name in d) + ")"
        return self.__class__.__name__ + repr_fmt % tuple(d.values())

    def _asdict(self) -> dict[str, T_co]:
        """Return a flattened dict which maps field names to their values."""
        d: dict[str, T_co] = {}
        for k, v in self._d.items():
            if isinstance(v, namedcollection):
                d.update({f"{k}.{k1}": v1 for k1, v1 in v._asdict().items()})
            else:
                d[k] = v
        return d

    def _replace(self, d: Mapping[str, T] = {}, **kwargs: T) -> Self:
        """Return a new instance replacing (or adding) specified fields with new values.

        Example:
            >>> n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
            >>> n2 = n1._replace(foo=4)
            >>> assert n2 == namedcollection({"foo": 4, "bar": 2, "hey": 3})

            >>> n3 = namedcollection({"foo": 1, "bar.bar": 2, "bar.foo": 4, "hey": 3})
            >>> n4 = n3._replace({"bar.foo": 5, "bar.bar": 6}, hey=8)
            >>> assert n4 == namedcollection({"foo": 1, "bar.foo": 5, "bar.bar": 6, "hey": 8})

        Args:
            d: mapping of {name: value} where name supports dot notation.
            kwargs: mapping of {name: value}.

        Returns:
            New namedcollection with replaced (or added) values.

        """
        return self.__class__((self._asdict() | d), **kwargs)  # type: ignore

    def _find(self, *values: Any) -> tuple[str, ...]:
        """Find locations of values in namedcollection and nested namesets."""
        locs = []
        for v in values:
            for k, v1 in self._asdict().items():
                if v == v1:
                    locs.append(k)
                elif isinstance(v1, Iterable) and v in v1:
                    locs.append(k)
        return tuple(locs)

    def _rename(self, names: Mapping[str, str]) -> Self:
        """Rename namedcollection names recursively splitting on dots.

        Example:
        >>> n1 = namedcollection({"foo": 1, "boo": 2, "bar": 3, "hey": 4})
        >>> n2 = n1._rename({"foo": "foo2", "boo": "boo2"})
        >>> assert n2 == namedcollection({"foo2": 1, "boo2": 2, "bar": 3, "hey": 4})

        >>> n3 = n1._rename({"bar": "bar2.bee"})
        >>> assert n3 == namedcollection({"foo": 1, "boo": 2, "bar2.bee": 3, "hey": 4})

        Args:
            names: mapping of {current name: new name}.

        Returns:
            New namedcollection with renamed names.

        """
        d = self._asdict()
        names = _fill_wildcard_collections(names, self)
        for ok, nk in names.items():
            for k in tuple(d):
                ksplit, oksplit = k.split("."), ok.split(".")
                if k.startswith(ok) and ksplit[: len(oksplit)] == oksplit:
                    rk = k.replace(ok, nk, 1)
                    d[rk] = d[rk] | d.pop(k) if rk in d else d.pop(k)  # type: ignore[operator]

        return self.__class__(d)

    def _union(self, *s: Self) -> Self:
        return reduce(lambda xi, si: xi | si, s, self)

    @cached_property
    def _depth(self) -> int:
        """Maximum number of levels of nested namedcollections.

        Example:
            >>> n1 = namedcollection({"foo": 1, "bar": 2, "hey": 3})
            >>> assert n1._depth == 0
            >>> n2 = namedcollection({"foo.foo.foo": 1, "foo.bar": 2, "bar.bar": 2}, boo=4)
            >>> assert n2._depth == 2

        Returns:
            int: maximum number of levels of nested namedcollections.
        """
        children = [v._depth for v in self._d.values() if isinstance(v, namedcollection)]
        return 1 + max(children) if children else 0


ncoll = namedcollection[T_co]
NamedCollection = namedcollection[T_co]


def _fill_wildcard_collections(
    names: Mapping[str, str], collection: namedcollection[T_co]
) -> Mapping[str, str]:
    resolved = dict[str, str]()

    def resolve_new_key(ok1: str, ok2: str, nk1: str, nk2: str) -> None:
        if nk1 == "*":
            nk1 = ok1
        if ok2:
            ok = f"{ok1}.{ok2}"
        else:
            ok = ok1
        if nk2:
            nk = f"{nk1}.{nk2}"
        else:
            nk = nk1
        resolved[ok] = nk

    for ok, nk in names.items():
        ok_split, nk_split = ok.split(".", 1), nk.split(".", 1)
        ok1, ok2 = ok_split if len(ok_split) == 2 else (ok, "")
        nk1, nk2 = nk_split if len(nk_split) == 2 else (nk, "")
        if not ok2:
            resolved[ok] = nk
        else:
            if ok1 != "*":
                resolve_new_key(ok1, ok2, nk1, nk2)
            else:
                for k1 in collection:
                    ck1 = collection[k1]
                    if isinstance(ck1, namedcollection) and ok2 in ck1:
                        resolve_new_key(k1, ok2, nk1, nk2)
    return resolved
