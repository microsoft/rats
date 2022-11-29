from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence, TypeAlias, TypeVar, cast

from ..dag import DagNode, InProcessorParam, OutProcessorParam
from ._pipeline import (
    InCollection,
    InParameter,
    OutCollection,
    OutParameter,
    Pipeline,
    PipelineInput,
    PipelineIO,
    PipelineOutput,
    PipelineParam,
    PipelineParamCollection,
)

PP = TypeVar("PP", bound=InProcessorParam | OutProcessorParam, covariant=True)
PM = TypeVar("PM", bound=PipelineParam[Any], covariant=True)
PC = TypeVar("PC", bound=PipelineParamCollection[Any], covariant=True)
PL = TypeVar("PL", bound=PipelineIO[Any], covariant=True)

UserInput: TypeAlias = Mapping[str, InParameter | InCollection]
UserOutput: TypeAlias = Mapping[str, OutParameter | OutCollection]
DagInput: TypeAlias = Mapping[DagNode, Mapping[str, InProcessorParam]]
DagOutput: TypeAlias = Mapping[DagNode, Mapping[str, OutProcessorParam]]


class PipelineUtils:
    @classmethod
    def dag_inputs_to_pipeline_inputs(
        cls, inputs: DagInput, pipelines: Sequence[Pipeline] = ()
    ) -> PipelineInput:
        return cls._io2pipeline(inputs, pipelines, InParameter, InCollection, PipelineInput)

    @classmethod
    def dag_outputs_to_pipeline_outputs(
        cls, outputs: DagOutput, pipelines: Sequence[Pipeline] = ()
    ) -> PipelineOutput:
        return cls._io2pipeline(outputs, pipelines, OutParameter, OutCollection, PipelineOutput)

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
        return cls._io2dag(inputs, InParameter, InCollection)

    @classmethod
    def pipeline_outputs_to_dag_outputs(cls, outputs: PipelineOutput) -> DagOutput:
        return cls._io2dag(outputs, OutParameter, OutCollection)

    @classmethod
    def user_inputs_to_dag_inputs(cls, inputs: UserInput, name: str) -> DagInput:
        return cls._io2dag(inputs, InParameter, InCollection, name)

    @classmethod
    def user_outputs_to_dag_outputs(cls, outputs: UserOutput, name: str) -> DagOutput:
        return cls._io2dag(outputs, OutParameter, OutCollection, name)

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
        io: Mapping[DagNode, Mapping[str, PP]],
        pipelines: Sequence[Pipeline],
        param_type: type[PM],
        collection_type: type[PC],
        pipelineio_type: type[PL],
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

        names: set[str] = set()
        counter: defaultdict[tuple[str, str], tuple[DagNode, ...]] = defaultdict(tuple)
        for n, in_params in io.items():
            for k in in_params:
                name, space = split_key(k, get_default(n))
                names.add(name)
                counter[(name, space)] += (n,)
        if any(len(nodes) > 1 for nodes in counter.values()):
            err: tuple[str, ...] = ()
            for (name, space), nodes in counter.items():
                if len(nodes) > 1:
                    err += (f"Colliding variable name and entry: {name}.{space} in {nodes};",)
            raise ValueError("\n".join(err))
        sig = {
            name: collection_type(
                {
                    split_key(k, get_default(n))[1]: param_type(n, p)
                    for n, in_params in io.items()
                    for k, p in in_params.items()
                    if split_key(k, get_default(n))[0] == name
                }
            )
            for name in names
        }
        return pipelineio_type(sig)

    @staticmethod
    def _io2dag(
        io: Mapping[str, PM | PC], param_type: type[PM], collection_type: type[PC], name: str = ""
    ) -> Mapping[DagNode, Mapping[str, PP]]:
        dag_io: defaultdict[DagNode, dict[str, PP]] = defaultdict(dict)
        for k, params in io.items():
            if isinstance(params, param_type):
                dag_io[params.node.decorate(name)].update({k: params.param})
            elif isinstance(params, collection_type):
                if k.count(".") > 0 and len(params) > 1:
                    raise ValueError("Dot notation is not meaningful when assigning a collection.")
                for space, p in params.items():
                    new_space = "" if k.count(".") == 1 or space == p.node.name else "." + space
                    dag_io[p.node.decorate(name)].update({k + new_space: p.param})
        return dag_io
