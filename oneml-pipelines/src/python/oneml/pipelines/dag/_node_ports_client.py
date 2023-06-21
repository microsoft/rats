from abc import abstractmethod
from typing import Any, Protocol

from ._structs import PipelineNode, PipelinePort


class IGetPipelineNodePorts(Protocol):
    @abstractmethod
    def get_node_input_ports(self, node: PipelineNode) -> tuple[PipelinePort[Any], ...]:
        ...

    @abstractmethod
    def get_node_output_ports(self, node: PipelineNode) -> tuple[PipelinePort[Any], ...]:
        ...


class IRegisterPipelineNodePorts(Protocol):
    @abstractmethod
    def register_node_input_ports(
        self, node: PipelineNode, ports: tuple[PipelinePort[Any], ...]
    ) -> None:
        ...

    @abstractmethod
    def register_node_output_ports(
        self, node: PipelineNode, ports: tuple[PipelinePort[Any], ...]
    ) -> None:
        ...


class IManagePipelineNodePorts(IGetPipelineNodePorts, IRegisterPipelineNodePorts, Protocol):
    pass


class PipelineNodePortsClient(IManagePipelineNodePorts):
    _input_ports: dict[PipelineNode, tuple[PipelinePort[Any], ...]]
    _output_ports: dict[PipelineNode, tuple[PipelinePort[Any], ...]]

    def __init__(self) -> None:
        self._input_ports = {}
        self._output_ports = {}

    def register_node_input_ports(
        self, node: PipelineNode, ports: tuple[PipelinePort[Any], ...]
    ) -> None:
        self._input_ports[node] = ports

    def register_node_output_ports(
        self, node: PipelineNode, ports: tuple[PipelinePort[Any], ...]
    ) -> None:
        self._output_ports[node] = ports

    def get_node_input_ports(self, node: PipelineNode) -> tuple[PipelinePort[Any], ...]:
        return self._input_ports.get(node, tuple())

    def get_node_output_ports(self, node: PipelineNode) -> tuple[PipelinePort[Any], ...]:
        return self._output_ports.get(node, tuple())
