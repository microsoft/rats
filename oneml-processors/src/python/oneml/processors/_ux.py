from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, List, Mapping, Optional, Sequence, Tuple, cast, overload

from ._environment_singletons import (
    EmptyParamsFromEnvironmentContract,
    IParamsFromEnvironmentSingletonsContract,
)
from ._frozendict import frozendict
from ._frozendict_with_attr_access import FrozenDictWithAttrAccess
from ._pipeline import (
    IProcessorProps,
    KnownParamsGetter,
    PDependency,
    Pipeline,
    PNode,
    ProcessorProps,
)
from ._processor import IHashableGetParams, IProcess


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
    sig: FrozenDictWithAttrAccess[InputPort]
    ret: FrozenDictWithAttrAccess[OutputPort]

    def __init__(
        self,
        name: str,
        pipeline: Pipeline,
        input_targets: Mapping[str, Sequence[TaskParam]],
        output_sources: Mapping[str, TaskParam],
    ) -> None:
        sig = FrozenDictWithAttrAccess[InputPort](
            {port_name: InputPort(self, port_name) for port_name in input_targets}
        )
        ret = FrozenDictWithAttrAccess[OutputPort](
            {port_name: OutputPort(self, port_name) for port_name in output_sources}
        )

        object.__setattr__(self, "_pipeline", pipeline)
        object.__setattr__(self, "_input_targets", input_targets)
        object.__setattr__(self, "_output_sources", output_sources)

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "sig", sig)
        object.__setattr__(self, "ret", ret)

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


class WorkflowClient:
    @classmethod
    def single_task(
        cls,
        name: str,
        processor_type: type[IProcess],
        param_getter: IHashableGetParams = KnownParamsGetter(),
        params_from_environment_contract: IParamsFromEnvironmentSingletonsContract = (
            EmptyParamsFromEnvironmentContract()
        ),
    ) -> Workflow:
        props = ProcessorProps(processor_type, param_getter, params_from_environment_contract)
        return cls.single_task_from_props(name, props)

    @classmethod
    def single_task_from_props(cls, name: str, processor_props: IProcessorProps) -> Workflow:
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
        seen_inputs = set[Tuple[str, str]]()
        seen_outputs = set[Tuple[str, str]]()

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

        input_targets = defaultdict[str, List[TaskParam]](list)
        if input_dependencies is None:
            input_dependencies = [
                InputDependency(w, port_name, port_name)
                for w in workflows
                for port_name in w.sig
                if (w.name, port_name) not in seen_inputs
            ]
        assert input_dependencies is not None
        accounted_input_targets = set[TaskParam]()
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
