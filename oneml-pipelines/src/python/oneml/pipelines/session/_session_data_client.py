import logging
from functools import lru_cache
from typing import Any, Dict, Sequence, Tuple

from oneml.pipelines.dag import (
    PipelineDataDependenciesClient,
    PipelineNode,
    PipelinePort,
    PipelinePortDataType,
)
from oneml.pipelines.data._serialization import DataTypeId

from ._io_managers import IOManagerClient
from ._io_protocols import ILoadPipelineNodeData, IManagePipelineData, IManagePipelineNodeData

logger = logging.getLogger(__name__)


class PipelineNodeDataClient(IManagePipelineNodeData):
    _iomanager_client: IOManagerClient
    _node: PipelineNode

    def __init__(self, iomanager_client: IOManagerClient, node: PipelineNode) -> None:
        self._iomanager_client = iomanager_client
        self._node = node

    def publish_data(
        self, port: PipelinePort[PipelinePortDataType], data: PipelinePortDataType
    ) -> None:
        data_client = self._iomanager_client.get_dataclient(self._node, port)
        data_client.publish_data(self._node, port, data)

    def get_data(self, port: PipelinePort[PipelinePortDataType]) -> PipelinePortDataType:
        data_client = self._iomanager_client.get_dataclient(self._node, port)
        return data_client.get_data(self._node, port)


class PipelineNodeInputDataClient(ILoadPipelineNodeData):
    _iomanager_client: IOManagerClient
    _data_mapping: Dict[PipelinePort[Any], Tuple[PipelineNode, PipelinePort[Any]]]

    def __init__(
        self,
        iomanager_client: IOManagerClient,
        data_mapping: Dict[PipelinePort[Any], Tuple[PipelineNode, PipelinePort[Any]]],
    ) -> None:
        self._iomanager_client = iomanager_client
        self._data_mapping = data_mapping

    def get_data(self, port: PipelinePort[PipelinePortDataType]) -> PipelinePortDataType:
        data_id = self._data_mapping[port]
        data_client = self._iomanager_client.get_dataclient(*data_id)
        return data_client.get_data(*data_id)

    def get_ports(self) -> Sequence[PipelinePort[Any]]:
        return tuple(self._data_mapping.keys())


class PipelineNodeDataClientFactory:
    _iomanager_client: IOManagerClient

    def __init__(self, iomanager_client: IOManagerClient) -> None:
        self._iomanager_client = iomanager_client

    @lru_cache()
    def get_instance(self, node: PipelineNode) -> PipelineNodeDataClient:
        return PipelineNodeDataClient(self._iomanager_client, node)


class PipelineNodeInputDataClientFactory:
    _data_dependencies_client: PipelineDataDependenciesClient
    _iomanager_client: IOManagerClient

    def __init__(
        self,
        data_dependencies_client: PipelineDataDependenciesClient,
        iomanager_client: IOManagerClient,
    ) -> None:
        self._data_dependencies_client = data_dependencies_client
        self._iomanager_client = iomanager_client

    def get_instance(self, node: PipelineNode) -> PipelineNodeInputDataClient:
        dependencies = self._data_dependencies_client.get_node_dependencies(node=node)
        data_mapping = {}
        for dep in dependencies:
            data_mapping[dep.input_port] = (dep.node, dep.output_port)

        return PipelineNodeInputDataClient(
            iomanager_client=self._iomanager_client, data_mapping=data_mapping
        )


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

    def register(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        type_id: DataTypeId[PipelinePortDataType],
    ) -> None:
        pass

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        if node in self._proxied_nodes:
            return self._proxy_client.get_data(node, port)

        return self._primary_client.get_data(node, port)
