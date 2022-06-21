import dataclasses
from typing import Any, Dict, List, Tuple

from .dag import Inputs, Nodes
from .processor import Processor, ProcessorProvider
from .step import Matrix, Output, Predictions, Vector


class MyDag(Processor):
    nodes: Dict[str, Processor] = dataclasses.asdict(Nodes())  # nodes or providers?
    edges: Dict[str, Dict[str, str]] = dataclasses.asdict(Inputs())
    inputs: Dict[str, str] = {"X": Matrix, "Y": Vector}
    outputs: Output = {"Z": Predictions}


class Objective:
    def __init__(self, processor_provider: ProcessorProvider, metric: List[str]) -> None:
        super().__init__()
        self.processor_provider = processor_provider
        self.metric = metric

    def __call__(self, X: Matrix, Y: Vector, config: Dict[str, Any]) -> Output:
        config_sample = self._draw_config(config)
        processor = self.processor_provider(config_sample)
        result = processor.process(X, Y)
        metric = self._get_metric_from_result(result)
        return metric

    def _draw_config(self, config: Dict[str, Any]):
        pass

    def _get_metric_from_result(self, result: Output):
        pass


class HPO(Processor):
    def __init__(self, objective: Objective, search_space, algorithm, num_trials: int) -> None:
        super().__init__()
        self.objective = objective
        self.search_space = search_space
        self.algorithm = algorithm
        self.num_trials = num_trials

    def process(self, X: Matrix, Y: Vector) -> Output:
        pass


class XVal(Processor):
    def __init__(self, processor: Processor, num_folds: int) -> None:
        super().__init__()
        self.processor = processor
        self.num_folds = num_folds

    def process(self, X: Matrix, Y: Vector) -> Output:
        for i, (Xs, Ys) in enumerate(self._split_ds(X, Y, self.num_folds)):
            result = self.processor(Xs, Ys)
        return result

    def _split_ds(self, X: Matrix, Y: Vector, num_folds: int) -> Tuple[Matrix, Vector]:
        pass
