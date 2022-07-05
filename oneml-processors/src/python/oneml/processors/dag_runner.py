"""Interface for running FlatDAG."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict

from .dag import DAG
from .dag_flattener import DAGFlattener
from .data_annotation import Data
from .flat_dag import FlatDAG
from .processor import OutputPortName

if TYPE_CHECKING:
    from .run_context import RunContext


class DAGRunner:
    def __init__(self, dag_flattener: DAGFlattener = DAGFlattener()) -> None:
        self.dag_flattener = dag_flattener

    def run(self, dag: DAG, run_context: RunContext, **inputs: Any) -> Dict[OutputPortName, Data]:
        flat_dag = self.dag_flattener.flatten(dag)
        outputs = self.run_flattened(flat_dag, run_context, **inputs)
        return outputs

    @abstractmethod
    def run_flattened(
        self, flat_dag: FlatDAG, run_context: RunContext, **inputs: Any
    ) -> Dict[OutputPortName, Data]:
        ...
