from functools import lru_cache
from typing import Any

from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.building._executable_pickling import PickleableExecutable
from oneml.pipelines.dag import PipelineDataDependency, PipelineNode, PipelinePort
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._serialization import DataTypeId, DemoSerializer, SerializationClient
from oneml.pipelines.session import PipelineSessionClient
from oneml.pipelines.session._components import ComponentId

from ._di_provider import DiProvider
from ._executables import App1PipelineExecutables


class DeferredExecutable(PickleableExecutable):

    _name: str

    def __init__(self, name: str) -> None:
        self._name = name

    def execute(self, session: PipelineSessionClient) -> None:
        di = session.get_component(ComponentId[DiProvider](key="oneml.lorenzo.app1._di_container"))
        executables = di.pipeline_executables()
        executables.__getattribute__(self._name)().execute()


class App1Pipeline:

    _pipeline_builder_factory: PipelineBuilderFactory
    _pipeline_executables: App1PipelineExecutables
    _type_mapping_client: MappedPipelineDataClient
    _serialization_client: SerializationClient
    _demo_serializer: DemoSerializer[Any]

    def __init__(
        self,
        pipeline_builder_factory: PipelineBuilderFactory,
        pipeline_executables: App1PipelineExecutables,
        type_mapping_client: MappedPipelineDataClient,
        serialization_client: SerializationClient,
        demo_serializer: DemoSerializer[Any],
    ) -> None:
        self._pipeline_builder_factory = pipeline_builder_factory
        self._pipeline_executables = pipeline_executables
        self._type_mapping_client = type_mapping_client
        self._serialization_client = serialization_client
        self._demo_serializer = demo_serializer

    def execute(self) -> None:
        self._session().run()

    def execute_node(self, node: PipelineNode) -> None:
        self._session().run_node(node)

    @lru_cache()
    def _session(self) -> PipelineSessionClient:
        builder = self._pipeline_builder_factory.get_instance()

        builder.add_nodes(
            [
                builder.node("generate-samples"),
                builder.node("count-samples"),
            ]
        )
        builder.add_data_dependency(
            builder.node("count-samples"),
            PipelineDataDependency(
                node=builder.node("generate-samples"),
                output_port=PipelinePort[int]("__main__"),
                input_port=PipelinePort("__main__"),
            ),
        )
        # I think we can use more of a plugin system here
        # builder.add_executable(provider)
        # provider will be asked to execute nodes
        # provider.execute(node)?

        """
        - we want to be able to map pipeline ports to serialization types easily
        - the user should be able to specify the type when creating the port
        - maybe a decorator on the output port?
        """
        type_id = DataTypeId[int]("ints")
        data_id = (builder.node("count-samples"), PipelinePort[int]("__main__"))
        self._type_mapping_client.register(data_id, type_id)

        self._serialization_client.register(type_id, self._demo_serializer)

        builder.add_remote_executable(
            builder.node("generate-samples"),
            DeferredExecutable("generate_samples"),
        )
        builder.add_remote_executable(
            builder.node("count-samples"),
            DeferredExecutable("count_samples"),
        )

        return builder.build_session()
