"""
    A TrainAndEval is a pipeline that fits using train data and evaluates on that same train data
    and on a separate validation data.
    A TrainAndEval pipeline takes collection inputs with `train` `val` entries, and outputs
    collection outputs with `train` `val` entries.  It also outputs the fitted models as output
    entries.

"""
from __future__ import annotations

from collections import ChainMap
from itertools import chain
from typing import Any, Iterable, Mapping, Sequence, Tuple

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
        validation_names: Iterable[str],
    ):
        # A config holding the parameters of this TrainAndEval.
        config = TrainAndEvalConf(
            name=name,
            train_pl=train_pl._config,
            eval_pl=eval_pl._config,
            second_eval_pl=None if second_eval_pl is None else second_eval_pl._config,
            validation_names=tuple(validation_names),
        )

        validation_names = frozenset(validation_names)
        if "train" in validation_names:
            raise ValueError(
                "validation_names may not contain `train`, as this is reserved for the train "
                "dataset."
            )

        # A dictionary from dataset name to the corresponding eval pipeline.
        eval_pls: Mapping[str, Pipeline] = ChainMap(
            {
                ds_name: (second_eval_pl or eval_pl).decorate(ds_name)
                for ds_name in validation_names
            },
            {"train": eval_pl.decorate("train")},
        )
        # Convert inputs, except for those that correspond to train_pl outputs, to collections, and
        # convert all outputs to collections.
        eval_pls = {
            ds_name: pl.rename_inputs(
                {name: f"{name}.{ds_name}" for name in pl.inputs if name not in train_pl.outputs}
            ).rename_outputs({name: f"{name}.{ds_name}" for name in pl.outputs})
            for ds_name, pl in eval_pls.items()
        }
        # Now that these are renamed, we can just combine all the eval pipelines into one.
        # Each collection input and output will be merged into a collection with the union the per
        # ds_name entries.
        # Each non-collection input will become a single input of the combined pipeline.

        evals_pl = PipelineBuilder.combine(
            name="eval",
            pipelines=tuple(eval_pls.values()),
        )

        # Do a similar renaming trick for the train pipeline:
        # inputs are all converted to input collections, each with a single entry called "train".
        # outputs, except those mapped to evals_pl inputs, are converted to output collections,
        # again each with a single entry "train".

        if train_pl.name != "train":
            train_pl = train_pl.decorate("train")
        train_pl = train_pl.rename_inputs(
            {name: f"{name}.train" for name in train_pl.inputs}
        ).rename_outputs(
            {name: f"{name}.train" for name in train_pl.outputs if name not in evals_pl.inputs}
        )

        # Combine the train and eval pipelines into one.
        # Input will be merged into the correct collections.
        # Outputs are combined as the fitted parameters in train_pl.outputs, the output collections
        # of evals_pl, and the single entry "train" in the output collections of train_pl.
        pipeline = PipelineBuilder.combine(
            name=name,
            pipelines=[train_pl, evals_pl],
            dependencies=tuple(
                train_pl.outputs[name] >> evals_pl.inputs[name] for name in evals_pl.inputs
            ),
            outputs=ChainMap(
                {name: train_pl.outputs[name] for name in train_pl.outputs},
                {name: evals_pl.out_collections[name] for name in evals_pl.out_collections},
                {
                    f"{name}.train": train_pl.out_collections[name].train
                    for name in train_pl.out_collections
                },
            ),
        )

        super().__init__(
            other=pipeline,
            config=config,
        )


@hydrated_dataclass(
    _TrainAndEval,
)
class TrainAndEvalConf(PipelineConf):
    name: str = MISSING

    # Train pipeline, taking train data and outputing the fitted parameters:
    train_pl: PipelineConf = MISSING

    # Evaluation pipeline taking fitted parameters and data and outputting processed data.  Used
    # for the train data, and if `second_eval_pl` is None, also for the validation data:
    eval_pl: PipelineConf = MISSING  #

    # Evaluation pipeline taking fitted parameters and data and outputting processed data.  If not
    # None, Used for the validation data.  Otherwise, `eval_pl` is used for the validation data:
    second_eval_pl: PipelineConf | None = None
    validation_names: Tuple[str, ...] = ("validation",)


class _TrainAndEvalWhenFitEvaluatesOnTrain(ITrainAndEval):
    _config: TrainAndEvalWhenFitEvaluatesOnTrainConf

    def __init__(
        self,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        dependencies: Sequence[DependencyOp],
        validation_names: Iterable[str],
    ):
        # A config holding the parameters of this TrainAndEval.
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
            validation_names=tuple(validation_names),
        )
        validation_names = frozenset(validation_names)
        if "train" in validation_names:
            raise ValueError(
                "validation_names may not contain `train`, as this is reserved for the train dataset."
            )

        eval_inputs_to_train_outputs = {
            dp.out_param.param.name: dp.in_param.param.name
            for dp in chain.from_iterable(dependencies)
        }
        train_outputs_mapping_to_eval_inputs = set(eval_inputs_to_train_outputs.values())

        # A dictionary from dataset name to the corresponding eval pipeline.
        eval_pls = {ds_name: eval_pl.decorate(ds_name) for ds_name in validation_names}
        # Convert inputs, except for those that correspond to train_pl outputs, to collections, and
        # convert all outputs to collections.
        eval_pls = {
            ds_name: pl.rename_inputs(
                {
                    name: f"{name}.{ds_name}"
                    for name in pl.inputs
                    if name not in eval_inputs_to_train_outputs
                }
            ).rename_outputs({name: f"{name}.{ds_name}" for name in pl.outputs})
            for ds_name, pl in eval_pls.items()
        }
        # Now that these are renamed, we can just combine all the eval pipelines into one.
        # Each collection input and output will be merged into a collection with the union the per
        # ds_name entries.
        # Each non-collection input will become a single input of the combined pipeline.
        evals_pl = PipelineBuilder.combine(
            name="eval",
            pipelines=tuple(eval_pls.values()),
        )

        # Do a similar renaming trick for the train pipeline:
        # inputs are all converted to input collections, each with a single entry called "train".
        # outputs, except those mapped to evals_pl inputs, are converted to output collections,
        # again each with a single entry "train".

        if train_pl.name != "train":
            train_pl = train_pl.decorate("train")
        train_pl = train_pl.rename_inputs(
            {name: f"{name}.train" for name in train_pl.inputs}
        ).rename_outputs(
            {
                name: f"{name}.train"
                for name in train_pl.outputs
                if name not in train_outputs_mapping_to_eval_inputs
            }
        )

        # Combine the train and eval pipelines into one.
        # Input will be merged into the correct collections.
        # Outputs are combined as the fitted parameters in train_pl.outputs, the output collections
        # of evals_pl, and the single entry "train" in the output collections of train_pl.
        pipeline = PipelineBuilder.combine(
            name=name,
            pipelines=[train_pl, evals_pl],
            dependencies=tuple(
                train_pl.outputs[source] >> evals_pl.inputs[target]
                for target, source in eval_inputs_to_train_outputs.items()
            ),
            outputs=ChainMap(
                {name: train_pl.outputs[name] for name in train_pl.outputs},
                {name: evals_pl.out_collections[name] for name in evals_pl.out_collections},
                {
                    f"{name}.train": train_pl.out_collections[name].train
                    for name in train_pl.out_collections
                },
            ),
        )

        super().__init__(
            other=pipeline,
            config=config,
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

    # Train pipeline, taking train data and outputing the fitted parameters and processed train
    # data:
    train_pl: PipelineConf = MISSING
    # Evaluation pipeline taking fitted parameters and validation data, and outputing the
    # processed validation data:
    eval_pl: PipelineConf = MISSING
    # Fitted parameters, expressed as a list of DependencyOpConf between the train and eval
    # pipelines:
    dependencies: Any = ()
    validation_names: Tuple[str, ...] = ("validation",)


class TrainAndEvalBuilders:
    """Builders for TrainAndEval pipelines.

    A TrainAndEval is a pipeline that fits using train data and evaluates on that same train data
    and on a separate validation data.
    A TrainAndEval pipeline takes collection inputs with `train` `validation` entries, and outputs
    collection outputs with `train` `validation` entries.  It also outputs the fitted models as
    output entries.
    """

    @classmethod
    def build_when_fit_evaluates_on_train(
        cls,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        dependencies: Sequence[DependencyOp] = (),
        validation_names: set[str] = {"validation"},
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
            become collection inputs, with `train` entries going to `train_pl` and `validation`
            entries going to `eval_pl.
          * Outputs from `train_pl` and `eval_pl`, except those indicated in
            `dependencies` become collection outputs, with `train` entries comming from
            `train_pl` and `validation` entries comming from `eval_pl`.
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
          * Inputs: `X` (`X.train`, `X.validation`).
          * Outputs: `Z` (`Z.train`, `Z.validation`), `mean`, `std`.
        """
        return _TrainAndEvalWhenFitEvaluatesOnTrain(
            name, train_pl, eval_pl, dependencies, validation_names
        )

    @classmethod
    def build_using_fit_and_two_evals(
        cls,
        name: str,
        train_pl: Pipeline,
        train_eval_pl: Pipeline,
        validation_eval_pl: Pipeline,
        validation_names: set[str] = {"validation"},
    ) -> Pipeline:
        """Builds a TrainAndEval pipeline, supporting different eval on train and validation data.

        Args:
        * name: ename for the built pipeline.
        * train_pl: A pipeline that takes data, and outputs models/parameters fitted from the
          data.  Inputs and outputs are assumed to be entires, not collections.
        * train_eval_pl: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          train data.  Inputs and outputs are assumed to be entires, not collections.
        * validation_eval_pl: A pipeline that takes fitted models/parameters and data, and
          evaluates the data using these fitted parameters.  This pipeline will be used on the
          validation data.    Inputs and outputs are assumed to be entires, not collections.

        All outputs of `train_pl` are assumed to be fitted models/parameters.

        This builder uses names to match inputs/outputs across the given pipelines, in the
        following ways:
        1. Inputs of `train_pl` and `train_eval_pl` that share the same name, e.g. X
          become a single inputs to the built pipeline (X.train).  That inputs is passed as X to
          both `train_pl` and `train_eval_pl`.
        2. Outputs of `train_pl` are matched to inputs of `train_eval_pl` and
          `validation_eval_pl` by name, and passed accordingly.

        Returns:
          A pipeline that meets the TrainAndEval pattern.
          * Outputs of `train_pl` that match to inputs of `train_eval_pl` or
            `validation_eval_pl` by name, are assumed to be fitted parameters.  Each such fitted
            parameter is piped from the output of `train_pl` to the input of
            `train_eval_pl` and/or `validation_eval_pl`, and also exposed as an output of
            the TrainAndEval pipeline.
          * Inputs of either of the three pipelines, except those identified as fitted parameters,
            become collection inputs, with `train` entries going to `train_pl` and
            `train_eval_pl`, and `validation` entries going to `validation_eval_pl`.
          * Outputs of `train_eval_pl` and `validation_eval_pl` become collection outputs,
            with `train` entries coming from `train_eval_pl` and `validation` entries coming from
            `validation_eval_pl`.
        """
        return _TrainAndEval(
            name=name,
            train_pl=train_pl,
            eval_pl=train_eval_pl,
            second_eval_pl=validation_eval_pl,
            validation_names=validation_names,
        )

    @classmethod
    def build_using_eval_on_train_and_eval(
        cls,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        validation_names: set[str] = {"validation"},
    ) -> Pipeline:
        """Builds a TrainAndEval pipeline from a fit pipeline and an eval pipeline.

        Args:
        * name: ename for the built pipeline.
        * train_pl: A pipeline that takes data, and outputs models/parameters fitted from the
          data.  Inputs and outputs are assumed to be entires, not collections.
        * eval_pl: A pipeline that takes fitted models/parameters and data, and evaluates the
          data using these fitted parameters.  Will be used on both train data and validation data.
          Inputs and outputs are assumed to be entires, not collections.

        All outputs of `train_pl` are assumed to be fitted models/parameters.

        `eval_pl` is duplicated.  One copy will be used to evaluate on train data and the
        other on validation data.

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
            copy of `eval_pl`, and `validation` entries going to the validation copy of
            `eval_pl`.
          * Outputs of both copies of `eval_pl` become collection outputs, with `train`
            entries coming from the train copy and `validation` entries coming from the validation
            copy.
        """
        return _TrainAndEval(
            name=name,
            train_pl=train_pl,
            eval_pl=eval_pl,
            second_eval_pl=None,
            validation_names=validation_names,
        )
