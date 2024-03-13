from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol

from rats.pipelines.dag import PipelineNode


class ICreatePipelineNamespaces(Protocol):
    @abstractmethod
    def namespace(self, name: str) -> ICreatePipelineNamespaces:
        pass


class INamespacePipelineNodes(Protocol):
    @abstractmethod
    def node(self, name: str) -> PipelineNode:
        pass

    @abstractmethod
    def nodes(self, names: Iterable[str]) -> Iterable[PipelineNode]:
        pass

    @abstractmethod
    def head_node(self) -> PipelineNode:
        pass

    @abstractmethod
    def tail_node(self) -> PipelineNode:
        pass


class PipelineNamespaceClient(ICreatePipelineNamespaces, INamespacePipelineNodes):
    _name: str

    def __init__(self, name: str):
        self._name = name

    def namespace(self, name: str) -> PipelineNamespaceClient:
        return PipelineNamespaceClient(self.node(name).key)

    def nodes(self, names: Iterable[str]) -> Iterable[PipelineNode]:
        return [PipelineNode(f"{self._name}/{name}") for name in names]

    def node(self, name: str) -> PipelineNode:
        return PipelineNode(f"{self._name}/{name}")

    def head_node(self) -> PipelineNode:
        return PipelineNode(f"{self._name}[head]")

    def tail_node(self) -> PipelineNode:
        return PipelineNode(f"{self._name}[tail]")
