import json
import logging
from pathlib import Path

from rats.io2 import LocalIoSettings
from rats.io2._local_json_formattable import JsonFormattable
from rats.io2._local_json_writer import LocalJsonWriter
from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.pipelines.session import PipelineSession

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestLocalJsonWriter:
    def test_basics(self, tmp_path: Path) -> None:
        io_settings = LocalIoSettings(
            default_path=lambda: tmp_path,
            pipeline_ctx=lambda: PipelineSession("fake"),
        )
        client = LocalJsonWriter(
            io_settings=io_settings,
            node_ctx=lambda: PipelineNode("a"),
            port_ctx=lambda: PipelinePort[JsonFormattable]("out"),
        )

        client.write({"foo": "bar"})
        """
        Still a leaky abstraction but not as bad as before.
        The suffix is a private detail of the LocalJsonWriter.
        """
        filepath = io_settings.get_pipeline_port_file(
            node=PipelineNode("a"),
            port=PipelinePort[JsonFormattable]("out"),
            suffix=".json",
        )

        assert filepath.is_file()
        data = json.loads(filepath.read_text())
        assert data == {"foo": "bar"}
