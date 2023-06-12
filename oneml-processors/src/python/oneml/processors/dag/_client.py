from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

from oneml.io._pipeline_data import IPipelineDataLoader, IPipelineDataPublisher, PipelineDataId
from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.dag import PipelineDataDependency, PipelineNode, PipelinePort
from oneml.pipelines.session import IExecutable, PipelineSessionClient
from oneml.processors.utils import orderedset
from oneml.services import IProvideServices

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
        for dp in dependencies:
            data_dps.append(cls.data_dp(dp.node, dp.in_arg.name, dp.out_arg.name))

        return tuple(data_dps)


class ProcessorDataLoader:
    _loader: IPipelineDataLoader
    _dependencies: dict[str, list[PipelineDataId[Any]]]

    def __init__(self, loader: IPipelineDataLoader, dependencies: Sequence[DagDependency]) -> None:
        self._loader = loader
        self._dependencies = self._group_dependencies(dependencies)

    def _group_dependencies(
        self, dependencies: Sequence[DagDependency]
    ) -> dict[str, list[PipelineDataId[Any]]]:
        grouped_dps: defaultdict[str, list[PipelineDataId[Any]]] = defaultdict(list)
        for dp in dependencies:
            grouped_dps[dp.in_arg.name].append(
                PipelineDataId[Any](P2Pipeline.node(dp.node), PipelinePort(dp.out_arg.name))
            )

        return dict(grouped_dps)

    def _load_single(self, port_key: str, allow_missing: bool) -> tuple[Any, ...]:
        if port_key in self._dependencies:
            return (self._loader.load(self._dependencies[port_key][0]),)
        elif allow_missing:
            return ()
        else:
            raise RuntimeError(f"Data not found for required input param {port_key}.")

        # PipelineNodeInputDataClient was used here to get the output from the correct node

    def _load_sequence(self, port_key: str) -> tuple[Any, ...]:
        return tuple(self._loader.load(id) for id in self._dependencies[port_key])

    def _load_dictionary(self, port_key: str) -> dict[str, Any]:
        data: tuple[dict[str, Any], ...] = self._load_sequence(port_key)
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
    _publisher: IPipelineDataPublisher
    _loader: IPipelineDataLoader
    _node: DagNode
    _dependencies: orderedset[DagDependency]
    _props: ProcessorProps

    def __init__(
        self,
        # session_provider: "IProvideExecutionContexts[PipelineSessionClient]",
        services_provider: IProvideServices,
        publisher: IPipelineDataPublisher,
        loader: IPipelineDataLoader,
        node: DagNode,
        dependencies: Sequence[DagDependency],
        props: ProcessorProps,
    ) -> None:
        self._services_provider = services_provider
        self._publisher = publisher
        self._loader = loader
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
        pipeline_node = P2Pipeline.node(self._node)
        # TODO: we should be able to turn DataClient into a ProcessorDataLoader
        data_client = ProcessorDataLoader(self._loader, self._dependencies)
        processor = self.get_processor(data_client)
        pos_args, kw_args = data_client.load_parameters(self._props.inputs, InMethod.process)
        outputs = processor.process(*pos_args, **kw_args)
        if outputs:
            for key, val in outputs.items():
                data_id = PipelineDataId[Any](
                    node=pipeline_node,
                    port=PipelinePort(key),
                )
                self._publisher.publish(data_id, val)
        logger.debug(f"Node {self._node} execute end.")


class PipelineSessionProvider:
    _services_provider: IProvideServices
    _builder_factory: PipelineBuilderFactory
    _pipeline_publisher: IPipelineDataPublisher
    _pipeline_loader: IPipelineDataLoader

    def __init__(
        self,
        services_provider: IProvideServices,
        builder_factory: PipelineBuilderFactory,
        pipeline_publisher: IPipelineDataPublisher,
        pipeline_loader: IPipelineDataLoader,
    ) -> None:
        self._services_provider = services_provider
        self._builder_factory = builder_factory
        self._pipeline_publisher = pipeline_publisher
        self._pipeline_loader = pipeline_loader

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
                publisher=self._pipeline_publisher,
                loader=self._pipeline_loader,
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
