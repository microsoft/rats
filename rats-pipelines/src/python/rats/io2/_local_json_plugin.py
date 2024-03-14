from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.pipelines.session import PipelineSession
from rats.services import ContextOpener, ContextProvider

from ._data import IWriteData
from ._io_plugins import RatsIoPlugin
from ._local_json_formattable import JsonFormattable, T_JsonFormattable
from ._pipeline_data import ILoadPipelineData


class LocalJsonIoSettings:
    _pipeline_ctx: ContextProvider[PipelineSession]

    _registered: dict[PipelineSession, dict[PipelineNode, set[PipelinePort[Any]]]]

    def __init__(self, pipeline_ctx: ContextProvider[PipelineSession]) -> None:
        self._pipeline_ctx = pipeline_ctx

        self._registered = defaultdict(lambda: defaultdict(set))

    def register_port(
        self,
        node: PipelineNode,
        port: PipelinePort[T_JsonFormattable],
    ) -> None:
        self._registered[self._pipeline_ctx()][node].add(port)

    def get_ports(self, node: PipelineNode) -> Iterable[PipelinePort[JsonFormattable]]:
        return tuple(self._registered[self._pipeline_ctx()].get(node, ()))


class LocalJsonIoPlugin(RatsIoPlugin):
    _source: ILoadPipelineData
    _writer: IWriteData[JsonFormattable]
    _node_ctx: ContextProvider[PipelineNode]
    _storage: LocalJsonIoSettings
    _port_opener: ContextOpener[PipelinePort[Any]]

    def __init__(
        self,
        source: ILoadPipelineData,
        writer: IWriteData[JsonFormattable],
        node_ctx: ContextProvider[PipelineNode],
        storage: LocalJsonIoSettings,
        port_opener: ContextOpener[PipelinePort[Any]],
    ) -> None:
        self._source = source
        self._writer = writer
        self._node_ctx = node_ctx
        self._storage = storage
        self._port_opener = port_opener

    def on_node_completion(self, node: PipelineNode) -> None:
        ports = self._storage.get_ports(node)

        for port in ports:
            with self._port_opener(port):
                self._writer.write(self._source.load(node, port))
