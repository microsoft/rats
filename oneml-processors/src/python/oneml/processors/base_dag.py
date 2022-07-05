"""Base class for DAG of processing nodes."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from itertools import chain
from typing import Dict, Generic, Optional, Type, TypeVar, overload

from .data_annotation import Data
from .identifiers import Address, ObjectIdentifier, SimpleObjectIdentifier, _member_separator
from .node import InputPortName, Node, OutputPortName
from .processor import Processor


class NodeName(ObjectIdentifier):
    """Identifier of a node in a DAG."""

    pass


class SimpleNodeName(SimpleObjectIdentifier, NodeName):
    """Identifier of a node in a flat DAG."""

    pass


PortNameT = TypeVar("PortNameT", bound=ObjectIdentifier)


class PortAddress(Address[NodeName, PortNameT], Generic[PortNameT]):
    @property
    def node(self) -> NodeName:
        return self._object_name

    @property
    def port(self) -> PortNameT:
        return self._member_name

    @classmethod
    def _get_object_class(cls) -> Type[ObjectIdentifier]:
        return NodeName


class InputPortAddress(PortAddress[InputPortName]):
    f"""Address of a node input port within a DAG.

    Args:
        address: given in `NodeIdentifier{_member_separator}PortIdentifier` format.

    """

    @overload
    def __new__(cls, address: str) -> InputPortAddress:
        ...

    @overload
    def __new__(cls, node_name: str, port_name: str) -> InputPortAddress:
        ...

    def __new__(cls, first: str, second: Optional[str] = None) -> InputPortAddress:
        # see comment in Address.__new__
        return super().__new__(cls, first, second)

    @classmethod
    def _get_member_class(cls) -> Type[ObjectIdentifier]:
        return InputPortName


class OutputPortAddress(PortAddress[OutputPortName]):
    f"""Address of a node output port within a DAG.

    Args:
        address: given in `NodeIdentifier{_member_separator}PortIdentifier` format.
    """

    @overload
    def __new__(cls, address: str) -> OutputPortAddress:
        ...

    @overload
    def __new__(cls, node_name: str, port_name: str) -> OutputPortAddress:
        ...

    def __new__(cls, first: str, second: Optional[str] = None) -> OutputPortAddress:
        # see comment in Address.__new__
        return super().__new__(cls, first, second)

    @classmethod
    def _get_member_class(cls) -> Type[ObjectIdentifier]:
        return InputPortName


NodeNameT = TypeVar("NodeNameT", NodeName, SimpleNodeName)


@dataclass
class BaseDAG(Generic[NodeNameT], Node):
    nodes: Dict[NodeNameT, Processor]
    input_edges: Dict[InputPortAddress, InputPortName]
    output_edges: Dict[OutputPortName, OutputPortAddress]
    edges: Dict[InputPortAddress, OutputPortAddress]

    def __post_init__(self) -> None:
        # Consider: Move this to a seperate DAG_validation class (client)?  Initialize a default validator in the DAG's __init__?
        node_name_class = self._node_name_class()
        self.nodes = {node_name_class(k): v for k, v in self.nodes.items()}
        self.input_edges = {
            InputPortAddress(k): InputPortName(v) for k, v in self.input_edges.items()
        }
        self.output_edges = {
            OutputPortName(k): OutputPortAddress(v) for k, v in self.output_edges.items()
        }
        self.edges = {InputPortAddress(k): OutputPortAddress(v) for k, v in self.edges.items()}
        for node_name, port_name in chain(self.input_edges.keys(), self.edges.keys()):
            node = self.nodes[node_name]
            schema = node.get_input_schema()
            if port_name not in schema:
                available_ports = ", ".join(schema.keys())
                raise Exception(
                    f"Can't find input port <{port_name}> in node <{node_name}> that has input ports <{available_ports}>."
                )
        for node_name, port_name in chain(self.output_edges.values(), self.edges.values()):
            node = self.nodes[node_name]
            schema = node.get_output_schema()
            if port_name not in schema:
                available_ports = ", ".join(schema.keys())
                raise Exception(
                    f"Can't find output port <{port_name}> in node <{node_name}> that has output ports <{available_ports}>."
                )
        for node_name, node in self.nodes.items():
            for port_name in node.get_input_schema().keys():
                input_port_address = InputPortAddress(node_name, port_name)
                if (
                    input_port_address not in self.input_edges
                    and input_port_address not in self.edges
                ):
                    raise Exception(
                        f"Input port <{port_name}> of node <{node_name}> is not connect to any edge."
                    )
        self._input_schema = {}
        for input_port_address, input_port_name in self.input_edges.items():
            self._input_schema[input_port_name] = self.nodes[
                input_port_address.node
            ].get_input_schema()[input_port_address.port]
        self._output_schema = {
            outputPortName: self.nodes[output_port_address.node].get_output_schema()[
                output_port_address.port
            ]
            for outputPortName, output_port_address in self.output_edges.items()
        }

    @abstractmethod
    def _node_name_class(self) -> Type[NodeNameT]:
        ...

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return self._input_schema

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return self._output_schema

    def is_dag(self) -> bool:
        """Whether this node holds a dag internally.  Used by DAGFlattener."""
        return True
