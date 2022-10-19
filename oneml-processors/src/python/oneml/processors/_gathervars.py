from enum import Enum
from inspect import _ParameterKind
from typing import Any, Mapping, Sequence, TypedDict

from ._pipeline import IExpandPipeline, PDependency, Pipeline, PNode, ProcessorProps
from ._processor import InParameter, InParameterTargetMethod, IProcess, OutParameter

SequenceOutput = TypedDict("SequenceOutput", {"output": Sequence[Any]})
MappingOutput = TypedDict("MappingOutput", {"output": Mapping[str, Any]})
CollectionOutput = TypedDict("CollectionOutput", {"output": object})


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
    GatherVarKind.SEQUENCE: InParameter.VAR_POSITIONAL,
    GatherVarKind.MAPPING: InParameter.VAR_KEYWORD,
    GatherVarKind.NAMEDTUPLE: InParameter.VAR_KEYWORD,
    GatherVarKind.DATACLASS: InParameter.VAR_KEYWORD,
}


class GatherVarsPipelineExpander(IExpandPipeline):
    _pipeline: Pipeline
    _gathervars: Mapping[PNode, Sequence[tuple[InParameter, GatherVarKind]]]

    def __init__(
        self,
        pipeline: Pipeline,
        gathervars: Mapping[PNode, Sequence[tuple[InParameter, GatherVarKind]]],
    ) -> None:
        super().__init__()
        self._pipeline = pipeline
        self._gathervars = gathervars

    def _add_gathering_node(
        self,
        pipeline: Pipeline,
        node: PNode,
        dependencies: Sequence[PDependency],
        kind: GatherVarKind,
    ) -> Pipeline:
        if not all(dp.node for dp in dependencies):
            dps = tuple(dp for dp in dependencies if not dp.node)
            raise ValueError(f"Trying to gather inputs from hanging dependencies: {dps}.")

        if not all(dp.in_arg == dependencies[0].in_arg for dp in dependencies):
            raise ValueError("Not all dependencies have same input argument name.")

        in_arg, in_arg_ann = dependencies[0].in_arg, dependencies[0].in_arg.annotation

        # create gathering pipeline with gathering node and modifyied dependencies
        gathering_node = PNode(node.name + ":" + in_arg.name + ":", node.namespace)
        gathering_nodes: dict[PNode, ProcessorProps] = {
            gathering_node: ProcessorProps(GATHERVAR2PROCESSOR[kind])
        }
        gathering_dependencies = {
            gathering_node: set(
                PDependency(
                    dp.node,
                    InParameter(
                        GATHERVAR2ARG[kind],
                        Any,
                        InParameterTargetMethod.Process,
                        GATHERVAR2KIND[kind],
                    ),
                    dp.out_arg,
                )
                for dp in dependencies
            )
        }
        gathering_pipeline = Pipeline(gathering_nodes, gathering_dependencies)

        # create new pipeline removing redirected dependencies
        new_dp = PDependency(gathering_node, in_arg, OutParameter("output", in_arg_ann))
        new_dependencies = pipeline.dependencies[node] - set(dependencies) | set((new_dp,))
        new_pipeline = pipeline.set_dependencies(node, new_dependencies)

        return new_pipeline + gathering_pipeline  # return joint gathering and modified pipelines

    def expand(self) -> Pipeline:
        new_pipeline = self._pipeline
        for node, in_args in self._gathervars.items():
            for in_arg in in_args:
                param, kind = in_arg
                dps = tuple(dp for dp in self._pipeline.dependencies[node] if dp.in_arg == param)
                new_pipeline = self._add_gathering_node(new_pipeline, node, dps, kind)

        return new_pipeline
