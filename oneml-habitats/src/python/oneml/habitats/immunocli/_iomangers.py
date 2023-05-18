from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelineNode, PipelinePort, PipelinePortDataType
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._serialization import DataTypeId
from oneml.pipelines.session import IManagePipelineData, PipelineSessionClient


class LocalNumpyIOManager(IManagePipelineData):
    _type_mapping: MappedPipelineDataClient
    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    _data: Dict[Tuple[PipelineNode, PipelinePort[Any]], Any]

    def __init__(
        self,
        type_mapping: MappedPipelineDataClient,
        session_context: IProvideExecutionContexts[PipelineSessionClient],
    ) -> None:
        self._type_mapping = type_mapping
        self._session_context = session_context
        self._data = {}

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        if (node, port) in self._data:
            return self._data[(node, port)]

        session_id = self._session_context.get_context().session_id()
        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.npz"
        return np.load(file)

    def publish_data(
        self,
        node: PipelineNode,
        port: PipelinePort[Any],
        data: Any,
    ) -> None:
        self._data[(node, port)] = data
        session_id = self._session_context.get_context().session_id()
        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.npz"
        data_dir.mkdir(parents=True, exist_ok=True)
        np.save(file, data)

    def get_data_from_given_session_id(
        self, session_id: str, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.npz"
        return np.load(file)

    def register(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        type_id: DataTypeId[PipelinePortDataType],
    ) -> None:
        self._type_mapping.register(node, port, type_id)


class LocalPandasIOManager(IManagePipelineData):
    _type_mapping: MappedPipelineDataClient
    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    _data: Dict[Tuple[PipelineNode, PipelinePort[Any]], Any]

    def __init__(
        self,
        type_mapping: MappedPipelineDataClient,
        session_context: IProvideExecutionContexts[PipelineSessionClient],
    ) -> None:
        self._type_mapping = type_mapping
        self._session_context = session_context
        self._data = {}

    def get_data(
        self, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        if (node, port) in self._data:
            return self._data[(node, port)]

        session_id = self._session_context.get_context().session_id()
        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.npz"
        return pd.read_csv(file)  # type: ignore[return-value]

    def publish_data(
        self,
        node: PipelineNode,
        port: PipelinePort[Any],
        data: PipelinePortDataType,
    ) -> None:
        self._data[(node, port)] = data
        session_id = self._session_context.get_context().session_id()
        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.npz"
        data_dir.mkdir(parents=True, exist_ok=True)
        data.to_csv(file)  # type: ignore[attr-defined]

    def get_data_from_given_session_id(
        self, session_id: str, node: PipelineNode, port: PipelinePort[PipelinePortDataType]
    ) -> PipelinePortDataType:
        data_dir = Path(f"../.tmp/session-data/{session_id}/{node.key}")
        file = data_dir / f"{port.key}.npz"
        return pd.read_csv(file)  # type: ignore[return-value]

    def register(
        self,
        node: PipelineNode,
        port: PipelinePort[PipelinePortDataType],
        type_id: DataTypeId[PipelinePortDataType],
    ) -> None:
        self._type_mapping.register(node, port, type_id)
