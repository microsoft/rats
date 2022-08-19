# type: ignore
# flake8: noqa
import dataclasses
from typing import Any, Dict, List, Tuple

from .dag import Inputs, Nodes
from .processor import Estimator, Processor, ProcessorProvider, Transformer, TransformerProvider
from .step import Dataset, Matrix, Output, Predictions, Vector


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


class HPO(Estimator):
    def __init__(self, objective: Objective, search_space, algorithm, num_trials: int) -> None:
        super().__init__()
        self.objective = objective
        self.search_space = search_space
        self.algorithm = algorithm
        self.num_trials = num_trials
        self._transformer_provider = objective.processor_provider

    def process(self, X: Matrix, Y: Vector) -> Output:
        pass


class DatasetSplitter(Transformer):
    def __init__(self, splits: int) -> None:
        super().__init__()
        self.splits = splits

    def process(self, dataset: Dataset) -> Output:
        pass


class XVal(Estimator):
    _num_folds: int
    _transformer_provider: TransformerProvider

    nodes: Dict[str, Processor]
    edges: Dict[str, Dict[str, str]]
    inputs: Dict[str, str] = {"X": Matrix, "Y": Vector}
    outputs: Dict[str, str] = {"Z": Predictions}

    def __init__(self, processor: Processor, num_folds: int) -> None:
        super().__init__()
        self._num_folds = num_folds
        self.nodes = {f"fold{i}": processor for i in range(num_folds)}
        self.nodes["dataset_splitter"] = DatasetSplitter(num_folds)
        self.edges = {
            f"fold{i}": {"X": "dataset_splitter.X{i}", "Y": "dataset_splitter.Y{i}"}
            for i in range(num_folds)
        }
        self.edges["dataset_splitter"] + {"input.X", "input.Y"}
        self._transformer_provider = (
            processor._transformer_provider if isinstance(processor, Estimator) else processor
        )

    def process(self, X: Matrix, Y: Vector) -> Output:
        for i, (Xs, Ys) in enumerate(self._split_ds(X, Y, self.num_folds)):
            result = self.processor(Xs, Ys)
        return result

    def _split_ds(self, X: Matrix, Y: Vector, num_folds: int) -> Tuple[Matrix, Vector]:
        pass
