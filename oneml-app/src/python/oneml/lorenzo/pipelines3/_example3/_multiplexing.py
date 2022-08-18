# type: ignore
# flake8: noqa
from __future__ import annotations

import itertools
import logging
from abc import abstractmethod
from typing import Callable, Iterable, Protocol, Union

from oneml.pipelines import CallableExecutable, PipelineNode

from .._example._builders import PipelineNodeExecutable
from ._namespaces import PipelineNamespaceClient
from ._pipeline_builder import PipelineBuilder

logger = logging.getLogger(__name__)

PipelineMultiplexValuesType = Iterable[Union[str, int]]


class MultiPipelineNodeExecutable(Protocol):
    @abstractmethod
    def execute(self, node: PipelineNode) -> None:
        pass


class CallableMultiExecutable(MultiPipelineNodeExecutable):

    _callback: Callable[[PipelineNode], None]

    def __init__(self, callback: Callable[[PipelineNode], None]):
        self._callback = callback

    def execute(self, node: PipelineNode) -> None:
        self._callback(node)


class PipelineNodeMultiplexer:
    _pipeline: PipelineBuilder
    _namespace: PipelineNamespaceClient
    _values: PipelineMultiplexValuesType

    def __init__(
        self,
        pipeline: PipelineBuilder,
        namespace: PipelineNamespaceClient,
        values: PipelineMultiplexValuesType,
    ):
        self._pipeline = pipeline
        self._namespace = namespace
        self._values = values

    def multiplex(self, values: PipelineMultiplexValuesType) -> PipelineNodeMultiplexer:
        cartesian_folds = [f"{a},{b}" for a, b in itertools.product(self._values, values)]

        return PipelineNodeMultiplexer(
            pipeline=self._pipeline,
            namespace=self._namespace,
            values=cartesian_folds,
        )

    def apply(self, prefix: str, callback: Callable[[PipelineNode], None]) -> None:
        for node in self.nodes(prefix):
            callback(node)

    def nodes(self, prefix: str) -> Iterable[PipelineNode]:
        return tuple([self._namespace.node(f"{prefix}[{x}]") for x in self._values])

    def add_internal_dependencies(self, prefix: str, dependencies: Iterable[str]) -> None:
        for dependency in dependencies:
            self.add_internal_dependency(prefix, dependency)

    def add_internal_dependency(self, prefix: str, dependency: str) -> None:
        for x in self._values:
            self._pipeline.add_dependency(
                self._namespace.node(f"{prefix}[{x}]"), self._namespace.node(f"{dependency}[{x}]")
            )

    def add_external_dependencies(self, prefix: str, dependencies: Iterable[PipelineNode]) -> None:
        for dependency in dependencies:
            self.add_external_dependency(prefix, dependency)

    def add_external_dependency(self, prefix: str, dependency: PipelineNode) -> None:
        for node in self.nodes(prefix):
            self._pipeline.add_dependency(node, dependency)

    def add_executable(self, prefix: str, executable: MultiPipelineNodeExecutable) -> None:
        def build_executable(n: PipelineNode) -> CallableExecutable:
            return CallableExecutable(lambda: executable.execute(n))

        logger.debug(f"multiplexing executable for prefix: {prefix}")
        for node in self.nodes(prefix):
            logger.debug(f"multiplexed executable for node: {node}")
            self._pipeline.add_executable(node, build_executable(node))


class PipelineNodeMultiplexerFactory:
    _pipeline: PipelineBuilder

    def __init__(self, pipeline: PipelineBuilder):
        self._pipeline = pipeline

    def get_instance(
        self, namespace: PipelineNamespaceClient, values: PipelineMultiplexValuesType
    ) -> PipelineNodeMultiplexer:
        return PipelineNodeMultiplexer(
            pipeline=self._pipeline,
            namespace=namespace,
            values=values,
        )
