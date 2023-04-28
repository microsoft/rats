"""
    A TrainAndEval is a pipeline that fits using train data and evaluates on that same train data
    and on a separate eval data.
    A TrainAndEval pipeline takes collection inputs with `train` `eval` entries, and outputs
    collection outputs with `train` `eval` entries.  It also outputs the fitted models as output
    entries.

"""
from __future__ import annotations

from collections import ChainMap
from itertools import chain
from typing import Any, Iterable, Sequence, Tuple

from hydra_zen import hydrated_dataclass
from omegaconf import MISSING

from ..ux import DependencyOp, Pipeline, PipelineBuilder, PipelineConf
from ..ux._utils import _parse_dependencies_to_list


class ITrainAndEval(Pipeline):
    """
    A TrainAndEval is a pipeline that fits using train data and evaluates on that same train data
    and on a separate eval data.
    A TrainAndEval pipeline takes collection inputs with `train` `eval` entries, and outputs
    collection outputs with `train` `eval` entries.  It also outputs the fitted models as output
    entries.
    """


class _TrainAndEval(ITrainAndEval):
    _config: TrainAndEvalConf

    def __init__(
        self,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        second_eval_pl: Pipeline | None,
        eval_names: Iterable[str],
    ):
        eval_names = frozenset(eval_names)
        if "train" in eval_names:
            raise ValueError(
                "eval_names may not contain `train`, as this is reserved for the train " "dataset."
            )
        if second_eval_pl is None:
            second_eval_pl = eval_pl
        train_eval_pl = PipelineBuilder.combine(pipelines=[eval_pl], name="train")
        eval_eval_pls = {
            ds_name: PipelineBuilder.combine(pipelines=[second_eval_pl], name=ds_name)
            for ds_name in eval_names
        }
        fitted_params_used_by_train_eval = frozenset(train_pl.outputs) & frozenset(eval_pl.inputs)
        fitted_params_used_by_eval_eval = frozenset(train_pl.outputs) & frozenset(
            second_eval_pl.inputs
        )
        inputs_used_by_train_eval = frozenset(eval_pl.inputs) - fitted_params_used_by_train_eval
        inputs_used_by_eval_eval = (
            frozenset(second_eval_pl.inputs) - fitted_params_used_by_eval_eval
        )
        pipeline = PipelineBuilder.combine(
            pipelines=[train_pl, train_eval_pl] + list(eval_eval_pls.values()),
            name=name,
            dependencies=(
                tuple(
                    train_pl.outputs[n] >> train_eval_pl.inputs[n]
                    for n in fitted_params_used_by_train_eval
                )
                + tuple(
                    train_pl.outputs[n] >> p.inputs[n]
                    for p in eval_eval_pls.values()
                    for n in fitted_params_used_by_eval_eval
                )
            ),
            inputs=ChainMap(
                {
                    f"{n}.train": train_pl.inputs[n]
                    for n in frozenset(train_pl.inputs) - inputs_used_by_train_eval
                },
                {
                    f"{n}.train": train_eval_pl.inputs[n]
                    for n in inputs_used_by_train_eval - frozenset(train_pl.inputs)
                },
                {
                    f"{n}.train": train_pl.inputs[n] | train_eval_pl.inputs[n]
                    for n in frozenset(train_pl.inputs) & inputs_used_by_train_eval
                },
                {
                    f"{n}.{ds_name}": p.inputs[n]
                    for ds_name, p in eval_eval_pls.items()
                    for n in inputs_used_by_eval_eval
                },
            ),
            outputs=ChainMap(
                {f"{n}.train": train_eval_pl.outputs[n] for n in train_eval_pl.outputs},
                {
                    f"{n}.{ds_name}": p.outputs[n]
                    for ds_name, p in eval_eval_pls.items()
                    for n in second_eval_pl.outputs
                },
                {n: train_pl.outputs[n] for n in train_pl.outputs},
            ),
        )
        config = TrainAndEvalConf(
            name=name,
            train_pl=train_pl._config,
            eval_pl=eval_pl._config,
            second_eval_pl=None if second_eval_pl is None else second_eval_pl._config,
        )
        super().__init__(
            name,
            pipeline._dag,
            config,
            pipeline.inputs,
            pipeline.outputs,
            pipeline.in_collections,
            pipeline.out_collections,
        )


@hydrated_dataclass(
    _TrainAndEval,
)
class TrainAndEvalConf(PipelineConf):
    name: str = MISSING
    train_pl: PipelineConf = MISSING
    eval_pl: PipelineConf = MISSING
    second_eval_pl: PipelineConf | None = None
    eval_names: Tuple[str] = ("eval",)


class _TrainAndEvalWhenFitEvaluatesOnTrain(ITrainAndEval):
    _config: TrainAndEvalWhenFitEvaluatesOnTrainConf

    def __init__(
        self,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        dependencies: Sequence[DependencyOp],
        eval_names: Iterable[str],
    ):
        eval_names = frozenset(eval_names)
        fitted_names_in_fit = frozenset(
            dp.out_param.param.name for dp in chain.from_iterable(dependencies)
        )
        fitted_names_in_eval = frozenset(
            dp.in_param.param.name for dp in chain.from_iterable(dependencies)
        )
        eval_pls = {
            ds_name: PipelineBuilder.combine(pipelines=[eval_pl], name=ds_name)
            for ds_name in eval_names
        }
        expended_dependencies = tuple(
            d.decorate(in_name=ds_name, out_name=None)
            for ds_name in eval_names
            for d in dependencies
        )
        pipeline = PipelineBuilder.combine(
            pipelines=[train_pl] + list(eval_pls.values()),
            dependencies=expended_dependencies,
            name=name,
            inputs=ChainMap(
                {f"{n}.train": train_pl.inputs[n] for n in train_pl.inputs},
                {
                    f"{n}.{ds_name}": p.inputs[n]
                    for ds_name, p in eval_pls.items()
                    for n in eval_pl.inputs
                    if n not in (fn for fn in fitted_names_in_eval)
                },
            ),
            outputs=ChainMap(
                {
                    f"{n}.train": train_pl.outputs[n]
                    for n in train_pl.outputs
                    if n not in (fn for fn in fitted_names_in_fit)
                },
                {
                    f"{n}.{ds_name}": p.outputs[n]
                    for ds_name, p in eval_pls.items()
                    for n in eval_pl.outputs
                },
                {n: train_pl.outputs[n] for n in (fn for fn in fitted_names_in_fit)},
            ),
        )
        dp_confs = {
            f"d{i}": dp.get_dependencyopconf(pipelines=[train_pl, eval_pl])
            for i, dp in enumerate(dependencies)
        }
        dp_confs = {d: v.rename_pipelineports("train_pl", "eval_pl") for d, v in dp_confs.items()}
        config = TrainAndEvalWhenFitEvaluatesOnTrainConf(
            name=name,
            train_pl=train_pl._config,
            eval_pl=eval_pl._config,
            dependencies=dp_confs,
        )
        super().__init__(
            name,
            pipeline._dag,
            config,
            pipeline.inputs,
            pipeline.outputs,
            pipeline.in_collections,
            pipeline.out_collections,
        )


@hydrated_dataclass(
    _TrainAndEvalWhenFitEvaluatesOnTrain,
    zen_wrappers=[
        "${parse_dependencies: ${..dependencies}}",
        _parse_dependencies_to_list,
    ],
)
class TrainAndEvalWhenFitEvaluatesOnTrainConf(PipelineConf):
    name: str = MISSING
    train_pl: PipelineConf = MISSING
    eval_pl: PipelineConf = MISSING
    dependencies: Any = ()
    eval_names: Tuple[str] = ("eval",)


class TrainAndEvalBuilders:
    """Builders for TrainAndEval pipelines.

    A TrainAndEval is a pipeline that fits using train data and evaluates on that same train data
    and on a separate eval data.
    A TrainAndEval pipeline takes collection inputs with `train` `eval` entries, and outputs
    collection outputs with `train` `eval` entries.  It also outputs the fitted models as output
    entries.
    """

    @classmethod
    def build_when_fit_evaluates_on_train(
        cls,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        dependencies: Sequence[DependencyOp] = (),
        eval_names: set[str] = {"eval"},
    ) -> ITrainAndEval:
        """Builds a TrainAndEval pipeline when the fit pipeline also evaluates train data.

        Args:
        * name: name for the built pipeline.
        * train_pl: A pipeline that takes data, fits parameters to it, and evaluates the data
          using these fitted parameters.  Inputs and outputs are assumed to be entires, not
          collections.
        * eval_pl: A pipeline that takes fitted parameters and data, and evaluates the data
          using these fitted parameters.  Inputs and outputs are assumed to be entires, not
          collections.
        * dependencies: A sequence of dependencies mapping the fitted parameters from train_pl
          outputs to eval_pl inputs.
        Returns:
          A pipeline that meets the TrainAndEval pattern.
          * Inputs to `train_pl` and `eval_pl`, except those indicated in `dependencies`
            become collection inputs, with `train` entries going to `train_pl` and `eval`
            entries going to `eval_pl.
          * Outputs from `train_pl` and `eval_pl`, except those indicated in
            `dependencies` become collection outputs, with `train` entries comming from
            `train_pl` and `eval` entries comming from `eval_pl`.
          * Fitted parameter, i.e. outputs of `train_pl` that are indicated in `dependencies`
            becomes outputs of the built pipeline.

        Example:
          Assuming
          * `fit` is a pipeline taking a vector `X` and returning fitted scalars `mean`
            and `std` and standardized array `Z`.
          * `eval` is a pipeline taking scalars `offset` and `scale` and vector `X` and
            returning standardized array `Z`.
          ```python
          w = TrainAndEvalBuilders(
                  "standardize", fit, eval,
                  (fit.outputs.mean >> eval.inputs.offset,
                   fit.outputs.std >> eval.inputs.scale,))
          ```
          Would create `w` as a worfkflow with the following input and outputs:
          * Inputs: `X` (`X.train`, `X.eval`).
          * Outputs: `Z` (`Z.train`, `Z.eval`), `mean`, `std`.
        """
        return _TrainAndEvalWhenFitEvaluatesOnTrain(
            name, train_pl, eval_pl, dependencies, eval_names
        )

    @classmethod
    def build_using_fit_and_two_evals(
        cls,
        name: str,
        train_pl: Pipeline,
        train_eval_pl: Pipeline,
        eval_eval_pl: Pipeline,
        eval_names: set[str] = {"eval"},
    ) -> Pipeline:
        """Builds a TrainAndEval pipeline, supporting different eval on train and eval data.

        Args:
        * name: ename for the built pipeline.
        * train_pl: A pipeline that takes data, and outputs models/parameters fitted from the
          data.  Inputs and outputs are assumed to be entires, not collections.
        * train_eval_pl: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          train data.  Inputs and outputs are assumed to be entires, not collections.
        * eval_eval_pl: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          eval data.    Inputs and outputs are assumed to be entires, not collections.

        All outputs of `train_pl` are assumed to be fitted models/parameters.

        This builder uses names to match inputs/outputs across the given pipelines, in the
        following ways:
        1. Inputs of `train_pl` and `train_eval_pl` that share the same name, e.g. X
          become a single inputs to the built pipeline (X.train).  That inputs is passed as X to
          both `train_pl` and `train_eval_pl`.
        2. Outputs of `train_pl` are matched to inputs of `train_eval_pl` and
          `eval_eval_pl` by name, and passed accordingly.

        Returns:
          A pipeline that meets the TrainAndEval pattern.
          * Outputs of `train_pl` that match to inputs of `train_eval_pl` or
            `eval_eval_pl` by name, are assumed to be fitted parameters.  Each such fitted
            parameter is piped from the output of `train_pl` to the input of
            `train_eval_pl` and/or `eval_eval_pl`, and also exposed as an output of
            the TrainAndEval pipeline.
          * Inputs of either of the three pipelines, except those identified as fitted parameters,
            become collection inputs, with `train` entries going to `train_pl` and
            `train_eval_pl`, and `eval` entries going to `eval_eval_pl`.
          * Outputs of `train_eval_pl` and `eval_eval_pl` become collection outputs,
            with `train` entries coming from `train_eval_pl` and `eval` entries coming from
            `eval_eval_pl`.
        """
        return _TrainAndEval(
            name=name,
            train_pl=train_pl,
            eval_pl=train_eval_pl,
            second_eval_pl=eval_eval_pl,
            eval_names=eval_names,
        )

    @classmethod
    def build_using_eval_on_train_and_eval(
        cls,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        eval_names: set[str] = {"eval"},
    ) -> Pipeline:
        """Builds a TrainAndEval pipeline from a fit pipeline and an eval worflow.

        Args:
        * name: ename for the built pipeline.
        * train_pl: A pipeline that takes data, and outputs models/parameters fitted from the
          data.  Inputs and outputs are assumed to be entires, not collections.
        * eval_pl: A pipeline that takes fitted models/parameters and data, and evaluates the
          data using these fitted parameters.  Will be used on both train data and eval data.
          Inputs and outputs are assumed to be entires, not collections.

        All outputs of `train_pl` are assumed to be fitted models/parameters.

        `eval_pl` is duplicated.  One copy will be used to evaluate on train data and the
        other on eval data.

        This builder uses names to match inputs/outputs across the given pipelines, in the
        following ways:
        1. Inputs of `train_pl` and `eval_pl` that share the same name, e.g. X
          become a single train inputs to the built pipeline (train_X).  That inputs is passed as X
          to both `train_pl` and the train copy of `eval_pl`.
        2. Outputs of `train_pl` are matched to inputs of `eval_pl` and passed
          accordingly to its two copies.

        Returns:
          A pipeline that meets the TrainAndEval pattern.
          * Outputs of `train_pl` that match to inputs of `eval_pl` by name, are assumed
            to be fitted parameters.  Each such fitted parameter is piped from the output of
            `train_pl` to the input of both copies of `eval_pl`, and also exposed as an
            output of the TrainAndEval pipeline.
          * Inputs of either of the pipelines, except those identified as fitted parameters,
            become collection inputs, with `train` entries going to `train_pl` and the train
            copy of `eval_pl`, and `eval` entries going to the eval copy of
            `eval_pl`.
          * Outputs of both copies of `eval_pl` become collection outputs, with `train`
            entries coming from the train copy and `eval` entries coming from the eval copy
        """
        return _TrainAndEval(
            name=name,
            train_pl=train_pl,
            eval_pl=eval_pl,
            second_eval_pl=None,
            eval_names=eval_names,
        )
