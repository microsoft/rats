from __future__ import annotations

import logging
import re
from collections import defaultdict
from inspect import Parameter
from itertools import groupby
from typing import Any, Iterable, Mapping, Sequence, cast

from oneml.pipelines.building import IPipelineSessionExecutable, PipelineBuilderFactory
from oneml.pipelines.dag import PipelineDataDependency, PipelineNode
from oneml.pipelines.session import (
    PipelineNodeDataClient,
    PipelineNodeInputDataClient,
    PipelinePort,
    PipelineSessionClient,
)

from ._gathervars import GatherVarsPipelineExpander
from ._pipeline import PDependency, Pipeline, PNode
from ._processor import Provider

logger = logging.getLogger(__name__)


class P2Pipeline:
    @staticmethod
    def node(node: PNode) -> PipelineNode:
        return PipelineNode(repr(node))

    @classmethod
    def data_dp(cls, node: PNode, in_name: str, out_name: str) -> PipelineDataDependency[Any]:
        in_port: PipelinePort[Any] = PipelinePort(in_name)
        out_port: PipelinePort[Any] = PipelinePort(out_name)
        return PipelineDataDependency(P2Pipeline.node(node), out_port, in_port)

    @classmethod
    def data_dependencies(
        cls, dependencies: Iterable[PDependency]
    ) -> tuple[PipelineDataDependency[Any], ...]:
        if any(dp.node is None for dp in dependencies):
            raise ValueError("Trying to convert a hanging depencency.")

        data_dps: list[PipelineDataDependency[Any]] = []
        grouped_dps: defaultdict[str, list[PDependency]] = defaultdict(list)
        for k, g in groupby(dependencies, key=lambda dp: dp.in_arg.name):
            grouped_dps[k].extend(list(g))

        for k, dps in grouped_dps.items():
            if len(dps) == 1:
                dp_node = cast(PNode, dps[0].node)
                data_dps.append(cls.data_dp(dp_node, dps[0].in_arg.name, dps[0].out_arg.name))
            else:
                for i, dp in enumerate(dps):
                    dp_node = cast(PNode, dps[0].node)
                    data_dps.append(
                        cls.data_dp(dp_node, dp.in_arg.name + ":" + str(i), dp.out_arg.name)
                    )

        return tuple(data_dps)


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
                (s, int(match.group(1)))  # converts to integer
                for s in self._input_client.get_ports()
                for match in (p.match(s.key),)
                if match
            ]
            gathered_inputs.sort(key=lambda sm: sm[1])  # sorts by integer number
            if param.kind == param.VAR_POSITIONAL:
                return tuple(self._input_client.get_data(s) for s, _ in gathered_inputs)
            elif param.kind == param.VAR_KEYWORD:
                if not all(isinstance(gi, dict) for gi, _ in gathered_inputs):
                    raise ValueError("Gathered inputs should be of dictionary type.")
                return {k: v for gi, _ in gathered_inputs for k, v in gi.items()}  # type: ignore

    def load_parameters(
        self, parameters: Mapping[str, Parameter], exclude: Sequence[str] = ()
    ) -> tuple[Sequence[Any], Mapping[str, Any]]:
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

        return (pos_only + pos_vars, {**kw_args, **kw_vars})

    def save(self, name: str, data: Any) -> None:
        self._output_client.publish_data(PipelinePort(name), data)


class SessionExecutableProvider(IPipelineSessionExecutable):
    _node: PNode
    _provider: Provider

    def __init__(self, node: PNode, provider: Provider) -> None:
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
        pipeline = GatherVarsPipelineExpander(pipeline).expand()
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
