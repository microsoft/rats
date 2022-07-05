"""A DAG of processors that is a processor itself."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Type

from .base_dag import BaseDAG, NodeNameT, SimpleNodeName
from .data_annotation import Data
from .processor import OutputPortName
from .processor_decorator import processor

if TYPE_CHECKING:
    from .run_context import RunContext


@dataclass
@processor
class DAG(BaseDAG[SimpleNodeName]):
    """A nestable, runnable DAG of Processors."""

    def _node_name_class(self) -> Type[NodeNameT]:
        return SimpleNodeName

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        return run_context.run_dag(self, **inputs)
