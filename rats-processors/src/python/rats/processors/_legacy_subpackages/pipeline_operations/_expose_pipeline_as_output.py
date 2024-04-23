from rats.processors._legacy_subpackages.ux import (
    UPipeline,
    UPipelineBuilder,
    ensure_non_clashing_pipeline_names,
)

from ._expose_given_outputs import ExposeGivenOutputs


class ExposePipelineAsOutput:
    _expose_given_outputs: ExposeGivenOutputs

    def __init__(
        self,
        expose_given_outputs: ExposeGivenOutputs,
    ):
        self._expose_given_outputs = expose_given_outputs

    def _expose_self_pipeline(self, pipeline: UPipeline) -> UPipeline:
        if "pipeline" in pipeline.outputs:
            raise ValueError(
                "pipeline already has an output called `pipeline`. Rename before calling "
                + "ExposePipelineAsOutput."
            )
        expose_pipeline_pl = self._expose_given_outputs(outputs={"pipeline": pipeline})
        expose_pipeline_pl, pipeline = ensure_non_clashing_pipeline_names(
            expose_pipeline_pl, pipeline
        )
        pl = UPipelineBuilder.combine(
            [expose_pipeline_pl, pipeline],
            name=pipeline.name,
        )
        return pl

    def __call__(self, pipeline: UPipeline) -> UPipeline:
        """Add an output called `pipeline` that will expose the pipeline provided.

        Add that output to the collection outputs_to_save and call LoadInputsSaveOutputs to
        persist the pipeline (along with any other outputs in outputs_to_save).

        Given pipeline must not have an output called `pipeline`.
        """
        return self._expose_self_pipeline(pipeline)
