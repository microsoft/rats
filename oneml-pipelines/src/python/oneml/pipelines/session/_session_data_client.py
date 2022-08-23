import logging
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Generic, Protocol, Tuple, TypeVar

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.dag._data_dependencies_client import PipelineDataDependenciesClient

logger = logging.getLogger(__name__)
# TODO: Move DataType and PipelineDataNode into DAG package
DataType = TypeVar("DataType")
# TODO: javier wants these to be called `save()` and `load()`


@dataclass(frozen=True)
class PipelineDataNode(Generic[DataType]):
    key: str


class ILoadPipelineData(Protocol):
    @abstractmethod
    def get_data(
            self, pipeline_node: PipelineNode, data_node: PipelineDataNode[DataType]) -> DataType:
        pass


class IPublishPipelineData(Protocol):
    @abstractmethod
    def publish_data(
            self,
            pipeline_node: PipelineNode,
            data_node: PipelineDataNode[DataType],
            data: DataType) -> None:
        pass


class IManagePipelineData(IPublishPipelineData, ILoadPipelineData, Protocol):
    pass


class ILoadPipelineNodeData(Protocol):
    @abstractmethod
    def get_data(self, data_node: PipelineDataNode[DataType]) -> DataType:
        pass


class IPublishPipelineNodeData(Protocol):
    @abstractmethod
    def publish_data(self, data_node: PipelineDataNode[DataType], data: DataType) -> None:
        pass


class IManagePipelineNodeData(IPublishPipelineNodeData, ILoadPipelineNodeData, Protocol):
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


class PipelineNodeDataClient(IManagePipelineNodeData):

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


# can we give Javier a single client for input/output?
class PipelineNodeInputDataClient(ILoadPipelineNodeData):

    _data_client: ILoadPipelineData
    _data_mapping: Dict[PipelineDataNode, PipelineNode]

    def __init__(
            self,
            data_client: ILoadPipelineData,
            data_mapping: Dict[PipelineDataNode, PipelineNode]) -> None:
        self._data_client = data_client
        self._data_mapping = data_mapping

    def get_data(self, data_node: PipelineDataNode[DataType]) -> DataType:
        return self._data_client.get_data(self._data_mapping[data_node], data_node)


class PipelineNodeDataClientFactory:

    _pipeline_data_client: IManagePipelineData

    def __init__(self, pipeline_data_client: IManagePipelineData) -> None:
        self._pipeline_data_client = pipeline_data_client

    @lru_cache()
    def get_instance(self, pipeline_node: PipelineNode) -> PipelineNodeDataClient:
        return PipelineNodeDataClient(self._pipeline_data_client, pipeline_node)


class PipelineNodeInputDataClientFactory:
    _data_dependencies_client: PipelineDataDependenciesClient
    _data_client: IManagePipelineData

    def __init__(
            self,
            data_dependencies_client: PipelineDataDependenciesClient,
            data_client: IManagePipelineData) -> None:
        self._data_dependencies_client = data_dependencies_client
        self._data_client = data_client

    def get_instance(self, node: PipelineNode) -> ILoadPipelineNodeData:
        dependencies = self._data_dependencies_client.get_node_dependencies(pipeline_node=node)
        data_mapping = {}
        for dep in dependencies:
            data_mapping[dep.data_node] = dep.pipeline_node

        return PipelineNodeInputDataClient(
            data_client=self._data_client, data_mapping=data_mapping)
