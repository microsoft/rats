import pytest

from oneml.pipelines.settings import (
    DuplicatePipelineSettingError,
    PipelineSettingNotFoundError,
    PipelineSettingsClient,
    SettingName,
)


class TestPipelineSettingsClient:
    _client: PipelineSettingsClient

    def setup_method(self) -> None:
        self._client = PipelineSettingsClient()

    def test_basics(self) -> None:
        self._client.set(SettingName[str]("foo1"), "bar")
        assert self._client.get(SettingName[str]("foo1")) == "bar"

        with pytest.raises(DuplicatePipelineSettingError):
            self._client.set(SettingName[str]("foo1"), "baz")

        with pytest.raises(PipelineSettingNotFoundError):
            self._client.get(SettingName[str]("foo2"))
