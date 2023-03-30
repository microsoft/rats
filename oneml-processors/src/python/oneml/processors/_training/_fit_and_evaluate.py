"""
    A FitAndEvaluate is a pipeline that fits using train data and evaluates on that same train data
    and on a separate eval data.
    A FitAndEvaluate pipeline takes collection inputs with `train` `eval` entries, and outputs
    collection outputs with `train` `eval` entries.  It also outputs the fitted models as output
    entries.

"""
from collections import ChainMap
from itertools import chain
from typing import Sequence

from ..ux import DependencyOp, Pipeline, PipelineBuilder


class FitAndEvaluateBuilders:
    """Builders for FitAndEvaluate pipelines.

    A FitAndEvaluate is a pipeline that fits using train data and evaluates on that same train data
    and on a separate eval data.
    A FitAndEvaluate pipeline takes collection inputs with `train` `eval` entries, and outputs
    collection outputs with `train` `eval` entries.  It also outputs the fitted models as output
    entries.
    """

    @classmethod
    def build_when_fit_evaluates_on_train(
        cls,
        estimator_name: str,
        fit_pipeline: Pipeline,
        eval_pipeline: Pipeline,
        dependencies: Sequence[DependencyOp] = (),
    ) -> Pipeline:
        """Builds a FitAndEvaluate pipeline when the fit pipeline also evaluates train data.

        Args:
        * estimator_name: name for the built pipeline.
        * fit_pipeline: A pipeline that takes data, fits parameters to it, and evaluates the data
          using these fitted parameters.  Inputs and outputs are assumed to be entires, not
          collections.
        * eval_pipeline: A pipeline that takes fitted parameters and data, and evaluates the data
          using these fitted parameters.  Inputs and outputs are assumed to be entires, not
          collections.
        * dependencies: A sequence of dependencies mapping the fitted parameters from fit_pipeline
          outputs to eval_pipeline inputs.
        Returns:
          A pipeline that meets the FitAndEvaluate pattern.
          * Inputs to `fit_pipeline` and `eval_pipeline`, except those indicated in `dependencies`
            become collection inputs, with `train` entries going to `fit_pipeline` and `eval`
            entries going to `eval_pipeline.
          * Outputs from `fit_pipeline` and `eval_pipeline`, except those indicated in
            `dependencies` become collection outputs, with `train` entries comming from
            `fit_pipeline` and `eval` entries comming from `eval_pipeline`.
          * Fitted parameter, i.e. outputs of `fit_pipeline` that are indicated in `dependencies`
            becomes outputs of the built pipeline.

        Example:
          Assuming
          * `fit` is a pipeline taking a vector `X` and returning fitted scalars `mean`
            and `std` and standardized array `Z`.
          * `eval` is a pipeline taking scalars `offset` and `scale` and vector `X` and
            returning standardized array `Z`.
          ```python
          w = FitAndEvaluateBuilders(
                  "standardize", fit, eval,
                  (fit.outputs.mean >> eval.inputs.offset,
                   fit.outputs.std >> eval.inputs.scale,))
          ```
          Would create `w` as a worfkflow with the following input and outputs:
          * Inputs: `X` (`X.train`, `X.eval`).
          * Outputs: `Z` (`Z.train`, `Z.eval`), `mean`, `std`.
        """
        fitted_names_in_fit = frozenset(
            dp.out_param.param.name for dp in chain.from_iterable(dependencies)
        )
        fitted_names_in_eval = frozenset(
            dp.in_param.param.name for dp in chain.from_iterable(dependencies)
        )
        pipeline = PipelineBuilder.combine(
            pipelines=[fit_pipeline, eval_pipeline],
            dependencies=dependencies,
            name=estimator_name,
            inputs=ChainMap(
                {f"{n}.train": fit_pipeline.inputs[n] for n in fit_pipeline.inputs},
                {
                    f"{n}.eval": eval_pipeline.inputs[n]
                    for n in eval_pipeline.inputs
                    if n not in (fn for fn in fitted_names_in_eval)
                },
            ),
            outputs=ChainMap(
                {
                    f"{n}.train": fit_pipeline.outputs[n]
                    for n in fit_pipeline.outputs
                    if n not in (fn for fn in fitted_names_in_fit)
                },
                {f"{n}.eval": eval_pipeline.outputs[n] for n in eval_pipeline.outputs},
                {n: fit_pipeline.outputs[n] for n in (fn for fn in fitted_names_in_fit)},
            ),
        )
        return pipeline

    @classmethod
    def build_using_fit_and_two_evals(
        cls,
        estimator_name: str,
        fit_pipeline: Pipeline,
        train_eval_pipeline: Pipeline,
        eval_eval_pipeline: Pipeline,
    ) -> Pipeline:
        """Builds a FitAndEvaluate pipeline, supporting different eval on train and eval data.

        Args:
        * estimator_name: ename for the built pipeline.
        * fit_pipeline: A pipeline that takes data, and outputs models/parameters fitted from the
          data.  Inputs and outputs are assumed to be entires, not collections.
        * train_eval_pipeline: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          train data.  Inputs and outputs are assumed to be entires, not collections.
        * eval_eval_pipeline: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          eval data.    Inputs and outputs are assumed to be entires, not collections.

        All outputs of `fit_pipeline` are assumed to be fitted models/parameters.

        This builder uses names to match inputs/outputs across the given pipelines, in the
        following ways:
        1. Inputs of `fit_pipeline` and `train_eval_pipeline` that share the same name, e.g. X
          become a single inputs to the built pipeline (X.train).  That inputs is passed as X to
          both `fit_pipeline` and `train_eval_pipeline`.
        2. Outputs of `fit_pipeline` are matched to inputs of `train_eval_pipeline` and
          `eval_eval_pipeline` by name, and passed accordingly.

        Returns:
          A pipeline that meets the FitAndEvaluate pattern.
          * Outputs of `fit_pipeline` that match to inputs of `train_eval_pipeline` or
            `eval_eval_pipeline` by name, are assumed to be fitted parameters.  Each such fitted
            parameter is piped from the output of `fit_pipeline` to the input of
            `train_eval_pipeline` and/or `eval_eval_pipeline`, and also exposed as an output of
            the FitAndEvaluate pipeline.
          * Inputs of either of the three pipelines, except those identified as fitted parameters,
            become collection inputs, with `train` entries going to `fit_pipeline` and
            `train_eval_pipeline`, and `eval` entries going to `eval_eval_pipeline`.
          * Outputs of `train_eval_pipeline` and `eval_eval_pipeline` become collection outputs,
            with `train` entries coming from `train_eval_pipeline` and `eval` entries coming from
            `eval_eval_pipeline`.
        """
        fitted_params_used_by_train_eval = frozenset(fit_pipeline.outputs) & frozenset(
            train_eval_pipeline.inputs
        )
        fitted_params_used_by_eval_eval = frozenset(fit_pipeline.outputs) & frozenset(
            eval_eval_pipeline.inputs
        )
        inputs_used_by_train_eval = (
            frozenset(train_eval_pipeline.inputs) - fitted_params_used_by_train_eval
        )
        inputs_used_by_eval_eval = (
            frozenset(eval_eval_pipeline.inputs) - fitted_params_used_by_eval_eval
        )
        pipeline = PipelineBuilder.combine(
            pipelines=[fit_pipeline, train_eval_pipeline, eval_eval_pipeline],
            name=estimator_name,
            dependencies=(
                tuple(
                    fit_pipeline.outputs[n] >> train_eval_pipeline.inputs[n]
                    for n in fitted_params_used_by_train_eval
                )
                + tuple(
                    fit_pipeline.outputs[n] >> eval_eval_pipeline.inputs[n]
                    for n in fitted_params_used_by_eval_eval
                )
            ),
            inputs=ChainMap(
                {
                    f"{n}.train": fit_pipeline.inputs[n]
                    for n in frozenset(fit_pipeline.inputs) - inputs_used_by_train_eval
                },
                {
                    f"{n}.train": train_eval_pipeline.inputs[n]
                    for n in inputs_used_by_train_eval - frozenset(fit_pipeline.inputs)
                },
                {
                    f"{n}.train": fit_pipeline.inputs[n] | train_eval_pipeline.inputs[n]
                    for n in frozenset(fit_pipeline.inputs) & inputs_used_by_train_eval
                },
                {f"{n}.eval": eval_eval_pipeline.inputs[n] for n in inputs_used_by_eval_eval},
            ),
            outputs=ChainMap(
                {
                    f"{n}.train": train_eval_pipeline.outputs[n]
                    for n in train_eval_pipeline.outputs
                },
                {f"{n}.eval": eval_eval_pipeline.outputs[n] for n in eval_eval_pipeline.outputs},
                {n: fit_pipeline.outputs[n] for n in fit_pipeline.outputs},
            ),
        )
        return pipeline

    @classmethod
    def build_using_eval_on_train_and_eval(
        cls,
        estimator_name: str,
        fit_pipeline: Pipeline,
        eval_pipeline: Pipeline,
    ) -> Pipeline:
        """Builds a FitAndEvaluate pipeline from a fit pipeline and an eval worflow.

        Args:
        * estimator_name: ename for the built pipeline.
        * fit_pipeline: A pipeline that takes data, and outputs models/parameters fitted from the
          data.  Inputs and outputs are assumed to be entires, not collections.
        * eval_pipeline: A pipeline that takes fitted models/parameters and data, and evaluates the
          data using these fitted parameters.  Will be used on both train data and eval data.
          Inputs and outputs are assumed to be entires, not collections.

        All outputs of `fit_pipeline` are assumed to be fitted models/parameters.

        `eval_pipeline` is duplicated.  One copy will be used to evaluate on train data and the
        other on eval data.

        This builder uses names to match inputs/outputs across the given pipelines, in the
        following ways:
        1. Inputs of `fit_pipeline` and `eval_pipeline` that share the same name, e.g. X
          become a single train inputs to the built pipeline (train_X).  That inputs is passed as X
          to both `fit_pipeline` and the train copy of `eval_pipeline`.
        2. Outputs of `fit_pipeline` are matched to inputs of `eval_pipeline` and passed
          accordingly to its two copies.

        Returns:
          A pipeline that meets the FitAndEvaluate pattern.
          * Outputs of `fit_pipeline` that match to inputs of `eval_pipeline` by name, are assumed
            to be fitted parameters.  Each such fitted parameter is piped from the output of
            `fit_pipeline` to the input of both copies of `eval_pipeline`, and also exposed as an
            output of the FitAndEvaluate pipeline.
          * Inputs of either of the pipelines, except those identified as fitted parameters,
            become collection inputs, with `train` entries going to `fit_pipeline` and the train
            copy of `eval_pipeline`, and `eval` entries going to the eval copy of
            `eval_pipeline`.
          * Outputs of both copies of `eval_pipeline` become collection outputs, with `train`
            entries coming from the train copy and `eval` entries coming from the eval copy
        """
        train_eval_pipeline = PipelineBuilder.combine(pipelines=[eval_pipeline], name="train")
        eval_eval_pipeline = PipelineBuilder.combine(pipelines=[eval_pipeline], name="eval")
        return cls.build_using_fit_and_two_evals(
            estimator_name, fit_pipeline, train_eval_pipeline, eval_eval_pipeline
        )
