# type: ignore
# flake8: noqa
"""A DAG of processors that is a processor itself."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

from .base_dag import BaseDAG, NodeNameT, SimpleNodeName
from .data_annotation import Data
from .processor import OutputPortName
from .processor_decorator import processor

if TYPE_CHECKING:
    from .run_context import RunContext


@processor
class DAG(BaseDAG[SimpleNodeName]):
    """A nestable, runnable DAG of Processors."""

    def _node_name_class(self) -> Type[NodeNameT]:
        return SimpleNodeName

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        unknown_inputs = set(inputs.keys()) - set(self.get_input_schema().keys())
        if len(unknown_inputs) > 0:
            raise TypeError(
                f"Unknown inputs {unknown_inputs}. "
                f"Expected inputs are {self.get_input_schema().keys()}."
            )
        return run_context.run_dag(self, **inputs)
