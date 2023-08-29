from __future__ import annotations

from collections import ChainMap
from functools import reduce
from itertools import chain
from typing import Any, Mapping, Sequence, TypeAlias, TypeVar, final

from hydra_zen import hydrated_dataclass
from omegaconf import MISSING

from oneml.services import ServiceId

from ..dag import DAG, ComputeReqs, DagDependency, DagNode, IProcess, ProcessorProps
from ..utils import frozendict
from ._ops import DependencyOp
from ._pipeline import (
    InCollections,
    InEntry,
    InParameter,
    Inputs,
    IOCollections,
    OutCollections,
    OutEntry,
    OutParameter,
    Outputs,
    ParamCollection,
    ParamEntry,
    Pipeline,
    PipelineConf,
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
PL = TypeVar("PL", bound=IOCollections[Any])

UserIO = Mapping[str, PE | PC]
UserInput: TypeAlias = UserIO[InEntry, Inputs]
UserOutput: TypeAlias = UserIO[OutEntry, Outputs]


@final
class Task(Pipeline):
    _config: TaskConf

    def __init__(
        self,
        processor_type: type,
        name: str | None = None,
        config: Mapping[str, Any] | None = None,
        services: Mapping[str, ServiceId[Any]] | None = None,
        input_annotation: Mapping[str, type] | None = None,
        return_annotation: Mapping[str, type] | None = None,
        compute_reqs: ComputeReqs = ComputeReqs(),
    ) -> None:
        if not (isinstance(processor_type, type) and callable(getattr(processor_type, "process"))):
            raise ValueError("`processor_type` needs to satisfy the `IProcess` protocol.")
        if name is not None and not isinstance(name, str):
            raise ValueError("`name` needs to be string or None.")
        if not isinstance(compute_reqs, ComputeReqs):
            raise ValueError("`compute_reqs` needs to be `ComputeReqs` object.")
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
            processor_type=processor_type,
            config=config if config is not None else frozendict(),
            services=services if services is not None else frozendict(),
            input_annotation=input_annotation,
            return_annotation=return_annotation,
            compute_reqs=compute_reqs,
        )
        inputs = {k: InEntry((InParameter(node, p),)) for k, p in props.inputs.items()}
        outputs = {k: OutEntry((OutParameter(node, p),)) for k, p in props.outputs.items()}
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
            inputs=Inputs(inputs),
            outputs=Outputs(outputs),
        )


class CombinedPipeline(Pipeline):
    _config: CombinedConf

    def __init__(
        self,
        pipelines: Sequence[Pipeline],
        name: str,
        dependencies: Sequence[DependencyOp] | None = None,
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
        flat_input: tuple[InParameter, ...] = ()
        for uv in inputs.values() if inputs else ():  # flattens user inputs
            if isinstance(uv, InEntry):
                flat_input += tuple(uv)
            elif isinstance(uv, Inputs):
                flat_input += tuple(chain.from_iterable(chain(uv.values())))
            else:
                raise ValueError(f"Invalid input type {uv}.")

        if set(shared_input) & set(flat_input):  # verifies no input is declared in a dependency
            collissions = set(shared_input) & set(flat_input)
            msg = f"Inputs declared as dependencies and inputs: {collissions}"
            raise ValueError(msg)

        if inputs is not None:  # verifies all pipeline inputs have been specified
            pl_input: tuple[InParameter, ...] = ()
            for pl in pipelines:
                pl_input += reduce(lambda x, y: x + tuple(y), pl.inputs.values(), pl_input)
                for c in pl.in_collections.values():
                    pl_input += reduce(lambda x, y: x + tuple(y), c.values(), pl_input)
            if set(pl_input) - set(flat_input) - set(shared_input):
                missing = set(pl_input) - set(flat_input) - set(shared_input)
                msg = f"Not all inputs have been specified as inputs or dependencies: {missing}"
                raise ValueError(msg)

        in_entries = Inputs()  # build inputs
        in_collections = InCollections()
        if inputs is None:  # build default inputs
            for pl in pipelines:
                in_entries |= (pl.inputs - shared_input).decorate(name)
                in_collections |= (pl.in_collections - shared_input).decorate(name)
        else:  # build inputs from user input
            in_entries, in_collections = self._format_io(inputs, in_entries, in_collections)
            in_entries, in_collections = in_entries.decorate(name), in_collections.decorate(name)

        out_entries = Outputs()  # build outputs
        out_collections = OutCollections()
        if outputs is None:  # build default outputs
            for pl in pipelines:
                out_entries |= (pl.outputs - shared_out).decorate(name)
                out_collections |= (pl.out_collections - shared_out).decorate(name)
        else:  # build outputs from user output
            out_entries, out_collections = self._format_io(outputs, out_entries, out_collections)
            out_entries = out_entries.decorate(name)
            out_collections = out_collections.decorate(name)
        gathererd_outputs = self._gather_outputs(out_collections, out_entries, name)
        out_entries, out_collections, out_tasks, out_dependencies = gathererd_outputs

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
            inputs=in_entries,
            outputs=out_entries,
            in_collections=in_collections,
            out_collections=out_collections,
        )

    @staticmethod
    def _format_io(user_io: UserIO[PE, PC], entries: PC, collections: PL) -> tuple[PC, PL]:
        empty_collection = entries.__class__()
        for k, v in user_io.items():
            if k.count(".") > 1:
                raise ValueError(f"Invalid input name {k}.")
            elif k.count(".") == 0 and isinstance(v, ParamEntry):
                entries |= {k: v}  # ParamEntry or ParamCollection.ParamEntry -> ParamEntry
            elif k.count(".") == 1 and isinstance(v, ParamEntry):
                k0, k1 = k.split(".")
                temp_c = collections.get(k0, empty_collection)
                collections |= {k0: temp_c | {k1: v}}  # ParamEntry -> ParamCollection.ParamEntry
            elif k.count(".") == 0 and isinstance(v, ParamCollection):
                collections |= {k: v}  # ParamCollection -> ParamCollection
            elif k.count(".") == 1 and isinstance(v, ParamCollection):
                k0, k1 = k.split(".")  # ParamCollection -> ParamCollection.ParamEntry
                temp_c = collections.get(k0, empty_collection)
                collections |= {k0: temp_c | {k1: reduce(lambda x, y: x | y, v.values())}}
            else:
                raise ValueError(f"Invalid formatting string {k} or input type {v}.")
        return entries, collections

    @staticmethod
    def _gather_outputs(
        out_collections: OutCollections, out_entries: Outputs, name: str
    ) -> tuple[Outputs, OutCollections, tuple[Pipeline, ...], tuple[DependencyOp, ...]]:
        def gathering_tasks(entries: dict[str, OutEntry]) -> dict[str, Pipeline]:
            return {
                en: Task(
                    GatherSequence,
                    name="Gather_" + en,
                    return_annotation={"output": tuple[entry[0].param.annotation, ...]},  # type: ignore[name-defined]
                ).rename_outputs({"output": en})
                for en, entry in entries.items()
            }

        # multiple output entries and collections
        gathered_entries = {k: v for k, v in out_entries.items() if len(v) > 1}
        gathered_collections = {
            k + "." + en: entry
            for k, v in out_collections.items()
            for en, entry in v.items()
            if len(entry) > 1
        }
        gathered_all = ChainMap(gathered_entries, gathered_collections)

        # gathering tasks
        entries_tasks = gathering_tasks(gathered_entries)
        collections_tasks = gathering_tasks(gathered_collections)
        all_tasks = ChainMap(entries_tasks, collections_tasks)

        # dependencies from multiple output entries and collections to gathering tasks
        dependencies = tuple(all_tasks[en].inputs.args << et for en, et in gathered_all.items())

        # output entries and collections
        entries_map = map(lambda x: x.outputs, entries_tasks.values())
        new_entries = reduce(lambda a, b: a | b, entries_map, Outputs())
        new_entries = (out_entries - gathered_entries) | new_entries.decorate(name)

        collections_map = map(lambda x: x.out_collections, collections_tasks.values())
        new_collections = reduce(lambda a, b: a | b, collections_map, OutCollections())
        new_collections = (out_collections - gathered_collections) | new_collections.decorate(name)

        return new_entries, new_collections, tuple(all_tasks.values()), dependencies


class GatherSequence(IProcess):
    def process(self, *args: Any) -> Mapping[str, Sequence[Any]]:
        return {"output": args}


class PipelineBuilder:
    @classmethod
    def task(
        cls,
        processor_type: type,
        name: str | None = None,
        config: Mapping[str, Any] | None = None,
        services: Mapping[str, ServiceId[Any]] | None = None,
        input_annotation: Mapping[str, type] | None = None,
        return_annotation: Mapping[str, type] | None = None,
        compute_reqs: ComputeReqs = ComputeReqs(),
    ) -> Pipeline:
        """Create a single node pipeline wrapping a Processor.

        Args:
            name: Name for the built pipeline.
            processor_type: A class following the IProcess pattern.  See below.
            config: A mapping from (a subset of) the constructor parameters of `processor_type` to
               values.
            services: A mapping from (a subset of) the constructor parameters of `processor_type`
               to ids of OneML services that will provide their value at run time.
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
        be able to take multiple dependecies.  See example below.

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

                eval_standardize = PipelineBuilder.task(
                    name="standardize", processor_type=Standardize
                )

            `predefined_standardize` and `eval_standardize` are single-node pipelines.

            `predefined_standardize` uses predefined standartization parameters, provided by
                `config`.  Its single inputs will be `X`, and at runtime that inputs will be
                provided as an argument to `process`.
            `eval_standardize` uses standartization parameters fitted at run time by an upstream
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
                    name="concat_strings_as_lines",
                    processor_type=ConcatStringsAsLines
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

    @staticmethod
    def combine(
        pipelines: Sequence[Pipeline],
        name: str,
        dependencies: Sequence[DependencyOp] | None = None,
        inputs: UserInput | None = None,
        outputs: UserOutput | None = None,
    ) -> Pipeline:
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
            * include dependenies mapping `w1` outputs `C` to `w2` inputs `D` and `w3` inputs `A` and
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
            * include dependenies mapping `w1` outputs `C` to `w2` inputs `D` and mapping `w2` outputs
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
            * include dependenies mapping
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


@hydrated_dataclass(Task, zen_wrappers=[_processor_type, _input_annotation, _return_annotation])
class TaskConf(PipelineConf):
    processor_type: str = MISSING
    name: str = "${parent_or_processor_name:}"
    config: Any = None
    services: Any = None
    input_annotation: dict[str, str] | None = None
    return_annotation: dict[str, str] | None = None


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
