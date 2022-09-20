import logging
from typing import Any, Generic, Iterable, Mapping, Tuple, TypeVar

from oneml.pipelines.building import IPipelineSessionExecutable, PipelineBuilderFactory
from oneml.pipelines.dag import PipelineDataDependency, PipelineNode
from oneml.pipelines.session import PipelinePort, PipelineSessionClient

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
    ) -> Tuple[PipelineDataDependency[TI], ...]:
        if any(dp.node is None for dp in dependencies):
            raise ValueError("Trying to convert a hanging depencency.")
        return tuple(cls.data_dp(dp.node, dp.in_arg, dp.out_arg) for dp in dependencies if dp.node)


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
        publish_client = session_client.node_data_client_factory().get_instance(pipeline_node)
        self._provider.execute(input_client, publish_client)
        logger.debug(f"Node {self._node} execute end.")


class PipelineSessionProvider:
    @classmethod
    def get_session(cls, pipeline: Pipeline) -> PipelineSessionClient:
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
