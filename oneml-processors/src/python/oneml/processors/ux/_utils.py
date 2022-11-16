from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence, TypeAlias, cast

from .._frozendict import frozendict
from .._pipeline import PNode
from .._processor import InParameter, OutParameter, Parameter
from ._workflow import (
    InWorkflowParam,
    InWorkflowParamCollection,
    OutWorkflowParam,
    OutWorkflowParamCollection,
    Workflow,
    WorkflowInput,
    WorkflowOutput,
    WorkflowParam,
    WorkflowParamCollection,
)

UserInput: TypeAlias = Mapping[str, InWorkflowParam | InWorkflowParamCollection]
UserOutput: TypeAlias = Mapping[str, OutWorkflowParam | OutWorkflowParamCollection]
PipelineInput: TypeAlias = Mapping[PNode, Mapping[str, InParameter]]
PipelineOutput: TypeAlias = Mapping[PNode, Mapping[str, OutParameter]]


class WorkflowUtils:
    @staticmethod
    def merge_workflow_inputs(
        *workflows: Workflow, exclude: Sequence[InWorkflowParam] = ()
    ) -> WorkflowInput:
        params_exclude = tuple((p.node, p.param) for p in exclude)
        pipeline_input = {
            n: {k: v for k, v in d.items() if (n, v) not in params_exclude}
            for wf in workflows
            for n, d in WorkflowIO.workflow_inputs_to_pipeline_inputs(wf.inputs).items()
        }
        return WorkflowIO.pipeline_inputs_to_workflow_inputs(pipeline_input, workflows)

    @staticmethod
    def merge_workflow_outputs(
        *workflows: Workflow, exclude: Sequence[OutWorkflowParam] = ()
    ) -> WorkflowOutput:
        params_exclude = tuple((p.node, p.param) for p in exclude)
        pipeline_output = {
            n: {k: v for k, v in d.items() if (n, v) not in params_exclude}
            for wf in workflows
            for n, d in WorkflowIO.workflow_outputs_to_pipeline_outputs(wf.outputs).items()
        }
        return WorkflowIO.pipeline_outputs_to_workflow_outputs(pipeline_output, workflows)


class WorkflowIO:
    @classmethod
    def pipeline_inputs_to_workflow_inputs(
        cls, inputs: PipelineInput, workflows: Sequence[Workflow] = ()
    ) -> WorkflowInput:
        io = cls._io2workflow(inputs, workflows, InWorkflowParam, InWorkflowParamCollection)
        return cast(WorkflowInput, io)

    @classmethod
    def pipeline_outputs_to_workflow_outputs(
        cls, outputs: PipelineOutput, workflows: Sequence[Workflow] = ()
    ) -> WorkflowOutput:
        io = cls._io2workflow(outputs, workflows, OutWorkflowParam, OutWorkflowParamCollection)
        return cast(WorkflowOutput, io)

    @classmethod
    def user_inputs_to_workflow_inputs(
        cls, user_input: UserInput, name: str, workflows: Sequence[Workflow]
    ) -> WorkflowInput:
        pipeline_input = cls.user_inputs_to_pipeline_inputs(user_input, name)
        return cls.pipeline_inputs_to_workflow_inputs(pipeline_input, workflows)

    @classmethod
    def user_outputs_to_workflow_outputs(
        cls, user_output: UserOutput, name: str, workflows: Sequence[Workflow]
    ) -> WorkflowOutput:
        pipeline_output = cls.user_outputs_to_pipeline_outputs(user_output, name)
        return cls.pipeline_outputs_to_workflow_outputs(pipeline_output, workflows)

    @classmethod
    def workflow_inputs_to_pipeline_inputs(cls, inputs: WorkflowInput) -> PipelineInput:
        pipeline_input = cls._io2pipeline(inputs, InWorkflowParam, InWorkflowParamCollection)
        return cast(PipelineInput, pipeline_input)

    @classmethod
    def workflow_outputs_to_pipeline_outputs(cls, outputs: WorkflowOutput) -> PipelineOutput:
        pipeline_output = cls._io2pipeline(outputs, OutWorkflowParam, OutWorkflowParamCollection)
        return cast(PipelineOutput, pipeline_output)

    @classmethod
    def user_inputs_to_pipeline_inputs(cls, inputs: UserInput, name: str) -> PipelineInput:
        pipeline_input = cls._io2pipeline(inputs, InWorkflowParam, InWorkflowParamCollection, name)
        return cast(PipelineInput, pipeline_input)

    @classmethod
    def user_outputs_to_pipeline_outputs(cls, outputs: UserOutput, name: str) -> PipelineOutput:
        p_output = cls._io2pipeline(outputs, OutWorkflowParam, OutWorkflowParamCollection, name)
        return cast(PipelineOutput, p_output)

    @classmethod
    def workflow_inputs_to_user_inputs(cls, inputs: WorkflowInput) -> UserInput:
        return cast(UserInput, inputs)

    @classmethod
    def workflow_outputs_to_user_outputs(cls, outputs: WorkflowOutput) -> UserOutput:
        return cast(UserOutput, outputs)

    @classmethod
    def pipeline_inputs_to_user_inputs(
        cls, inputs: PipelineInput, workflows: Sequence[Workflow]
    ) -> UserInput:
        workflow_input = cls.pipeline_inputs_to_workflow_inputs(inputs, workflows)
        return cls.workflow_inputs_to_user_inputs(workflow_input)

    @classmethod
    def pipeline_outputs_to_user_outputs(
        cls, outputs: PipelineOutput, workflows: Sequence[Workflow]
    ) -> UserOutput:
        workflow_output = cls.pipeline_outputs_to_workflow_outputs(outputs, workflows)
        return cls.workflow_outputs_to_user_outputs(workflow_output)

    @staticmethod
    def _io2workflow(
        io: Mapping[PNode, Mapping[str, Parameter]],
        workflows: Sequence[Workflow],
        param_type: type[WorkflowParam],
        collection_type: type[WorkflowParamCollection],
    ) -> frozendict[str, WorkflowParamCollection]:
        pipeline_parameter_type = {InWorkflowParam: InParameter, OutWorkflowParam: OutParameter}
        if not all(isinstance(node, PNode) for node in io):
            raise ValueError("Keys have to be instances of PNode.")
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

        def get_default(node: PNode) -> str:
            return next(iter(wf.name for wf in workflows if node in wf.pipeline), node.name)

        names: set[str] = set()
        spaces: dict[PNode, str] = {}
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
    def _io2pipeline(
        io: Mapping[str, WorkflowParam | WorkflowParamCollection],
        param_type: type[WorkflowParam],
        collection_type: type[WorkflowParamCollection],
        name: str = "",
    ) -> Mapping[PNode, Mapping[str, Parameter]]:
        pipeline_io: defaultdict[PNode, dict[str, Parameter]] = defaultdict(dict)
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
