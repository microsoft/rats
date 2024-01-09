from collections.abc import Mapping
from typing import Any, NamedTuple

from ..dag import IProcess


class InputsToDictOutput(NamedTuple):
    dct: dict[str, Any]


class InputsToDict(IProcess):
    def process(self, **inputs: Any) -> InputsToDictOutput:
        return InputsToDictOutput(dct=inputs)


class DictToOutputs(IProcess):
    def process(self, dct: Mapping[str, Any]) -> dict[str, Any]:
        return dict(dct)
