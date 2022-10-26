"""
    A FitAndEvaluate is a pipeline that fits using train data and evaluates on train and holdout
    data.
    To that end, the FitAndEvaluate has two sets of input ports and two sets of output ports:
    * train input/output ports whose names start with "train_"
    * holdout input/output ports whose names start with "holdout_"

"""

from typing import Sequence

from .._ux import Dependency, Workflow, WorkflowClient


class FitAndEvaluateBuilders:
    @classmethod
    def build_when_fit_evaluates_on_train(
        cls,
        estimator_name: str,
        fit_workflow: Workflow,
        eval_workflow: Workflow,
        shared_params: Sequence[Dependency] = (),
    ) -> Workflow:
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
        train_eval_workflow = WorkflowClient.compose_workflow(
            "train", (eval_workflow,), dependencies=()
        )
        holdout_eval_workflow = WorkflowClient.compose_workflow(
            "holdout", (eval_workflow,), dependencies=()
        )
        return cls.build_using_fit_and_two_evals(
            estimator_name, fit_workflow, train_eval_workflow, holdout_eval_workflow
        )
