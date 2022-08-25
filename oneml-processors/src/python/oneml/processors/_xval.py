# type: ignore
from typing import Any, Mapping, Tuple, Type, TypeVar

from ._pipeline import IExpandPipeline, IPrunePipeline, Namespace, PDependency, Pipeline, PNode
from ._processor import Processor, Provider

T = TypeVar("T", covariant=True)  # output mapping of processors
M = Mapping[str, T]  # mapping for processor inputs and outputs
TI = TypeVar("TI", bound=Type[Any], contravariant=True)  # generic input types for processor
TO = TypeVar("TO", bound=Type[Any], covariant=True)  # generic output types for processor


# WIP!!


class DataSplitter(Processor[T]):
    def __init__(self, num_folds: int) -> None:
        assert num_folds > 0

        super().__init__()
        self._num_folds = num_folds

    def process(self, X: Any = None, Y: Any = None) -> M[T]:
        return super().process()

    @property
    def num_folds(self) -> int:
        return self._num_folds


class XValTrain(IExpandPipeline[T, TI, TO]):
    _pipeline: Pipeline[T, TI, TO]
    _data_splitter: DataSplitter[T]
    _summary: Provider[T]

    def __init__(
        self, num_folds: int, data_splitter: DataSplitter[T], pipeline: Pipeline[T, TI, TO]
    ) -> None:
        super().__init__()
        self._data_splitter = data_splitter
        self._summary = Provider()
        self._pipeline = pipeline

    def expand(self) -> Pipeline[T, TI, TO]:
        kfolds = []
        datasplit = PNode("data_splitter")
        tail_dependencies: Tuple[PDependency[TI, TO], ...] = ()
        # insert datasplit onto external dependencies
        new_pipeline = self._pipeline.substitute_external_dependencies(datasplit)
        for k in range(self.num_folds):
            ns = Namespace(f"fold{k}")
            new_kfold = new_pipeline.decorate(ns)  # decorate each kfold
            # remove tail if last node exists and accumulate tail_dependencies
            if len(new_kfold.end_nodes) == 1 and new_kfold.end_nodes[0].key == "tail":
                tail_dependencies += new_kfold.dependencies[new_kfold.end_nodes[0]]
                new_kfold = new_kfold.pop(new_kfold.end_nodes[0])
            kfolds.append(new_kfold)

        folds_pipeline: Pipeline[T, TI, TO] = sum(kfolds, start=Pipeline())  # merge kfold
        tail = PNode("summary")  # create new tail for xval_train pipeline
        datasplit_and_tail_pipeline = Pipeline(  # create new pipeline w/ datasplit and summary
            {datasplit: self._data_splitter, tail: self._summary},
            {datasplit: self._pipeline.external_dependencies, tail: tail_dependencies},
        )

        return folds_pipeline + datasplit_and_tail_pipeline

    @property
    def num_folds(self) -> int:
        return self._data_splitter.num_folds


class XValEval(IPrunePipeline[T, TI, TO]):
    _xval_train: Pipeline[T, TI, TO]
    _summary: Provider[T]

    def __init__(self, xval_train: Pipeline[T, TI, TO]) -> None:
        super().__init__()
        self._xval_train = xval_train
        self._summary = Provider()

    def prune(self) -> Pipeline[T, TI, TO]:
        prune_pipeline: Tuple[Pipeline[T, TI, TO], ...] = ()
        train_ns = Namespace("train")
        for node, provider in self._xval_train.nodes.items():
            if train_ns in node.namespace:
                prune_pipeline += (Pipeline({node: provider}),)

        datasplit = PNode("data_splitter")
        datasplit_dps = self._xval_train.dependencies[datasplit]  # get datasplit dependencies
        new_pipeline = self._xval_train.pop(datasplit)  # remove datasplit
        for node, dps in new_pipeline.dependencies.items():
            if datasplit in (dp.node for dp in dps):
                # remove lingering datasplit depenencies
                newds = tuple(dp for dp in (set(dps) | set(datasplit_dps)) if dp.node != datasplit)
                new_pipeline.dependencies[node] = newds

        return new_pipeline - sum(prune_pipeline, start=Pipeline())
