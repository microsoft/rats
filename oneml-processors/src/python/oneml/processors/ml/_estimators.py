from dataclasses import dataclass
from itertools import chain
from typing import Iterable, Sequence, final

from ..ux._builder import PipelineBuilder, UserOutput
from ..ux._pipeline import Dependency, Pipeline


@final
@dataclass(frozen=True, init=False)
class Estimator(Pipeline):
    def __init__(
        self,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        shared_params: Iterable[Sequence[Dependency]] = ((),),
    ) -> None:
        shared_params = tuple(shared_params)
        if not isinstance(name, str):
            raise ValueError("`name` needs to be of `str` type.")
        if not isinstance(train_pl, Pipeline):
            raise ValueError("`train_pl` needs to be of `Pipeline` type.")
        if not isinstance(eval_pl, Pipeline):
            raise ValueError("`eval_pl` needs to be of `Pipeline` type.")
        if not all(dp.in_param.node in eval_pl.dag for dp in chain.from_iterable(shared_params)):
            raise ValueError("All shared parameters must flow from `train_pl` to `eval_pl`.")
        if not all(dp.out_param.node in train_pl.dag for dp in chain.from_iterable(shared_params)):
            raise ValueError("All shared parameters must flow from `train_pl` to `eval_pl`.")

        in_common = set(train_pl.inputs) & set(eval_pl.inputs)
        out_common = set(train_pl.outputs) & set(eval_pl.outputs)
        train_pl = train_pl.rename_inputs({v: v + ".train" for v in in_common})
        train_pl = train_pl.rename_outputs({v: v + ".train" for v in out_common})
        train_pl = train_pl.decorate("train")
        eval_pl = eval_pl.rename_inputs({v: v + ".eval" for v in in_common})
        eval_pl = eval_pl.rename_outputs({v: v + ".eval" for v in out_common})
        eval_pl = eval_pl.decorate("eval")
        dependencies = (dp.decorate("eval", "train") for dp in chain.from_iterable(shared_params))
        outputs: UserOutput = dict(train_pl.outputs | eval_pl.outputs)
        outputs |= dict(train_pl.out_collections | eval_pl.out_collections)
        p = PipelineBuilder.combine(
            train_pl,
            eval_pl,
            name=name,
            outputs=outputs,
            dependencies=(tuple(dependencies),),
        )
        super().__init__(name, p.dag, p.inputs, p.outputs, p.in_collections, p.out_collections)


class EstimatorClient:
    @classmethod
    def estimator(
        cls,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        shared_params: Iterable[Sequence[Dependency]] = ((),),
    ) -> Estimator:
        return Estimator(name, train_pl, eval_pl, shared_params)


@final
@dataclass(frozen=True)
class XVal(Pipeline):
    pass
    # data_splitter


@final
@dataclass(frozen=True)
class HPO(Pipeline):
    pass
    # search_space: dict[str, Any]
