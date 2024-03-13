from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence, Set
from dataclasses import InitVar, dataclass, field
from functools import cached_property
from typing import Any, final

from rats.services import ServiceId

from ..utils._frozendict import frozendict
from ..utils._orderedset import orderedset
from ._processor import Annotations, InProcessorParam, IProcess, OutProcessorParam

logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True, init=False)
class Namespace:
    key: str

    def __init__(self, key: str = "") -> None:
        object.__setattr__(self, "key", key.strip("/"))

    def __bool__(self) -> bool:
        return bool(self.key)

    def __contains__(self, namespace: Namespace) -> bool:
        return namespace.key in self.key

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
    config: Mapping[str, Any] = frozendict()  # noqa: RUF009
    services: Mapping[str, ServiceId[Any]] = frozendict()  # noqa: RUF009
    input_annotation: InitVar[Mapping[str, type] | None] = None
    return_annotation: InitVar[Mapping[str, type] | None] = None
    compute_reqs: ComputeReqs | None = None

    inputs: frozendict[str, InProcessorParam] = field(init=False)
    outputs: frozendict[str, OutProcessorParam] = field(init=False)

    def __post_init__(
        self,
        input_annotation: Mapping[str, type] | None,
        return_annotation: Mapping[str, type] | None,
    ) -> None:
        sig = Annotations.get_processor_signature(self.processor_type)

        _spurious_config_keys = self.config.keys() - sig.keys()
        if len(_spurious_config_keys) > 0:
            raise ValueError(
                "These config keys do not match any parameter in the processor's signature: "
                + ", ".join(_spurious_config_keys)
            )
        _spurious_services_keys = self.services.keys() - sig.keys()
        if len(_spurious_services_keys) > 0:
            raise ValueError(
                "These services keys do not match any parameter in the processor's signature: "
                + ", ".join(_spurious_services_keys)
            )
        _duplicate_config_and_services_keys = self.config.keys() & self.services.keys()
        if len(_duplicate_config_and_services_keys) > 0:
            raise ValueError(
                "These keys appear in both config and services: "
                + ", ".join(_duplicate_config_and_services_keys)
            )

        inputs = {k: v for k, v in sig.items() if k not in self.config and k not in self.services}

        kwargs = set(i for i in inputs.values() if i.kind == InProcessorParam.VAR_KEYWORD)
        if len(kwargs) > 1:
            raise ValueError("Var keyword arguments in both __init__ and process not supported.")
        if len(kwargs) > 0 and input_annotation is None:
            raise ValueError("Var keyword argument in processor, `input_annotation` expected.")
        elif len(kwargs) == 0 and input_annotation is not None:
            raise ValueError("`input_annotation` provided; processor does not have keyword vars.")
        elif len(kwargs) == 1 and input_annotation is not None:
            k = next(iter(kwargs))
            in_method = k.in_method
            in_kwargs: dict[str, InProcessorParam] = {
                k: InProcessorParam(k, ann, in_method, InProcessorParam.KEYWORD_ONLY)
                for k, ann in input_annotation.items()
            }
            inputs.pop(k.name)
            if set(in_kwargs) & set(inputs):
                raise ValueError("Duplicate vars in processor signature and input_annotation.")
            inputs |= in_kwargs

        if return_annotation is not None:
            ra = {k: OutProcessorParam(k, t) for k, t in return_annotation.items()}
        else:
            ra = dict(Annotations.get_return_annotation(self.processor_type.process))

        object.__setattr__(self, "inputs", frozendict(inputs))
        object.__setattr__(self, "outputs", frozendict(ra))

    def __hash__(self) -> int:
        return hash((self.processor_type, self.config, self.services))


@final
@dataclass(frozen=True, init=False)
class DagNode:
    name: str
    namespace: Namespace

    def __init__(self, name: str, namespace: str | Namespace = "") -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "namespace",
            namespace if isinstance(namespace, Namespace) else Namespace(namespace),
        )

    def __contains__(self, namespace: Namespace) -> bool:
        return namespace in self.namespace

    def __repr__(self) -> str:
        return repr(self.namespace) + self.name

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise Exception("Name must be a string.")
        if not isinstance(self.namespace, Namespace):
            raise Exception("Namespace must be a Namespace.")
        if self.name == "":
            raise Exception("No empty names allowed.")

    def decorate(self, namespace: str | Namespace) -> DagNode:
        namespace = namespace if isinstance(namespace, Namespace) else Namespace(namespace)
        return DagNode(self.name, namespace / self.namespace)


@final
class DagDependency:
    _node: DagNode
    _in_arg: InProcessorParam
    _out_arg: OutProcessorParam | None

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
        out_arg: OutProcessorParam | None = None,
    ) -> None:
        self._node = node
        self._in_arg = in_arg
        self._out_arg = out_arg

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ == other.__class__
            and self.node == other.node
            and self.in_arg == other.in_arg
            and self.out_arg == other.out_arg
        )

    def __hash__(self) -> int:
        return hash((self.node, self.in_arg, self.out_arg))

    def __repr__(self) -> str:
        return "self." + repr(self.in_arg) + " <- " + repr(self.node) + "." + repr(self.out_arg)

    def decorate(self, namespace: str | Namespace) -> DagDependency:
        return self.__class__(self.node.decorate(namespace), self.in_arg, self.out_arg)


@final
class DAG:
    _nodes: frozendict[DagNode, ProcessorProps]
    _dependencies: frozendict[DagNode, orderedset[DagDependency]]

    @property
    def nodes(self) -> Mapping[DagNode, ProcessorProps]:
        return self._nodes

    @property
    def dependencies(self) -> Mapping[DagNode, orderedset[DagDependency]]:
        return self._dependencies

    def __init__(
        self,
        nodes: Mapping[DagNode, ProcessorProps] = {},
        dependencies: Mapping[DagNode, Sequence[DagDependency]] = {},
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
            dependencies[node_key] = orderedset()

        self._nodes = frozendict(nodes)
        self._dependencies = frozendict({k: orderedset(dps) for k, dps in dependencies.items()})

    def __add__(self, dag: DAG) -> DAG:
        distinct_nodes = self._nodes | dag._nodes - (self._nodes & dag._nodes)
        if len(set(repr(node) for node in distinct_nodes)) != len(distinct_nodes):
            raise Exception("Nodes in both dags with same name need to have same props.")
        new_nodes = self._nodes | dag._nodes
        new_dependencies = defaultdict(orderedset, self.dependencies)
        for node, dependencies in dag.dependencies.items():
            new_dependencies[node] |= dependencies
        return self.__class__(new_nodes, new_dependencies)

    def __contains__(self, node: DagNode) -> bool:
        return node in self.nodes

    def __eq__(self, other: Any) -> bool:
        return (
            self.__class__ == other.__class__
            and self.nodes == other.nodes
            and self.dependencies == other.dependencies
        )

    def __hash__(self) -> int:
        return hash((self.nodes, self.dependencies))

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

        new_dependencies = self._dependencies[node] | orderedset(dependencies)
        return self.__class__(self._nodes, self._dependencies.set(node, new_dependencies))

    def set_dependencies(self, node: DagNode, dependencies: Iterable[DagDependency]) -> DAG:
        if node not in self:
            raise Exception("Node not in current dag; cannot set dependencies.")

        return self.__class__(self._nodes, self._dependencies.set(node, orderedset(dependencies)))

    def decorate(self, namespace: str | Namespace) -> DAG:
        nodes: dict[DagNode, ProcessorProps] = {}
        dependencies: dict[DagNode, orderedset[DagDependency]] = {}

        for node, props in self.nodes.items():
            new_node = node.decorate(namespace)
            nodes[new_node] = props
            dependencies[new_node] = orderedset(
                dp.decorate(namespace) if dp not in self.external_dependencies[node] else dp
                for dp in self.dependencies[node]
            )

        return self.__class__(nodes, dependencies)

    def remove(self, node: DagNode) -> DAG:
        return self.__class__(self._nodes - set((node,)), self._dependencies.delete(node))

    @cached_property
    def all_dependencies(self) -> Set[DagDependency]:
        """All dependencies gathered from all nodes in the dag."""
        return orderedset(dp for dps in self.dependencies.values() for dp in dps)

    @cached_property
    def external_dependencies(self) -> Mapping[DagNode, Set[DagDependency]]:
        """Dependencies that point to other nodes not from the dag."""
        return {
            n: orderedset({dp for dp in dps if dp.node not in self._nodes})
            for n, dps in self._dependencies.items()
        }

    @cached_property
    def hanging_dependencies(self) -> Mapping[DagNode, Set[InProcessorParam]]:
        """Dependencies that do not have an external DagNode assigned."""
        return {
            n: orderedset(
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
        dependencies: dict[DagNode, orderedset[DagDependency]] = {node: self.dependencies[node]}
        frontier: set[DagNode] = set(dp.node for dp in self.dependencies[node])

        while frontier:
            past_node = frontier.pop()
            nodes[past_node] = self.nodes[past_node]
            dependencies[past_node] = self.dependencies[past_node]
            frontier |= set(dp.node for dp in self.dependencies[past_node])

        return self.__class__(nodes, dependencies)
