import logging
from abc import abstractmethod
from functools import lru_cache
from typing import Any, Dict, Protocol, Tuple

from oneml.pipelines.dag import (
    PipelineDataDependenciesClient,
    PipelineNode,
    PipelinePort,
    PipelinePortDataType,
)

logger = logging.getLogger(__name__)


class ILoadPipelineData(Protocol):
    @abstractmethod
    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        pass


class IPublishPipelineData(Protocol):
    @abstractmethod
    def publish_data(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        data: PipelinePortDataType,
    ) -> None:
        pass


class IManagePipelineData(IPublishPipelineData, ILoadPipelineData, Protocol):
    pass


class ILoadPipelineNodeData(Protocol):
    @abstractmethod
    def get_data(self, port: PipelinePort[PipelinePortDataType]) -> PipelinePortDataType:
        pass


class IPublishPipelineNodeData(Protocol):
    @abstractmethod
    def publish_data(
        self, port: PipelinePort[PipelinePortDataType], data: PipelinePortDataType
    ) -> None:
        pass


class IManagePipelineNodeData(IPublishPipelineNodeData, ILoadPipelineNodeData, Protocol):
    pass


class PipelineDataClient(IManagePipelineData):

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
        key = (node, port)
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
        proxied_nodes: Tuple[PipelineNode, ...],
    ) -> None:
        self._primary_client = primary_client
        self._proxy_client = proxy_client
        self._proxied_nodes = proxied_nodes

    def publish_data(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        data: PipelinePortDataType,
    ) -> None:
        if node in self._proxied_nodes:
            raise RuntimeError(f"Cannot proxy writes to node: {node}")

        self._primary_client.publish_data(node, port, data)

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        if node in self._proxied_nodes:
            return self._proxy_client.get_data(node, port)

        return self._primary_client.get_data(node, port)


class PipelineNodeDataClient(IManagePipelineNodeData):

    _pipeline_data_client: IManagePipelineData
    _node: PipelineNode

    def __init__(self, pipeline_data_client: IManagePipelineData, node: PipelineNode) -> None:
        self._pipeline_data_client = pipeline_data_client
        self._node = node

    def publish_data(
        self, port: PipelinePort[PipelinePortDataType], data: PipelinePortDataType
    ) -> None:
        self._pipeline_data_client.publish_data(self._node, port, data)

    def get_data(self, port: PipelinePort[PipelinePortDataType]) -> PipelinePortDataType:
        return self._pipeline_data_client.get_data(self._node, port)


class PipelineNodeInputDataClient(ILoadPipelineNodeData):

    _data_client: ILoadPipelineData
    _data_mapping: Dict[PipelinePort[Any], Tuple[PipelineNode, PipelinePort[Any]]]

    def __init__(
        self,
        data_client: ILoadPipelineData,
        data_mapping: Dict[PipelinePort[Any], Tuple[PipelineNode, PipelinePort[Any]]],
    ) -> None:
        self._data_client = data_client
        self._data_mapping = data_mapping

    def get_data(self, port: PipelinePort[PipelinePortDataType]) -> PipelinePortDataType:
        return self._data_client.get_data(
            self._data_mapping[port][0],
            self._data_mapping[port][1],
        )


class PipelineNodeDataClientFactory:

    _pipeline_data_client: IManagePipelineData

    def __init__(self, pipeline_data_client: IManagePipelineData) -> None:
        self._pipeline_data_client = pipeline_data_client

    @lru_cache()
    def get_instance(self, node: PipelineNode) -> PipelineNodeDataClient:
        return PipelineNodeDataClient(self._pipeline_data_client, node)


class PipelineNodeInputDataClientFactory:
    _data_dependencies_client: PipelineDataDependenciesClient
    _data_client: IManagePipelineData

    def __init__(
        self,
        data_dependencies_client: PipelineDataDependenciesClient,
        data_client: IManagePipelineData,
    ) -> None:
        self._data_dependencies_client = data_dependencies_client
        self._data_client = data_client

    def get_instance(self, node: PipelineNode) -> ILoadPipelineNodeData:
        dependencies = self._data_dependencies_client.get_node_dependencies(node=node)
        data_mapping = {}
        for dep in dependencies:
            data_mapping[dep.input_port] = (dep.node, dep.output_port)

        return PipelineNodeInputDataClient(
            data_client=self._data_client, data_mapping=data_mapping
        )
