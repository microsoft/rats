from __future__ import annotations

from functools import reduce
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Protocol,
    overload,
    runtime_checkable,
)

from typing_extensions import Self, TypeVar

if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class SupportsAsDict(Protocol[T]):
    def _asdict(self) -> dict[str, T]:
        ...


class namedcollection(Generic[T_co]):
    """Ordered, immutable set of names and mapped attributes supporting recursive operations.

    Access of attributes is supported via dot notation and bracket notation.

    Examples:
        >>> from oneml.processors.utils import namedcollection
        >>> stz = namedcollection(X=namedcollection(train=1.0, eval=2.0), shift=3.0, scale=4.0)
        >>> stz.X.train
        1.0
        >>> stz["X"]["train"]
        1.0

    Initialization of namedcollections is supported via `collections.abc.Mapping`,
    `oneml.processors.utils.SupportsAsDict` (e.g., `collections.namedtuple`, subclasses of
    `oneml.processors.utils.namedcollection`), iterable of tuples of name and value, and keyword
    arguments. namedcollection keys cannot contain dots.

    Supported operators:
        __eq__: equality of keys and values.
        __len__: number of keys.
        __iter__: iterator over keys.
        __or__: union of keys and recursive union of values across namedcollections.
        __sub__: subtract keys. Supports dot notation for subtracting nested namesets.
        __and__: NotImplemented.
        __repr__: string representation in the form of `namedcollection(X=..., shift=..., scale=...)`.

    Supported methods:
        _asdict: return a new dict which maps field names to their values.
        _replace: return a new instance of the namedcollection replacing specified fields with new values.
        _find: find locations of values in namedcollection and nested namesets.
        _rename: rename namedcollection names recursively splitting on dots (cannot rename across levels).
        _union: union of namedcollections.

    Warning: this class does not extend `collections.abc.Set` and is not a python exchangable set.

    """

    _d: dict[str, T_co]
    _hash: int | None = None

    @overload
    def __init__(self) -> None:
        ...

    @overload
    def __init__(self, **kwargs: T_co) -> None:
        ...

    @overload
    def __init__(self, __map: SupportsKeysAndGetItem[str, T_co], **kwargs: T_co) -> None:
        ...

    @overload
    def __init__(self, __iterable: Iterable[tuple[str, T_co]], **kwargs: T_co) -> None:
        ...

    @overload
    def __init__(self, __asdict: SupportsAsDict[T_co], **kwargs: T_co) -> None:
        ...

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        mod_args = (a._asdict() if isinstance(a, SupportsAsDict) else a for a in args)
        self._d = dict(*mod_args, **kwargs)
        self._hash = None
        if not all(isinstance(k, str) for k in self._d):
            raise ValueError("Input keys need to be `str` types.")
        if any(k.count(".") > 0 for k in self._d):
            raise ValueError("Input keys cannot contain dots.")

    def __eq__(self, __o: Any) -> bool:
        return self.__class__ == __o.__class__ and self._d == __o._d

    def __len__(self) -> int:
        return len(self._d)

    def __iter__(self) -> Iterator[str]:
        return iter(self._d)

    def __contains__(self, o: object) -> bool:
        return o in self._d

    def __getitem__(self, key: str) -> T_co:
        return self._d[key]

    def __getattr__(self, key: str) -> T_co:
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

    def __or__(self, other: Self | Mapping[str, T_co]) -> Self:
        """Union of keys and recursive union of values."""
        ix = set(self) & set(other)
        other_d = other._d if issubclass(other.__class__, namedcollection) else other
        values = self._d | other_d | {k: self[k] | other[k] for k in ix}  # type: ignore
        return self.__class__(**values)

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
        ns = {}
        okeys = set(tuple(o.split(".", maxsplit=1)) if "." in o else (o, "") for o in other)
        for k, v in self._d.items():
            if all(k != o1 for (o1, _) in okeys):
                ns[k] = v
            elif any(k == o1 and o2 for (o1, o2) in okeys) and issubclass(
                v.__class__, namedcollection
            ):
                res = v - tuple(o2 for (o1, o2) in okeys if o1 == k and o2)  # type: ignore
                if res:
                    ns[k] = res
            elif any(k == o1 and o2 for (o1, o2) in okeys) and not issubclass(
                v.__class__, namedcollection
            ):
                raise ValueError(f"Cannot subtract {other} from {dict(k=v)}.")
        return self.__class__(**ns)

    def __repr__(self) -> str:
        repr_fmt = "(" + ", ".join(f"{name}=%r" for name in self._d) + ")"
        return self.__class__.__name__ + repr_fmt % tuple(self._d.values())

    def _asdict(self) -> dict[str, T_co]:
        """Return a new dict which maps field names to their values."""
        return self._d.copy()

    def _replace(self, **kwargs: T) -> Self:
        """Return a new instance of the namedcollection replacing fields with new values."""
        return self.__class__(**(self._d | kwargs))

    def _find(self, *values: Any) -> tuple[str, ...]:
        """Find locations of values in namedcollection and nested namesets."""
        locs = []
        for v in values:
            for k, v1 in self._d.items():
                if v == v1:
                    locs.append(k)
                elif issubclass(v1.__class__, namedcollection):
                    locs.extend(f"{k}.{i}" for i in v1._find(v))  # type: ignore
                elif isinstance(v1, Iterable) and v in v1:
                    locs.append(k)
        return tuple(locs)

    def _rename(
        self,
        names: Mapping[str, str],
    ) -> Self:
        """Rename namedcollection names recursively splitting on dots.

        Args:
            names: mapping of {current name: new name}.

        Returns:
            New namedcollection with renamed names.

        Examples:
            >>> train_stz.rename_inputs({"X": "X0"})
            >>> train_stz.rename_inputs({"X.train": "X.train0"})
            >>> train_stz.rename_inputs({"X.train": "X0.train0"})

        """
        d = self._d.copy()
        for ok, nk in names.items():
            ok_split = ok.split(".", maxsplit=1)
            nk_split = nk.split(".", maxsplit=1)
            if len(ok_split) == 1 and len(nk_split) == 1:
                d[nk] = d.pop(ok) if nk not in d else d[nk] | d.pop(ok)  # type: ignore
            elif len(ok_split) == 2 and len(nk_split) == 2:
                if nk_split[0] == ok_split[0]:
                    d[nk_split[0]] = d.pop(ok_split[0])._rename({ok_split[1]: nk_split[1]})  # type: ignore
                else:
                    new_v = d[ok_split[0]].__class__(**{nk_split[1]: d[ok_split[0]][ok_split[1]]})  # type: ignore
                    d[nk_split[0]] = new_v if nk_split[0] not in d else d[nk_split[0]] | new_v  # type: ignore
                    d[ok_split[0]] -= (ok_split[1],)  # type: ignore
                    if len(d[ok_split[0]]) == 0:  # type: ignore[arg-type]
                        d.pop(ok_split[0])
            else:
                raise ValueError(f"Cannot rename {ok} to {nk}.")
        return self.__class__(**d)

    def _union(self, *s: Self) -> Self:
        return reduce(lambda xi, si: xi | si, s, self)


ncoll = namedcollection[T_co]
NamedCollection = namedcollection[T_co]
