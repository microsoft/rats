from pathlib import Path

import pytest

from rats.io2 import LocalIoSettings
from rats.pipelines.session import PipelineSession


class TestLocalIoSettings:
    def test_basics(self, tmp_path: Path) -> None:
        client = LocalIoSettings(
            default_path=lambda: tmp_path / "default",
            pipeline_ctx=lambda: PipelineSession("fake"),
        )

        assert client.get_data_path() == tmp_path / "default"

        client.set_data_path(tmp_path)
        assert client.get_data_path() == tmp_path

        with pytest.raises(RuntimeError):
            # can only set data path once
            client.set_data_path(tmp_path)
