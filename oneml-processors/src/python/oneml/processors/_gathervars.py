import sys
from collections import Counter
from inspect import Parameter, _ParameterKind
from typing import Any, Mapping, Sequence, TypedDict, TypeVar

from ._pipeline import IExpandPipeline, PDependency, Pipeline, PNode, PNodeProperties
from ._processor import GatherVarKind, IProcessor, OutParameter, Provider

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

_T: TypeAlias = Mapping[str, Any]
T = TypeVar("T", bound=_T, covariant=True)  # output mapping of processors


SequenceOutput = TypedDict("SequenceOutput", {"output": Sequence[Any]})
MappingOutput = TypedDict("MappingOutput", {"output": Mapping[str, Any]})
CollectionOutput = TypedDict("CollectionOutput", {"output": object})


class GatherSequence(IProcessor[SequenceOutput]):
    def __init__(self) -> None:
        super().__init__()

    def process(self, *args: Any) -> SequenceOutput:
        return SequenceOutput(output=args)


class GatherMapping(IProcessor[MappingOutput]):
    def __init__(self) -> None:
        super().__init__()

    def process(self, **kwargs: Any) -> MappingOutput:
        return MappingOutput(output=kwargs)


class GatherCollection(IProcessor[CollectionOutput]):
    """Gathers variable inputs for collection object, e.g., namedtuple or dataclass."""

    def __init__(self, collection_type: type[object]) -> None:
        super().__init__()
        self._collection_type = collection_type

    def process(self, **kwargs: Any) -> CollectionOutput:
        return CollectionOutput(output=self._collection_type(**kwargs))


GATHERVAR2PROCESSOR: Mapping[GatherVarKind, type[IProcessor[_T]]] = {
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
    GatherVarKind.SEQUENCE: Parameter.VAR_POSITIONAL,
    GatherVarKind.MAPPING: Parameter.VAR_KEYWORD,
    GatherVarKind.NAMEDTUPLE: Parameter.VAR_KEYWORD,
    GatherVarKind.DATACLASS: Parameter.VAR_KEYWORD,
}


class GatherVarsPipelineExpander(IExpandPipeline):
    def __init__(self, pipeline: Pipeline) -> None:
        super().__init__()
        self._pipeline = pipeline

    def _add_gathering_node(
        self, pipeline: Pipeline, node: PNode, dependencies: Sequence[PDependency]
    ) -> Pipeline:
        if not all(dp.node for dp in dependencies):
            dps = tuple(dp for dp in dependencies if not dp.node)
            raise ValueError(f"Trying to gather inputs from hanging dependencies: {dps}.")

        if not all(dp.in_arg == dependencies[0].in_arg for dp in dependencies):
            raise ValueError("Not all dependencies have same input argument name.")

        in_arg, in_arg_ann = dependencies[0].in_arg, dependencies[0].in_arg.annotation
        kind = dependencies[0].gathervar_kind

        # create gathering pipeline with gathering node and modifyied dependencies
        gathering_node = PNode(node.name + ":" + in_arg.name + ":", node.namespace)
        gathering_props = {gathering_node: PNodeProperties(Provider(GATHERVAR2PROCESSOR[kind]))}
        gathering_dependencies = {
            gathering_node: set(
                PDependency(
                    dp.node,
                    Parameter(GATHERVAR2ARG[kind], GATHERVAR2KIND[kind], annotation=Any),
                    dp.out_arg,
                )
                for dp in dependencies
            )
        }
        gathering_pipeline = Pipeline({gathering_node}, gathering_dependencies, gathering_props)

        # create new pipeline removing redirected dependencies
        new_dp = PDependency(gathering_node, in_arg, OutParameter("output", in_arg_ann))
        new_dependencies = pipeline.dependencies[node] - set(dependencies) | set((new_dp,))
        new_pipeline = pipeline.set_dependencies(node, new_dependencies)

        return new_pipeline + gathering_pipeline  # return joint gathering and modified pipelines

    def expand(self) -> Pipeline:
        new_pipeline = self._pipeline
        for node in self._pipeline.nodes:
            # validation that each input argument has a unique kind
            arg_counts = Counter(
                (dp.in_arg, dp.gathervar_kind) for dp in self._pipeline.dependencies[node]
            )
            in_arg_counts = Counter(dp.in_arg for dp in self._pipeline.dependencies[node])
            if not all(arg_counts[k] == in_arg_counts[k[0]] for k in arg_counts):
                raise ValueError(f"At least one `in_arg` dependency in {node} has multiple kinds.")

            in_args = set(  # input arguments that gather inputs across nodes
                dp.in_arg
                for dp in self._pipeline.dependencies[node]
                if dp.gathervar_kind != GatherVarKind.STANDARD
            )
            for in_arg in in_args:
                dps = tuple(dp for dp in self._pipeline.dependencies[node] if dp.in_arg == in_arg)
                new_pipeline = self._add_gathering_node(new_pipeline, node, dps)

        return new_pipeline
