from typing import Dict, Type

from .data_annotation import Data
from .identifiers import SimpleObjectIdentifier


class InputPortName(SimpleObjectIdentifier):
    """Identifier of an input port of a node."""

    pass


class OutputPortName(SimpleObjectIdentifier):
    """Identifier of an output port of a node."""

    pass


class Node:
    """Base class for DAG nodes."""

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        """Gets a mapping from input port name to expected type for the input."""
        ...

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        """Gets a mapping from output port name to the type of the output that will be produced."""
        ...

    def is_dag(self) -> bool:
        """Whether this node holds a dag internally.  Used by DAGFlattener."""
        return False
