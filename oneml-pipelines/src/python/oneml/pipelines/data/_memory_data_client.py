import logging
from typing import Any, Dict, Tuple

from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
from oneml.pipelines.data._serialization import DataTypeId
from oneml.pipelines.session import IManagePipelineData

logger = logging.getLogger(__name__)


class InMemoryDataClient(IManagePipelineData):
    _data: Dict[Tuple[PipelineNode, PipelinePort[Any]], Any]

    def __init__(self) -> None:
        self._data = {}

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

        self._data[key] = data

    def register(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        type_id: DataTypeId[PipelinePortDataType],
    ) -> None:
        pass

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        key = (node, port)
        if key not in self._data:
            raise RuntimeError(f"Data key not found: {key}")

        return self._data[key]

    def get_data_from_given_session_id(  # type: ignore
        self, session_id: str, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        pass
