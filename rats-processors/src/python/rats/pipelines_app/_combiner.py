from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, Protocol

from rats.processors import ux


class IPipelineCombiner(Protocol):
    @abstractmethod
    def __call__(
        self,
        pipelines: Sequence[ux.UPipeline],
        name: str | None = None,
        dependencies: Sequence[ux.DependencyOp[Any]] | None = None,
        inputs: ux.UserInput | None = None,
        outputs: ux.UserOutput | None = None,
    ) -> ux.UPipeline:
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
