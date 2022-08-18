from typing import List

from ._session_client import PipelineSessionClient
from ._session_plugins import IPipelineSessionPlugin


class PipelineSessionPluginClient:

    _plugins: List[IPipelineSessionPlugin]

    def __init__(self) -> None:
        self._plugins = []

    def register_plugin(self, plugin: IPipelineSessionPlugin) -> None:
        self._plugins.append(plugin)

    def activate_all(self, session_client: PipelineSessionClient) -> None:
        for plugin in self._plugins:
            plugin.on_session_init(session_client)
