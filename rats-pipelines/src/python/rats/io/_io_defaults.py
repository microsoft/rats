from typing import Any

from rats.pipelines.dag import IManagePipelineDags
from rats.pipelines.session import PipelineSession
from rats.services import ContextProvider, IExecutable

from ._io_manager import IManageLoaders, IManagePublishers, PipelineDataId
from ._services import RatsIoServices


class DefaultIoRw(IExecutable):
    _context: ContextProvider[PipelineSession]
    _dag_client: IManagePipelineDags
    _loaders: IManageLoaders[Any]
    _publishers: IManagePublishers[Any]

    def __init__(
        self,
        context: ContextProvider[PipelineSession],
        dag_client: IManagePipelineDags,
        loaders: IManageLoaders[Any],
        publishers: IManagePublishers[Any],
    ) -> None:
        self._context = context
        self._dag_client = dag_client
        self._loaders = loaders
        self._publishers = publishers

    def execute(self) -> None:
        # TODO: fix this so we don't depend on data dependencies existing
        # TODO: I don't understand why this class is needed
        for node in self._dag_client.get_nodes():
            for dp in self._dag_client.get_data_dependencies(node):
                input_data_id = PipelineDataId[Any](
                    pipeline=self._context(),
                    node=node,
                    port=dp.input_port,
                )
                output_data_id = PipelineDataId[Any](
                    pipeline=self._context(),
                    node=dp.node,
                    port=dp.output_port,
                )
                self._loaders.register(
                    input_data_id,
                    output_data_id,
                    RatsIoServices.INMEMORY_URI_FORMATTER,
                    RatsIoServices.INMEMORY_READER,
                )
                self._publishers.register(
                    output_data_id,
                    RatsIoServices.INMEMORY_URI_FORMATTER,
                    RatsIoServices.INMEMORY_WRITER,
                )
