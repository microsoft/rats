from typing import cast
from unittest.mock import Mock

from oneml.io2._io_plugins import OnemlIoOnNodeCompletion, OnemlIoPlugin
from oneml.pipelines.dag import PipelineNode


class TestOnemlIoOnNodeCompletion:
    def test_plugin_execution(self) -> None:
        plugin_1 = Mock(OnemlIoPlugin)
        plugin_2 = Mock(OnemlIoPlugin)

        client = OnemlIoOnNodeCompletion(
            node_ctx=lambda: PipelineNode("fake"),
            plugins=[
                cast(OnemlIoPlugin, plugin_1),
                cast(OnemlIoPlugin, plugin_2),
            ],
        )
        client.execute()

        plugin_1.on_node_completion.assert_called_once_with(PipelineNode("fake"))
        plugin_2.on_node_completion.assert_called_once_with(PipelineNode("fake"))
