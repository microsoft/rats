from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence, TypeAlias, cast

from ..dag._dag import DagNode
from ..dag._processor import InProcessorParam, OutProcessorParam, ProcessorParam
from ..utils._frozendict import frozendict
from ._pipeline import (
    InParamCollection,
    InParameter,
    OutParamCollection,
    OutParameter,
    Pipeline,
    PipelineInput,
    PipelineOutput,
    PipelineParam,
    PipelineParamCollection,
)

UserInput: TypeAlias = Mapping[str, InParameter | InParamCollection]
UserOutput: TypeAlias = Mapping[str, OutParameter | OutParamCollection]
DagInput: TypeAlias = Mapping[DagNode, Mapping[str, InProcessorParam]]
DagOutput: TypeAlias = Mapping[DagNode, Mapping[str, OutProcessorParam]]


class PipelineUtils:
    @staticmethod
    def merge_pipeline_inputs(
        *pipelines: Pipeline, exclude: Sequence[InParameter] = ()
    ) -> PipelineInput:
        params_exclude = tuple((p.node, p.param) for p in exclude)
        dag_input = {
            n: {k: v for k, v in d.items() if (n, v) not in params_exclude}
            for pl in pipelines
            for n, d in PipelineIO.pipeline_inputs_to_dag_inputs(pl.inputs).items()
        }
        return PipelineIO.dag_inputs_to_pipeline_inputs(dag_input, pipelines)

    @staticmethod
    def merge_pipeline_outputs(
        *pipelines: Pipeline, exclude: Sequence[OutParameter] = ()
    ) -> PipelineOutput:
        params_exclude = tuple((p.node, p.param) for p in exclude)
        dag_output = {
            n: {k: v for k, v in d.items() if (n, v) not in params_exclude}
            for pl in pipelines
            for n, d in PipelineIO.pipeline_outputs_to_dag_outputs(pl.outputs).items()
        }
        return PipelineIO.dag_outputs_to_pipeline_outputs(dag_output, pipelines)


class PipelineIO:
    @classmethod
    def dag_inputs_to_pipeline_inputs(
        cls, inputs: DagInput, pipelines: Sequence[Pipeline] = ()
    ) -> PipelineInput:
        io = cls._io2pipeline(inputs, pipelines, InParameter, InParamCollection)
        return cast(PipelineInput, io)

    @classmethod
    def dag_outputs_to_pipeline_outputs(
        cls, outputs: DagOutput, pipelines: Sequence[Pipeline] = ()
    ) -> PipelineOutput:
        io = cls._io2pipeline(outputs, pipelines, OutParameter, OutParamCollection)
        return cast(PipelineOutput, io)

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
        dag_input = cls._io2dag(inputs, InParameter, InParamCollection)
        return cast(DagInput, dag_input)

    @classmethod
    def pipeline_outputs_to_dag_outputs(cls, outputs: PipelineOutput) -> DagOutput:
        dag_output = cls._io2dag(outputs, OutParameter, OutParamCollection)
        return cast(DagOutput, dag_output)

    @classmethod
    def user_inputs_to_dag_inputs(cls, inputs: UserInput, name: str) -> DagInput:
        dag_input = cls._io2dag(inputs, InParameter, InParamCollection, name)
        return cast(DagInput, dag_input)

    @classmethod
    def user_outputs_to_dag_outputs(cls, outputs: UserOutput, name: str) -> DagOutput:
        p_output = cls._io2dag(outputs, OutParameter, OutParamCollection, name)
        return cast(DagOutput, p_output)

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
        io: Mapping[DagNode, Mapping[str, ProcessorParam]],
        pipelines: Sequence[Pipeline],
        param_type: type[PipelineParam],
        collection_type: type[PipelineParamCollection],
    ) -> frozendict[str, PipelineParamCollection]:
        pipeline_parameter_type = {
            InParameter: InProcessorParam,
            OutParameter: OutProcessorParam,
        }
        if not all(isinstance(node, DagNode) for node in io):
            raise ValueError("Keys have to be instances of DagNode.")
        if not all(
            isinstance(k, str) and isinstance(p, pipeline_parameter_type[param_type])
            for d in io.values()
            for k, p in d.items()
        ):
            raise ValueError(f"values of inputs have to be Mapping[str, {param_type}].")
        if any(k.count(".") > 1 for params in io.values() for k in params):
            raise ValueError("Input keys in mapping admit single dot notation.")

        def split_key(key: str, default: str) -> tuple[str, str]:
            split = key.split(".")
            return split[0], split[1] if split[1:] else default

        def get_default(node: DagNode) -> str:
            return next(iter(pl.name for pl in pipelines if node in pl.dag), node.name)

        names: set[str] = set()
        spaces: dict[DagNode, str] = {}
        counter: defaultdict[tuple[str, str], int] = defaultdict(int)
        for n, in_params in io.items():
            for k in in_params:
                name, space = split_key(k, get_default(n))
                names.add(name)
                spaces[n] = space
                counter[(name, space)] += 1
                if counter[(name, space)] > 1:
                    raise ValueError("Multiple colliding variable names and spaces.")
        sig = {
            name: collection_type(
                {
                    spaces[n]: param_type(n, p)
                    for n, in_params in io.items()
                    for k, p in in_params.items()
                    if split_key(k, get_default(n))[0] == name
                }
            )
            for name in names
        }
        return frozendict(sig)

    @staticmethod
    def _io2dag(
        io: Mapping[str, PipelineParam | PipelineParamCollection],
        param_type: type[PipelineParam],
        collection_type: type[PipelineParamCollection],
        name: str = "",
    ) -> Mapping[DagNode, Mapping[str, ProcessorParam]]:
        pipeline_io: defaultdict[DagNode, dict[str, ProcessorParam]] = defaultdict(dict)
        for k, params in io.items():
            if isinstance(params, param_type):
                pipeline_io[params.node.decorate(name)].update({k: params.param})
            elif isinstance(params, collection_type):
                if k.count(".") > 0 and len(params) > 1:
                    raise ValueError("Dot notation is not meaningful when assigning a collection.")
                for space, p in params.collection.items():
                    new_space = "." + space if space != p.node.name else ""
                    pipeline_io[p.node.decorate(name)].update({k + new_space: p.param})
        return pipeline_io
