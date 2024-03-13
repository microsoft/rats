from abc import abstractmethod
from typing import Any, Generic, Protocol, TypeVar

from typing_extensions import NamedTuple

from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.pipelines.session import PipelineSession
from rats.services import ContextProvider

from ._data import T_DataType, Tcontra_DataType


class PipelineDataId(NamedTuple, Generic[T_DataType]):
    node: PipelineNode
    port: PipelinePort[T_DataType]


class IPublishNodePortData(Protocol[Tcontra_DataType]):
    @abstractmethod
    def publish_node_port(self, data: Tcontra_DataType) -> None: ...


class ILoadNodeData(Protocol):
    @abstractmethod
    def load_port(self, port: PipelinePort[T_DataType]) -> T_DataType: ...


class IPublishNodeData(Protocol):
    @abstractmethod
    def publish_port(self, port: PipelinePort[T_DataType], data: T_DataType) -> None: ...


class IManageNodeData(
    ILoadNodeData,
    IPublishNodeData,
    Protocol,
): ...


class ILoadPipelineData(Protocol):
    @abstractmethod
    def load(self, node: PipelineNode, port: PipelinePort[T_DataType]) -> T_DataType: ...


class IPublishPipelineData(Protocol):
    @abstractmethod
    def publish(
        self,
        node: PipelineNode,
        port: PipelinePort[T_DataType],
        data: T_DataType,
    ) -> None: ...


class IManagePipelineData(
    ILoadPipelineData,
    IPublishPipelineData,
    Protocol,
): ...


T2_DataType = TypeVar("T2_DataType")


class PipelineData(
    IManagePipelineData,
    IManageNodeData,
):
    _data: dict[PipelineSession, dict[PipelineDataId[Any], Any]]

    _namespace: ContextProvider[PipelineSession]
    _node_ctx: ContextProvider[PipelineNode]

    def __init__(
        self,
        namespace: ContextProvider[PipelineSession],
        node_ctx: ContextProvider[PipelineNode],
    ) -> None:
        self._data = {}
        self._namespace = namespace
        self._node_ctx = node_ctx

    def publish_port(self, port: PipelinePort[T2_DataType], data: T2_DataType) -> None:
        self.publish(self._node_ctx(), port, data)

    def publish(
        self,
        node: PipelineNode,
        port: PipelinePort[T2_DataType],
        data: T2_DataType,
    ) -> None:
        ns = self._namespace()
        if ns not in self._data:
            self._data[ns] = {}

        key = PipelineDataId(node, port)
        if key in self._data[ns]:
            raise DuplicatePipelineDataError(key)

        self._data[ns][key] = data

    def load_port(self, port: PipelinePort[T2_DataType]) -> T2_DataType:
        return self.load(self._node_ctx(), port)

    def load(self, node: PipelineNode, port: PipelinePort[T2_DataType]) -> T2_DataType:
        ns = self._namespace()
        key = PipelineDataId(node, port)

        if ns not in self._data:
            raise PipelineDataNotFoundError(key)

        if key not in self._data[ns]:
            raise PipelineDataNotFoundError(key)

        return self._data[ns][key]


class DuplicatePipelineDataError(RuntimeError, Generic[T_DataType]):
    key: PipelineDataId[T_DataType]

    def __init__(self, key: PipelineDataId[T_DataType]) -> None:
        self.key = key
        super().__init__(f"duplicate key found: {key}")


class PipelineDataNotFoundError(RuntimeError, Generic[T_DataType]):
    key: PipelineDataId[T_DataType]

    def __init__(self, key: PipelineDataId[T_DataType]) -> None:
        self.key = key
        super().__init__(f"data key not found: {key}")
