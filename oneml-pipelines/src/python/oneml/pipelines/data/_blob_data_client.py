import logging

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
from oneml.pipelines.session import IManagePipelineData, PipelineSessionClient

from ._data_type_mapping import MappedPipelineDataClient
from ._filesystem import IManageFiles
from ._serialization import SerializationClient

logger = logging.getLogger(__name__)


class BlobDataClient(IManagePipelineData):

    _fs_client: IManageFiles
    _serializer: SerializationClient
    _type_mapping: MappedPipelineDataClient
    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    def __init__(
        self,
        fs_client: IManageFiles,
        serializer: SerializationClient,
        type_mapping: MappedPipelineDataClient,
        session_context: IProvideExecutionContexts[PipelineSessionClient],
    ) -> None:
        self._fs_client = fs_client
        self._serializer = serializer
        self._type_mapping = type_mapping
        # TODO: decouple this from the context and make a path provider
        self._session_context = session_context

    def publish_data(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        data: PipelinePortDataType,
    ) -> None:
        # TODO: make sure we can't publish data twice
        logger.debug(f"publishing node data: {node.key}[{port.key}]")

        type_id = self._type_mapping.get_data_id((node, port))
        serialized = self._serializer.serialize(type_id, data)

        self._fs_client.write(self._get_data_path(node, port), bytes(serialized, "utf-8"))

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        type_id = self._type_mapping.get_data_id((node, port))
        return self._serializer.deserialize(
            type_id, self._fs_client.read(self._get_data_path(node, port)).decode("utf-8")
        )

    def _get_data_path(self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]) -> str:
        # TODO: make this resilient to failures
        #       when running on a remote pod, we can use the pod name in the path
        #       we can have the driver record the pod name and determine this path
        #       downstream pods can be given the paths to the data they need
        session_id = self._session_context.get_context().session_id()
        return f"/oneml-outputs/session.{session_id}/{node.key.lstrip('/')}/{port.key}.json"
