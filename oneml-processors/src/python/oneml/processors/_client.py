from __future__ import annotations

import logging
import re
from inspect import Parameter
from typing import Any, Generic, Iterable, Mapping, Sequence, TypeVar

from oneml.pipelines.building import IPipelineSessionExecutable, PipelineBuilderFactory
from oneml.pipelines.dag import PipelineDataDependency, PipelineNode
from oneml.pipelines.session import (
    PipelineNodeDataClient,
    PipelineNodeInputDataClient,
    PipelinePort,
    PipelineSessionClient,
)

from ._dependency_kind import DependencyKindPipelineExpander
from ._pipeline import PDependency, Pipeline, PNode
from ._processor import DataArg, Provider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)
TI = TypeVar("TI", contravariant=True)  # generic input types for processor
TO = TypeVar("TO", covariant=True)  # generic output types for processor


class P2Pipeline:
    @staticmethod
    def node(node: PNode) -> PipelineNode:
        return PipelineNode(repr(node))

    @classmethod
    def data_dp(
        cls, node: PNode, in_arg: DataArg[TI], out_arg: DataArg[TO]
    ) -> PipelineDataDependency[TI]:
        in_port = PipelinePort[in_arg.annotation](in_arg.key)  # type: ignore[name-defined]
        out_port = PipelinePort[out_arg.annotation](out_arg.key)  # type: ignore[name-defined]
        return PipelineDataDependency(P2Pipeline.node(node), out_port, in_port)

    @classmethod
    def data_dependencies(
        cls, dependencies: Iterable[PDependency[TI, TO]]
    ) -> tuple[PipelineDataDependency[TI], ...]:
        if any(dp.node is None for dp in dependencies):
            raise ValueError("Trying to convert a hanging depencency.")
        return tuple(cls.data_dp(dp.node, dp.in_arg, dp.out_arg) for dp in dependencies if dp.node)


class DataClient:
    def __init__(
        self, input_client: PipelineNodeInputDataClient, output_client: PipelineNodeDataClient
    ) -> None:
        super().__init__()
        self._input_client = input_client
        self._output_client = output_client

    def load(self, param: Parameter) -> Any:
        if param.kind in [param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY]:
            return self._input_client.get_data(PipelinePort(param.name))
        elif param.kind in [param.VAR_POSITIONAL, param.VAR_KEYWORD]:
            p = re.compile(rf"^{param.name}:(\d+)")
            gathered_inputs = [
                (s, int(match.group(1)))
                for s in self._input_client.get_ports()
                for match in (p.match(s.key),)
                if match
            ]
            gathered_inputs.sort(key=lambda sm: sm[1])
            if param.kind == param.VAR_POSITIONAL:
                return tuple(self._input_client.get_data(s) for s, _ in gathered_inputs)
            elif param.kind == param.VAR_KEYWORD:
                if not all(isinstance(gi, dict) for gi, _ in gathered_inputs):
                    raise ValueError("Gathered inputs should be of dictionary type.")
                return {k: v for gi, _ in gathered_inputs for k, v in gi.items()}  # type: ignore

    def save(self, name: str, data: Any) -> None:
        self._output_client.publish_data(PipelinePort(name), data)

    def get_formatted_args(
        self, parameters: Mapping[str, Parameter], exclude: Sequence[str] = ()
    ) -> Mapping[str, Any]:
        pos_only, pos_vars, kw_args, kw_vars = [], [], {}, {}
        for k, param in parameters.items():
            if k in exclude:
                continue
            elif param.kind == param.POSITIONAL_ONLY:
                pos_only.append(self.load(param))  # one value is returned
            elif param.kind == param.VAR_POSITIONAL:
                pos_vars.extend(self.load(param))  # a sequence of values is returned
            elif param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
                kw_args[k] = self.load(param)  # one value is returned
            elif param.kind == param.VAR_KEYWORD:
                kw_vars.update(self.load(param))  # a ditionary of values is returned

        return {"positional_args": pos_only + pos_vars, "keyword_args": {**kw_args, **kw_vars}}


class SessionExecutableProvider(IPipelineSessionExecutable, Generic[T]):
    _node: PNode
    _provider: Provider[T]

    def __init__(self, node: PNode, provider: Provider[T]) -> None:
        super().__init__()
        self._node = node
        self._provider = provider

    def execute(self, session_client: PipelineSessionClient) -> None:
        logger.debug(f"Node {self._node} execute start.")
        pipeline_node = P2Pipeline.node(self._node)
        input_client = session_client.node_input_data_client_factory().get_instance(pipeline_node)
        output_client = session_client.node_data_client_factory().get_instance(pipeline_node)
        self._provider.execute(DataClient(input_client, output_client))
        logger.debug(f"Node {self._node} execute end.")


class PipelineSessionProvider:
    @classmethod
    def get_session(cls, pipeline: Pipeline) -> PipelineSessionClient:
        pipeline = DependencyKindPipelineExpander(pipeline).expand()
        builder = PipelineBuilderFactory().get_instance()

        for node in pipeline.nodes:
            builder.add_node(P2Pipeline.node(node))
            sess_executable = SessionExecutableProvider(node, pipeline.props[node].exec_provider)
            builder.add_executable(P2Pipeline.node(node), sess_executable)

        for node, dependencies in pipeline.dependencies.items():
            builder.add_data_dependencies(
                P2Pipeline.node(node), P2Pipeline.data_dependencies(dependencies)
            )

        session = builder.build_session()
        return session
