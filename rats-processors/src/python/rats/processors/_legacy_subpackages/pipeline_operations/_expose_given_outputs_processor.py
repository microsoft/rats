from collections.abc import Mapping
from typing import Any

from rats.processors._legacy_subpackages.dag import IProcess


class ExposeGivenOutputsProcessor(IProcess):
    def __init__(self, outputs: Mapping[str, Any]) -> None:
        self._outputs = outputs

    def process(self) -> Mapping[str, Any]:
        return self._outputs
