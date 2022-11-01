from __future__ import annotations

from collections import Counter, defaultdict
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

    def __repr__(self) -> str:
        return f"{self.workflow.name}.{self.name}"


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

    def __repr__(self) -> str:
        return f"{self.workflow.name}.{self.name}"


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
        """Create a single node workflow wrapping a Processor.

        Args:
            name: Name for the built workflow.
            processor_type: A class following the IProcess pattern.  See below.
            params_getter: A hashable mapping providing values to (a subset of) the constructor
              parameters of `processor_type`.
            compute_reqs: TBD
            return_annotation: overrides the static return annotation of `processor_type.process`.

        processor_type should be a class following the IProcess pattern, i.e.:
        * Should have a `process` method.
        * The parameters of the `process` method are type-annotated.
        * The return type of the `process` method should be annotated, and should be either a
          `TypeDict` or a `Dict[str, *]`.  In the latter case, `return_annotation` should be
          provided.
        * Could have a constructor (`__init__` or `__new__`).
        * The parameters of the constructor are type-annotated.

        The inputs of the built workflow will be the union of the constructor and `process`
        parameters of `processor_type`, except for those specified by `params_getter`.

        The `process` method may take a variable length parameters (*param). Like any other
        parameter, it will become an input to the workflow. Unlike other inputs, this input will
        be able to take multiple dependecies.  See example below.

        If `return_annotation` is given, then it defines the outputs of the built workflow. It is
        expected that the `process_method` will return a dictionary with the appropriate keys and
        values.

        If `return_annotation` is not given, then the return type annotation of the `process`
        method defines the outputs of the built workflow.

        Example:
            Statically defined outputs::

                StandardizeOutput = TypedDict("StandardizeOutput", {"Z": Array})


                class Standardize(IProcess):
                    def __init__(self, shift: float, scale: float) -> None:
                        self._shift = shift
                        self._scale = scale

                    def process(self, X: Array) -> StandardizeOutput:
                        Z = (X - self._shift) / self._scale
                        return StandardizeOutput({"Z": Z})

                predefined_standardize = WorkflowClient.single_task(
                    name="standardize",
                    processor_type=Standardize,
                    params_getter=frozendict(
                        shift=10.0,
                        scale=2.0,
                    ),
                )

                eval_standardize = WorkflowClient.single_task(
                    name="standardize",
                    processor_type=Standardize,
                    params_getter=frozendict()
                )

            `predefined_standardize` and `eval_standardize` are single-node workflows.

            `predefined_standardize` uses predefined standartization parameters, provided by
                `param_getters`.  Its single input will be `X`, and at runtime that input will be
                provided as an argument to `process`.
            `eval_standardize` uses standartization parameters fitted at run time by an upstream
                workflow.  Its inputs will be `scale` and `shift` that will be provided at runtime
                as constructor arguments, and `X` that will be provided at runtime as an argument
                to `process`.

            The outputs of both workflows are defined in the output annotation of `process`, i.e.
                by `StandardizeOutput`.  Both workflows will have a single output, `Z`, which is
                expected, at run time, to be a key in the dictionary returned by `process`.

        Example:
            Workflow build defined outputs::

                class Scatter:
                    def __init__(self, K: int) -> None:
                        self._K = K

                    @classmethod
                    def get_return_annotation(cls, K: int) -> Dict[str, OutParameter]:
                        out_names = [f"in1_{k}" for k in range(K)] + [f"in2_{k}" for k in range(K)]
                        return {out_name: OutParameter(out_name, str) for out_name in out_names}

                    def process(self, in1: str, in2: str) -> Dict[str, str]:
                        return {f"in1_{k}": f"{in1}_{k}" for k in range(self._K)} | {
                            f"in2_{k}": f"{in2}_{k}" for k in range(self._K)
                        }

                scatter = WorkflowClient.single_task(
                    name="scatter",
                    processor_type=Scatter,
                    params_getter=frozendict(K=3),
                    return_annotation=Scatter.get_return_annotation(3)
                )
            `scatter` is a single node workflow with two inputs: `in1` and `in2`.

            Its outputs are defined by `return_annotation` to be `in1_0`, `in1_1`, `in1_2`,
                `in2_0`, `in2_1`, `in2_2`.

        Example:
            Workflow with input accepting multiple dependencies::

                ConcatStringsAsLinesOutput = TypedDict("ConcatStringsAsLinesOutput", {"out": str})


                class ConcatStringsAsLines:
                    def process(self, *inp: str) -> ConcatStringsAsLinesOutput:
                        return ConcatStringsAsLinesOutput(out="\n".join(inp))

                concat_strings_as_lines = WorkflowClient.single_task(
                    name="concat_strings_as_lines",
                    processor_type=ConcatStringsAsLines
                )

            `concat_strings_as_lines` is a single node workflow with one input - `inp` and one
                output - `out`.  `inp` accepts multiple dependencies.  See
                `WorkflowClient.compose_workflow` how to define dependencies.

        """
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
        dependencies: Sequence[Dependency] = tuple(),
        input_dependencies: Optional[Sequence[InputDependency]] = None,
        output_dependencies: Optional[Sequence[OutputDependency]] = None,
    ) -> Workflow:
        """Combine multiple workflows into one workflow.

        Args:
            name: Name for the built workflow.
            workflows: The workflows to combine.  Verified to have distinct names.
            dependencies: Each dependency maps an output of one of the combined workflows to an
                input of another. See below for syntax.
            input_dependencies: Defines the inputs to the built workflow, and the mapping of each
                one of them to an input of one or more of the combined workflows. See below for
                syntax and for behaviour when not given.
            output_dependencies: Each output dependency defines an output of the built workflow and
                maps an output of a one of the combined workflows to that combined workflow output.
                Verified to not define the same output twice. See below for syntax and for
                behaviour when not given.

        All inputs to all combined workflows must be covered by one and only one dependency or
            input dependency.

        Example:
            Assuming the following:
            * `w1` is a workflow with inputs `A` and `B` and output `C`
            * `w2` is a workflow with input `D` and outputs `E` and `F`
            * `w3` is a workflow with inputs `A` and `G` and outputs `H`
            * `w4` is a workflow with input `A` and outputs `E`

            Parallel workflows with no dependencies and default inputs and outputs::

                combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w1, w2))

            `combined` will:
            * not include any dependencies between `w1` and `w2`.
            * have inputs `A`, `B` and `D`, mapped to `w1` input `A`, `w1` input `B` and `w2` input
                `D` respectively.
            * have outputs `C`, `E` and `F`, mapped from `w1` output `C`, `w2` output `E` and `w2`
                output `F` respectively.

            Specifying dependencies and using default inputs and outputs::

                combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w1, w2, w3),
                    dependencies=(
                        w1.ret.C >> w2.sig.D,
                        w1.ret.C >> w3.sig.A,
                        w2.ret.E >> w3.sig.G,
                    ),
                )

            `combined` will:
            * include dependenies mapping `w1` output `C` to `w2` input `D` and `w3` input `A` and
                mapping `w2` output `E` to `w3` input `G`.
            * have inputs `A` and `B`, mapped to `w1` inputs `A` and `B` respectively.
            * have outputs `F` and `H`, mapped from `w2` output `F` and `w3` output `H`
                respectively.

            Specifying dependencies, using default inputs and outputs, where the
                same input is mapped to multiple composed workflows::

                combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w1, w2, w3),
                    dependencies=(
                        w1.ret.C >> w2.sig.D,
                        w2.ret.E >> w3.sig.G,
                    ),
                )

            `combined` will:
            * include dependenies mapping `w1` output `C` to `w2` input `D` and mapping `w2` output
                `E` to `w3` input `G`.
            * have inputs `A` and `B`, `A` mapped to `w1` input `A` and `w3` input `A`, and `B`
                mapped to `w1` input `B`.
            * have outputs `F` and `H`, mapped from `w2` output `F` and `w3` output `H`
                respectively.

            Specifying dependencies, input-dependencies and output-dependencies::

                combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w1, w2, w3, w4),
                    dependencies=(
                        w1.ret.C >> w2.sig.D,
                        w1.ret.C >> w3.sig.A,
                        w2.ret.E >> w3.sig.G,
                        w2.ret.E >> w4.sig.A,
                    ),
                    input_dependencies=(
                        "a1" >> w1.sig.A,
                        "b" >> w1.sig.B,
                        "a2" >> w3.sig.A,
                    ),
                    output_dependencies=(
                        w1.ret.C >> "c",
                        w3.ret.H >> "h",
                        w4.ret.E >> "e",
                    ),
                )

            `combined` will:
            * include dependenies mapping
            * * `w1` output `C` to `w2` input `D` and `w3` input `A`.
            * * `w2` output `E` to `w3` input `G` and `w4` input `A`.
            * have inputs `a1`, `b`, and `a2` mapped to `w1` input `A` and `w1` input `B`, and `w3`
                input `A` respectively.
            * have outputs `c`, `h` and `e`, mapped from `w1` output `C`, `w3` output `H` and `w4`
                output `E` respectively.  Note that `w1` output `C` is used as a source of internal
                and output dependencies, and that `w2` output `F` is not used.

            The definition of `error_combined` will raise ValueError because `w1` input `B` is not
                provided. The definition of `mitigated_combined` mitigates the error::

                error_combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w1, w2),
                    dependencies=(
                        w1.ret.C >> w2.sig.D,
                    ),
                    input_dependencies=(
                        "a" >> w1.sig.A,
                    )
                )

                mitigated_combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w1, w2),
                    dependencies=(
                        w1.ret.C >> w2.sig.D,
                    ),
                    input_dependencies=(
                        "a" >> w1.sig.A,
                        "b" >> w1.sig.B,
                    )
                )


             The definition of `error_combined` will raise ValueError because the default outputs
                include multiple definitions of output `E`. The definition of
                `mitigated_combined` mitigates the error::

                error_combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w2, w4),
                )

                mitigated_combined = WorkflowClient.compose_workflow(
                    name="combined",
                    workflows=(w2, w4),
                    output_dependencies=(
                        w2.ret.E >> "e",
                    )
                )
        """
        name_counts = Counter((w.name for w in workflows))
        if max(name_counts.values()) > 1:
            repeated_names = ", ".join([name for name, c in name_counts.items() if c > 1])
            raise ValueError(
                "Given workflows must have distinct names, but the following names were repeated: "
                f"{repeated_names}."
            )

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
    def rename(
        workflow: Workflow,
        name: Optional[str] = None,
        inputs: Callable[[str], str] | Mapping[str, str] = {},
        outputs: Callable[[str], str] | Mapping[str, str] = {},
    ) -> Workflow:
        """Rename workflow and/or workflow ports.

        Args:
            name: Name for built workflow. If not given, original name is used.
            inputs: Either a function taking original input name and returning new name, or a
                mapping from original input name to new name.  If a mapping, then original input
                names that are not in the mapping are kept without renaming.
            outputs: Either a function taking original output name and returning new name, or a
                mapping from original output name to new name.  If a mapping, then original output
                names that are not in the mapping are kept without renaming.
        """

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
            name or workflow.name,
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
