from dataclasses import dataclass
from itertools import chain
from typing import Iterable, Sequence, final

from ..ux._client import WorkflowClient
from ..ux._utils import WorkflowUtils
from ..ux._workflow import Dependency, Workflow


@final
@dataclass(frozen=True, init=False)
class Estimator(Workflow):
    def __init__(
        self,
        name: str,
        train_wf: Workflow,
        eval_wf: Workflow,
        shared_params: Iterable[Sequence[Dependency]] = ((),),
    ) -> None:
        shared_params = tuple(shared_params)
        if not all(
            dp.in_param.node in eval_wf.pipeline for dp in chain.from_iterable(shared_params)
        ) and not all(
            dp.out_param.node in train_wf.pipeline for dp in chain.from_iterable(shared_params)
        ):
            raise ValueError("All shared parameters must flow from `train_wf` to `eval_wf`.")

        train_wf = train_wf.decorate(name="train")
        eval_wf = eval_wf.decorate(name="eval")
        dependencies = (dp.decorate("eval", "train") for dp in chain.from_iterable(shared_params))
        # estimators expose shared parameters from the train_wf
        outputs = WorkflowUtils.merge_workflow_outputs(train_wf, eval_wf)
        wf = WorkflowClient.combine(
            train_wf, eval_wf, name=name, outputs=outputs, dependencies=(tuple(dependencies),)
        )
        super().__init__(name, wf.pipeline, wf.inputs, wf.outputs)


class EstimatorClient:
    @classmethod
    def estimator(
        cls,
        name: str,
        train_wf: Workflow,
        eval_wf: Workflow,
        shared_params: Iterable[Sequence[Dependency]] = ((),),
    ) -> Estimator:
        return Estimator(name, train_wf, eval_wf, shared_params)


@final
@dataclass(frozen=True)
class XVal(Workflow):
    pass
    # data_splitter


@final
@dataclass(frozen=True)
class HPO(Workflow):
    pass
    # search_space: dict[str, Any]
