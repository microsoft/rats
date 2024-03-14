import logging
from typing import Any

from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.pipelines.session import PipelineSession
from rats.services import ContextProvider

from ._io_data import IGetPublishers, IManagePublishers, PipelineDataId
from ._rw_data import T_DataType

logger = logging.getLogger(__name__)


class NodeOutputClient:
    _pipeline_context: ContextProvider[PipelineSession]
    _node_context: ContextProvider[PipelineNode]
    _publishers: IGetPublishers[Any] | IManagePublishers[Any]

    def __init__(
        self,
        pipeline_context: ContextProvider[PipelineSession],
        node_context: ContextProvider[PipelineNode],
        publishers: IGetPublishers[Any] | IManagePublishers[Any],
    ) -> None:
        self._pipeline_context = pipeline_context
        self._node_context = node_context
        self._publishers = publishers

    def publish(self, port: PipelinePort[T_DataType], payload: T_DataType) -> None:
        node = self._node_context()
        pipeline_context = self._pipeline_context()
        data_id = PipelineDataId[T_DataType](
            pipeline=pipeline_context,
            node=node,
            port=port,
        )

        logger.debug(f"publishing {node}[{port}]")
        pub = self._publishers.get(data_id=data_id)
        pub.publish(payload)
