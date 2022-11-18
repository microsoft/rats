from dataclasses import dataclass
from itertools import chain
from typing import Iterable, Sequence, final

from ..ux._client import PipelineBuilder
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

        train_pl = train_pl.rename({train_pl.name: "train"}).decorate(name="train")
        eval_pl = eval_pl.rename({eval_pl.name: "eval"}).decorate(name="eval")
        dependencies = (dp.decorate("eval", "train") for dp in chain.from_iterable(shared_params))
        outputs = train_pl.outputs | eval_pl.outputs  # estimators expose shared parameters
        pl = PipelineBuilder.combine(
            train_pl,
            eval_pl,
            name=name,
            outputs=outputs,
            dependencies=(tuple(dependencies),),
        )
        super().__init__(name, pl.dag, pl.inputs, pl.outputs)


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
