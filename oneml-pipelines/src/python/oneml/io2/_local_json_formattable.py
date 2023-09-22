from typing import Mapping, Sequence, TypeAlias, TypeVar, Union

JsonFormattable: TypeAlias = Union[
    Mapping[str, "JsonFormattable"],
    str,
    int,
    float,
    Sequence["JsonFormattable"],
]


T_JsonFormattable = TypeVar("T_JsonFormattable", bound=JsonFormattable)
