import json

from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.services import ContextProvider

from ._data import IWriteData
from ._local_json_formattable import JsonFormattable
from ._local_settings import LocalIoSettings


class LocalJsonWriter(IWriteData[JsonFormattable]):
    _io_settings: LocalIoSettings
    _node_ctx: ContextProvider[PipelineNode]
    _port_ctx: ContextProvider[PipelinePort[JsonFormattable]]

    def __init__(
        self,
        io_settings: LocalIoSettings,
        node_ctx: ContextProvider[PipelineNode],
        port_ctx: ContextProvider[PipelinePort[JsonFormattable]],
    ) -> None:
        self._io_settings = io_settings
        self._node_ctx = node_ctx
        self._port_ctx = port_ctx

    def write(self, payload: JsonFormattable) -> None:
        filepath = self._io_settings.get_pipeline_port_file(
            node=self._node_ctx(),
            port=self._port_ctx(),
            suffix=".json",
        )

        directory = filepath.parent
        directory.mkdir(parents=True, exist_ok=True)

        data_json = f"{json.dumps(payload)}\n"
        filepath.write_text(data_json)
