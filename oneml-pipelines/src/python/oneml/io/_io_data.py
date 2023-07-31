from abc import abstractmethod
from typing import Generic, Protocol

from typing_extensions import NamedTuple

from oneml.pipelines.dag import PipelineNode, PipelinePort
from oneml.pipelines.session import PipelineContext
from oneml.services import ServiceId

from ._rw_data import IReadData, IWriteData, RWDataUri, T_DataType, Tco_DataType, Tcontra_DataType


class PipelineDataId(NamedTuple, Generic[Tco_DataType]):
    # TODO: I think I can fix this confusing name soon
    pipeline: PipelineContext
    node: PipelineNode
    port: PipelinePort[Tco_DataType]

    def __str__(self) -> str:
        return f"{self.pipeline.id}/{self.node.key}/{self.port.key}"


# TODO: Why is this generic? We're not using the type parameter, so we can instead accept
# PipelineDataId[Any].
class IFormatUri(Protocol[T_DataType]):
    def __call__(self, data_id: PipelineDataId[T_DataType]) -> RWDataUri:
        ...


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
    def get(self, data_id: PipelineDataId[T_DataType]) -> ILoadPipelineData[T_DataType]:
        ...


class IGetPublishers(Protocol[T_DataType]):
    @abstractmethod
    def get(self, data_id: PipelineDataId[T_DataType]) -> IPublishPipelineData[T_DataType]:
        ...


class IRegisterLoaders(Protocol[T_DataType]):
    @abstractmethod
    def register(
        self,
        input_data_id: PipelineDataId[T_DataType],
        output_data_id: PipelineDataId[T_DataType],
        uri_formatter_id: ServiceId[IFormatUri[T_DataType]],
        reader_id: ServiceId[IReadData[T_DataType]],
    ) -> None:
        ...


class IRegisterPublishers(Protocol[T_DataType]):
    @abstractmethod
    def register(
        self,
        data_id: PipelineDataId[T_DataType],
        uri_formatter_id: ServiceId[IFormatUri[T_DataType]],
        writer_id: ServiceId[IWriteData[T_DataType]],
    ) -> None:
        ...


class IManagePublishers(
    IGetPublishers[T_DataType], IRegisterPublishers[T_DataType], Protocol[T_DataType]
):
    pass


class IManageLoaders(IGetLoaders[T_DataType], IRegisterLoaders[T_DataType], Protocol[T_DataType]):
    pass
