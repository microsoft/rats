# type: ignore
"""
    A TrainAndEval is a pipeline that fits using train data and evaluates on that same train data
    and on a separate evaluation data.
    A TrainAndEval pipeline takes collection inputs with `train` `eval` entries, and outputs
    collection outputs with `train` `eval` entries.  It also outputs the fitted models as output
    entries.

"""
from __future__ import annotations

from collections import ChainMap, defaultdict
from typing import Any, Literal, Mapping, Sequence, Tuple

from hydra_zen import hydrated_dataclass
from itertools import chain
from omegaconf import MISSING

from ..dag._utils import DAG, find_downstream_nodes
from ..utils import frozendict, orderedset
from ..ux import (
    DependencyOp,
    InCollections,
    InEntry,
    InParameter,
    Inputs,
    OutCollections,
    OutEntry,
    OutParameter,
    Outputs,
    Pipeline,
    PipelineBuilder,
    PipelineConf,
)
from ..ux._utils import (
    _parse_dependencies_to_list,
    filter_in_collections,
    filter_inputs,
    filter_out_collections,
    filter_outputs,
)


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
    ):
        # A config holding the parameters of this TrainAndEval.
        config = TrainAndEvalConf(
            name=name,
            train_pl=train_pl._config,
            eval_pl=eval_pl._config,
            second_eval_pl=None if second_eval_pl is None else second_eval_pl._config,
        )

        # A dictionary from dataset name to the corresponding eval pipeline.
        eval_pls: Mapping[str, Pipeline] = {
            "eval": (second_eval_pl or eval_pl).decorate("eval"),
            "train": eval_pl.decorate("train"),
        }
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
    # for the train data, and if `second_eval_pl` is None, also for the eval data:
    eval_pl: PipelineConf = MISSING  #

    # Evaluation pipeline taking fitted parameters and data and outputting processed data.  If not
    # None, Used for the eval data.  Otherwise, `eval_pl` is used for the eval data:
    second_eval_pl: PipelineConf | None = None


class _TrainAndEvalWhenTrainAlsoEvaluates(ITrainAndEval):
    _config: TrainAndEvalWhenTrainAlsoEvaluatesConf

    def __init__(
        self,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        dependencies: Sequence[DependencyOp],
    ):
        # A config holding the parameters of this TrainAndEval.
        dp_confs = {
            f"d{i}": dp.get_dependencyopconf(pipelines=[train_pl, eval_pl])
            for i, dp in enumerate(dependencies)
        }
        dp_confs = {d: v.rename_pipelineports("train_pl", "eval_pl") for d, v in dp_confs.items()}
        config = TrainAndEvalWhenTrainAlsoEvaluatesConf(
            name=name,
            train_pl=train_pl._config,
            eval_pl=eval_pl._config,
            dependencies=dp_confs,
        )

        eval_inputs_to_train_outputs = {
            dp.out_param.param.name: dp.in_param.param.name
            for dp in chain.from_iterable(dependencies)
        }
        train_outputs_mapping_to_eval_inputs = set(eval_inputs_to_train_outputs.values())

        # Convert inputs, except for those that correspond to train_pl outputs, to collections, and
        # convert all outputs to collections.
        if eval_pl.name != "eval":
            eval_pl = eval_pl.decorate("eval")
        eval_pl = eval_pl.rename_inputs(
            {
                name: f"{name}.eval"
                for name in eval_pl.inputs
                if name not in eval_inputs_to_train_outputs
            }
        ).rename_outputs({name: f"{name}.eval" for name in eval_pl.outputs})

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
            pipelines=[train_pl, eval_pl],
            dependencies=tuple(
                train_pl.outputs[source] >> eval_pl.inputs[target]
                for target, source in eval_inputs_to_train_outputs.items()
            ),
            outputs=ChainMap(
                {name: train_pl.outputs[name] for name in train_pl.outputs},
                {
                    f"{name}.eval": eval_pl.out_collections[name].eval
                    for name in eval_pl.out_collections
                },
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
    _TrainAndEvalWhenTrainAlsoEvaluates,
    zen_wrappers=[
        "${parse_dependencies: ${..dependencies}}",
        _parse_dependencies_to_list,
    ],
)
class TrainAndEvalWhenTrainAlsoEvaluatesConf(PipelineConf):
    name: str = MISSING

    # Train pipeline, taking train data and outputing the fitted parameters and processed train
    # data:
    train_pl: PipelineConf = MISSING
    # Evaluation pipeline taking fitted parameters and eval data, and outputing the
    # processed eval data:
    eval_pl: PipelineConf = MISSING
    # Fitted parameters, expressed as a list of DependencyOpConf between the train and eval
    # pipelines:
    dependencies: Any = ()


class TrainAndEvalBuilders:
    """Builders for TrainAndEval pipelines.

    A TrainAndEval is a pipeline that fits using train data and evaluates on that same train data
    and on a separate eval data.
    A TrainAndEval pipeline takes collection inputs with `train` `eval` entries, and outputs
    collection outputs with `train` `eval` entries.  It also outputs the fitted models as
    output entries.
    """

    @classmethod
    def build_when_train_also_evaluates(
        cls,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        dependencies: Sequence[DependencyOp] = (),
    ) -> Pipeline:
        """Builds a TrainAndEval pipeline when the train pipeline also evaluates train data.

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
          * `train` is a pipeline taking a vector `X` and returning fitted scalars `mean`
            and `std` and standardized array `Z`.
          * `eval` is a pipeline taking scalars `offset` and `scale` and vector `X` and
            returning standardized array `Z`.
          ```python
          w = TrainAndEvalBuilders(
                  "standardize", train, eval,
                  (train.outputs.mean >> eval.inputs.offset,
                   train.outputs.std >> eval.inputs.scale,))
          ```
          Would create `w` as a worfkflow with the following input and outputs:
          * Inputs: `X` (`X.train`, `X.eval`).
          * Outputs: `Z` (`Z.train`, `Z.eval`), `mean`, `std`.
        """
        return _TrainAndEvalWhenTrainAlsoEvaluates(name, train_pl, eval_pl, dependencies)

    @classmethod
    def build_using_train_and_two_evals(
        cls,
        name: str,
        train_pl: Pipeline,
        train_eval_pl: Pipeline,
        eval_eval_pl: Pipeline,
    ) -> Pipeline:
        """Builds a TrainAndEval pipeline, using different eval pipelines for train and eval data.

        Args:
        * name: name for the built pipeline.
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
        )

    @classmethod
    def build_using_train_and_eval(
        cls,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
    ) -> Pipeline:
        """Builds a TrainAndEval pipeline from a fit pipeline and an eval pipeline.

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
          become a single train inputs to the built pipeline (X.train).  That inputs is passed as X
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
          * Outputs of both copies of `eval_pl` become collection outputs, with `train` entries
            coming from the train copy and `eval` entries coming from the eval copy.
        """
        return _TrainAndEval(
            name=name,
            train_pl=train_pl,
            eval_pl=eval_pl,
            second_eval_pl=None,
        )

    @classmethod
    def with_multiple_eval_inputs(
        cls,
        pipeline: Pipeline,
        eval_names: Tuple[str, ...],
    ) -> Pipeline:
        """Builds a pipeline accepting multiple eval inputs from a TrainAndEval pipeline."""
        train_pl, eval_pl = cls.split_pipeline(pipeline)
        eval_pls = [
            (
                eval_pl.decorate(eval_name)
                .rename_inputs({"*.eval": f"*.{eval_name}"})
                .rename_outputs({"*.eval": f"*.{eval_name}"})
            )
            for eval_name in eval_names
        ]
        # Note: we need to specify outputs because there's a bug in the way PipelineBuilder.combine
        # builds the default outputs.
        # See oneml_test.processors.test_pipeline_userio.test_combine_outputs.
        p = PipelineBuilder.combine(
            name=pipeline.name,
            pipelines=[train_pl] + eval_pls,
            dependencies=tuple(
                train_pl.out_collections.fitted >> eval_pl.in_collections.fitted
                for eval_pl in eval_pls
            ),
            outputs=ChainMap(
                {name: train_pl.outputs[name] for name in train_pl.outputs},
                {
                    f"{col_name}.{entry_name}": train_pl.out_collections[col_name][entry_name]
                    for col_name in train_pl.out_collections
                    if col_name != "fitted"
                    for entry_name in train_pl.out_collections[col_name]
                },
                {name: eval_pl.outputs[name] for eval_pl in eval_pls for name in eval_pl.outputs},
                {
                    f"{col_name}.{entry_name}": eval_pl.out_collections[col_name][entry_name]
                    for eval_pl in eval_pls
                    for col_name in eval_pl.out_collections
                    for entry_name in eval_pl.out_collections[col_name]
                },
            ),
        )
        return p

    @classmethod
    def split_pipeline(
        cls,
        train_and_eval_pl: Pipeline,
    ) -> tuple[Pipeline, Pipeline]:
        """Splits a TrainAndEval pipeline into a train pipeline and an eval pipeline.

        Args:
            train_and_eval_pl: A pipeline that meets the TrainAndEval pattern.  Specifically, the
            following assumptions are made:
            * No input, input collection, output or output collection called `fitted`.
            * Any input or output collection that has a `train` or `eval` entry does not have
                any other entries.

        The eval pipeline will be composed of all noded that depends on any `eval` inputs
        entry.  It will have an additional input collection called `fitted`.

        The train pipeline will be composed of all the other nodes.  It will have an additional
        output collection called `fitted`.

        Edges that cross from the train pipeline to the eval pipeline will be converted to entries
        in the `fitted` output collection of the train pipeline, and input entries in the `fitted`
        input collection of the eval pipeline.  The entry names will be composed from their
        source's output port name (in the train pipeline) plus a sequential suffix for uniqueness.

        By definition, no edges cross from the eval pipeline to the train pipeline.
        """

        def validate_io(iol: Literal["input", "output"]) -> None:
            if iol == "input":
                pll = "eval"
                io: Inputs | Outputs = train_and_eval_pl.inputs
                ioc: InCollections | OutCollections = train_and_eval_pl.in_collections
            else:
                pll = "train"
                io = train_and_eval_pl.outputs
                ioc = train_and_eval_pl.out_collections
            if "fitted" in io or "fitted" in ioc:
                raise ValueError(
                    f"Pipeline already has a `fitted` {iol}.  Please rename it because "
                    f"we need it for the {iol}s of the {pll} pipeline."
                )
            train_and_eval_entry_names = frozenset(("train", "eval"))
            for collection_name, collection in ioc.items():
                entry_names = frozenset(collection)
                intersection = entry_names & train_and_eval_entry_names
                if intersection:
                    other_entry_names = entry_names - train_and_eval_entry_names
                    if other_entry_names:
                        raise ValueError(
                            f"{iol} collection {collection_name} has entries {intersection} but "
                            f"also other entries: {other_entry_names}"
                        )

        validate_io("input")
        validate_io("output")

        eval_nodes = {
            node: train_and_eval_pl._dag.nodes[node]
            for node in find_downstream_nodes(
                train_and_eval_pl._dag,
                (
                    in_param.node
                    for collection in train_and_eval_pl.in_collections.values()
                    for entry_name, entry in collection.items()
                    if entry_name == "eval"
                    for in_param in entry
                ),
            )
        }
        eval_dependencies = frozendict(
            {
                node: orderedset(dp for dp in dependencies if dp.node in eval_nodes)
                for node, dependencies in train_and_eval_pl._dag.dependencies.items()
                if node in eval_nodes
            }
        )
        eval_dag = DAG(nodes=eval_nodes, dependencies=eval_dependencies)

        train_nodes = {
            node: train_and_eval_pl._dag.nodes[node]
            for node in train_and_eval_pl._dag.nodes
            if node not in eval_nodes
        }
        train_dependencies = frozendict(
            {
                node: dependencies
                for node, dependencies in train_and_eval_pl._dag.dependencies.items()
                if node not in eval_nodes
            }
        )
        train_dag = DAG(nodes=train_nodes, dependencies=train_dependencies)

        fitted_param_names = defaultdict[str, int](int)
        fitted_outputs = dict[str, OutParameter]()
        fitted_inputs = defaultdict[str, list[InParameter]](list)
        for node, dependencies in train_and_eval_pl._dag.dependencies.items():
            for dependency in dependencies:
                if node in eval_nodes and dependency.node in train_nodes:
                    source_node = dependency.node
                    source_param = dependency.out_arg
                    target_node = node
                    target_param = dependency.in_arg
                    copy_number = fitted_param_names[source_param.name]
                    fitted_param_names[source_param.name] = copy_number + 1
                    entry_name = f"{source_param.name}_{copy_number}"
                    fitted_outputs[entry_name] = OutParameter(source_node, source_param)
                    fitted_inputs[entry_name].append(InParameter(target_node, target_param))

        def is_train_param(param: InParameter | OutParameter) -> bool:
            return param.node in train_nodes

        def is_eval_param(param: InParameter | OutParameter) -> bool:
            return param.node in eval_nodes

        eval_inputs = filter_inputs(train_and_eval_pl.inputs, is_eval_param)
        eval_in_collections = InCollections(
            fitted=Inputs(
                {entry_name: InEntry(in_params) for entry_name, in_params in fitted_inputs.items()}
            )
        ) | filter_in_collections(train_and_eval_pl.in_collections, is_eval_param)
        eval_outputs = filter_outputs(train_and_eval_pl.outputs, is_eval_param)
        eval_out_collections = filter_out_collections(
            train_and_eval_pl.out_collections, is_eval_param
        )

        eval_pl = Pipeline(
            name=train_and_eval_pl.name,
            dag=eval_dag,
            inputs=eval_inputs,
            in_collections=eval_in_collections,
            outputs=eval_outputs,
            out_collections=eval_out_collections,
            config=PipelineConf(),  # TODO: fix config!
        ).decorate("eval")

        train_inputs = filter_inputs(train_and_eval_pl.inputs, is_train_param)
        train_in_collections = filter_in_collections(
            train_and_eval_pl.in_collections, is_train_param
        )

        train_outputs = filter_outputs(train_and_eval_pl.outputs, is_train_param)
        train_out_collections = OutCollections(
            fitted=Outputs(
                {
                    entry_name: OutEntry((out_param,))
                    for entry_name, out_param in fitted_outputs.items()
                }
            )
        ) | filter_out_collections(train_and_eval_pl.out_collections, is_train_param)
        train_pl = Pipeline(
            name=train_and_eval_pl.name,
            dag=train_dag,
            inputs=train_inputs,
            in_collections=train_in_collections,
            outputs=train_outputs,
            out_collections=train_out_collections,
            config=PipelineConf(),  # TODO: fix config!
        ).decorate("train")

        return train_pl, eval_pl
