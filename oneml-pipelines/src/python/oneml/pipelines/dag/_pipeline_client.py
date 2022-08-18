from ._node_client import IManagePipelineNodes
from ._node_dependencies_client import IManagePipelineNodeDependencies


class PipelineClient:
    _node_client: IManagePipelineNodes
    _node_dependencies_client: IManagePipelineNodeDependencies

    def __init__(
            self,
            node_client: IManagePipelineNodes,
            node_dependencies_client: IManagePipelineNodeDependencies):
        self._node_client = node_client
        self._node_dependencies_client = node_dependencies_client

    def node_client(self) -> IManagePipelineNodes:
        return self._node_client

    def node_dependencies_client(self) -> IManagePipelineNodeDependencies:
        return self._node_dependencies_client
