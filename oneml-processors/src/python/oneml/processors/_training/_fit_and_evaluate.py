"""
    A FitAndEvaluate is a workflow that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

"""

from typing import Sequence

from .._ux import Dependency, Workflow, WorkflowClient


class FitAndEvaluateBuilders:
    """Builders for FitAndEvaluate workflows.

    A FitAndEvaluate is a workflow that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"
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
          * Every input to `fit_workflow` becomes an input to the built workflow, with a `train_`
            prefix added to its name.
          * Every output of `fit_workflow`, except those indicated in `shared_params` becomes an
            output of the build workflow, with a `train_` prefix added to its name.
          * Every input to `eval_workflow`, except those indicated in `shared_params` becomes an
            input to the built workflow, with a `holdout_` prefix added to its name.
          * Every output of `eval_workflow` becomes an output of the built workflow, with a
            `holdout_` prefix added to its name.
          * Every fit parameters, i.e. output of `fit_workflow` that is indicated in
            `shared_params` becomes an output of the built workflow.

        Example:
          Assuming
          * `fit` is a workflow taking a vector `X` and returning fitted scalars `mean`
            and `std` and standardized array `Z`.
          * `eval` is a workflow taking scalars `offset` and `scale` and vector `X` and
            returning standardized array `Z`.
          ```python
          w = FitAndEvaluateBuilders(
                  "standardize", fit, eval,
                  (fit.ret.mean >> eval.sig.offset,
                   fit.ret.std >> eval.sig.scale,))
          ```
          Would create `w` as a worfkflow with the following inputs and outputs:
          * Inputs: `train_X`, `holdout_X`
          * Outputs: `train_Z`, `holdout_Z`, `mean`, `std`.
        """
        fitted_names_in_fit = frozenset((d.out_param for d in shared_params))
        fitted_names_in_eval = frozenset((d.in_param for d in shared_params))
        workflow = WorkflowClient.compose_workflow(
            workflows=(fit_workflow, eval_workflow),
            dependencies=shared_params,
            name=estimator_name,
            input_dependencies=(
                tuple(f"train_{n}" >> fit_workflow.sig[n] for n in fit_workflow.sig)
                + tuple(
                    f"holdout_{n}" >> eval_workflow.sig[n]
                    for n in eval_workflow.sig
                    if n not in fitted_names_in_eval
                )
            ),
            output_dependencies=(
                tuple(
                    f"train_{n}" << fit_workflow.ret[n]
                    for n in fit_workflow.ret
                    if n not in fitted_names_in_fit
                )
                + tuple(f"holdout_{n}" << eval_workflow.ret[n] for n in eval_workflow.ret)
                + tuple(n << fit_workflow.ret[n] for n in fitted_names_in_fit)
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
          become a single input to the built workflow (train_X).  That input is passed as X to both
          `fit_workflow` and `train_eval_workflow`.
        2. Outputs of `fit_workflow` are matched to inputs of `train_eval_workflow` and
          `holdout_eval_workflow` by name, and passed accordingly.

        Returns:
          A workflow that meets the FitAndEvaluate pattern.
          * Outputs of `fit_workflow` are matched to inputs of `train_eval_workflow` and
            `holdout_eval_workflow` by name, and passed accordingly.
          * Every input to `fit_workflow` becomes an input to the built workflow, with a `train_`
            prefix added to its name.
          * Every input to `train_eval_workflow` that is not matched to an output of `fit_workflow`
            becomes an input to the built workflow, with a `train_` prefix added to its name.
          * Every input to `holdout_eval_workflow` that is not matched to an output of
            `fit_workflow` becomes an input to the built workflow, with a `holdout_` prefix added
            to its name.
          * Every output of `train_eval_workflow` becomes an output of the built workflow, with a
            `train_` prefix added to its name.
          * Every output of `holdout_eval_workflow` becomes an output of the built workflow, with a
            `holdout_` prefix added to its name.
          * Every fit parameter, i.e. output of `train_fit` becomes an output of the built
            workflow.
        """
        fitted_params_used_by_train_eval = frozenset(fit_workflow.ret) & frozenset(
            train_eval_workflow.sig
        )
        fitted_params_used_by_holdout_eval = frozenset(fit_workflow.ret) & frozenset(
            holdout_eval_workflow.sig
        )
        workflow = WorkflowClient.compose_workflow(
            name=estimator_name,
            workflows=(fit_workflow, train_eval_workflow, holdout_eval_workflow),
            dependencies=(
                tuple(
                    fit_workflow.ret[n] >> train_eval_workflow.sig[n]
                    for n in fitted_params_used_by_train_eval
                )
                + tuple(
                    fit_workflow.ret[n] >> holdout_eval_workflow.sig[n]
                    for n in fitted_params_used_by_holdout_eval
                )
            ),
            input_dependencies=(
                tuple(f"train_{n}" >> fit_workflow.sig[n] for n in fit_workflow.sig)
                + tuple(
                    f"train_{n}" >> train_eval_workflow.sig[n]
                    for n in train_eval_workflow.sig
                    if n not in fitted_params_used_by_train_eval
                )
                + tuple(
                    f"holdout_{n}" >> holdout_eval_workflow.sig[n]
                    for n in holdout_eval_workflow.sig
                    if n not in fitted_params_used_by_holdout_eval
                )
            ),
            output_dependencies=(
                tuple(f"train_{n}" << train_eval_workflow.ret[n] for n in train_eval_workflow.ret)
                + tuple(
                    f"holdout_{n}" << holdout_eval_workflow.ret[n]
                    for n in holdout_eval_workflow.ret
                )
                + tuple(n << fit_workflow.ret[n] for n in fit_workflow.ret)
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
          become a single train input to the built workflow (train_X).  That input is passed as X
          to both `fit_workflow` and the train copy of `eval_workflow`.
        2. Outputs of `fit_workflow` are matched to inputs of `eval_workflow` and passed
          accordingly to its two copies.

        Returns:
          A workflow that meets the FitAndEvaluate pattern.
          * `eval_workflow` is duplicated to create a train eval workflow and a
            holdout eval workflow.
          * Outputs of `fit_workflow` are matched to inputs of `eval_workflow` and by name, and
            passed accordingly to the two copies of `eval_workflow`.
          * Every input to `fit_workflow` becomes an input to the built workflow, with a `train_`
            prefix added to its name.
          * Every input to `eval_workflow` that is not matched to an output of `fit_workflow`
            becomes two inputs to the built workflow. One with a `train_` prefix added to its name,
            passed to the train copy of `eval_workflow` and one with a `holdout_` prefix add to its
            name, passed to the holdout copy of `eval_workflow`.
          * Every output of `eval_workflow` becomes two outputs of the built workflow, One with a
            `train_` prefix added to its name, taken from the train copy of `eval_workflow` and one
            with a `holdout_` prefix added to its name, taken from the holdout copy of
            `eval_workflow`.
          * Every fit parameter, i.e. output of `train_fit` becomes an output of the built
            workflow.
        """
        train_eval_workflow = WorkflowClient.compose_workflow(
            "train", (eval_workflow,), dependencies=()
        )
        holdout_eval_workflow = WorkflowClient.compose_workflow(
            "holdout", (eval_workflow,), dependencies=()
        )
        return cls.build_using_fit_and_two_evals(
            estimator_name, fit_workflow, train_eval_workflow, holdout_eval_workflow
        )
