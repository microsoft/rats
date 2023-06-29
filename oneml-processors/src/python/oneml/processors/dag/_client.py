from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

from oneml.io import IGetLoaders, PipelineDataId
from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.dag import (
    PipelineDataDependency,
    PipelineNode,
    PipelinePort,
    PipelineSessionId,
)
from oneml.pipelines.session import IExecutable, PipelineSessionClient
from oneml.pipelines.session._context import OnemlSessionContextIds
from oneml.pipelines.session._running_session_registry import IGetSessionClient
from oneml.processors.utils import orderedset
from oneml.services import IProvideServices
from oneml.services._context import ContextClient

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
        for dp in dependencies:
            grouped_dps[dp.in_arg.name].append(dp)

        for dps in grouped_dps.values():
            for i, dp in enumerate(dps):
                in_arg_name = dp.in_arg.name + ":" + str(i)
                data_dps.append(cls.data_dp(dp.node, in_arg_name, dp.out_arg.name))

        return tuple(data_dps)


class ProcessorDataLoader:
    _node: DagNode
    _session_id: PipelineSessionId
    _loaders_getter: IGetLoaders[Any]
    _port_mapper: dict[str, list[PipelineDataId[Any]]]

    def __init__(
        self,
        node: DagNode,
        session_id: PipelineSessionId,
        loaders_getter: IGetLoaders[Any],
        dependencies: Sequence[DagDependency],
    ) -> None:
        self._node = node
        self._session_id = session_id
        self._loaders_getter = loaders_getter
        self._port_mapper = self._map_ports(dependencies)

    def _map_ports(
        self, dependencies: Sequence[DagDependency]
    ) -> dict[str, list[PipelineDataId[Any]]]:
        grouped_dps: defaultdict[str, list[DagDependency]] = defaultdict(list)
        for dp in dependencies:
            grouped_dps[dp.in_arg.name].append(dp)

        return {
            port_name: [
                PipelineDataId(
                    self._session_id,
                    P2Pipeline.node(self._node),
                    PipelinePort(dp.in_arg.name + ":" + str(i)),
                )
                for i, dp in enumerate(dps)
            ]
            for port_name, dps in grouped_dps.items()
        }

    def _load_single(self, port: str, allow_missing: bool) -> tuple[Any, ...]:
        if port in self._port_mapper:
            loader = self._loaders_getter.get(self._port_mapper[port][0])
            return (loader.load(),)
        elif allow_missing:
            return ()
        else:
            raise RuntimeError(f"Data not found for required input param {port}.")

    def _load_sequence(self, port: str) -> tuple[Any, ...]:
        return tuple(self._loaders_getter.get(id).load() for id in self._port_mapper[port])

    def _load_dictionary(self, port: str) -> dict[str, Any]:
        data: tuple[dict[str, Any], ...] = self._load_sequence(port)
        if not all(isinstance(d, dict) for d in data):
            raise ValueError("Gathered inputs should be of dictionary type.")
        return {k: v for d in data for k, v in d.items()}

    def load_parameters(
        self,
        parameters: Mapping[str, InProcessorParam],
        in_method: InMethod,
        exclude: Sequence[str] = (),
    ) -> tuple[Sequence[Any], Mapping[str, Any]]:
        pos_only: list[Any] = []
        pos_vars: list[Any] = []
        kw_args: dict[str, Any] = {}
        kw_vars: dict[str, Any] = {}
        for k, param in parameters.items():
            if k in exclude:
                continue
            if param.in_method != in_method:
                continue
            elif param.kind == param.POSITIONAL_ONLY:
                pos_only.extend(self._load_single(param.name, allow_missing=param.optional))
            elif param.kind == param.VAR_POSITIONAL:
                pos_vars.extend(self._load_sequence(param.name))
            elif param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
                for v in self._load_single(param.name, allow_missing=param.optional):
                    kw_args[k] = v
            elif param.kind == param.VAR_KEYWORD:
                kw_vars.update(self._load_dictionary(param.name))

        return (pos_only + pos_vars, {**kw_args, **kw_vars})


class SessionExecutableProvider(IExecutable):
    _services_provider: IProvideServices
    _context_client: ContextClient
    _session_client_getter: IGetSessionClient
    _node: DagNode
    _dependencies: orderedset[DagDependency]
    _props: ProcessorProps

    def __init__(
        self,
        # session_provider: "IProvideExecutionContexts[PipelineSessionClient]",
        services_provider: IProvideServices,
        context_client: ContextClient,
        session_client_getter: IGetSessionClient,
        node: DagNode,
        dependencies: Sequence[DagDependency],
        props: ProcessorProps,
    ) -> None:
        self._services_provider = services_provider
        self._context_client = context_client
        self._session_client_getter = session_client_getter
        self._node = node
        self._dependencies = orderedset(dependencies)
        self._props = props

    def get_processor(self, data_client: ProcessorDataLoader) -> IProcess:
        params = {k: v for k, v in self._props.config.items()}
        params.update(
            {k: self._services_provider.get_service(v) for k, v in self._props.services.items()}
        )
        pos_args, kw_args = data_client.load_parameters(self._props.inputs, InMethod.init)
        return self._props.processor_type(*pos_args, **params, **kw_args)

    def execute(self) -> None:
        logger.debug(f"Node {self._node} execute start.")
        session_id = self._context_client.get_context(OnemlSessionContextIds.SESSION_ID)
        pipeline_session_client = self._session_client_getter.get(session_id)
        publishers_getter = pipeline_session_client.pipeline_publisher_getter()
        loaders_getter = pipeline_session_client.pipeline_loader_getter()
        pipeline_node = P2Pipeline.node(self._node)

        # TODO: we should be able to turn DataClient into a ProcessorDataLoader
        data_client = ProcessorDataLoader(
            self._node, session_id, loaders_getter, self._dependencies
        )
        processor = self.get_processor(data_client)
        pos_args, kw_args = data_client.load_parameters(self._props.inputs, InMethod.process)
        outputs = processor.process(*pos_args, **kw_args)
        if outputs:
            # outputs could be either a dict or a namedtuple
            if isinstance(outputs, tuple):
                outputs = outputs._asdict()
            for key, val in outputs.items():
                data_id = PipelineDataId(
                    session_id,
                    node=pipeline_node,
                    port=PipelinePort[Any](key),
                )
                publishers_getter.get(data_id).publish(val)
        logger.debug(f"Node {self._node} execute end.")


class PipelineSessionProvider:
    _services_provider: IProvideServices
    _context_client: ContextClient
    _session_client_getter: IGetSessionClient
    _builder_factory: PipelineBuilderFactory

    def __init__(
        self,
        services_provider: IProvideServices,
        context_client: ContextClient,
        session_client_getter: IGetSessionClient,
        builder_factory: PipelineBuilderFactory,
    ) -> None:
        self._services_provider = services_provider
        self._context_client = context_client
        self._session_client_getter = session_client_getter
        self._builder_factory = builder_factory

    def get_session(self, dag: DAG) -> PipelineSessionClient:
        builder = self._builder_factory.get_instance()

        for node in dag.nodes:
            builder.add_node(P2Pipeline.node(node))
            props = dag.nodes[node]

            sess_executable = SessionExecutableProvider(
                # session_provider=self._session_context,
                # TODO: we're only depending on services provider to pass it down to this class
                #       we should use a factory class and hide these details from this client
                services_provider=self._services_provider,
                context_client=self._context_client,
                session_client_getter=self._session_client_getter,
                node=node,
                dependencies=dag.dependencies[node],
                props=props,
            )
            builder.add_executable(P2Pipeline.node(node), sess_executable)
            # for output, id in props.io_managers.items():
            #     type_id = props.serializers.get(
            #         output, default_type_mapper[props.outputs[output].annotation]
            #     )
            #     builder.add_iomanager(P2Pipeline.node(node), PipelinePort(output), id, type_id)

        for node, dependencies in dag.dependencies.items():
            builder.add_data_dependencies(
                P2Pipeline.node(node), P2Pipeline.data_dependencies(dependencies)
            )

        session = builder.build_session()
        return session
