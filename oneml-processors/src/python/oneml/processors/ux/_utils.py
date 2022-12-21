from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence, TypeAlias, TypedDict, TypeVar, cast

from ..dag import DagNode, InProcessorParam, OutProcessorParam
from ._pipeline import (
    InCollection,
    InCollectionEntry,
    InParameter,
    OutCollection,
    OutCollectionEntry,
    OutParameter,
    ParamCollectionEntry,
    Pipeline,
    PipelineInput,
    PipelineIO,
    PipelineOutput,
    PipelineParam,
    PipelineParamCollection,
)

PP = TypeVar("PP", bound=InProcessorParam | OutProcessorParam, covariant=True)
PM = TypeVar("PM", bound=PipelineParam[Any], covariant=True)
PE = TypeVar("PE", bound=ParamCollectionEntry[Any], covariant=True)
PC = TypeVar("PC", bound=PipelineParamCollection[Any], covariant=True)
PL = TypeVar("PL", bound=PipelineIO[Any], covariant=True)

UserIO = Mapping[str, PE | PC | Sequence[PE | PC]]
UserInput: TypeAlias = UserIO[InCollectionEntry, InCollection]
UserOutput: TypeAlias = UserIO[OutCollectionEntry, OutCollection]

DagIO = Mapping[DagNode, Mapping[str, PP]]
DagInput: TypeAlias = DagIO[InProcessorParam]
DagOutput: TypeAlias = DagIO[OutProcessorParam]


IOTypes = TypedDict(
    "IOTypes",
    {"param": type[PM], "entry": type[PE], "collection": type[PC], "pipeline": type[PL]},
)
INPUT_TYPES = IOTypes(
    {
        "param": InParameter,
        "entry": InCollectionEntry,
        "collection": InCollection,
        "pipeline": PipelineInput,
    }
)
OUTPUT_TYPES = IOTypes(
    {
        "param": OutParameter,
        "entry": OutCollectionEntry,
        "collection": OutCollection,
        "pipeline": PipelineOutput,
    }
)


class PipelineUtils:
    @classmethod
    def dag_inputs_to_pipeline_inputs(
        cls, inputs: DagInput, pipelines: Sequence[Pipeline] = ()
    ) -> PipelineInput:
        return cls._io2pipeline(inputs, pipelines, INPUT_TYPES)

    @classmethod
    def dag_outputs_to_pipeline_outputs(
        cls, outputs: DagOutput, pipelines: Sequence[Pipeline] = ()
    ) -> PipelineOutput:
        return cls._io2pipeline(outputs, pipelines, OUTPUT_TYPES)

    @classmethod
    def user_inputs_to_pipeline_inputs(
        cls, user_input: UserInput, name: str, pipelines: Sequence[Pipeline]
    ) -> PipelineInput:
        dag_input = cls.user_inputs_to_dag_inputs(user_input, name)
        return cls.dag_inputs_to_pipeline_inputs(dag_input, pipelines)

    @classmethod
    def user_outputs_to_pipeline_outputs(
        cls, user_output: UserOutput, name: str, pipelines: Sequence[Pipeline]
    ) -> PipelineOutput:
        dag_output = cls.user_outputs_to_dag_outputs(user_output, name)
        return cls.dag_outputs_to_pipeline_outputs(dag_output, pipelines)

    @classmethod
    def pipeline_inputs_to_dag_inputs(cls, inputs: PipelineInput) -> DagInput:
        return cls._io2dag(inputs, INPUT_TYPES)

    @classmethod
    def pipeline_outputs_to_dag_outputs(cls, outputs: PipelineOutput) -> DagOutput:
        return cls._io2dag(outputs, OUTPUT_TYPES)

    @classmethod
    def user_inputs_to_dag_inputs(cls, inputs: UserInput, name: str) -> DagInput:
        return cls._io2dag(inputs, INPUT_TYPES, name)

    @classmethod
    def user_outputs_to_dag_outputs(cls, outputs: UserOutput, name: str) -> DagOutput:
        return cls._io2dag(outputs, OUTPUT_TYPES, name)

    @classmethod
    def pipeline_inputs_to_user_inputs(cls, inputs: PipelineInput) -> UserInput:
        return cast(UserInput, inputs)

    @classmethod
    def pipeline_outputs_to_user_outputs(cls, outputs: PipelineOutput) -> UserOutput:
        return cast(UserOutput, outputs)

    @classmethod
    def dag_inputs_to_user_inputs(
        cls, inputs: DagInput, pipelines: Sequence[Pipeline]
    ) -> UserInput:
        pipeline_input = cls.dag_inputs_to_pipeline_inputs(inputs, pipelines)
        return cls.pipeline_inputs_to_user_inputs(pipeline_input)

    @classmethod
    def dag_outputs_to_user_outputs(
        cls, outputs: DagOutput, pipelines: Sequence[Pipeline]
    ) -> UserOutput:
        pipeline_output = cls.dag_outputs_to_pipeline_outputs(outputs, pipelines)
        return cls.pipeline_outputs_to_user_outputs(pipeline_output)

    @staticmethod
    def _io2pipeline(
        io: DagIO[PP],
        pipelines: Sequence[Pipeline],
        iotypes: IOTypes[PM, PE, PC, PL],
    ) -> PL:
        if not all(isinstance(node, DagNode) for node in io):
            raise ValueError("Keys have to be instances of DagNode.")
        if any(k.count(".") > 1 for params in io.values() for k in params):
            raise ValueError("Input keys in mapping admit single dot notation.")

        def split_key(key: str, default: str) -> tuple[str, str]:
            split = key.split(".")
            return split[0], split[1] if split[1:] else default

        def get_default(node: DagNode) -> str:
            return next(iter(pl.name for pl in pipelines if node in pl.dag), node.name)

        sig: dict[str, dict[str, tuple[PM, ...]]] = defaultdict(lambda: defaultdict(tuple))
        for n, d in io.items():
            for k, p in d.items():
                cname, ename = split_key(k, get_default(n))
                sig[cname][ename] += (iotypes["param"](n, p),)

        return iotypes["pipeline"](
            {
                cname: iotypes["collection"](
                    {ename: iotypes["entry"](entry) for ename, entry in collection.items()}
                )
                for cname, collection in sig.items()
            }
        )

    @staticmethod
    def _io2dag(io: UserIO[PE, PC], iotypes: IOTypes[PM, PE, PC, PL], name: str = "") -> DagIO[PP]:
        def update_entry(key: str, entry: ParamCollectionEntry[Any]) -> None:
            for p in entry:
                dag_io[p.node.decorate(name)].update({key: p.param})

        def update_collection(key: str, collection: PipelineParamCollection[Any]) -> None:
            for ename, entry in collection.items():
                new_ename = (
                    ""
                    if key.count(".") == 1 or (len(entry) == 1 and ename == entry[0].node.name)
                    else "." + ename
                )  # do not append ename if key constains a `.` or is the default node's name
                update_entry(key + new_ename, entry)

        dag_io: defaultdict[DagNode, dict[str, PP]] = defaultdict(dict)
        for k, uv in io.items():
            if isinstance(uv, iotypes["entry"]):
                update_entry(k, uv)
            elif isinstance(uv, iotypes["collection"]):
                update_collection(k, uv)
            elif isinstance(uv, Sequence):
                for i in uv:
                    if isinstance(i, iotypes["entry"]):
                        update_entry(k, i)
                    elif isinstance(i, iotypes["collection"]):
                        update_collection(k, i)
                    else:
                        raise ValueError(f"Unexpected `io` format {i}.")
            else:
                raise ValueError(f"Unexpected `io` format {uv}.")

        return dag_io
