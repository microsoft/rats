from abc import abstractmethod
from typing import Generic, Protocol

from typing_extensions import NamedTuple

from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.pipelines.session import PipelineSession
from rats.services import ServiceId

from ._rw_data import IReadData, IWriteData, RWDataUri, T_DataType, Tco_DataType, Tcontra_DataType


class PipelineDataId(NamedTuple, Generic[Tco_DataType]):
    pipeline: PipelineSession
    node: PipelineNode
    port: PipelinePort[Tco_DataType]

    def __str__(self) -> str:
        return f"{self.pipeline.id}/{self.node.key}/{self.port.key}"


class IFormatUri(Protocol[Tcontra_DataType]):
    def __call__(self, data_id: PipelineDataId[Tcontra_DataType]) -> RWDataUri: ...


class ILoadPipelineData(Protocol[Tco_DataType]):
    @abstractmethod
    def load(self) -> Tco_DataType:
        pass


class IPublishPipelineData(Protocol[Tcontra_DataType]):
    @abstractmethod
    def publish(self, payload: Tcontra_DataType) -> None:
        pass


class IGetLoaders(Protocol[T_DataType]):
    @abstractmethod
    def get(self, data_id: PipelineDataId[T_DataType]) -> ILoadPipelineData[T_DataType]: ...


class IGetPublishers(Protocol[Tcontra_DataType]):
    @abstractmethod
    def get(
        self, data_id: PipelineDataId[Tcontra_DataType]
    ) -> IPublishPipelineData[Tcontra_DataType]: ...


class IRegisterLoaders(Protocol[T_DataType]):
    @abstractmethod
    def register(
        self,
        input_data_id: PipelineDataId[T_DataType],
        output_data_id: PipelineDataId[T_DataType],
        uri_formatter_id: ServiceId[IFormatUri[T_DataType]],
        reader_id: ServiceId[IReadData[T_DataType]],
    ) -> None: ...


class IRegisterPublishers(Protocol[T_DataType]):
    @abstractmethod
    def register(
        self,
        data_id: PipelineDataId[T_DataType],
        uri_formatter_id: ServiceId[IFormatUri[T_DataType]],
        writer_id: ServiceId[IWriteData[T_DataType]],
    ) -> None: ...


class IManagePublishers(
    IGetPublishers[T_DataType], IRegisterPublishers[T_DataType], Protocol[T_DataType]
):
    pass


class IManageLoaders(IGetLoaders[T_DataType], IRegisterLoaders[T_DataType], Protocol[T_DataType]):
    pass
