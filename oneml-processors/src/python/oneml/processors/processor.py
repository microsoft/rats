"""A node in a processing DAG."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

from .data_annotation import Data
from .identifiers import SimpleObjectIdentifier

if TYPE_CHECKING:
    from .run_context import RunContext


class InputPortName(SimpleObjectIdentifier):
    """Identifier of an input port of a node."""

    pass


class OutputPortName(SimpleObjectIdentifier):
    """Identifier of an output port of a node."""

    pass


class ProcessingNode:
    """Interface all DAG nodes should implement."""

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        """Gets a mapping from input port name to expected type for the input."""
        ...

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        """Gets a mapping from output port name to the type of the output that will be produced."""
        ...


class Processor(ProcessingNode):
    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        ...


class ProcessorUsingSignature(Processor):
    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return self.__class__.input_schema

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return self.__class__.output_schema

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        return self._process(run_context, **inputs)
