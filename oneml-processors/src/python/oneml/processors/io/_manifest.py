from typing import Mapping, Sequence, TypeAlias, Union

JsonFormattable: TypeAlias = Union[
    Mapping[str, "JsonFormattable"],
    str,
    int,
    float,
    Sequence["JsonFormattable"],
]


class Manifest(dict[str, JsonFormattable]):
    ...
