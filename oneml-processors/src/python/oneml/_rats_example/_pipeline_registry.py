"""Seeing if we can make a plugin that makes pipelines available for others to use.
"""
from typing import Protocol


class PipelineRegistry(Protocol):
    def register(self) -> None:
        pass
