from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from functools import cached_property
from typing import AbstractSet, Any, Iterable, Mapping, Optional, Protocol, Sequence, final

from ..utils._frozendict import frozendict
from ..utils._orderedset import oset
from ._processor import (
    Annotations,
    IGetParams,
    InMethod,
    InProcessorParam,
    IProcess,
    OutProcessorParam,
)

logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True)
class Namespace:
    key: str = ""

    def __bool__(self) -> bool:
        return bool(self.key)

    def __contains__(self, namespace: Namespace) -> bool:
        return namespace.key in self.key

    def __post_init__(self) -> None:
        if len(self.key) > 0:
            assert self.key[0] != "/" and self.key[-1] != "/", """No leading nor trailing "/"."""

    def __repr__(self) -> str:
        return "/" + self.key + ("/" if self.key else "")

    def __truediv__(self, namespace: Namespace) -> Namespace:
        return Namespace(self.key + ("/" if self.key and namespace.key else "") + namespace.key)


@dataclass(frozen=True)
class ComputeReqs:
    registry: str = ""
    image_tag: str = ""
    cpus: int = 4
    gpus: int = 0
    memory: str = "50Gi"
    pods: int = 1


@final
@dataclass(frozen=True)
class ProcessorProps:
    processor_type: type[IProcess]
    params_getter: IGetParams = frozendict[str, Any]()
    compute_reqs: ComputeReqs = ComputeReqs()
    return_annotation: InitVar[Mapping[str, OutProcessorParam] | None] = None

    inputs: frozendict[str, InProcessorParam] = field(init=False)
    outputs: frozendict[str, OutProcessorParam] = field(init=False)

    def __post_init__(self, return_annotation: Mapping[str, type] | None) -> None:
        inputs = {
            k: v
            for k, v in Annotations.get_processor_signature(self.processor_type).items()
            if k not in self.params_getter
        }
        for k in self.params_getter:
            try:
                self.params_getter[k]
            except Exception:  # add missing dependencies required by param_getter
                inputs[k] = InProcessorParam(
                    k, self.params_getter.__annotations__.get(k, Any), InMethod.init
                )

        if return_annotation:
            ra = {k: OutProcessorParam(k, t) for k, t in return_annotation.items()}
        else:
            ra = dict(Annotations.get_return_annotation(self.processor_type.process))

        object.__setattr__(self, "inputs", frozendict(inputs))
        object.__setattr__(self, "outputs", frozendict(ra))

    def __hash__(self) -> int:
        return hash((self.processor_type, self.params_getter))


@final
@dataclass(frozen=True)
class DagNode:
    name: str
    namespace: Namespace = Namespace()

    def __contains__(self, namespace: Namespace) -> bool:
        return namespace in self.namespace

    def __repr__(self) -> str:
        return repr(self.namespace) + self.name

    def __post_init__(self) -> None:
        if self.name == "":
            raise Exception("No empty names allowed.")

    def decorate(self, namespace: str | Namespace) -> DagNode:
        namespace = namespace if isinstance(namespace, Namespace) else Namespace(namespace)
        return DagNode(self.name, namespace / self.namespace)


@final
class DagDependency:
    _node: DagNode
    _in_arg: InProcessorParam
    _out_arg: Optional[OutProcessorParam]

    @property
    def node(self) -> DagNode:
        return self._node

    @property
    def in_arg(self) -> InProcessorParam:
        return self._in_arg

    @cached_property
    def out_arg(self) -> OutProcessorParam:
        return (
            self._out_arg
            if self._out_arg
            else OutProcessorParam(self._in_arg.name, self._in_arg.annotation)
        )

    def __init__(
        self,
        node: DagNode,
        in_arg: InProcessorParam,
        out_arg: Optional[OutProcessorParam] = None,
    ) -> None:
        self._node = node
        self._in_arg = in_arg
        self._out_arg = out_arg

    def __repr__(self) -> str:
        return "self." + repr(self.in_arg) + " <- " + repr(self.node) + "." + repr(self.out_arg)

    def decorate(self, namespace: str | Namespace) -> DagDependency:
        return self.__class__(self.node.decorate(namespace), self.in_arg, self.out_arg)


@final
class DAG:
    _nodes: frozendict[DagNode, ProcessorProps]
    _dependencies: frozendict[DagNode, oset[DagDependency]]

    @property
    def nodes(self) -> Mapping[DagNode, ProcessorProps]:
        return self._nodes

    @property
    def dependencies(self) -> Mapping[DagNode, oset[DagDependency]]:
        return self._dependencies

    def __init__(
        self,
        nodes: Mapping[DagNode, ProcessorProps] = {},
        dependencies: Mapping[DagNode, Sequence[DagDependency] | oset[DagDependency]] = {},
    ) -> None:
        if dependencies.keys() - nodes:
            raise Exception("More dependencies than nodes.")
        if not all(
            len(set((dp.node, dp.in_arg) for dp in dependencies[n])) == len(dependencies[n])
            for n in dependencies
        ):
            raise Exception("A node cannot have an input name more than once per dependency.")

        # Fill missing node dependencies for all nodes
        dependencies = dict(dependencies)
        for node_key in nodes.keys() - dependencies.keys():
            dependencies[node_key] = oset()

        self._nodes = frozendict(nodes)
        self._dependencies = frozendict({k: oset(dps) for k, dps in dependencies.items()})

    def __add__(self, dag: DAG) -> DAG:
        distinct_nodes = self._nodes | dag._nodes - (self._nodes & dag._nodes)
        if len(set(repr(node) for node in distinct_nodes)) != len(distinct_nodes):
            raise Exception("Nodes in both dags with same name need to have same props.")
        new_nodes = self._nodes | dag._nodes
        new_dependencies = defaultdict(oset, self.dependencies)
        for node, dependencies in dag.dependencies.items():
            new_dependencies[node] |= dependencies
        return self.__class__(new_nodes, new_dependencies)

    def __contains__(self, node: DagNode) -> bool:
        return node in self.nodes

    def __len__(self) -> int:
        return len(self.nodes)

    def __repr__(self) -> str:
        return f"DAG(\n\tnodes = {self.nodes},\n\tdependencies = {self.dependencies}\n)"

    def __sub__(self, nodes: Mapping[DagNode, ProcessorProps]) -> DAG:
        # Overload w/ nodes and dags support?
        new_nodes = self._nodes - dict(nodes)
        new_dependencies = {n: self.dependencies[n] for n in new_nodes}
        return self.__class__(new_nodes, new_dependencies)

    # maybe have a client that performs these operations? more consistent w/ python frozens?
    def add_dependencies(self, node: DagNode, dependencies: Iterable[DagDependency]) -> DAG:
        if node not in self:
            raise Exception("Node not in current dag; cannot add dependencies.")

        new_dependencies = self._dependencies[node] | oset(dependencies)
        return self.__class__(self._nodes, self._dependencies.set(node, new_dependencies))

    def set_dependencies(self, node: DagNode, dependencies: Iterable[DagDependency]) -> DAG:
        if node not in self:
            raise Exception("Node not in current dag; cannot set dependencies.")

        return self.__class__(self._nodes, self._dependencies.set(node, oset(dependencies)))

    def decorate(self, namespace: str | Namespace) -> DAG:
        nodes: dict[DagNode, ProcessorProps] = {}
        dependencies: dict[DagNode, oset[DagDependency]] = {}

        for node, props in self.nodes.items():
            new_node = node.decorate(namespace)
            nodes[new_node] = props
            dependencies[new_node] = oset(
                dp.decorate(namespace) if dp not in self.external_dependencies[node] else dp
                for dp in self.dependencies[node]
            )

        return self.__class__(nodes, dependencies)

    def remove(self, node: DagNode) -> DAG:
        return self.__class__(self._nodes - set((node,)), self._dependencies.delete(node))

    @cached_property
    def all_dependencies(self) -> AbstractSet[DagDependency]:
        """All dependencies gathered from all nodes in the dag."""
        return oset(dp for dps in self.dependencies.values() for dp in dps)

    @cached_property
    def external_dependencies(self) -> Mapping[DagNode, AbstractSet[DagDependency]]:
        """Dependencies that point to other nodes not from the dag."""
        return {
            n: oset({dp for dp in dps if dp.node not in self._nodes})
            for n, dps in self._dependencies.items()
        }

    @cached_property
    def hanging_dependencies(self) -> Mapping[DagNode, AbstractSet[InProcessorParam]]:
        """Dependencies that do not have an external DagNode assigned."""
        return {
            n: oset(
                in_arg
                for in_arg in props.inputs.values()
                if in_arg not in (dp.in_arg for dp in self._dependencies[n])
            )
            for n, props in self._nodes.items()
        }

    @cached_property
    def root_nodes(self) -> Mapping[DagNode, ProcessorProps]:
        """Nodes with external or hanging dependencies."""
        return {
            n: props
            for n, props in self.nodes.items()
            if (n in self.external_dependencies or n in self.hanging_dependencies)
        }

    @cached_property
    def leaf_nodes(self) -> Mapping[DagNode, ProcessorProps]:
        """Nodes that other nodes in the dag do not depend on."""
        leaf_nodes = self._nodes.keys() - set(dp.node for dp in self.all_dependencies)
        return {n: self._nodes[n] for n in leaf_nodes}

    def history(self, node: DagNode) -> DAG:
        nodes: dict[DagNode, ProcessorProps] = {node: self.nodes[node]}
        dependencies: dict[DagNode, oset[DagDependency]] = {node: self.dependencies[node]}
        frontier: set[DagNode] = set(dp.node for dp in self.dependencies[node])

        while frontier:
            past_node = frontier.pop()
            nodes[past_node] = self.nodes[past_node]
            dependencies[past_node] = self.dependencies[past_node]
            frontier |= set(dp.node for dp in self.dependencies[past_node])

        return self.__class__(nodes, dependencies)


class IExpandDag(Protocol):
    def expand(self) -> DAG:
        pass


class IPruneDag(Protocol):
    def prune(self) -> DAG:
        pass
