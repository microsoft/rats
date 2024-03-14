from collections.abc import Mapping, Sequence
from typing import TypeAlias

JsonFormattable: TypeAlias = (
    Mapping[str, "JsonFormattable"] | str | int | float | Sequence["JsonFormattable"]
)


class Manifest(dict[str, JsonFormattable]): ...
