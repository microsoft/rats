from dataclasses import dataclass
from typing import Any, Dict, Tuple

from oneml.pipelines.dag import PipelineNode, PipelinePort

from ..data._serialization import DataType, DataTypeId
from ._io_protocols import IManagePipelineData
from ._services import ServiceId


@dataclass(frozen=True)
class IOManagerId(ServiceId[IManagePipelineData]):
    pass


class IOManagerRegistry:
    _mapping: Dict[IOManagerId, IManagePipelineData]

    def __init__(self) -> None:
        self._mapping = {}

    def register(
        self,
        id: IOManagerId,
        iomanager: IManagePipelineData,
    ) -> None:
        self._mapping[id] = iomanager

    def get_dataclient(
        self,
        iomanager_id: IOManagerId,
    ) -> IManagePipelineData:
        return self._mapping[iomanager_id]


class IOManagerClient:
    _mapping: Dict[Tuple[PipelineNode, PipelinePort[Any]], IOManagerId]
    _iomanager_registry: IOManagerRegistry
    _default: IManagePipelineData

    def __init__(
        self, iomanager_registry: IOManagerRegistry, default: IManagePipelineData
    ) -> None:
        self._mapping = {}
        self._iomanager_registry = iomanager_registry
        self._default = default

    def register(
        self,
        node: PipelineNode,
        port: PipelinePort[DataType],
        iomanager_id: IOManagerId,
        type_id: DataTypeId[DataType],
    ) -> None:
        self._mapping[(node, port)] = iomanager_id
        iomanager = self._iomanager_registry.get_dataclient(iomanager_id)
        iomanager.register(node, port, type_id)

    def get_dataclient(
        self,
        node: PipelineNode,
        port: PipelinePort[DataType],
    ) -> IManagePipelineData:
        id = self._mapping.get((node, port))
        return self._iomanager_registry.get_dataclient(id) if id else self._default

    def iomanager_registry(self) -> IOManagerRegistry:
        return self._iomanager_registry
