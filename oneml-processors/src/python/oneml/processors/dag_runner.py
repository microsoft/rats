# type: ignore
# flake8: noqa
"""Interface for running FlatDAG."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, Sequence

from .base_dag import BaseDAG
from .dag import DAG
from .dag_flattener import DAGFlattener
from .data_annotation import Data
from .flat_dag import FlatDAG
from .processor import OutputPortName

if TYPE_CHECKING:
    from .run_context import RunContext


class DAGRunner:
    def __init__(self, dag_modifiers: Sequence[Callable[[BaseDAG], BaseDAG]]) -> None:
        self._dag_modifiers = tuple(dag_modifiers)

    def run(self, dag: DAG, run_context: RunContext, **inputs: Any) -> Dict[OutputPortName, Data]:
        for modifier in self._dag_modifiers:
            dag = modifier(dag)
        assert isinstance(dag, FlatDAG)
        outputs = self.run_flattened(dag, run_context, **inputs)
        return outputs

    @abstractmethod
    def run_flattened(
        self, flat_dag: FlatDAG, run_context: RunContext, **inputs: Any
    ) -> Dict[OutputPortName, Data]:
        ...
