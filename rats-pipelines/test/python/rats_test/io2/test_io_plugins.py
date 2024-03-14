from typing import cast
from unittest.mock import Mock

from rats.io2._io_plugins import RatsIoOnNodeCompletion, RatsIoPlugin
from rats.pipelines.dag import PipelineNode


class TestRatsIoOnNodeCompletion:
    def test_plugin_execution(self) -> None:
        plugin_1 = Mock(RatsIoPlugin)
        plugin_2 = Mock(RatsIoPlugin)

        client = RatsIoOnNodeCompletion(
            node_ctx=lambda: PipelineNode("fake"),
            plugins=[
                cast(RatsIoPlugin, plugin_1),
                cast(RatsIoPlugin, plugin_2),
            ],
        )
        client.execute()

        plugin_1.on_node_completion.assert_called_once_with(PipelineNode("fake"))
        plugin_2.on_node_completion.assert_called_once_with(PipelineNode("fake"))
