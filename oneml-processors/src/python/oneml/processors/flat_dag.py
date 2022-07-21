"""A runnable flattened DAG of processors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from .base_dag import BaseDAG, NodeName


@dataclass
class FlatDAG(BaseDAG[NodeName]):
    """A flat DAG of processors.  Not to be used by clients external to processors package."""

    def __post_init__(self) -> None:
        for node_name, node in self.nodes.items():
            if isinstance(node, BaseDAG):
                raise Exception(
                    f"FlatDAG cannot hold nodes that are DAGs.  Node <{node_name}> is a DAG."
                )
        super().__post_init__()

    def _node_name_class(self) -> Type[NodeName]:
        return NodeName
