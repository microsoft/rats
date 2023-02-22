from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from itertools import groupby
from typing import Any, Iterable, Mapping, Sequence

from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.context._client import IManageExecutionContexts, IProvideExecutionContexts
from oneml.pipelines.dag import PipelineDataDependency, PipelineNode
from oneml.pipelines.session import (
    IExecutable,
    PipelineNodeDataClient,
    PipelineNodeInputDataClient,
    PipelinePort,
    PipelineSessionClient,
)
from oneml.pipelines.session._components import ComponentId

from ._dag import DAG, DagDependency, DagNode, ProcessorProps
from ._processor import InMethod, InProcessorParam, IProcess

logger = logging.getLogger(__name__)


class P2Pipeline:
    @staticmethod
    def node(node: DagNode) -> PipelineNode:
        return PipelineNode(repr(node))

    @classmethod
    def data_dp(cls, node: DagNode, in_name: str, out_name: str) -> PipelineDataDependency[Any]:
        in_port: PipelinePort[Any] = PipelinePort(in_name)
        out_port: PipelinePort[Any] = PipelinePort(out_name)
        return PipelineDataDependency(P2Pipeline.node(node), out_port, in_port)

    @classmethod
    def data_dependencies(
        cls, dependencies: Iterable[DagDependency]
    ) -> tuple[PipelineDataDependency[Any], ...]:
        if any(dp.node is None for dp in dependencies):
            raise ValueError("Trying to convert a hanging depencency.")

        data_dps: list[PipelineDataDependency[Any]] = []
        grouped_dps: defaultdict[str, list[DagDependency]] = defaultdict(list)
        for k, g in groupby(dependencies, key=lambda dp: dp.in_arg.name):
            grouped_dps[k].extend(list(g))

        for k, dps in grouped_dps.items():
            for i, dp in enumerate(dps):
                in_arg_name = dp.in_arg.name + ":" + str(i)
                data_dps.append(cls.data_dp(dp.node, in_arg_name, dp.out_arg.name))

        return tuple(data_dps)


class DataClient:
    def __init__(
        self, input_client: PipelineNodeInputDataClient, output_client: PipelineNodeDataClient
    ) -> None:
        super().__init__()
        self._input_client = input_client
        self._output_client = output_client

    def load(self, param: InProcessorParam) -> Any:
        p = re.compile(rf"^{param.name}:(\d+)")
        gathered_inputs = [
            (s, int(match.group(1)))  # converts to integer
            for s in self._input_client.get_ports()
            for match in (p.match(s.key),)
            if match
        ]
        if param.kind in [param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY]:
            if len(gathered_inputs) > 1:
                raise ValueError("Too many dependencies for a positional or keyword parameter.")
            return self._input_client.get_data(gathered_inputs.pop()[0])

        gathered_inputs.sort(key=lambda sm: sm[1])  # sorts by integer number
        if param.kind == param.VAR_POSITIONAL:
            return tuple(self._input_client.get_data(s) for s, _ in gathered_inputs)
        elif param.kind == param.VAR_KEYWORD:
            if not all(isinstance(gi, dict) for gi, _ in gathered_inputs):
                raise ValueError("Gathered inputs should be of dictionary type.")
            return {k: v for gi, _ in gathered_inputs for k, v in gi.items()}  # type: ignore

    def load_parameters(
        self,
        parameters: Mapping[str, InProcessorParam],
        in_method: InMethod,
        exclude: Sequence[str] = (),
    ) -> tuple[Sequence[Any], Mapping[str, Any]]:
        pos_only, pos_vars, kw_args, kw_vars = [], [], {}, {}
        for k, param in parameters.items():
            if k in exclude:
                continue
            if param.in_method != in_method:
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


class SessionExecutableProvider(IExecutable):
    _session_provider: IProvideExecutionContexts[PipelineSessionClient]
    _node: DagNode
    _props: ProcessorProps

    def __init__(
        self,
        session_provider: IProvideExecutionContexts[PipelineSessionClient],
        node: DagNode,
        props: ProcessorProps,
    ) -> None:
        self._session_provider = session_provider
        self._node = node
        self._props = props

    def get_processor(
        self, data_client: DataClient, session_client: PipelineSessionClient
    ) -> IProcess:
        params = {
            k: session_client.get_component(ComponentId(v.name))
            if isinstance(v, RegistryId)
            else v
            for k, v in self._props.params_getter.items()
        }
        pos_args, kw_args = data_client.load_parameters(self._props.inputs, InMethod.init)
        return self._props.processor_type(*pos_args, **params, **kw_args)

    def execute(self) -> None:
        session_client = self._session_provider.get_context()
        logger.debug(f"Node {self._node} execute start.")
        pipeline_node = P2Pipeline.node(self._node)
        input_client = session_client.node_input_data_client_factory().get_instance(pipeline_node)
        output_client = session_client.node_data_client_factory().get_instance(pipeline_node)
        data_client = DataClient(input_client, output_client)
        processor = self.get_processor(data_client, session_client)
        pos_args, kw_args = data_client.load_parameters(self._props.inputs, InMethod.process)
        outputs = processor.process(*pos_args, **kw_args)
        if outputs:
            for key, val in outputs.items():
                data_client.save(key, val)
        logger.debug(f"Node {self._node} execute end.")


@dataclass(frozen=True)
class RegistryId:
    name: str
    param_type: type


class ParamsRegistry:
    _registry: dict[str, RegistryId]

    def __init__(self) -> None:
        self._registry = {}

    def add(self, id: RegistryId, param: Any) -> None:
        ...

    def get(self, id: RegistryId) -> Any:
        ...


# class SingletonsGetter(IGetSingletons):
#     _singletons_ids: tuple[SingletonId, ...]
#     _registry: SingletonsRegistry

#     def __init__(self, singleton_ids: Sequence[SingletonId], registry: SingletonsRegistry) -> None:
#         self._singletons_ids = tuple(singleton_ids)
#         self._registry = registry

#     def __call__(self) -> Mapping[str, Any]:
#         params: dict[str, Any] = {}
#         for id in self._singletons_ids:
#             params.update(self._registry.get_singleton(id))
#         return params


class PipelineSessionProvider:

    _builder_factory: PipelineBuilderFactory
    _session_context: IManageExecutionContexts[PipelineSessionClient]

    def __init__(
        self,
        builder_factory: PipelineBuilderFactory,
        session_context: IManageExecutionContexts[PipelineSessionClient],
    ) -> None:
        self._builder_factory = builder_factory
        self._session_context = session_context

    def get_session(self, dag: DAG) -> PipelineSessionClient:
        builder = self._builder_factory.get_instance()

        for node in dag.nodes:
            builder.add_node(P2Pipeline.node(node))
            props = dag.nodes[node]

            sess_executable = SessionExecutableProvider(
                session_provider=self._session_context,
                node=node,
                props=props,
            )
            builder.add_executable(P2Pipeline.node(node), sess_executable)

        for node, dependencies in dag.dependencies.items():
            builder.add_data_dependencies(
                P2Pipeline.node(node), P2Pipeline.data_dependencies(dependencies)
            )

        session = builder.build_session()
        return session
