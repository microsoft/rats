"""An estimator is a pipeline that takes training data and eval data.

An estimator trains some model using only the training data, and then applies that model to the
holdout data.

We define a standard to the inputs and outputs of an estimator.  This allows other software
components to assume this standard and operate on any estimator.

Let `e` be an estimator object.
* `e` is a `Pipeline`.
* `len(e.inputs)==0`, i.e. an estimator does not take simple inputs, just collection inputs.
* `e.in_collections` hold either `train` entries, `eval` entries, or both, but no other entries.
* The nodes of an estimator pipeline are defined as `train`` nodes if they DO NOT depend on `eval`
   input entries.  The are defined as `eval` nodes if they DO depend on `eval` input entries.
   Note that `eval` nodes are allowed to depend on `train` input entries.
* `e.out_collections` hold either `train` entries, `eval` entries, or both, but no other entries.
* `train` output entries can only be outputs of `train` nodes (and therefore cannot depend on
   `eval` inputs).
* `e.outputs` are fitted parameters, i.e. outputs of `train` nodes that are inputs of `eval` nodes.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import chain
from typing import Any, Generic, cast, final

from hydra_zen import hydrated_dataclass
from omegaconf import MISSING

from ..ux import (
    CombinedPipeline,
    DependencyOp,
    Pipeline,
    PipelineConf,
    TInputs,
    TOutputs,
    UPipeline,
    UserOutput,
)
from ..ux._utils import _parse_dependencies_to_list


@final
class Estimator(Pipeline[TInputs, TOutputs]):
    _config: EstimatorConf

    def __init__(
        self,
        name: str,
        train_pl: UPipeline,
        eval_pl: UPipeline,
        dependencies: Sequence[DependencyOp[Any]] | None = None,
    ) -> None:
        dependencies = tuple(dependencies) if dependencies is not None else ()
        if not isinstance(name, str):
            raise ValueError("`name` needs to be of `str` type.")
        if not isinstance(train_pl, Pipeline):
            raise ValueError("`train_pl` needs to be of `Pipeline` type.")
        if not isinstance(eval_pl, Pipeline):
            raise ValueError("`eval_pl` needs to be of `Pipeline` type.")
        if not all(dp.in_param.node in eval_pl._dag for dp in chain.from_iterable(dependencies)):
            raise ValueError("All shared parameters must flow from `train_pl` to `eval_pl`.")
        if not all(dp.out_param.node in train_pl._dag for dp in chain.from_iterable(dependencies)):
            raise ValueError("All shared parameters must flow from `train_pl` to `eval_pl`.")

        # find shared parameters between train and eval
        in_common = set(train_pl.inputs) & set(eval_pl.inputs)
        out_common = set(train_pl.outputs) & set(eval_pl.outputs)

        # rename shared parameters into train & eval entries of collections
        new_train = train_pl.rename_inputs({v: v + ".train" for v in in_common})
        new_eval = eval_pl.rename_inputs({v: v + ".eval" for v in in_common})
        new_train = new_train.rename_outputs({v: v + ".train" for v in out_common})
        new_eval = new_eval.rename_outputs({v: v + ".eval" for v in out_common})

        # decorate train and eval pipelines for tracking purposes
        new_train = new_train.decorate("train")  # TODO: implement decorate config
        new_eval = new_eval.decorate("eval")

        # decorate shared dependencies to match newly decorated train and eval pipelines
        new_dps = tuple(dp_op.decorate("eval", "train") for dp_op in dependencies)

        # merge the `outputs` and `out_collections` of train and eval pipelines
        outputs: UserOutput = (new_train.outputs | new_eval.outputs)._asdict()

        # combine all ingredients into a new pipeline
        p: UPipeline = CombinedPipeline(
            pipelines=[new_train, new_eval],
            name=name,
            outputs=outputs,
            dependencies=new_dps,
        )
        dp_confs = {
            f"d{i}": dp.get_dependencyopconf(pipelines=[train_pl, eval_pl])
            for i, dp in enumerate(dependencies)
        }
        dp_confs = {d: v.rename_pipelineports("eval_pl", "train_pl") for d, v in dp_confs.items()}
        config = EstimatorConf(
            name=name, train_pl=train_pl._config, eval_pl=eval_pl._config, dependencies=dp_confs
        )
        super().__init__(other=cast(Pipeline[TInputs, TOutputs], p), config=config)


@hydrated_dataclass(
    Estimator,
    zen_wrappers=[
        "${parse_strs: 1, train_pl, eval_pl}",
        "${parse_dependencies: ${..dependencies}}",
        _parse_dependencies_to_list,
    ],
)
class EstimatorConf(PipelineConf):
    name: str = MISSING
    train_pl: Any = MISSING
    eval_pl: Any = MISSING
    dependencies: Any = None


class EstimatorClient(Generic[TInputs, TOutputs]):
    @classmethod
    def estimator(
        cls,
        name: str,
        train_pl: UPipeline,
        eval_pl: UPipeline,
        dependencies: Sequence[DependencyOp[Any]] | None = None,
    ) -> Estimator[TInputs, TOutputs]:
        return Estimator(name, train_pl, eval_pl, dependencies)
