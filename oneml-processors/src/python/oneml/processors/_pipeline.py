from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from typing import (
    Any,
    Dict,
    FrozenSet,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    TypeVar,
)

from ._frozendict import FrozenDict
from ._processor import ProcessorInput, Provider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)  # output mapping of processors
TI = TypeVar("TI", contravariant=True)  # generic input types for processor
TO = TypeVar("TO", covariant=True)  # generic output types for processor


@dataclass(frozen=True)
class Namespace:
    key: str = ""

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
class PNode:
    name: str
    namespace: Namespace = Namespace()

    def __contains__(self, namespace: Namespace) -> bool:
        return namespace in self.namespace

    def __repr__(self) -> str:
        return repr(self.namespace) + self.name

    def __post_init__(self) -> None:
        if self.name == "":
            raise Exception("No empty names allowed.")

    def decorate(self, namespace: Namespace) -> PNode:
        return PNode(self.name, namespace / self.namespace)


@dataclass(frozen=True)
class PDependency(Generic[TI, TO]):
    node: Optional[PNode]
    in_arg: Tuple[str, Type[TI]]  # Generic input contravariant on TI
    out_arg: Optional[Tuple[str, Type[TO]]] = None  # Generic output covariant on TO

    def __repr__(self) -> str:
        in_arg = ": ".join(map(str, self.in_arg))
        out_arg = ": ".join(map(str, self.out_arg)) if self.out_arg else None
        return "self." + in_arg + " <- " + repr(self.node) + "." + str(out_arg)

    def __post_init__(self) -> None:
        if self.out_arg is not None and not issubclass(self.out_arg[1], self.in_arg[1]):
            raise ValueError("Output type argument must be a subclas of the input type argument.")

    def decorate(self, namespace: Namespace) -> PDependency[TI, TO]:
        return (
            PDependency(self.node.decorate(namespace), self.in_arg, self.out_arg)
            if self.node
            else self
        )

    def set_node(
        self, node: PNode, out_arg: Optional[Tuple[str, Type[TO]]] = None
    ) -> PDependency[TI, TO]:
        return self.__class__(node, self.in_arg, out_arg)


@dataclass(frozen=True)
class PComputeReqs:
    registry: str = ""
    image_tag: str = ""
    cpus: int = 4
    gpus: int = 0
    memory: str = "50Gi"
    pods: int = 1


@dataclass(frozen=True)
class PNodeProperties(Generic[T]):
    exec_provider: Provider[T]
    compute_reqs: PComputeReqs = PComputeReqs()

    def __hash__(self) -> int:
        return hash(self.exec_provider)


@dataclass(frozen=True)
class Pipeline(Generic[T, TI, TO]):
    nodes: FrozenSet[PNode] = field(default_factory=frozenset)
    dependencies: FrozenDict[PNode, FrozenSet[PDependency[TI, TO]]] = field(
        default_factory=FrozenDict
    )
    props: FrozenDict[PNode, PNodeProperties[T]] = field(default_factory=FrozenDict)

    def __add__(self, pipeline: Pipeline[T, TI, TO]) -> Pipeline[T, TI, TO]:
        # instead of __add__, maybe __or__?
        # overload with pipeline, nodes, dependencies, props?
        if not all(
            self.props[node] == pipeline.props[node] for node in self.nodes & pipeline.nodes
        ):
            raise Exception("Nodes in both pipelines need to have same props.")
        new_nodes = self.nodes | pipeline.nodes
        new_props = {**self.props, **pipeline.props}
        new_dependencies = defaultdict(frozenset, self.dependencies)
        for node, dependencies in pipeline.dependencies.items():
            new_dependencies[node] |= dependencies
        return self.__class__(new_nodes, FrozenDict(new_dependencies), FrozenDict(new_props))

    def __contains__(self, node: PNode) -> bool:
        return node in self.nodes

    def __len__(self) -> int:
        return len(self.nodes)

    def __post_init__(self) -> None:
        if set(self.dependencies.keys()) - self.nodes:
            raise Exception("More dependencies than nodes.")
        if any(n not in self.props for n in self.nodes):
            raise Exception("Missing props for some nodes.")
        if not all(
            len(set((dp.node, dp.in_arg[0]) for dp in self.dependencies[n]))
            == len(self.dependencies[n])
            for n in self.nodes
        ):
            raise Exception("A node cannot have an input name more than once per dependency.")

        # Fill missing node dependencies for all self.nodes
        dependencies = dict(self.dependencies)
        for node in self.nodes - set(dependencies.keys()):
            dependencies[node] = frozenset()

        # Fill all hanging dependencies for all unspecified dependencies
        for node in self.nodes:
            sig = ProcessorInput.signature_from_provider(self.props[node].exec_provider)
            for in_arg in sig.items():
                if not any(dp.in_arg == in_arg for dp in self.dependencies[node]):
                    dependencies[node] |= set((PDependency(None, in_arg),))

        # Set attribute in frozen dataclass during post_init: https://stackoverflow.com/a/54119384
        object.__setattr__(self, "dependencies", FrozenDict(dependencies))

    def __repr__(self) -> str:
        return f"Pipeline(nodes = {self.nodes}, dependencies = {self.dependencies})"

    def __sub__(self, nodes: Iterable[PNode]) -> Pipeline[T, TI, TO]:
        # Overload w/ nodes and pipelines support?
        new_nodes = self.nodes - set(nodes)
        new_props = {n: self.props[n] for n in new_nodes}
        new_dependencies = {n: self.dependencies[n] for n in new_nodes}
        return self.__class__(new_nodes, FrozenDict(new_dependencies), FrozenDict(new_props))

    # maybe have a client that performs these operations? more consistent w/ python frozens?
    def add_dependencies(
        self, node: PNode, dependencies: Iterable[PDependency[TI, TO]]
    ) -> Pipeline[T, TI, TO]:
        if node not in self:
            raise Exception("Node not in current pipeline; cannot add dependencies.")

        new_dependencies = self.dependencies[node] | frozenset(dependencies)
        return self.__class__(
            self.nodes, self.dependencies.set(node, new_dependencies), self.props
        )

    def set_dependencies(
        self, node: PNode, dependencies: Iterable[PDependency[TI, TO]]
    ) -> Pipeline[T, TI, TO]:
        if node not in self:
            raise Exception("Node not in current pipeline; cannot set dependencies.")

        return self.__class__(
            self.nodes, self.dependencies.set(node, frozenset(dependencies)), self.props
        )

    def decorate(self, namespace: Namespace) -> Pipeline[T, TI, TO]:
        nodes: set[PNode] = set()
        dependencies: Dict[PNode, FrozenSet[PDependency[TI, TO]]] = {}
        props: Dict[PNode, PNodeProperties[T]] = {}

        for node in self.nodes:
            new_node = node.decorate(namespace)
            nodes.add(new_node)
            dependencies[new_node] = frozenset(
                dp.decorate(namespace) if dp not in self.external_dependencies else dp
                for dp in self.dependencies[node]
            )
            props[new_node] = self.props[node]

        return self.__class__(frozenset(nodes), FrozenDict(dependencies), FrozenDict(props))

    def remove(self, node: PNode) -> Pipeline[T, TI, TO]:
        return self.__class__(
            self.nodes - frozenset((node,)),
            self.dependencies.delete(node),
            self.props.delete(node),
        )

    @cached_property
    def all_dependencies(self) -> FrozenSet[PDependency[TI, TO]]:
        """All dependencies gathered from all nodes in the pipeline."""
        return frozenset(dp for dps in self.dependencies.values() for dp in dps)

    @cached_property
    def external_dependencies(self) -> FrozenSet[PDependency[TI, TO]]:
        """Dependencies that point to other nodes not from the pipeline."""
        return frozenset(dp for dp in self.all_dependencies if dp.node not in self.nodes)

    @cached_property
    def internal_dependencies(self) -> FrozenSet[PDependency[TI, TO]]:
        """Dependencides that point to other nodes within the pipeline."""
        return self.all_dependencies - self.external_dependencies - self.hanging_dependencies

    @cached_property
    def hanging_dependencies(self) -> FrozenSet[PDependency[TI, TO]]:
        """Dependencies that do not have an external PNode assigned."""
        return frozenset(dp for dp in self.all_dependencies if dp.node is None)

    @cached_property
    def start_nodes(self) -> FrozenSet[PNode]:
        """Nodes with external or hanging dependencies."""
        return frozenset(
            n
            for n in self.nodes
            if (self.external_dependencies | self.hanging_dependencies) & self.dependencies[n]
        )

    @cached_property
    def end_nodes(self) -> FrozenSet[PNode]:
        """Nodes that other nodes in the pipeline do not depend on."""
        return self.nodes - frozenset(dp.node for dp in self.internal_dependencies if dp.node)

    def history(self, node: PNode) -> Pipeline[T, TI, TO]:
        nodes: Set[PNode] = set((node,))
        dependencies: Dict[PNode, FrozenSet[PDependency[TI, TO]]] = {node: self.dependencies[node]}
        props: Dict[PNode, PNodeProperties[T]] = {node: self.props[node]}
        frontier: Set[PNode] = set(dp.node for dp in self.dependencies[node] if dp.node)

        while frontier:
            past_node = frontier.pop()
            nodes.add(past_node)
            dependencies[past_node] = self.dependencies[past_node]
            props[past_node] = self.props[past_node]
            frontier |= set(dp.node for dp in self.dependencies[past_node] if dp.node)

        return self.__class__(frozenset(nodes), FrozenDict(dependencies), FrozenDict(props))


class IExpandPipeline(Protocol[T, TI, TO]):
    def expand(self) -> Pipeline[T, TI, TO]:
        pass


class IPrunePipeline(Protocol[T, TI, TO]):
    def prune(self) -> Pipeline[T, TI, TO]:
        pass
