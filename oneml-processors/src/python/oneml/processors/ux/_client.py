from dataclasses import dataclass
from itertools import chain
from typing import Any, Iterable, Mapping, Sequence, final

from ..dag._dag import DAG, ComputeReqs, DagDependency, DagNode, ProcessorProps
from ..dag._processor import IGetParams, OutProcessorParam
from ..utils._frozendict import frozendict
from ._pipeline import Dependency, InParameter, Pipeline
from ._utils import PipelineIO, PipelineUtils, UserInput, UserOutput


@final
@dataclass(frozen=True, init=False)
class Task(Pipeline):
    def __init__(
        self,
        processor_type: type,
        name: str | None = None,
        params_getter: IGetParams = frozendict[str, Any](),
        compute_reqs: ComputeReqs = ComputeReqs(),
        return_annotation: Mapping[str, OutProcessorParam] | None = None,
    ) -> None:
        name = name if name else processor_type.__name__
        node = DagNode(name)
        props = ProcessorProps(processor_type, params_getter, compute_reqs, return_annotation)
        inputs = PipelineIO.dag_inputs_to_pipeline_inputs(frozendict({node: props.inputs}))
        outs = PipelineIO.dag_outputs_to_pipeline_outputs(frozendict({node: props.outputs}))
        super().__init__(name, DAG({node: props}), inputs, outs)


@dataclass(frozen=True, init=False)
class CombinedPipeline(Pipeline):
    def __init__(
        self,
        *pipelines: Pipeline,
        name: str,
        inputs: UserInput | None = None,
        outputs: UserOutput | None = None,
        dependencies: Iterable[Sequence[Dependency]] = ((),),
    ) -> None:
        if len(set(pl.name for pl in pipelines)) != len(pipelines):
            raise ValueError("Trying to combine pipelines with the same name is not supported.")

        def get_props(node: DagNode) -> ProcessorProps:
            return next(iter(pl.dag.nodes[node] for pl in pipelines if node in pl))

        shared_input = tuple(dp.in_param for dp in chain.from_iterable(dependencies))
        shared_out = tuple(dp.out_param for dp in chain.from_iterable(dependencies))
        provided_input_params = tuple(
            p
            for params in (inputs.values() if inputs else ())
            for p in ((params,) if isinstance(params, InParameter) else params.values())
        )
        if inputs is None:  # build default inputs
            inputs = PipelineUtils.merge_pipeline_inputs(*pipelines, exclude=shared_input)
        elif inputs is not None and not all(  # verifies all worfklow inputs have been specified
            p in provided_input_params
            for pl in pipelines
            for params in pl.inputs.values()
            for p in params.values()
            if p not in shared_input
        ):
            raise ValueError("Not all pipeline inputs have been specified in inputs.")
        if outputs is None:  # build default outputs
            outputs = PipelineUtils.merge_pipeline_outputs(*pipelines, exclude=shared_out)

        dags = [pl.dag for pl in pipelines]
        for dp in chain.from_iterable(dependencies):
            pdp = DagDependency(dp.out_param.node, dp.in_param.param, dp.out_param.param)
            in_node = dp.in_param.node
            dags.append(DAG({in_node: get_props(in_node)}, {in_node: (pdp,)}))
        new_pipeline = sum(dags, start=DAG()).decorate(name)
        inputs = PipelineIO.user_inputs_to_pipeline_inputs(inputs, name, pipelines)
        outputs = PipelineIO.user_outputs_to_pipeline_outputs(outputs, name, pipelines)
        super().__init__(name, new_pipeline, inputs, outputs)


class PipelineBuilder:
    @classmethod
    def task(
        cls,
        name: str,
        processor_type: type,
        params_getter: IGetParams = frozendict[str, Any](),
        compute_reqs: ComputeReqs = ComputeReqs(),
        return_annotation: Mapping[str, OutProcessorParam] | None = None,
    ) -> Pipeline:
        """Create a single node pipeline wrapping a Processor.

        Args:
            name: Name for the built pipeline.
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

        The inputs of the built pipeline will be the union of the constructor and `process`
        parameters of `processor_type`, except for those specified by `params_getter`.

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
                    params_getter=frozendict(shift=10.0, scale=2.0),
                )

                eval_standardize = PipelineBuilder.task(
                    name="standardize", processor_type=Standardize
                )

            `predefined_standardize` and `eval_standardize` are single-node pipelines.

            `predefined_standardize` uses predefined standartization parameters, provided by
                `param_getters`.  Its single inputs will be `X`, and at runtime that inputs will be
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
                    params_getter=frozendict(K=3),
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
        return Task(processor_type, name, params_getter, compute_reqs, return_annotation)

    @staticmethod
    def combine(
        *pipelines: Pipeline,
        name: str,
        inputs: UserInput | None = None,
        outputs: UserOutput | None = None,
        dependencies: Iterable[Sequence[Dependency]] = ((),),
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
            *pipelines, name=name, inputs=inputs, outputs=outputs, dependencies=dependencies
        )