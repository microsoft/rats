from functools import lru_cache
from typing import Any

from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.dag import PipelineDataDependency, PipelineNode, PipelinePort
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._serialization import DataTypeId, DemoSerializer, SerializationClient
from oneml.pipelines.session import PipelineSessionClient

from ._executables import App1PipelineExecutables


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

        generate_samples_exe = self._pipeline_executables.generate_samples()
        count_samples_exe = self._pipeline_executables.count_samples()

        builder.add_executable(
            builder.node("generate-samples"),
            builder.remote_executable(generate_samples_exe),
            # generate_samples_exe,
        )
        builder.add_executable(
            builder.node("count-samples"),
            # builder.remote_executable(count_samples_exe),
            count_samples_exe,
        )

        return builder.build_session()
