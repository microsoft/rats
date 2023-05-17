import logging
from abc import abstractmethod
from typing import Protocol, runtime_checkable

from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
from oneml.pipelines.data._serialization import DataTypeId

logger = logging.getLogger(__name__)


class IRegisterDataTypeId(Protocol):
    @abstractmethod
    def register(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        type_id: DataTypeId[PipelinePortDataType],
    ) -> None:
        """ """


@runtime_checkable
class ILoadPipelineData(IRegisterDataTypeId, Protocol):
    @abstractmethod
    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        """ """


@runtime_checkable
class IPublishPipelineData(IRegisterDataTypeId, Protocol):
    @abstractmethod
    def publish_data(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        data: PipelinePortDataType,
    ) -> None:
        """ """


@runtime_checkable
class IManagePipelineData(IPublishPipelineData, ILoadPipelineData, Protocol):
    """ """


@runtime_checkable
class ILoadPipelineNodeData(Protocol):
    @abstractmethod
    def get_data(self, port: PipelinePort[PipelinePortDataType]) -> PipelinePortDataType:
        """ """


@runtime_checkable
class IPublishPipelineNodeData(Protocol):
    @abstractmethod
    def publish_data(
        self, port: PipelinePort[PipelinePortDataType], data: PipelinePortDataType
    ) -> None:
        """ """


@runtime_checkable
class IManagePipelineNodeData(IPublishPipelineNodeData, ILoadPipelineNodeData, Protocol):
    """ """
