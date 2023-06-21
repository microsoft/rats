from typing import Any

from ...io import OnemlIoServices, PipelineDataId
from ...io._io_data import IGetLoaders, IGetPublishers
from ...io._io_manager import PipelineLoaderGetter, PipelinePublisherGetter
from ...services import IProvideServices
from ..dag import IManagePipelineNodes, PipelineDataDependenciesClient, PipelineSessionId


class SessionDataClient:
    _services: IProvideServices

    def __init__(self, services: IProvideServices) -> None:
        self._services = services

    def configure_loaders_and_publishers(
        self,
        session_id: PipelineSessionId,
        node_client: IManagePipelineNodes,
        data_dependencies_client: PipelineDataDependenciesClient,
    ) -> tuple[IGetLoaders[Any], IGetPublishers[Any]]:
        loaders = PipelineLoaderGetter[Any](self._services)
        publishers = PipelinePublisherGetter[Any](self._services)
        for node in node_client.get_nodes():
            for dp in data_dependencies_client.get_node_dependencies(node):
                input_data_id = PipelineDataId(session_id, node, dp.input_port)
                output_data_id = PipelineDataId(session_id, dp.node, dp.output_port)
                loaders.register(
                    input_data_id,
                    output_data_id,
                    OnemlIoServices.INMEMORY_URI_FORMATTER,
                    OnemlIoServices.INMEMORY_READER,
                )
                publishers.register(
                    output_data_id,
                    OnemlIoServices.INMEMORY_URI_FORMATTER,
                    OnemlIoServices.INMEMORY_WRITER,
                )
        return loaders, publishers
