from typing import Any, Mapping, TypedDict

from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
from oneml.pipelines.session import IOManagerId, IOManagerRegistry

LoadFittedParameterOutput = TypedDict("LoadFittedParameterOutput", {"data": Any})


class LoadFittedParameter:
    _session_id: str
    _node: PipelineNode
    _port: PipelinePort[Any]
    _iomanager_id: IOManagerId
    _iomanager_registry: IOManagerRegistry

    def __init__(
        self,
        session_id: str,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        iomanager_id: IOManagerId,
        iomanager_registry: IOManagerRegistry,
    ) -> None:
        self._session_id = session_id
        self._node = node
        self._port = port
        self._iomanager_id = iomanager_id
        self._iomanager_registry = iomanager_registry

    def process(self) -> LoadFittedParameterOutput:
        iomanager = self._iomanager_registry.get_dataclient(self._iomanager_id)
        return dict(
            data=iomanager.get_data_from_given_session_id(
                self._session_id, self._node, self._port
            )
        )
