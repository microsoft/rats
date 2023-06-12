from abc import abstractmethod
from typing import Any, Dict, Generic, Protocol, TypeVar

from typing_extensions import NamedTuple

from oneml.pipelines.dag import PipelineNode, PipelinePort

DataType = TypeVar("DataType")


class PipelineDataId(NamedTuple, Generic[DataType]):
    node: PipelineNode
    port: PipelinePort[DataType]


class IPipelineDataPublisher(Protocol):

    @abstractmethod
    def publish(self, data_id: PipelineDataId[DataType], payload: DataType) -> None:
        pass


class IPipelineDataLoader(Protocol):
    """
    Note from Elon, it makes more sense for this interface to take the node/port of the data
    consumer instead of the publisher because the publisher side can be a private detail.

    Something for us to clean up after we get processors working again!
    """

    @abstractmethod
    def load(self, data_id: PipelineDataId[DataType]) -> DataType:
        pass


class IPipelineDataManager(IPipelineDataPublisher, IPipelineDataLoader, Protocol):
    pass


class PipelineDataMapper(IPipelineDataManager):

    _data: Dict[PipelineDataId[Any], Any]

    def __init__(self) -> None:
        self._data = {}

    def publish(self, data_id: PipelineDataId[DataType], payload: DataType) -> None:
        self._data[data_id] = payload

    def load(self, data_id: PipelineDataId[DataType]) -> DataType:
        return self._data[data_id]
