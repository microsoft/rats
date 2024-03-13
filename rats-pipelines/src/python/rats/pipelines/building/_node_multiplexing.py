from __future__ import annotations

import itertools
import logging
from abc import abstractmethod
from collections.abc import Callable, Iterable
from typing import Protocol

from rats.pipelines.dag import PipelineNode
from rats.pipelines.dag._dag_client import PipelineDagClient

from ._node_namespacing import PipelineNamespaceClient

logger = logging.getLogger(__name__)

PipelineMultiplexValuesType = Iterable[str | int]


class IMultiplexPipelineNodes(Protocol):
    @abstractmethod
    def multiplex(self, values: PipelineMultiplexValuesType) -> PipelineNodeMultiplexer:
        pass


class MultiPipelineNodeExecutable(Protocol):
    @abstractmethod
    def execute(self, node: PipelineNode) -> None:
        pass


class ICallableMultiExecutable(Protocol):
    """Represents a callable object that we expect to treat as the execute method."""

    @abstractmethod
    def __call__(self, node: PipelineNode) -> None:
        pass


class CallableMultiExecutable(MultiPipelineNodeExecutable):
    _callback: ICallableMultiExecutable

    def __init__(self, callback: ICallableMultiExecutable) -> None:
        self._callback = callback

    def execute(self, node: PipelineNode) -> None:
        self._callback(node)


class PipelineNodeMultiplexer(IMultiplexPipelineNodes):
    _dag_client: PipelineDagClient
    _namespace_client: PipelineNamespaceClient
    _values: PipelineMultiplexValuesType

    def __init__(
        self,
        dag_client: PipelineDagClient,
        namespace_client: PipelineNamespaceClient,
        values: PipelineMultiplexValuesType,
    ):
        self._dag_client = dag_client
        self._namespace_client = namespace_client
        self._values = values

    def multiplex(self, values: PipelineMultiplexValuesType) -> PipelineNodeMultiplexer:
        cartesian_folds = [f"{a},{b}" for a, b in itertools.product(self._values, values)]

        return PipelineNodeMultiplexer(
            dag_client=self._dag_client,
            namespace_client=self._namespace_client,
            values=cartesian_folds,
        )

    def apply(self, prefix: str, callback: Callable[[PipelineNode], None]) -> None:
        for node in self.nodes(prefix):
            callback(node)

    def nodes(self, prefix: str) -> Iterable[PipelineNode]:
        return tuple([self._namespace_client.node(f"{prefix}[{x}]") for x in self._values])

    def add_internal_dependencies(self, prefix: str, dependencies: Iterable[str]) -> None:
        for dependency in dependencies:
            self.add_internal_dependency(prefix, dependency)

    def add_internal_dependency(self, prefix: str, dependency: str) -> None:
        for x in self._values:
            self._dag_client.add_dependency(
                self._namespace_client.node(f"{prefix}[{x}]"),
                self._namespace_client.node(f"{dependency}[{x}]"),
            )

    def add_external_dependencies(self, prefix: str, dependencies: Iterable[PipelineNode]) -> None:
        for dependency in dependencies:
            self.add_external_dependency(prefix, dependency)

    def add_external_dependency(self, prefix: str, dependency: PipelineNode) -> None:
        for node in self.nodes(prefix):
            self._dag_client.add_dependency(node, dependency)

    # def add_executable(self, prefix: str, executable: MultiPipelineNodeExecutable) -> None:
    #     def build_executable(n: PipelineNode) -> CallableExecutable:
    #         return CallableExecutable(lambda: executable.execute(n))
    #
    #     logger.debug(f"multiplexing executable for prefix: {prefix}")
    #     for node in self.nodes(prefix):
    #         logger.debug(f"multiplexed executable for node: {node}")
    #         self._dag_client.add_executable(node, build_executable(node))


class PipelineNodeMultiplexerFactory:
    _pipeline: PipelineDagClient

    def __init__(self, pipeline: PipelineDagClient):
        self._pipeline = pipeline

    def get_instance(
        self, namespace: PipelineNamespaceClient, values: PipelineMultiplexValuesType
    ) -> PipelineNodeMultiplexer:
        return PipelineNodeMultiplexer(
            dag_client=self._pipeline,
            namespace_client=namespace,
            values=values,
        )
