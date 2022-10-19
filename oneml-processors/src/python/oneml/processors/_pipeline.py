from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from typing import (
    AbstractSet,
    Hashable,
    Iterable,
    Mapping,
    Optional,
    Protocol,
    Tuple,
    Union,
    final,
)

from ._environment_singletons import (
    EmptyParamsFromEnvironmentContract,
    IParamsFromEnvironmentSingletonsContract,
)
from ._frozendict import frozendict
from ._frozendict_with_attr_access import FrozenDictWithAttrAccess
from ._processor import (
    Annotations,
    IHashableGetParams,
    InParameter,
    IProcess,
    KnownParamsGetter,
    OutParameter,
)

logger = logging.getLogger(__name__)


@final
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


class InSignature(FrozenDictWithAttrAccess[InParameter]):
    pass


class OutSignature(FrozenDictWithAttrAccess[OutParameter]):
    pass


@dataclass(frozen=True)
class PComputeReqs:
    registry: str = ""
    image_tag: str = ""
    cpus: int = 4
    gpus: int = 0
    memory: str = "50Gi"
    pods: int = 1


class IProcessorProps(Hashable, Protocol):
    @property
    def processor_type(self) -> type[IProcess]:
        ...

    @property
    def params_getter(self) -> IHashableGetParams:
        ...

    @property
    def params_from_environment_contract(self) -> IParamsFromEnvironmentSingletonsContract:
        ...

    @property
    def compute_reqs(self) -> PComputeReqs:
        ...

    @property
    def sig(self) -> InSignature:
        ...

    @property
    def ret(self) -> OutSignature:
        ...


@dataclass(frozen=True)
class ProcessorProps:
    processor_type: type[IProcess]
    params_getter: IHashableGetParams = KnownParamsGetter()
    params_from_environment_contract: IParamsFromEnvironmentSingletonsContract = (
        EmptyParamsFromEnvironmentContract()
    )
    compute_reqs: PComputeReqs = PComputeReqs()

    sig: InSignature = field(init=False)
    ret: OutSignature = field(init=False)

    def __post_init__(self) -> None:
        provided_params = frozenset(self.params_getter) | frozenset(
            self.params_from_environment_contract
        )
        sig = InSignature(
            **(
                FrozenDictWithAttrAccess(
                    **Annotations.get_processor_signature(self.processor_type)
                )
                - provided_params
            )
        )
        ret = OutSignature(**Annotations.get_return_annotation(self.processor_type.process))
        object.__setattr__(self, "sig", sig)
        object.__setattr__(self, "ret", ret)

    def __hash__(self) -> int:
        return hash((self.processor_type, self.params_getter))


@final
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

    def decorate(self, namespace: str | Namespace) -> PNode:
        namespace = namespace if isinstance(namespace, Namespace) else Namespace(namespace)
        return PNode(self.name, namespace / self.namespace)


@final
class PDependency:
    _node: Optional[PNode]
    _in_arg: InParameter
    _out_arg: Optional[OutParameter]

    @property
    def node(self) -> Optional[PNode]:
        return self._node

    @property
    def in_arg(self) -> InParameter:
        return self._in_arg

    @cached_property
    def out_arg(self) -> OutParameter:
        return (
            self._out_arg
            if self._out_arg
            else OutParameter(self._in_arg.name, self._in_arg.annotation)
        )

    def __init__(
        self,
        node: Union[PNode, Pipeline, None],
        in_arg: InParameter,
        out_arg: Optional[OutParameter] = None,
    ) -> None:
        if isinstance(node, Pipeline):
            if len(node.end_nodes) != 1:
                raise ValueError(
                    "Dependency pipeline must have a single tail node; "
                    "This mechanism ensures pipelines can be referred as dependencies."
                )
            node = next(iter(node.end_nodes))

        self._node = node
        self._in_arg = in_arg
        self._out_arg = out_arg

    def __repr__(self) -> str:
        return "self." + repr(self.in_arg) + " <- " + repr(self.node) + "." + repr(self.out_arg)

    def decorate(self, namespace: str | Namespace) -> PDependency:
        return (
            self.__class__(self.node.decorate(namespace), self.in_arg, self.out_arg)
            if self.node
            else self
        )

    def set_node(self, node: PNode, out_arg: Optional[OutParameter] = None) -> PDependency:
        return self.__class__(node, self.in_arg, out_arg)


class Pipeline:
    _nodes: frozendict[PNode, IProcessorProps]
    _dependencies: frozendict[PNode, frozenset[PDependency]]

    @property
    def nodes(self) -> Mapping[PNode, IProcessorProps]:
        return self._nodes

    @property
    def dependencies(self) -> Mapping[PNode, AbstractSet[PDependency]]:
        return self._dependencies

    def __init__(
        self,
        nodes: Mapping[PNode, IProcessorProps] = {},
        dependencies: Mapping[PNode, AbstractSet[PDependency]] = {},
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
            dependencies[node_key] = set()

        self._nodes = frozendict(nodes)
        self._dependencies = frozendict({k: frozenset(dps) for k, dps in dependencies.items()})

    def __add__(self, pipeline: Pipeline) -> Pipeline:
        distinct_nodes = self._nodes | pipeline._nodes - (self._nodes & pipeline._nodes)
        if len(set(repr(node) for node in distinct_nodes)) != len(distinct_nodes):
            raise Exception("Nodes in both pipelines with same name need to have same props.")
        new_nodes = self._nodes | pipeline._nodes
        new_dependencies = defaultdict(frozenset, self.dependencies)
        for node, dependencies in pipeline.dependencies.items():
            new_dependencies[node] |= dependencies
        return self.__class__(new_nodes, new_dependencies)

    def __contains__(self, node: PNode) -> bool:
        return node in self.nodes

    def __len__(self) -> int:
        return len(self.nodes)

    def __repr__(self) -> str:
        return f"Pipeline(nodes = {self.nodes}, dependencies = {self.dependencies})"

    def __sub__(self, nodes: Mapping[PNode, IProcessorProps]) -> Pipeline:
        # Overload w/ nodes and pipelines support?
        new_nodes = self._nodes - dict(nodes)
        new_dependencies = {n: self.dependencies[n] for n in new_nodes}
        return self.__class__(new_nodes, new_dependencies)

    # maybe have a client that performs these operations? more consistent w/ python frozens?
    def add_dependencies(self, node: PNode, dependencies: Iterable[PDependency]) -> Pipeline:
        if node not in self:
            raise Exception("Node not in current pipeline; cannot add dependencies.")

        new_dependencies = self._dependencies[node] | frozenset(dependencies)
        return self.__class__(self._nodes, self._dependencies.set(node, new_dependencies))

    def set_dependencies(self, node: PNode, dependencies: Iterable[PDependency]) -> Pipeline:
        if node not in self:
            raise Exception("Node not in current pipeline; cannot set dependencies.")

        return self.__class__(self._nodes, self._dependencies.set(node, frozenset(dependencies)))

    def decorate(self, namespace: str | Namespace) -> Pipeline:
        nodes: dict[PNode, IProcessorProps] = {}
        dependencies: dict[PNode, set[PDependency]] = {}

        for node, props in self.nodes.items():
            new_node = node.decorate(namespace)
            nodes[new_node] = props
            dependencies[new_node] = set(
                dp.decorate(namespace) if dp not in self.external_dependencies else dp
                for dp in self.dependencies[node]
            )

        return self.__class__(nodes, dependencies)

    def remove(self, node: PNode) -> Pipeline:
        return self.__class__(self._nodes - set((node,)), self._dependencies.delete(node))

    @cached_property
    def all_dependencies(self) -> AbstractSet[PDependency]:
        """All dependencies gathered from all nodes in the pipeline."""
        return frozenset(dp for dps in self.dependencies.values() for dp in dps)

    @cached_property
    def external_dependencies(self) -> AbstractSet[PDependency]:
        """Dependencies that point to other nodes not from the pipeline."""
        return frozenset(dp for dp in self.all_dependencies if dp.node not in self.nodes)

    @cached_property
    def internal_dependencies(self) -> AbstractSet[PDependency]:
        """Dependencides that point to other nodes within the pipeline."""
        return self.all_dependencies - self.external_dependencies - self.hanging_dependencies

    @cached_property
    def hanging_dependencies(self) -> AbstractSet[PDependency]:
        """Dependencies that do not have an external PNode assigned."""
        # TODO: need to fix this convention; we should no longer add empty dependencies
        return frozenset(dp for dp in self.all_dependencies if dp.node is None)

    def unprovided_inputs_for_node(self, node: PNode) -> AbstractSet[str]:
        node_props = self.nodes[node]
        required_in_port_names = frozenset(node_props.sig)
        provided_in_port_names = frozenset(d.in_arg.name for d in self.dependencies[node])
        return required_in_port_names - provided_in_port_names

    @cached_property
    def unprovided_inputs(self) -> AbstractSet[Tuple[PNode, str]]:
        return frozenset.union(
            *(
                frozenset(((pnode, port) for port in self.unprovided_inputs_for_node(pnode)))
                for pnode in self.nodes
            ),
        )

    @cached_property
    def start_nodes(self) -> AbstractSet[PNode]:
        """Nodes with input ports that do not have corresponding dependencies."""
        return frozenset(n for n, _ in self.unprovided_inputs)

    @cached_property
    def end_nodes(self) -> AbstractSet[PNode]:
        """Nodes that other nodes in the pipeline do not depend on."""
        return self._nodes.keys() - set(dp.node for dp in self.internal_dependencies if dp.node)

    def history(self, node: PNode) -> Pipeline:
        nodes: dict[PNode, IProcessorProps] = {node: self.nodes[node]}
        dependencies: dict[PNode, AbstractSet[PDependency]] = {node: self.dependencies[node]}
        frontier: set[PNode] = set(dp.node for dp in self.dependencies[node] if dp.node)

        while frontier:
            past_node = frontier.pop()
            nodes[past_node] = self.nodes[past_node]
            dependencies[past_node] = self.dependencies[past_node]
            frontier |= set(dp.node for dp in self.dependencies[past_node] if dp.node)

        return self.__class__(nodes, dependencies)


class IExpandPipeline(Protocol):
    def expand(self) -> Pipeline:
        pass


class IPrunePipeline(Protocol):
    def prune(self) -> Pipeline:
        pass
