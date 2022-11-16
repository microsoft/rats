"""
    A FitAndEvaluate is a pipeline that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of inputs ports and two sets of outputs ports:
    * train inputs/outputs ports whose names start with "train_"
    * holdout inputs/outputs ports whose names start with "holdout_"

"""

from collections import ChainMap
from typing import Sequence

from ..ux._client import PipelineBuilder
from ..ux._pipeline import Dependency, Pipeline


class FitAndEvaluateBuilders:
    """Builders for FitAndEvaluate pipelines.

    A FitAndEvaluate is a pipeline that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of inputs ports and two sets of outputs ports:
    * train inputs/outputs ports whose names start with "train_"
    * holdout inputs/outputs ports whose names start with "holdout_"
    """

    @classmethod
    def build_when_fit_evaluates_on_train(
        cls,
        estimator_name: str,
        fit_pipeline: Pipeline,
        eval_pipeline: Pipeline,
        shared_params: Sequence[Dependency] = (),
    ) -> Pipeline:
        """Builds a FitAndEvaluate pipeline when the fit pipeline also evaluates train data.

        Args:
        * estimator_name: ename for the built pipeline.
        * fit_pipeline: A pipeline that takes data, fits parameters to it, and evaluates the data
          using these fitted parameters.
        * eval_pipeline: A pipeline that takes fitted parameters and data, and evaluates the data
          using these fitted parameters.
        * shared_params: A sequence of dependencies mapping the fitted parameters from fit_pipeline
          outputs to eval_pipeline inputs.
        Returns:
          A pipeline that meets the FitAndEvaluate pattern.
          * Every inputs to `fit_pipeline` becomes an inputs to the built pipeline, with a `train_`
            prefix added to its name.
          * Every outputs of `fit_pipeline`, except those indicated in `shared_params` becomes an
            outputs of the build pipeline, with a `train_` prefix added to its name.
          * Every inputs to `eval_pipeline`, except those indicated in `shared_params` becomes an
            inputs to the built pipeline, with a `holdout_` prefix added to its name.
          * Every outputs of `eval_pipeline` becomes an outputs of the built pipeline, with a
            `holdout_` prefix added to its name.
          * Every fit parameters, i.e. outputs of `fit_pipeline` that is indicated in
            `shared_params` becomes an outputs of the built pipeline.

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
          Would create `w` as a worfkflow with the following inputs and outputs:
          * Inputs: `train_X`, `holdout_X`
          * Outputs: `train_Z`, `holdout_Z`, `mean`, `std`.
        """
        fitted_names_in_fit = frozenset((d.out_param for d in shared_params))
        fitted_names_in_eval = frozenset((d.in_param for d in shared_params))
        pipeline = PipelineBuilder.combine(
            fit_pipeline,
            eval_pipeline,
            dependencies=(shared_params,),
            name=estimator_name,
            inputs=ChainMap(
                {f"train_{n}": fit_pipeline.inputs[n] for n in fit_pipeline.inputs},
                {
                    f"holdout_{n}": eval_pipeline.inputs[n]
                    for n in eval_pipeline.inputs
                    if n not in (fn.node.name for fn in fitted_names_in_eval)
                },
            ),
            outputs=ChainMap(
                {
                    f"train_{n}": fit_pipeline.outputs[n]
                    for n in fit_pipeline.outputs
                    if n not in (fn.node.name for fn in fitted_names_in_fit)
                },
                {f"holdout_{n}": eval_pipeline.outputs[n] for n in eval_pipeline.outputs},
                {n: fit_pipeline.outputs[n] for n in (fn.node.name for fn in fitted_names_in_fit)},
            ),
        )
        return pipeline

    @classmethod
    def build_using_fit_and_two_evals(
        cls,
        estimator_name: str,
        fit_pipeline: Pipeline,
        train_eval_pipeline: Pipeline,
        holdout_eval_pipeline: Pipeline,
    ) -> Pipeline:
        """Builds a FitAndEvaluate pipeline, supporting different eval on train and holdout.

        Args:
        * estimator_name: ename for the built pipeline.
        * fit_pipeline: A pipeline that takes data, and outputs models/parameters fitted from the
          data.
        * train_eval_pipeline: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          train data.
        * holdout_eval_pipeline: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          holdout data.

        All outputs of `fit_pipeline` are assumed to be fitted models/parameters.

        This builder uses names to match inputs/outputs across the given pipelines, in the
        following ways:
        1. Inputs of `fit_pipeline` and `train_eval_pipeline` that share the same name, e.g. X
          become a single inputs to the built pipeline (train_X).  That inputs is passed as X to both
          `fit_pipeline` and `train_eval_pipeline`.
        2. Outputs of `fit_pipeline` are matched to inputs of `train_eval_pipeline` and
          `holdout_eval_pipeline` by name, and passed accordingly.

        Returns:
          A pipeline that meets the FitAndEvaluate pattern.
          * Outputs of `fit_pipeline` are matched to inputs of `train_eval_pipeline` and
            `holdout_eval_pipeline` by name, and passed accordingly.
          * Every inputs to `fit_pipeline` becomes an inputs to the built pipeline, with a `train_`
            prefix added to its name.
          * Every inputs to `train_eval_pipeline` that is not matched to an outputs of `fit_pipeline`
            becomes an inputs to the built pipeline, with a `train_` prefix added to its name.
          * Every inputs to `holdout_eval_pipeline` that is not matched to an outputs of
            `fit_pipeline` becomes an inputs to the built pipeline, with a `holdout_` prefix added
            to its name.
          * Every outputs of `train_eval_pipeline` becomes an outputs of the built pipeline, with a
            `train_` prefix added to its name.
          * Every outputs of `holdout_eval_pipeline` becomes an outputs of the built pipeline, with a
            `holdout_` prefix added to its name.
          * Every fit parameter, i.e. outputs of `train_fit` becomes an outputs of the built
            pipeline.
        """
        fitted_params_used_by_train_eval = frozenset(fit_pipeline.outputs) & frozenset(
            train_eval_pipeline.inputs
        )
        fitted_params_used_by_holdout_eval = frozenset(fit_pipeline.outputs) & frozenset(
            holdout_eval_pipeline.inputs
        )
        pipeline = PipelineBuilder.combine(
            fit_pipeline,
            train_eval_pipeline,
            holdout_eval_pipeline,
            name=estimator_name,
            dependencies=(
                tuple(
                    fit_pipeline.outputs[n] >> train_eval_pipeline.inputs[n]
                    for n in fitted_params_used_by_train_eval
                )
                + tuple(
                    fit_pipeline.outputs[n] >> holdout_eval_pipeline.inputs[n]
                    for n in fitted_params_used_by_holdout_eval
                )
            ),
            inputs=ChainMap(
                {f"train.n{n}": fit_pipeline.inputs[n] for n in fit_pipeline.inputs},
                {
                    f"train.n{n}": train_eval_pipeline.inputs[n]
                    for n in train_eval_pipeline.inputs
                    if n not in fitted_params_used_by_train_eval
                },
                {
                    f"holdout.n{n}": holdout_eval_pipeline.inputs[n]
                    for n in holdout_eval_pipeline.inputs
                    if n not in fitted_params_used_by_holdout_eval
                },
            ),
            outputs=ChainMap(
                {
                    f"train.n{n}": train_eval_pipeline.outputs[n]
                    for n in train_eval_pipeline.outputs
                },
                {
                    f"holdout.n{n}": holdout_eval_pipeline.outputs[n]
                    for n in holdout_eval_pipeline.outputs
                },
                {f"n{n}": fit_pipeline.outputs[n] for n in fit_pipeline.outputs},
            ),
        )
        return pipeline

    @classmethod
    def build_using_eval_on_train_and_holdout(
        cls,
        estimator_name: str,
        fit_pipeline: Pipeline,
        eval_pipeline: Pipeline,
    ) -> Pipeline:
        """Builds a FitAndEvaluate pipeline from a fit pipeline and an eval worflow.

        Args:
        * estimator_name: ename for the built pipeline.
        * fit_pipeline: A pipeline that takes data, and outputs models/parameters fitted from the
          data.
        * eval_pipeline: A pipeline that takes fitted models/parameters and data, and evaluates the
          data using these fitted parameters.  Will be used on both train data and holdout data.

        All outputs of `fit_pipeline` are assumed to be fitted models/parameters.

        `eval_pipeline` is duplicated.  One copy will be used to evaluate on train data and the
        other on holdout data.

        This builder uses names to match inputs/outputs across the given pipelines, in the
        following ways:
        1. Inputs of `fit_pipeline` and `eval_pipeline` that share the same name, e.g. X
          become a single train inputs to the built pipeline (train_X).  That inputs is passed as X
          to both `fit_pipeline` and the train copy of `eval_pipeline`.
        2. Outputs of `fit_pipeline` are matched to inputs of `eval_pipeline` and passed
          accordingly to its two copies.

        Returns:
          A pipeline that meets the FitAndEvaluate pattern.
          * `eval_pipeline` is duplicated to create a train eval pipeline and a
            holdout eval pipeline.
          * Outputs of `fit_pipeline` are matched to inputs of `eval_pipeline` and by name, and
            passed accordingly to the two copies of `eval_pipeline`.
          * Every inputs to `fit_pipeline` becomes an inputs to the built pipeline, with a `train_`
            prefix added to its name.
          * Every inputs to `eval_pipeline` that is not matched to an outputs of `fit_pipeline`
            becomes two inputs to the built pipeline. One with a `train_` prefix added to its name,
            passed to the train copy of `eval_pipeline` and one with a `holdout_` prefix add to its
            name, passed to the holdout copy of `eval_pipeline`.
          * Every outputs of `eval_pipeline` becomes two outputs of the built pipeline, One with a
            `train_` prefix added to its name, taken from the train copy of `eval_pipeline` and one
            with a `holdout_` prefix added to its name, taken from the holdout copy of
            `eval_pipeline`.
          * Every fit parameter, i.e. outputs of `train_fit` becomes an outputs of the built
            pipeline.
        """
        train_eval_pipeline = PipelineBuilder.combine(eval_pipeline, name="train")
        holdout_eval_pipeline = PipelineBuilder.combine(eval_pipeline, name="holdout")
        return cls.build_using_fit_and_two_evals(
            estimator_name, fit_pipeline, train_eval_pipeline, holdout_eval_pipeline
        )
