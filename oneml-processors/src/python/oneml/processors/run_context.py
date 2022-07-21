"""Run context is an object passed to process methods holding information about the environment in which they run and providing hooks to interact with it.

The outputs of the process method should not be effected by the run context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .assignable import Assignable
from .dag_flattener import DAGFlattener
from .identifiers import ObjectIdentifier
from .processor import OutputPortName

if TYPE_CHECKING:
    from .dag import DAG
    from .dag_runner import DAGRunner


class RunContext(Assignable):
    def __init__(
        self,
        dag_runner: DAGRunner,
        identifier: ObjectIdentifier = ObjectIdentifier(""),
    ):
        self._dag_runner = dag_runner
        self.identifier = identifier

    def run_dag(self, dag: DAG, **inputs: Any) -> Dict[OutputPortName, Any]:
        return self._dag_runner.run(dag, self, **inputs)

    def add_identifier_level(self, level: str) -> RunContext:
        identifier = self.identifier + ObjectIdentifier(level)
        return self.assign(identifier=identifier)
