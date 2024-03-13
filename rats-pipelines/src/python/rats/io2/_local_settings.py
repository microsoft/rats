from pathlib import Path
from typing import Any

from rats.pipelines.dag import PipelineNode, PipelinePort
from rats.pipelines.session import PipelineSession
from rats.services import ContextProvider, ServiceProvider


class LocalIoSettings:
    _default_path: ServiceProvider[Path]
    _pipeline_ctx: ContextProvider[PipelineSession]

    _config: dict[PipelineSession, Path]

    def __init__(
        self,
        default_path: ServiceProvider[Path],
        pipeline_ctx: ContextProvider[PipelineSession],
    ) -> None:
        self._default_path = default_path
        self._pipeline_ctx = pipeline_ctx

        self._config = {}

    def set_data_path(self, root_path: Path) -> None:
        # TODO: this should only be called before any node is run
        ctx = self._pipeline_ctx()

        if ctx in self._config:
            # We expect this config to be set at most once per session
            raise RuntimeError("data path can only be set once")

        self._config[ctx] = root_path

    def get_data_path(self) -> Path:
        ctx = self._pipeline_ctx()

        return self._config.get(ctx, self._default_path())

    def get_pipeline_port_file(
        self,
        node: PipelineNode,
        port: PipelinePort[Any],
        suffix: str = "",
    ) -> Path:
        return self.get_data_path() / node.key.strip("/") / f"{port.key}{suffix}"
