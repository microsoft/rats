import pytest

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.settings import (
    DuplicateNodeSettingError,
    NodeSettingNotFoundError,
    NodeSettingsClient,
    SettingName,
)


class TestNodeSettingsClient:
    _client: NodeSettingsClient

    def setup_method(self) -> None:
        self._client = NodeSettingsClient()

    def test_basics(self) -> None:
        self._client.set(
            PipelineNode("node1"),
            SettingName("foo1"),
            "bar",
        )
        assert (
            self._client.get(
                PipelineNode("node1"),
                SettingName("foo1"),
            )
            == "bar"
        )

        with pytest.raises(DuplicateNodeSettingError):
            self._client.set(
                PipelineNode("node1"),
                SettingName("foo1"),
                "baz",
            )

        with pytest.raises(NodeSettingNotFoundError):
            self._client.get(
                PipelineNode("node1"),
                SettingName("foo2"),
            )

        with pytest.raises(NodeSettingNotFoundError):
            self._client.get(
                PipelineNode("node2"),
                SettingName("foo1"),
            )
