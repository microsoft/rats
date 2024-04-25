from __future__ import annotations

import logging
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Protocol

from rats.io import IGetLoaders, IGetPublishers, IManageLoaders, IManagePublishers, PipelineDataId
from rats.pipelines.building import PipelineBuilderClient
from rats.pipelines.dag import PipelineDataDependency, PipelineNode, PipelinePort
from rats.pipelines.session import RatsSessionContexts
from rats.processors._legacy_subpackages.utils import SupportsAsDict, orderedset
from rats.services import IExecutable, IGetContexts, IProvideServices

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
            raise ValueError("Trying to convert a hanging dependency.")

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
    _context_client: IGetContexts
    _loaders_getter: IGetLoaders[Any]
    _port_mapper: dict[str, list[PipelineDataId[Any]]]

    def __init__(
        self,
        node: DagNode,
        context_client: IGetContexts,
        loaders_getter: IGetLoaders[Any],
        dependencies: Sequence[DagDependency],
    ) -> None:
        self._node = node
        self._context_client = context_client
        self._loaders_getter = loaders_getter
        self._port_mapper = self._map_ports(dependencies)

    def _map_ports(
        self, dependencies: Sequence[DagDependency]
    ) -> dict[str, list[PipelineDataId[Any]]]:
        grouped_dps: defaultdict[str, list[DagDependency]] = defaultdict(list)
        for dp in dependencies:
            grouped_dps[dp.in_arg.name].append(dp)

        pipeline_context = self._context_client.get_context(RatsSessionContexts.PIPELINE)

        return {
            port_name: [
                PipelineDataId(
                    pipeline_context,
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
    _context_client: IGetContexts
    _publishers_getter: IGetPublishers[Any]
    _loaders_getter: IGetLoaders[Any]
    _node: DagNode
    _dependencies: orderedset[DagDependency]
    _props: ProcessorProps

    def __init__(
        self,
        publishers_getter: IGetPublishers[Any],
        loaders_getter: IGetLoaders[Any],
        services_provider: IProvideServices,
        context_client: IGetContexts,
        node: DagNode,
        dependencies: Sequence[DagDependency],
        props: ProcessorProps,
    ) -> None:
        self._services_provider = services_provider
        self._context_client = context_client
        self._publishers_getter = publishers_getter
        self._loaders_getter = loaders_getter
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
        pipeline_context = self._context_client.get_context(RatsSessionContexts.PIPELINE)
        pipeline_node = P2Pipeline.node(self._node)

        # TODO: we should be able to turn DataClient into a ProcessorDataLoader
        # TODO: this is a service and should come from a di container
        data_client = ProcessorDataLoader(
            node=self._node,
            context_client=self._context_client,
            loaders_getter=self._loaders_getter,
            dependencies=self._dependencies,
        )
        processor = self.get_processor(data_client)
        pos_args, kw_args = data_client.load_parameters(self._props.inputs, InMethod.process)
        outputs = processor.process(*pos_args, **kw_args)
        if outputs:
            # outputs could be either a dict or a namedtuple
            if isinstance(outputs, SupportsAsDict):
                outputs = outputs._asdict()
            for key, val in outputs.items():
                data_id = PipelineDataId(
                    pipeline_context,
                    node=pipeline_node,
                    port=PipelinePort[Any](key),
                )
                # TODO: fix law of demeter
                self._publishers_getter.get(data_id).publish(val)
        logger.debug(f"Node {self._node} execute end.")


class INodeExecutableFactory(Protocol):
    @abstractmethod
    def __call__(
        self,
        node: DagNode,
        dependencies: Sequence[DagDependency],
        props: ProcessorProps,
    ) -> IExecutable: ...


class NodeExecutableFactory(INodeExecutableFactory):
    _services_provider: IProvideServices
    _context_client: IGetContexts
    _publishers_getter: IGetPublishers[Any] | IManagePublishers[Any]
    _loaders_getter: IGetLoaders[Any] | IManageLoaders[Any]

    def __init__(
        self,
        services_provider: IProvideServices,
        context_client: IGetContexts,
        publishers_getter: IGetPublishers[Any] | IManagePublishers[Any],
        loaders_getter: IGetLoaders[Any] | IManageLoaders[Any],
    ) -> None:
        self._services_provider = services_provider
        self._context_client = context_client
        self._publishers_getter = publishers_getter
        self._loaders_getter = loaders_getter

    def __call__(
        self,
        node: DagNode,
        dependencies: Sequence[DagDependency],
        props: ProcessorProps,
    ) -> IExecutable:
        return SessionExecutableProvider(
            services_provider=self._services_provider,
            context_client=self._context_client,
            publishers_getter=self._publishers_getter,
            loaders_getter=self._loaders_getter,
            # Factory should take the below args
            node=node,
            dependencies=dependencies,
            props=props,
        )


class DagSubmitter:
    _builder: PipelineBuilderClient
    _node_executable_factory: INodeExecutableFactory

    def __init__(
        self,
        builder: PipelineBuilderClient,
        node_executable_factory: INodeExecutableFactory,
    ) -> None:
        self._builder = builder
        self._node_executable_factory = node_executable_factory

    def submit_dag(self, dag: DAG) -> None:
        for node in dag.nodes:
            self._builder.add_node(P2Pipeline.node(node))

            sess_executable = self._node_executable_factory(
                node=node,
                dependencies=dag.dependencies[node],
                props=dag.nodes[node],
            )
            self._builder.set_executable(P2Pipeline.node(node), sess_executable)

        for node, dependencies in dag.dependencies.items():
            self._builder.add_data_dependencies(
                P2Pipeline.node(node), P2Pipeline.data_dependencies(dependencies)
            )
