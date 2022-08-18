# type: ignore
# flake8: noqa
"""A node in a processing DAG."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from .data_annotation import Data
from .node import Node, OutputPortName

if TYPE_CHECKING:
    from .run_context import RunContext


class Processor(Node):
    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        ...
