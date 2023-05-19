import logging
from pathlib import Path
from typing import Any, Dict, Tuple

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._serialization import DataTypeId, SerializationClient
from oneml.pipelines.session import IManagePipelineData, IOManagerId, PipelineSessionClient

logger = logging.getLogger(__name__)


class LocalDataClient(IManagePipelineData):
    _serializer: SerializationClient
    _type_mapping: MappedPipelineDataClient
    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    _data: Dict[Tuple[PipelineNode, PipelinePort[Any]], Any]

    def __init__(
        self,
        serializer: SerializationClient,
        type_mapping: MappedPipelineDataClient,
        session_context: IProvideExecutionContexts[PipelineSessionClient],
    ) -> None:
        self._data = {}
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
        key = (node, port)
        if key in self._data:
            raise RuntimeError(f"Duplicate data key found: {key}")

        logger.debug(f"publishing node data: {node.key}[{port.key}]")

        type_id = self._type_mapping.get_data_id((node, port))
        serialized = self._serializer.serialize(type_id, data)

        session_id = self._session_context.get_context().session_id()

        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.json"
        data_dir.mkdir(parents=True, exist_ok=True)
        file.write_text(serialized)

        # TODO: move the in-memory data to a separate client
        self._data[key] = serialized

    def register(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        type_id: DataTypeId[PipelinePortDataType],
    ) -> None:
        self._type_mapping.register(node, port, type_id)

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        type_id = self._type_mapping.get_data_id((node, port))
        return self._serializer.deserialize(type_id, self._data[(node, port)])

    def get_data_from_given_session_id(
        self, session_id: str, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.json"
        serialized = file.read_text()
        type_id = self._type_mapping.get_data_id((node, port))
        return self._serializer.deserialize(type_id, serialized)


class IOManagerIds:
    LOCAL = IOManagerId("local")
