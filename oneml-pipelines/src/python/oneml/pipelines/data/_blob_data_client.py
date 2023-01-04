import logging
from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, BlobServiceClient

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
from oneml.pipelines.session import IManagePipelineData, PipelineSessionClient

from ._data_type_mapping import MappedPipelineDataClient
from ._serialization import SerializationClient

logger = logging.getLogger(__name__)


class BlobDataClient(IManagePipelineData):

    _serializer: SerializationClient
    _type_mapping: MappedPipelineDataClient
    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    def __init__(
        self,
        serializer: SerializationClient,
        type_mapping: MappedPipelineDataClient,
        session_context: IProvideExecutionContexts[PipelineSessionClient],
    ) -> None:
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

        blob_client = self._get_blob_client(node, port)
        blob_client.upload_blob(serialized)

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        type_id = self._type_mapping.get_data_id((node, port))
        blob_client = self._get_blob_client(node, port)
        return self._serializer.deserialize(type_id, str(blob_client.download_blob().readall()))

    @lru_cache()
    def _get_blob_client(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> BlobClient:
        client_service = self._get_blob_service_client()
        return client_service.get_blob_client("general", self._get_data_path(node, port))

    @lru_cache()
    def _get_blob_service_client(self) -> BlobServiceClient:
        storage_account = "ampdatasetsdev01"
        return BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net/",
            credential=self._get_credentials(),
        )

    @lru_cache()
    def _get_credentials(self) -> DefaultAzureCredential:
        return DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_interactive_browser_credential=True,
            exclude_powershell_credential=True,
            exclude_shared_token_cache_credential=True,
            exclude_visual_studio_code_credential=True,
        )

    def _get_data_path(self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]) -> str:
        # TODO: make this resilient to failures
        #       when running on a remote pod, we can use the pod name in the path
        #       we can have the driver record the pod name and determine this path
        #       downstream pods can be given the paths to the data they need
        session_id = self._session_context.get_context().session_id()
        return f"oneml-prototypes/{session_id}/{node.key.lstrip('/')}/{port.key}.json"
