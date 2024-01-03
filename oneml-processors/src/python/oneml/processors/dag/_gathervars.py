from collections.abc import Mapping, Sequence
from enum import Enum
from inspect import _ParameterKind
from typing import Any, TypedDict

from ..utils._orderedset import orderedset
from ._dag import DAG, DagDependency, DagNode, IExpandDag, ProcessorProps
from ._processor import InMethod, InProcessorParam, IProcess, OutProcessorParam


class SequenceOutput(TypedDict):
    output: Sequence[Any]


class MappingOutput(TypedDict):
    output: Mapping[str, Any]


class CollectionOutput(TypedDict):
    output: object


class GatherVarKind(Enum):
    STANDARD = 0  # one to one correspondence between processors outputs and inputs
    SEQUENCE = 1  # many to one correspondences
    MAPPING = 2
    NAMEDTUPLE = 3
    DATACLASS = 4


class GatherSequence(IProcess):
    def __init__(self) -> None:
        super().__init__()

    def process(self, *args: Any) -> SequenceOutput:
        return SequenceOutput(output=args)


class GatherMapping(IProcess):
    def __init__(self) -> None:
        super().__init__()

    def process(self, **kwargs: Any) -> MappingOutput:
        return MappingOutput(output=kwargs)


class GatherCollection(IProcess):
    """Gathers variable inputs for collection object, e.g., namedtuple or dataclass."""

    def __init__(self, collection_type: type[object]) -> None:
        self._collection_type = collection_type

    def process(self, **kwargs: Any) -> CollectionOutput:
        return CollectionOutput(output=self._collection_type(**kwargs))


GATHERVAR2PROCESSOR: Mapping[GatherVarKind, type[IProcess]] = {
    GatherVarKind.SEQUENCE: GatherSequence,
    GatherVarKind.MAPPING: GatherMapping,
    GatherVarKind.NAMEDTUPLE: GatherCollection,
    GatherVarKind.DATACLASS: GatherCollection,
}

GATHERVAR2ARG: Mapping[GatherVarKind, str] = {
    GatherVarKind.SEQUENCE: "args",
    GatherVarKind.MAPPING: "kwargs",
    GatherVarKind.NAMEDTUPLE: "kwargs",
    GatherVarKind.DATACLASS: "kwargs",
}

GATHERVAR2KIND: Mapping[GatherVarKind, _ParameterKind] = {
    GatherVarKind.SEQUENCE: InProcessorParam.VAR_POSITIONAL,
    GatherVarKind.MAPPING: InProcessorParam.VAR_KEYWORD,
    GatherVarKind.NAMEDTUPLE: InProcessorParam.VAR_KEYWORD,
    GatherVarKind.DATACLASS: InProcessorParam.VAR_KEYWORD,
}


class GatherVarsDagExpander(IExpandDag):
    _dag: DAG
    _gathervars: Mapping[DagNode, Sequence[tuple[InProcessorParam, GatherVarKind]]]

    def __init__(
        self,
        dag: DAG,
        gathervars: Mapping[DagNode, Sequence[tuple[InProcessorParam, GatherVarKind]]],
    ) -> None:
        super().__init__()
        self._dag = dag
        self._gathervars = gathervars

    def _add_gathering_node(
        self,
        dag: DAG,
        node: DagNode,
        dependencies: Sequence[DagDependency],
        kind: GatherVarKind,
    ) -> DAG:
        if not all(dp.node for dp in dependencies):
            dps = tuple(dp for dp in dependencies if not dp.node)
            raise ValueError(f"Trying to gather inputs from hanging dependencies: {dps}.")

        if not all(dp.in_arg == dependencies[0].in_arg for dp in dependencies):
            raise ValueError("Not all dependencies have same input argument name.")

        in_arg, in_arg_ann = dependencies[0].in_arg, dependencies[0].in_arg.annotation

        # create gathering dag with gathering node and modifyied dependencies
        gathering_node = DagNode(node.name + ":" + in_arg.name + ":", node.namespace)
        gathering_nodes: dict[DagNode, ProcessorProps] = {
            gathering_node: ProcessorProps(GATHERVAR2PROCESSOR[kind])
        }
        gathering_dependencies = {
            gathering_node: orderedset(
                DagDependency(
                    dp.node,
                    InProcessorParam(
                        GATHERVAR2ARG[kind],
                        Any,
                        InMethod.process,
                        GATHERVAR2KIND[kind],
                    ),
                    dp.out_arg,
                )
                for dp in dependencies
            )
        }
        gathering_dag = DAG(gathering_nodes, gathering_dependencies)

        # create new dag removing redirected dependencies
        new_dp = DagDependency(gathering_node, in_arg, OutProcessorParam("output", in_arg_ann))
        new_dependencies = dag.dependencies[node] - set(dependencies) | set((new_dp,))
        new_dag = dag.set_dependencies(node, new_dependencies)

        return new_dag + gathering_dag  # return joint gathering and modified dags

    def expand(self) -> DAG:
        new_dag = self._dag
        for node, in_args in self._gathervars.items():
            for in_arg in in_args:
                param, kind = in_arg
                dps = tuple(dp for dp in self._dag.dependencies[node] if dp.in_arg == param)
                new_dag = self._add_gathering_node(new_dag, node, dps, kind)

        return new_dag
