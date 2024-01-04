from typing import Any, Mapping

from oneml.processors.dag import IProcess


class ExposeGivenOutputsProcessor(IProcess):
    def __init__(self, outputs: Mapping[str, Any]) -> None:
        self._outputs = outputs

    def process(self) -> Mapping[str, Any]:
        return self._outputs
