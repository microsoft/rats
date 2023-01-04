from typing import Any, Dict, Tuple

from oneml.pipelines.dag import PipelineNode, PipelinePort

from ._serialization import DataType, DataTypeId, DefaultDataType


class MappedPipelineDataClient:

    _mapping: Dict[Tuple[PipelineNode, PipelinePort[Any]], DataTypeId[Any]]

    def __init__(self) -> None:
        self._mapping = {}

    def register(
        self,
        data_id: Tuple[PipelineNode, PipelinePort[DataType]],
        type_id: DataTypeId[DataType],
    ) -> None:
        self._mapping[data_id] = type_id

    def get_data_id(
        self,
        data_id: Tuple[PipelineNode, PipelinePort[DataType]],
    ) -> DataTypeId[DataType]:
        return self._mapping.get(data_id, DefaultDataType)
