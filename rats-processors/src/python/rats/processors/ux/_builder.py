from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import reduce
from itertools import chain
from typing import Any, Generic, TypeAlias, TypeVar, cast, final

from hydra_zen import hydrated_dataclass
from omegaconf import MISSING

from rats.services import ServiceId

from ..dag import DAG, ComputeReqs, DagDependency, DagNode, IProcess, ProcessorProps
from ..utils import frozendict
from ._ops import DependencyOp
from ._pipeline import (
    InParameter,
    InPort,
    InPorts,
    Inputs,
    OutParameter,
    OutPort,
    Outputs,
    ParamCollection,
    ParamEntry,
    Pipeline,
    PipelineConf,
    TInputs,
    TOutputs,
    UPipeline,
)
from ._utils import (
    _input_annotation,
    _parse_dependencies_to_list,
    _parse_pipelines_to_list,
    _processor_type,
    _return_annotation,
)

PE = TypeVar("PE", bound=ParamEntry[Any])
PC = TypeVar("PC", bound=ParamCollection[Any])

UserIO = Mapping[str, PE | PC]
UserInput: TypeAlias = UserIO[InPort[Any], Inputs]
UserOutput: TypeAlias = UserIO[OutPort[Any], Outputs]


@final
class Task(Pipeline[TInputs, TOutputs]):
    _config: TaskConf

    def __init__(
        self,
        processor_type: type[IProcess] | type,
        name: str | None = None,
        config: Mapping[str, Any] | None = None,
        services: Mapping[str, ServiceId[Any]] | None = None,
        input_annotation: Mapping[str, type] | None = None,
        return_annotation: Mapping[str, type] | None = None,
        compute_reqs: ComputeReqs | None = None,
    ) -> None:
        if not (
            isinstance(processor_type, type) and callable(getattr(processor_type, "process", None))
        ):
            raise ValueError("`processor_type` needs to satisfy the `IProcess` protocol.")
        if name is not None and not isinstance(name, str):
            raise ValueError("`name` needs to be string or None.")
        if compute_reqs is not None and not isinstance(compute_reqs, ComputeReqs):
            raise ValueError("`compute_reqs` needs to be `None` or `ComputeReqs` object.")
        if return_annotation is not None and not (
            isinstance(return_annotation, Mapping)
            and all(
                isinstance(k, str) and isinstance(v, type) for k, v in return_annotation.items()
            )
        ):
            raise ValueError("`return_annotation` needs to be `Mapping[str, type] | None`.")

        name = name if name else processor_type.__name__
        node = DagNode(name)
        props = ProcessorProps(
            processor_type=cast(type[IProcess], processor_type),
            config=config if config is not None else frozendict(),
            services=services if services is not None else frozendict(),
            input_annotation=input_annotation,
            return_annotation=return_annotation,
            compute_reqs=compute_reqs,
        )
        inputs = {k: InPort[Any]((InParameter(node, p),)) for k, p in props.inputs.items()}
        outputs = {k: OutPort[Any]((OutParameter(node, p),)) for k, p in props.outputs.items()}
        task_config = TaskConf(
            name=name,
            processor_type=processor_type.__module__ + "." + processor_type.__name__,
            input_annotation={k: str(v) for k, v in input_annotation.items()}
            if input_annotation is not None
            else None,
            return_annotation={k: str(v) for k, v in return_annotation.items()}
            if return_annotation is not None
            else None,
        )
        super().__init__(
            name=name,
            dag=DAG({node: props}),
            config=task_config,
            inputs=cast(TInputs, Inputs(inputs)),
            outputs=cast(TOutputs, Outputs(outputs)),
        )


UTask = Task[Inputs, Outputs]


@hydrated_dataclass(Task, zen_wrappers=[_processor_type, _input_annotation, _return_annotation])
class TaskConf(PipelineConf):
    processor_type: str = MISSING
    name: str = "${parent_or_processor_name:}"
    config: Any = None
    services: Any = None
    input_annotation: dict[str, str] | None = None
    return_annotation: dict[str, str] | None = None


class CombinedPipeline(Pipeline[TInputs, TOutputs]):
    _config: CombinedConf

    def __init__(
        self,
        pipelines: Sequence[UPipeline],
        name: str,
        dependencies: Sequence[DependencyOp[Any]] | None = None,
        inputs: UserInput | None = None,
        outputs: UserOutput | None = None,
    ) -> None:
        if len(set(pl.name for pl in pipelines)) != len(pipelines):
            raise ValueError("Trying to combine pipelines with the same name is not supported.")

        def get_props(node: DagNode, dags: Sequence[DAG]) -> ProcessorProps:
            return next(iter(dag.nodes[node] for dag in dags if node in dag))

        if dependencies is None:
            dependencies = ()
        shared_input = tuple(dp.in_param for dp in chain.from_iterable(dependencies))
        shared_out = tuple(dp.out_param for dp in chain.from_iterable(dependencies))
        flat_input: tuple[InParameter[Any], ...] = ()
        for uv in inputs.values() if inputs else ():  # flattens user inputs
            if isinstance(uv, InPort):
                flat_input += tuple(uv)
            elif isinstance(uv, InPorts):
                flat_input += tuple(chain.from_iterable(chain(uv._asdict().values())))
            else:
                raise ValueError(f"Invalid input type {uv}.")

        in_collissions = set(shared_input) & set(flat_input)
        if in_collissions:  # verifies no input is declared in a dependency
            msg = f"Inputs declared as dependencies and inputs: {in_collissions}"
            raise ValueError(msg)

        if inputs is not None:  # verifies all pipeline inputs have been specified
            pls_in: tuple[InParameter[Any], ...] = ()
            for pl in pipelines:
                required = (x for x in pl.inputs._asdict().values() if x.required)
                pls_in += reduce(lambda x, y: x + tuple(y), required, pls_in)
            missing = set(pls_in) - set(flat_input) - set(shared_input)
            if missing:
                msg = f"Not all inputs have been specified as inputs or dependencies: {missing}"
                raise ValueError(msg)

        if inputs is None:  # build default inputs
            in_entries = Inputs()
            for pl in pipelines:
                shared_input_strs = pl.inputs._find(*shared_input)
                in_entries |= (pl.inputs - shared_input_strs).decorate(name)
        else:  # build inputs from user input
            in_entries = Inputs(inputs).decorate(name)

        if outputs is None:  # build default outputs
            out_entries = Outputs()
            for pl in pipelines:
                shared_output_str = pl.outputs._find(*shared_out)
                out_entries |= (pl.outputs - shared_output_str).decorate(name)
        else:  # build outputs from user output
            out_entries = Outputs(outputs).decorate(name)
        gathered_outputs = self._gather_outputs(out_entries, name)
        out_entries, out_tasks, out_dependencies = gathered_outputs

        dags = [pl._dag for pl in chain(pipelines, out_tasks)]
        for dp in chain.from_iterable(chain(dependencies, out_dependencies)):
            ddp = DagDependency(dp.out_param.node, dp.in_param.param, dp.out_param.param)
            in_node = dp.in_param.node
            dags.append(DAG({in_node: get_props(in_node, dags)}, {in_node: (ddp,)}))
        new_pl = sum(dags, start=DAG()).decorate(name)

        config = CombinedConf(
            name=name,
            pipelines={pl.name: pl._config for pl in pipelines},
            dependencies={
                f"d{i}": v.get_dependencyopconf(pipelines) for i, v in enumerate(dependencies)
            },
        )
        super().__init__(
            name=name,
            dag=new_pl,
            config=config,
            inputs=cast(TInputs, in_entries),
            outputs=cast(TOutputs, out_entries),
        )

    @staticmethod
    def _gather_outputs(
        outputs: Outputs, name: str
    ) -> tuple[Outputs, tuple[Pipeline[ArgsIn, ArgsOut], ...], tuple[DependencyOp[Any], ...]]:
        # output entries with length > 1
        gathered = {k: v for k, v in outputs._asdict().items() if len(v) > 1}

        # gathering tasks
        tasks = _gathering_tasks(gathered)

        # dependencies from output entries to gathering tasks
        dependencies = tuple(tasks[en].inputs.args << et for en, et in gathered.items())

        # output entries and collections
        new_outs = reduce(lambda a, b: a | b, map(lambda x: x.outputs, tasks.values()), Outputs())
        new_outs = (outputs - gathered) | new_outs.decorate(name)

        return new_outs, tuple(tasks.values()), dependencies


class ArgsIn(Inputs):
    args: InPort[Any]


class ArgsOut(Outputs):
    output: OutPort[tuple[Any]]


class Gather2Tuple(IProcess):
    def process(self, *args: Any) -> dict[str, tuple[Any, ...]]:
        return {"output": args}


def _gathering_tasks(entries: dict[str, OutPort[Any]]) -> dict[str, Pipeline[ArgsIn, ArgsOut]]:
    return {
        en: cast(
            Pipeline[ArgsIn, ArgsOut],
            Task(
                Gather2Tuple,
                name="Gather_" + en,
                return_annotation={"output": tuple[entry[0].param.annotation, ...]},
            ).rename_outputs({"output": en}),
        )
        for en, entry in entries.items()
    }


class PipelineBuilder(Generic[TInputs, TOutputs]):
    @classmethod
    def task(
        cls,
        processor_type: type,
        name: str | None = None,
        config: Mapping[str, Any] | None = None,
        services: Mapping[str, ServiceId[Any]] | None = None,
        input_annotation: Mapping[str, type] | None = None,
        return_annotation: Mapping[str, type] | None = None,
        compute_reqs: ComputeReqs | None = None,
    ) -> Task[TInputs, TOutputs]:
        r"""Create a single node pipeline wrapping a Processor.

        Args:
            name: Name for the built pipeline.
            processor_type: A class following the IProcess pattern.  See below.
            config: A mapping from (a subset of) the constructor parameters of `processor_type` to
               values.
            services: A mapping from (a subset of) the constructor parameters of `processor_type`
               to ids of Rats services that will provide their value at run time.
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

        `config` and `services` should not intersect.

        The inputs of the built pipeline will be the union of the constructor and `process`
        parameters of `processor_type`, except for those specified by either `config` or
        `services`.

        The `process` method may take a variable length parameters (*param). Like any other
        parameter, it will become an inputs to the pipeline. Unlike other inputs, this inputs will
        be able to take multiple dependencies.  See example below.

        If `return_annotation` is given, then it defines the outputs of the built pipeline. It is
        expected that the `process_method` will return a dictionary with the appropriate keys and
        values.

        If `return_annotation` is not given, then the return type annotation of the `process`
        method defines the outputs of the built pipeline.

        Example:
            Statically defined outputs::

                StandardizeOutput = TypedDict("StandardizeOutput", {"Z": float})


                class Standardize(IProcess):
                    def __init__(self, shift: float, scale: float) -> None:
                        self._shift = shift
                        self._scale = scale

                    def process(self, X: Array) -> StandardizeOutput:
                        Z = (X - self._shift) / self._scale
                        return StandardizeOutput({"Z": Z})


                predefined_standardize = PipelineBuilder.task(
                    name="standardize",
                    processor_type=Standardize,
                    config=frozendict(shift=10.0, scale=2.0),
                )

                eval_standardize = PipelineBuilder.task(name="standardize", processor_type=Standardize)

            `predefined_standardize` and `eval_standardize` are single-node pipelines.

            `predefined_standardize` uses predefined standardization parameters, provided by
                `config`.  Its single inputs will be `X`, and at runtime that inputs will be
                provided as an argument to `process`.
            `eval_standardize` uses standardization parameters fitted at run time by an upstream
                pipeline.  Its inputs will be `scale` and `shift` that will be provided at runtime
                as constructor arguments, and `X` that will be provided at runtime as an argument
                to `process`.

            The outputs of both pipelines are defined in the outputs annotation of `process`, i.e.
                by `StandardizeOutput`.  Both pipelines will have a single outputs, `Z`, which is
                expected, at run time, to be a key in the dictionary returned by `process`.

        Example:
            Pipeline build defined outputs::

                class Scatter:
                    def __init__(self, K: int) -> None:
                        self._K = K

                    @classmethod
                    def get_return_annotation(cls, K: int) -> Dict[str, OutProcessorParam]:
                        out_names = [f"in1_{k}" for k in range(K)] + [f"in2_{k}" for k in range(K)]
                        return {out_name: OutProcessorParam(out_name, str) for out_name in out_names}

                    def process(self, in1: str, in2: str) -> Dict[str, str]:
                        return {f"in1_{k}": f"{in1}_{k}" for k in range(self._K)} | {
                            f"in2_{k}": f"{in2}_{k}" for k in range(self._K)
                        }

                scatter = PipelineBuilder.task(
                    name="scatter",
                    processor_type=Scatter,
                    config=frozendict(K=3),
                    return_annotation=Scatter.get_return_annotation(3)
                )
            `scatter` is a single node pipeline with two inputs: `in1` and `in2`.

            Its outputs are defined by `return_annotation` to be `in1_0`, `in1_1`, `in1_2`,
                `in2_0`, `in2_1`, `in2_2`.

        Example:
            Pipeline with inputs accepting multiple dependencies::

                ConcatStringsAsLinesOutput = TypedDict("ConcatStringsAsLinesOutput", {"out": str})


                class ConcatStringsAsLines:
                    def process(self, *inp: str) -> ConcatStringsAsLinesOutput:
                        return ConcatStringsAsLinesOutput(out="\n".join(inp))


                concat_strings_as_lines = PipelineBuilder.task(
                    name="concat_strings_as_lines", processor_type=ConcatStringsAsLines
                )

            `concat_strings_as_lines` is a single node pipeline with one inputs - `inp` and one
                outputs - `out`.  `inp` accepts multiple dependencies.  See
                `PipelineBuilder.combine` how to define dependencies.

        """
        return Task(
            processor_type=processor_type,
            name=name,
            config=config,
            services=services,
            input_annotation=input_annotation,
            return_annotation=return_annotation,
            compute_reqs=compute_reqs,
        )

    @classmethod
    def combine(
        cls,
        pipelines: Sequence[UPipeline],
        name: str,
        dependencies: Sequence[DependencyOp[Any]] | None = None,
        inputs: UserInput | None = None,
        outputs: UserOutput | None = None,
    ) -> Pipeline[TInputs, TOutputs]:
        """Combine multiple pipelines into one pipeline.

        Args:
            name: Name for the built pipeline.
            pipelines: The pipelines to combine.  Verified to have distinct names.
            dependencies: Each dependency maps an outputs of one of the combined pipelines to an
                inputs of another. See below for syntax.
            input_dependencies: Defines the inputs to the built pipeline, and the mapping of each
                one of them to an inputs of one or more of the combined pipelines. See below for
                syntax and for behaviour when not given.
            output_dependencies: Each outputs dependency defines an outputs of the built pipeline and
                maps an outputs of a one of the combined pipelines to that combined pipeline outputs.
                Verified to not define the same outputs twice. See below for syntax and for
                behaviour when not given.

        All inputs to all combined pipelines must be covered by one and only one dependency or
            inputs dependency.

        Example:
            Assuming the following:
            * `w1` is a pipeline with inputs `A` and `B` and outputs `C`
            * `w2` is a pipeline with inputs `D` and outputs `E` and `F`
            * `w3` is a pipeline with inputs `A` and `G` and outputs `H`
            * `w4` is a pipeline with inputs `A` and outputs `E`

            Parallel pipelines with no dependencies and default inputs and outputs::

                combined = PipelineBuilder.combine(w1, w2, name="combined")

            `combined` will:
            * not include any dependencies between `w1` and `w2`.
            * have inputs `A`, `B` and `D`, mapped to `w1` inputs `A`, `w1` inputs `B` and `w2` inputs
                `D` respectively.
            * have outputs `C`, `E` and `F`, mapped from `w1` outputs `C`, `w2` outputs `E` and `w2`
                outputs `F` respectively.

            Specifying dependencies and using default inputs and outputs::

                combined = PipelineBuilder.combine(
                    w1,
                    w2,
                    w3,
                    name="combined",
                    dependencies=(
                        w1.outputs.C >> w2.inputs.D,
                        w1.outputs.C >> w3.inputs.A,
                        w2.outputs.E >> w3.inputs.G,
                    ),
                )

            `combined` will:
            * include dependencies mapping `w1` outputs `C` to `w2` inputs `D` and `w3` inputs `A` and
                mapping `w2` outputs `E` to `w3` inputs `G`.
            * have inputs `A` and `B`, mapped to `w1` inputs `A` and `B` respectively.
            * have outputs `F` and `H`, mapped from `w2` outputs `F` and `w3` outputs `H`
                respectively.

            Specifying dependencies, using default inputs and outputs, where the
                same inputs is mapped to multiple composed pipelines::

                combined = PipelineBuilder.combine(
                    w1,
                    w2,
                    w3,
                    name="combined",
                    dependencies=(
                        w1.outputs.C >> w2.inputs.D,
                        w2.outputs.E >> w3.inputs.G,
                    ),
                )

            `combined` will:
            * include dependencies mapping `w1` outputs `C` to `w2` inputs `D` and mapping `w2` outputs
                `E` to `w3` inputs `G`.
            * have inputs `A` and `B`, `A` mapped to `w1` inputs `A` and `w3` inputs `A`, and `B`
                mapped to `w1` inputs `B`.
            * have outputs `F` and `H`, mapped from `w2` outputs `F` and `w3` outputs `H`
                respectively.

            Specifying dependencies, inputs-dependencies and outputs-dependencies::

                combined = PipelineBuilder.combine(
                    w1,
                    w2,
                    w3,
                    w4,
                    name="combined",
                    dependencies=(
                        w1.outputs.C >> w2.inputs.D,
                        w1.outputs.C >> w3.inputs.A,
                        w2.outputs.E >> w3.inputs.G,
                        w2.outputs.E >> w4.inputs.A,
                    ),
                    inputs={
                        "a1": w1.inputs.A,
                        "b": w1.inputs.B,
                        "a2": w3.inputs.A,
                    },
                    outputs={"c": w1.outputs.C, "h": w3.outputs.H, "e": w4.outputs.E},
                )

            `combined` will:
            * include dependencies mapping
            * * `w1` outputs `C` to `w2` inputs `D` and `w3` inputs `A`.
            * * `w2` outputs `E` to `w3` inputs `G` and `w4` inputs `A`.
            * have inputs `a1`, `b`, and `a2` mapped to `w1` inputs `A` and `w1` inputs `B`, and `w3`
                inputs `A` respectively.
            * have outputs `c`, `h` and `e`, mapped from `w1` outputs `C`, `w3` outputs `H` and `w4`
                outputs `E` respectively.  Note that `w1` outputs `C` is used as a source of internal
                and outputs dependencies, and that `w2` outputs `F` is not used.

            The definition of `error_combined` will raise ValueError because `w1` inputs `B` is not
                provided. The definition of `mitigated_combined` mitigates the error::

                error_combined = = PipelineBuilder.combine(
                    w1,
                    w2,
                    name="combined",
                    dependencies=(w1.outputs.C >> w2.inputs.D,),
                    inputs={"a": w1.inputs.A},
                )

                mitigated_combined = PipelineBuilder.combine(
                    w1,
                    w2,
                    name="combined",
                    dependencies=(w1.outputs.C >> w2.inputs.D,),
                    inputs={
                        "a": w1.inputs.A,
                        "b": w1.inputs.B,
                    },
                )


             The following pipelines won't rise an error because there is no collision on outputs:

                combined = PipelineBuilder.combine(w2, w4, name="combined")
                combined = PipelineBuilder.combine(
                    w2, w4, name="combined", outputs={"e": w2.outputs.E}
                )
        """
        return CombinedPipeline(
            pipelines, name=name, inputs=inputs, outputs=outputs, dependencies=dependencies
        )


UPipelineBuilder = PipelineBuilder[Inputs, Outputs]


@hydrated_dataclass(
    CombinedPipeline,
    zen_wrappers=[
        "${parse_dependencies: ${..dependencies}}",
        _parse_pipelines_to_list,
        _parse_dependencies_to_list,
    ],
)
class CombinedConf(PipelineConf):
    pipelines: Any = MISSING
    name: str = MISSING
    dependencies: Any = None
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
