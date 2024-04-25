# type: ignore
from typing import Any, TypedDict

from rats.pipelines.dag import PipelineNode, PipelinePort, T_PipelinePortDataType


class LoadFittedParameterOutput(TypedDict):
    data: Any


class LoadFittedParameter:
    _session_id: str
    _node: PipelineNode
    _port: PipelinePort[Any]

    def __init__(
        self,
        session_id: str,
        node: PipelineNode,
        port: PipelinePort[T_PipelinePortDataType],
    ) -> None:
        self._session_id = session_id
        self._node = node
        self._port = port

    def process(self) -> LoadFittedParameterOutput:
        iomanager = self._iomanager_registry.get_dataclient(self._iomanager_id)
        return dict(
            data=iomanager.get_data_from_given_session_id(self._session_id, self._node, self._port)
        )
