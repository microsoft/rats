"""
    A FitAndEvaluate is a workflow that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of inputs ports and two sets of outputs ports:
    * train inputs/outputs ports whose names start with "train_"
    * holdout inputs/outputs ports whose names start with "holdout_"

"""

from collections import ChainMap
from typing import Sequence

from ..ux._client import WorkflowClient
from ..ux._workflow import Dependency, Workflow


class FitAndEvaluateBuilders:
    """Builders for FitAndEvaluate workflows.

    A FitAndEvaluate is a workflow that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of inputs ports and two sets of outputs ports:
    * train inputs/outputs ports whose names start with "train_"
    * holdout inputs/outputs ports whose names start with "holdout_"
    """

    @classmethod
    def build_when_fit_evaluates_on_train(
        cls,
        estimator_name: str,
        fit_workflow: Workflow,
        eval_workflow: Workflow,
        shared_params: Sequence[Dependency] = (),
    ) -> Workflow:
        """Builds a FitAndEvaluate workflow when the fit workflow also evaluates train data.

        Args:
        * estimator_name: ename for the built workflow.
        * fit_workflow: A workflow that takes data, fits parameters to it, and evaluates the data
          using these fitted parameters.
        * eval_workflow: A workflow that takes fitted parameters and data, and evaluates the data
          using these fitted parameters.
        * shared_params: A sequence of dependencies mapping the fitted parameters from fit_workflow
          outputs to eval_workflow inputs.
        Returns:
          A workflow that meets the FitAndEvaluate pattern.
          * Every inputs to `fit_workflow` becomes an inputs to the built workflow, with a `train_`
            prefix added to its name.
          * Every outputs of `fit_workflow`, except those indicated in `shared_params` becomes an
            outputs of the build workflow, with a `train_` prefix added to its name.
          * Every inputs to `eval_workflow`, except those indicated in `shared_params` becomes an
            inputs to the built workflow, with a `holdout_` prefix added to its name.
          * Every outputs of `eval_workflow` becomes an outputs of the built workflow, with a
            `holdout_` prefix added to its name.
          * Every fit parameters, i.e. outputs of `fit_workflow` that is indicated in
            `shared_params` becomes an outputs of the built workflow.

        Example:
          Assuming
          * `fit` is a workflow taking a vector `X` and returning fitted scalars `mean`
            and `std` and standardized array `Z`.
          * `eval` is a workflow taking scalars `offset` and `scale` and vector `X` and
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
        workflow = WorkflowClient.combine(
            fit_workflow,
            eval_workflow,
            dependencies=(shared_params,),
            name=estimator_name,
            inputs=ChainMap(
                {f"train_{n}": fit_workflow.inputs[n] for n in fit_workflow.inputs},
                {
                    f"holdout_{n}": eval_workflow.inputs[n]
                    for n in eval_workflow.inputs
                    if n not in (fn.node.name for fn in fitted_names_in_eval)
                },
            ),
            outputs=ChainMap(
                {
                    f"train_{n}": fit_workflow.outputs[n]
                    for n in fit_workflow.outputs
                    if n not in (fn.node.name for fn in fitted_names_in_fit)
                },
                {f"holdout_{n}": eval_workflow.outputs[n] for n in eval_workflow.outputs},
                {n: fit_workflow.outputs[n] for n in (fn.node.name for fn in fitted_names_in_fit)},
            ),
        )
        return workflow

    @classmethod
    def build_using_fit_and_two_evals(
        cls,
        estimator_name: str,
        fit_workflow: Workflow,
        train_eval_workflow: Workflow,
        holdout_eval_workflow: Workflow,
    ) -> Workflow:
        """Builds a FitAndEvaluate workflow, supporting different eval on train and holdout.

        Args:
        * estimator_name: ename for the built workflow.
        * fit_workflow: A workflow that takes data, and outputs models/parameters fitted from the
          data.
        * train_eval_workflow: A workflow that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This workflow will be used on the
          train data.
        * holdout_eval_workflow: A workflow that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This workflow will be used on the
          holdout data.

        All outputs of `fit_workflow` are assumed to be fitted models/parameters.

        This builder uses names to match inputs/outputs across the given workflows, in the
        following ways:
        1. Inputs of `fit_workflow` and `train_eval_workflow` that share the same name, e.g. X
          become a single inputs to the built workflow (train_X).  That inputs is passed as X to both
          `fit_workflow` and `train_eval_workflow`.
        2. Outputs of `fit_workflow` are matched to inputs of `train_eval_workflow` and
          `holdout_eval_workflow` by name, and passed accordingly.

        Returns:
          A workflow that meets the FitAndEvaluate pattern.
          * Outputs of `fit_workflow` are matched to inputs of `train_eval_workflow` and
            `holdout_eval_workflow` by name, and passed accordingly.
          * Every inputs to `fit_workflow` becomes an inputs to the built workflow, with a `train_`
            prefix added to its name.
          * Every inputs to `train_eval_workflow` that is not matched to an outputs of `fit_workflow`
            becomes an inputs to the built workflow, with a `train_` prefix added to its name.
          * Every inputs to `holdout_eval_workflow` that is not matched to an outputs of
            `fit_workflow` becomes an inputs to the built workflow, with a `holdout_` prefix added
            to its name.
          * Every outputs of `train_eval_workflow` becomes an outputs of the built workflow, with a
            `train_` prefix added to its name.
          * Every outputs of `holdout_eval_workflow` becomes an outputs of the built workflow, with a
            `holdout_` prefix added to its name.
          * Every fit parameter, i.e. outputs of `train_fit` becomes an outputs of the built
            workflow.
        """
        fitted_params_used_by_train_eval = frozenset(fit_workflow.outputs) & frozenset(
            train_eval_workflow.inputs
        )
        fitted_params_used_by_holdout_eval = frozenset(fit_workflow.outputs) & frozenset(
            holdout_eval_workflow.inputs
        )
        workflow = WorkflowClient.combine(
            fit_workflow,
            train_eval_workflow,
            holdout_eval_workflow,
            name=estimator_name,
            dependencies=(
                tuple(
                    fit_workflow.outputs[n] >> train_eval_workflow.inputs[n]
                    for n in fitted_params_used_by_train_eval
                )
                + tuple(
                    fit_workflow.outputs[n] >> holdout_eval_workflow.inputs[n]
                    for n in fitted_params_used_by_holdout_eval
                )
            ),
            inputs=ChainMap(
                {f"train.n{n}": fit_workflow.inputs[n] for n in fit_workflow.inputs},
                {
                    f"train.n{n}": train_eval_workflow.inputs[n]
                    for n in train_eval_workflow.inputs
                    if n not in fitted_params_used_by_train_eval
                },
                {
                    f"holdout.n{n}": holdout_eval_workflow.inputs[n]
                    for n in holdout_eval_workflow.inputs
                    if n not in fitted_params_used_by_holdout_eval
                },
            ),
            outputs=ChainMap(
                {
                    f"train.n{n}": train_eval_workflow.outputs[n]
                    for n in train_eval_workflow.outputs
                },
                {
                    f"holdout.n{n}": holdout_eval_workflow.outputs[n]
                    for n in holdout_eval_workflow.outputs
                },
                {f"n{n}": fit_workflow.outputs[n] for n in fit_workflow.outputs},
            ),
        )
        return workflow

    @classmethod
    def build_using_eval_on_train_and_holdout(
        cls,
        estimator_name: str,
        fit_workflow: Workflow,
        eval_workflow: Workflow,
    ) -> Workflow:
        """Builds a FitAndEvaluate workflow from a fit workflow and an eval worflow.

        Args:
        * estimator_name: ename for the built workflow.
        * fit_workflow: A workflow that takes data, and outputs models/parameters fitted from the
          data.
        * eval_workflow: A workflow that takes fitted models/parameters and data, and evaluates the
          data using these fitted parameters.  Will be used on both train data and holdout data.

        All outputs of `fit_workflow` are assumed to be fitted models/parameters.

        `eval_workflow` is duplicated.  One copy will be used to evaluate on train data and the
        other on holdout data.

        This builder uses names to match inputs/outputs across the given workflows, in the
        following ways:
        1. Inputs of `fit_workflow` and `eval_workflow` that share the same name, e.g. X
          become a single train inputs to the built workflow (train_X).  That inputs is passed as X
          to both `fit_workflow` and the train copy of `eval_workflow`.
        2. Outputs of `fit_workflow` are matched to inputs of `eval_workflow` and passed
          accordingly to its two copies.

        Returns:
          A workflow that meets the FitAndEvaluate pattern.
          * `eval_workflow` is duplicated to create a train eval workflow and a
            holdout eval workflow.
          * Outputs of `fit_workflow` are matched to inputs of `eval_workflow` and by name, and
            passed accordingly to the two copies of `eval_workflow`.
          * Every inputs to `fit_workflow` becomes an inputs to the built workflow, with a `train_`
            prefix added to its name.
          * Every inputs to `eval_workflow` that is not matched to an outputs of `fit_workflow`
            becomes two inputs to the built workflow. One with a `train_` prefix added to its name,
            passed to the train copy of `eval_workflow` and one with a `holdout_` prefix add to its
            name, passed to the holdout copy of `eval_workflow`.
          * Every outputs of `eval_workflow` becomes two outputs of the built workflow, One with a
            `train_` prefix added to its name, taken from the train copy of `eval_workflow` and one
            with a `holdout_` prefix added to its name, taken from the holdout copy of
            `eval_workflow`.
          * Every fit parameter, i.e. outputs of `train_fit` becomes an outputs of the built
            workflow.
        """
        train_eval_workflow = WorkflowClient.combine(eval_workflow, name="train")
        holdout_eval_workflow = WorkflowClient.combine(eval_workflow, name="holdout")
        return cls.build_using_fit_and_two_evals(
            estimator_name, fit_workflow, train_eval_workflow, holdout_eval_workflow
        )
