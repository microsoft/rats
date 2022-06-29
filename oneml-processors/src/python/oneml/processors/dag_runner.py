"""Interface for running FlatDAG."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .dag import DAG
from .data_annotation import Data
from .processor import OutputPortName

if TYPE_CHECKING:
    from .run_context import RunContext


class DAGRunner:
    def run(self, dag: DAG, run_context: RunContext, **inputs: Any) -> Dict[OutputPortName, Data]:
        pass
