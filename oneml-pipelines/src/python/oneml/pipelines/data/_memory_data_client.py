import logging
from typing import Any, Dict, Tuple

from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
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

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        return self._data[(node, port)]
