import logging
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Generic, Protocol, Tuple, TypeVar

from oneml.pipelines.dag import PipelineNode

logger = logging.getLogger(__name__)
DataType = TypeVar("DataType")


@dataclass(frozen=True)
class PipelineDataNode(Generic[DataType]):
    key: str


# TODO: data dependencies might belong in `dag`.
# @dataclass(frozen=True)
# class PipelineDataDependency(Generic[DataType]):
#     pipeline_node: PipelineNode
#     data_node: PipelineDataNode[DataType]


# class PipelineDataDependenciesClient:
#
#     _dependencies: Dict[PipelineNode, Set[PipelineDataDependency]]
#
#     def register_data_dependency(
#             self,
#             pipeline_node: PipelineNode,
#             dependency: PipelineDataDependency) -> None:
#         current = self._dependencies.get(pipeline_node, set())
#         if dependency in current:
#             raise RuntimeError(f"Duplicate dependency found: {pipeline_node} -> {dependency}")
#
#         current.add(dependency)
#         self._dependencies[pipeline_node] = current
#
#     def get_node_dependencies(
#             self, pipeline_node: PipelineNode) -> Tuple[PipelineDataDependency, ...]:
#         return tuple(self._dependencies.get(pipeline_node, set()))


class IManagePipelineData(Protocol):
    @abstractmethod
    def publish_data(
            self,
            pipeline_node: PipelineNode,
            data_node: PipelineDataNode[DataType],
            data: DataType) -> None:
        pass

    @abstractmethod
    def get_data(
            self, pipeline_node: PipelineNode, data_node: PipelineDataNode[DataType]) -> DataType:
        pass


class PipelineDataClient(IManagePipelineData):

    _data: Dict[Tuple[PipelineNode, PipelineDataNode[DataType]], DataType]  # type: ignore

    def __init__(self) -> None:
        self._data = {}

    def publish_data(
            self,
            pipeline_node: PipelineNode,
            data_node: PipelineDataNode[DataType],
            data: DataType) -> None:
        key = (pipeline_node, data_node)
        if key in self._data:
            raise RuntimeError(f"Duplicate data key found: {key}")

        logger.debug(f"publishing node data: {pipeline_node.key}[{data_node.key}]")
        self._data[key] = data

    def get_data(
            self, pipeline_node: PipelineNode, data_node: PipelineDataNode[DataType]) -> DataType:
        key = (pipeline_node, data_node)
        if key not in self._data:
            raise RuntimeError(f"Data key not found: {key}")

        return self._data[key]


class ReadProxyPipelineDataClient(IManagePipelineData):

    _primary_client: IManagePipelineData
    _proxy_client: IManagePipelineData
    _proxied_nodes: Tuple[PipelineNode, ...]

    def __init__(
            self,
            primary_client: IManagePipelineData,
            proxy_client: IManagePipelineData,
            proxied_nodes: Tuple[PipelineNode, ...]) -> None:
        self._primary_client = primary_client
        self._proxy_client = proxy_client
        self._proxied_nodes = proxied_nodes

    def publish_data(
            self,
            pipeline_node: PipelineNode,
            data_node: PipelineDataNode[DataType],
            data: DataType) -> None:
        if pipeline_node in self._proxied_nodes:
            raise RuntimeError(f"Cannot proxy writes to node: {pipeline_node}")

        self._primary_client.publish_data(pipeline_node, data_node, data)

    def get_data(
            self, pipeline_node: PipelineNode, data_node: PipelineDataNode[DataType]) -> DataType:
        if pipeline_node in self._proxied_nodes:
            return self._proxy_client.get_data(pipeline_node, data_node)

        return self._primary_client.get_data(pipeline_node, data_node)


class PipelineNodeDataClient:

    _pipeline_data_client: IManagePipelineData
    _pipeline_node: PipelineNode

    def __init__(
            self, pipeline_data_client: IManagePipelineData, pipeline_node: PipelineNode) -> None:
        self._pipeline_data_client = pipeline_data_client
        self._pipeline_node = pipeline_node

    def publish_data(
            self,
            data_node: PipelineDataNode[DataType],
            data: DataType) -> None:

        self._pipeline_data_client.publish_data(self._pipeline_node, data_node, data)

    def get_data(self, data_node: PipelineDataNode[DataType]) -> DataType:
        return self._pipeline_data_client.get_data(self._pipeline_node, data_node)


class PipelineNodeDataClientFactory:

    _pipeline_data_client: IManagePipelineData

    def __init__(self, pipeline_data_client: IManagePipelineData) -> None:
        self._pipeline_data_client = pipeline_data_client

    @lru_cache()
    def get_instance(self, pipeline_node: PipelineNode) -> PipelineNodeDataClient:
        return PipelineNodeDataClient(self._pipeline_data_client, pipeline_node)
