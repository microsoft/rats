from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple, cast, overload

from ._frozendict import frozendict
from ._pipeline import PComputeReqs, PDependency, Pipeline, PNode, ProcessorProps
from ._processor import IGetParams, IProcess, OutParameter

# from ._utils import TailPipelineClient


@dataclass(frozen=True)
class Dependency:
    in_workflow: Workflow
    in_param: str
    out_workflow: Workflow
    out_param: str


@dataclass(frozen=True)
class InputDependency:
    in_workflow: Workflow
    in_param: str
    name: str


@dataclass(frozen=True)
class OutputDependency:
    out_workflow: Workflow
    out_param: str
    name: str


@dataclass(frozen=True)
class TaskParam:
    node: PNode
    param: str

    def decorate(self, name: str) -> TaskParam:
        return self.__class__(node=self.node.decorate(name), param=self.param)

    # def __lshift__(self, other: Any) -> Dependency:
    #     if not isinstance(other, TaskParam):
    #         raise ValueError("TaskDependency assignment only accepts other Tasks.")
    #     if not (isinstance(self.param, InParameter) and isinstance(other.param, OutParameter)):
    #         raise ValueError("Trying to assing input to output.")
    #     return Dependency(self.node, self.param, other.node, other.param)

    # def __rshift__(self, other: Any) -> Dependency:
    #     if not isinstance(other, TaskParam):
    #         raise ValueError("TaskDependency assignment only accepts other Tasks.")
    #     if not (isinstance(other.param, InParameter) and isinstance(self.param, OutParameter)):
    #         raise ValueError("Trying to assing input to output.")
    #     return Dependency(other.node, other.param, self.node, self.param)


@dataclass(frozen=False)
class InputPort:
    workflow: Workflow
    name: str

    @overload
    def __lshift__(self, other: OutputPort) -> Dependency:
        ...

    @overload
    def __lshift__(self, other: str) -> InputDependency:
        ...

    def __lshift__(self, other: OutputPort | str) -> Dependency | InputDependency:
        if isinstance(other, str):
            return InputDependency(self.workflow, self.name, other)
        else:
            return Dependency(self.workflow, self.name, other.workflow, other.name)

    def __rrshift__(self, other: str) -> InputDependency:
        return InputDependency(self.workflow, self.name, other)


@dataclass(frozen=True)
class OutputPort:
    workflow: Workflow
    name: str

    @overload
    def __rshift__(self, other: InputPort) -> Dependency:
        ...

    @overload
    def __rshift__(self, other: str) -> OutputDependency:
        ...

    def __rshift__(self, other: InputPort | str) -> Dependency | OutputDependency:
        if isinstance(other, str):
            return OutputDependency(self.workflow, self.name, other)
        else:
            return Dependency(other.workflow, other.name, self.workflow, self.name)

    def __rlshift__(self, other: str) -> OutputDependency:
        return OutputDependency(self.workflow, self.name, other)


@dataclass(init=False, frozen=True)
class Workflow:
    _pipeline: Pipeline
    _input_targets: frozendict[str, Sequence[TaskParam]]
    _output_sources: frozendict[str, TaskParam]
    name: str
    sig: frozendict[str, InputPort]
    ret: frozendict[str, OutputPort]

    def __init__(
        self,
        name: str,
        pipeline: Pipeline,
        input_targets: Mapping[str, Sequence[TaskParam]],
        output_sources: Mapping[str, TaskParam],
    ) -> None:
        sig = frozendict[str, InputPort](
            {port_name: InputPort(self, port_name) for port_name in input_targets}
        )
        ret = frozendict[str, OutputPort](
            {port_name: OutputPort(self, port_name) for port_name in output_sources}
        )

        object.__setattr__(self, "_pipeline", pipeline)
        object.__setattr__(self, "_input_targets", input_targets)
        object.__setattr__(self, "_output_sources", output_sources)

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "sig", sig)
        object.__setattr__(self, "ret", ret)

    # def __add__(self, workflow: Workflow) -> Workflow:
    #     return self.__class__(self._pipeline + workflow._pipeline)

    # def __contains__(self, node: PNode) -> bool:
    #     return node in self._pipeline

    # def add_dependency(self, dependency: Dependency) -> Workflow:
    #     dp = PDependency(dependency.out_node, dependency.in_param, dependency.out_param)
    #     return self.__class__(self._pipeline.add_dependencies(dependency.in_node, (dp,)))

    def decorate(self, name: str) -> Workflow:
        return self.__class__(
            name=self.name,
            pipeline=self._pipeline.decorate(name),
            input_targets={
                port_name: [target.decorate(name) for target in targets]
                for port_name, targets in self._input_targets.items()
            },
            output_sources={
                port_name: source.decorate(name)
                for port_name, source in self._output_sources.items()
            },
        )

    @property
    def pipeline(self) -> Pipeline:
        return self._pipeline


# @dataclass(init=False, frozen=True)
# class Task(Workflow):
#     def __init__(
#         self,
#         name: str,
#         processor_type: type[IProcess],
#         params_getter: IGetParams,
#     ) -> None:
#         node = {PNode(name): ProcessorProps(processor_type, params_getter)}
#         object.__setattr__(self, "_pipeline", Pipeline(node))


# @dataclass(frozen=True, init=False)
# class Estimator(Workflow):
#     def __init__(
#         self,
#         name: str,
#         train_wf: Workflow,
#         eval_wf: Workflow,
#         shared_params: Sequence[Dependency] = (),
#     ) -> None:
#         tail = TailPipelineClient.build(train_wf.pipeline, eval_wf.pipeline)
#         new_pipeline = WorkflowClient.compose_workflow(
#             workflows=(train_wf, eval_wf, Workflow(tail)), dependencies=shared_params, name=name
#         )
#         object.__setattr__(self, "_pipeline", new_pipeline)


class WorkflowClient:
    @classmethod
    def single_task(
        cls,
        name: str,
        processor_type: type[IProcess],
        params_getter: IGetParams = frozendict[str, Any](),
        compute_reqs: PComputeReqs = PComputeReqs(),
        return_annotation: Mapping[str, OutParameter] | None = None,
    ) -> Workflow:
        props = ProcessorProps(processor_type, params_getter, compute_reqs, return_annotation)
        return cls._single_task_from_props(name, props)
        # return Task(name, processor_type, params_getter)

    @classmethod
    def _single_task_from_props(cls, name: str, processor_props: ProcessorProps) -> Workflow:
        node_name = PNode(name)
        pipeline = Pipeline({node_name: processor_props})
        input_targets = frozendict[str, Sequence[TaskParam]](
            {
                name: [TaskParam(node_name, in_param.name)]
                for name, in_param in processor_props.sig.items()
            }
        )
        output_sources = frozendict[str, TaskParam](
            {
                name: TaskParam(node_name, out_param.name)
                for name, out_param in processor_props.ret.items()
            }
        )
        return Workflow(name, pipeline, input_targets, output_sources)

    # @staticmethod
    # def compose_workflow(
    #     name: str, workflows: Sequence[Workflow], dependencies: Sequence[Dependency]
    # ) -> Workflow:
    #     workflows = list(workflows)
    #     for i in range(len(workflows)):
    #         for dp in dependencies:
    #             if dp.in_node in workflows[i]:
    #                 workflows[i] = workflows[i].add_dependency(dp)  # TODO: duplicate nodes!
    #     return sum(workflows, start=Workflow()).decorate(name)

    @classmethod
    def compose_workflow(
        cls,
        name: str,
        workflows: Sequence[Workflow],
        dependencies: Sequence[Dependency],
        input_dependencies: Optional[Sequence[InputDependency]] = None,
        output_dependencies: Optional[Sequence[OutputDependency]] = None,
    ) -> Workflow:
        pipeline = sum([w.pipeline for w in workflows], start=Pipeline())
        seen_inputs: set[Tuple[str, str]] = set()
        seen_outputs: set[Tuple[str, str]] = set()

        for d in dependencies:
            seen_inputs.add((d.in_workflow.name, d.in_param))
            seen_outputs.add((d.out_workflow.name, d.out_param))
            out_task_param = d.out_workflow._output_sources[d.out_param]
            out_node = out_task_param.node
            out_param = d.out_workflow._pipeline.nodes[out_node].ret[out_task_param.param]
            for in_task_param in d.in_workflow._input_targets[d.in_param]:
                in_node = in_task_param.node
                in_param = pipeline.nodes[in_node].sig[in_task_param.param]
                pd = PDependency(node=out_node, out_arg=out_param, in_arg=in_param)
                pipeline = pipeline.add_dependencies(in_node, [pd])

        input_targets: dict[str, List[TaskParam]] = defaultdict(list)
        if input_dependencies is None:
            input_dependencies = [
                InputDependency(w, port_name, port_name)
                for w in workflows
                for port_name in w.sig
                if (w.name, port_name) not in seen_inputs
            ]
        assert input_dependencies is not None
        accounted_input_targets: set[TaskParam] = set()
        for in_d in input_dependencies:
            targets = in_d.in_workflow._input_targets[in_d.in_param]
            input_targets[in_d.name] += targets
            accounted_input_targets.update(targets)
        expected_input_targets = frozenset((TaskParam(*t) for t in pipeline.unprovided_inputs))
        if len(expected_input_targets - accounted_input_targets) > 0:
            raise ValueError(
                "Missing input dependencies.\n"
                "Please provide input dependencies for the following node inputs:\n"
                f"{expected_input_targets - accounted_input_targets}"
            )

        if output_dependencies is None:
            output_dependencies = [
                OutputDependency(w, port_name, port_name)
                for w in workflows
                for port_name in w.ret
                if (w.name, port_name) not in seen_outputs
            ]
        assert output_dependencies is not None
        output_sources = dict()
        for out_d in output_dependencies:
            if out_d.name in output_sources:
                raise ValueError(
                    f"Multiple output dependecies to the same output port {out_d.name}."
                )
            output_sources[out_d.name] = out_d.out_workflow._output_sources[out_d.out_param]

        return Workflow(name, pipeline, input_targets, output_sources).decorate(name)

    @staticmethod
    def rename_ports(
        workflow: Workflow,
        inputs: Callable[[str], str] | Mapping[str, str] = {},
        outputs: Callable[[str], str] | Mapping[str, str] = {},
    ) -> Workflow:
        def get_rename_func(
            func_to_mapping: Callable[[str], str] | Mapping[str, str]
        ) -> Callable[[str], str]:
            if hasattr(func_to_mapping, "get"):
                mapping = cast(Mapping[str, str], func_to_mapping)

                def func(n: str) -> str:
                    return mapping.get(n, n)

                return func
            else:
                return cast(Callable[[str], str], func_to_mapping)

        inputs_func = get_rename_func(inputs)
        outputs_func = get_rename_func(outputs)
        return Workflow(
            workflow.name,
            workflow._pipeline,
            input_targets={inputs_func(k): v for k, v in workflow._input_targets.items()},
            output_sources={outputs_func(k): v for k, v in workflow._output_sources.items()},
        )


@dataclass(frozen=True)
class XVal(Workflow):
    pass
    # data_splitter


@dataclass(frozen=True)
class HPO(Workflow):
    pass
    # search_space: dict[str, Any]
