from dataclasses import dataclass
from itertools import chain
from typing import Iterable, Sequence, final

from ..ux._client import PipelineBuilder
from ..ux._pipeline import Dependency, Pipeline
from ..ux._utils import PipelineUtils


@final
@dataclass(frozen=True, init=False)
class Estimator(Pipeline):
    def __init__(
        self,
        name: str,
        train_pipeline: Pipeline,
        eval_pipeline: Pipeline,
        shared_params: Iterable[Sequence[Dependency]] = ((),),
    ) -> None:
        shared_params = tuple(shared_params)
        if not all(
            dp.in_param.node in eval_pipeline.dag for dp in chain.from_iterable(shared_params)
        ) and not all(
            dp.out_param.node in train_pipeline.dag for dp in chain.from_iterable(shared_params)
        ):
            raise ValueError(
                "All shared parameters must flow from `train_pipeline` to `eval_pipeline`."
            )

        train_pipeline = train_pipeline.decorate(name="train")
        eval_pipeline = eval_pipeline.decorate(name="eval")
        dependencies = (dp.decorate("eval", "train") for dp in chain.from_iterable(shared_params))
        # estimators expose shared parameters from the train_pipeline
        outputs = PipelineUtils.merge_pipeline_outputs(train_pipeline, eval_pipeline)
        pl = PipelineBuilder.combine(
            train_pipeline,
            eval_pipeline,
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
        train_pipeline: Pipeline,
        eval_pipeline: Pipeline,
        shared_params: Iterable[Sequence[Dependency]] = ((),),
    ) -> Estimator:
        return Estimator(name, train_pipeline, eval_pipeline, shared_params)


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
