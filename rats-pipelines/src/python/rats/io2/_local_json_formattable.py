from collections.abc import Mapping, Sequence
from typing import TypeAlias, TypeVar

JsonFormattable: TypeAlias = (
    Mapping[str, "JsonFormattable"] | str | int | float | Sequence["JsonFormattable"]
)


T_JsonFormattable = TypeVar("T_JsonFormattable", bound=JsonFormattable)
