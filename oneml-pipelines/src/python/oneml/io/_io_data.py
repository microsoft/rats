from abc import abstractmethod
from typing import Generic, Iterator, Protocol

from typing_extensions import NamedTuple

from ..pipelines.dag import PipelineNode, PipelinePort, PipelineSessionId
from ..services import ServiceId
from ._rw_data import DataType, DataType_co, DataType_contra, IReadData, IWriteData, RWDataUri


class PipelineDataId(NamedTuple, Generic[DataType_co]):
    session_id: PipelineSessionId
    node: PipelineNode
    port: PipelinePort[DataType_co]

    def __str__(self) -> str:
        return f"{self.session_id.key}/{self.node.key}/{self.port.key}"


# TODO: Why is this generic? We're not using the type parameter, so we can instead accept
# PipelineDataId[Any].
class IFormatUri(Protocol[DataType]):
    def __call__(self, data_id: PipelineDataId[DataType]) -> RWDataUri:
        ...


class ILoadPipelineData(Protocol[DataType_co]):
    @abstractmethod
    def load(self) -> DataType_co:
        pass


class IPublishPipelineData(Protocol[DataType_contra]):
    @abstractmethod
    def publish(self, payload: DataType_contra) -> None:
        pass


class IGetLoaders(Protocol[DataType]):
    @abstractmethod
    def get(self, data_id: PipelineDataId[DataType]) -> ILoadPipelineData[DataType]:
        ...


class IGetPublishers(Protocol[DataType]):
    @abstractmethod
    def get(self, data_id: PipelineDataId[DataType]) -> IPublishPipelineData[DataType]:
        ...


class IRegisterLoaders(Protocol[DataType]):
    @abstractmethod
    def register(
        self,
        input_data_id: PipelineDataId[DataType],
        output_data_id: PipelineDataId[DataType],
        uri_formatter_id: ServiceId[IFormatUri[DataType]],
        reader_id: ServiceId[IReadData[DataType]],
    ) -> None:
        ...


class IRegisterPublishers(Protocol[DataType]):
    @abstractmethod
    def register(
        self,
        data_id: PipelineDataId[DataType],
        uri_formatter_id: ServiceId[IFormatUri[DataType]],
        writer_id: ServiceId[IWriteData[DataType]],
    ) -> None:
        ...


class IManagePublishers(
    IGetPublishers[DataType], IRegisterPublishers[DataType], Protocol[DataType]
):
    pass


class IManageLoaders(IGetLoaders[DataType], IRegisterLoaders[DataType], Protocol[DataType]):
    pass
