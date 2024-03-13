from rats.io2 import LocalJsonIoSettings
from rats.io2._local_json_formattable import JsonFormattable
from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.pipelines.session import PipelineSession


class TestLocalJsonIoSettings:
    def test_basics(self) -> None:
        client = LocalJsonIoSettings(
            pipeline_ctx=lambda: PipelineSession("fake"),
        )

        client.register_port(
            node=PipelineNode("a"),
            port=PipelinePort[JsonFormattable]("out"),
        )

        assert client.get_ports(PipelineNode("a")) == (PipelinePort[JsonFormattable]("out"),)

        assert client.get_ports(PipelineNode("b")) == ()
