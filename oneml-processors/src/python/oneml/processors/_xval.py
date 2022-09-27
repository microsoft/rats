# type: ignore
from typing import Any, Mapping, TypeVar

from ._pipeline import IExpandPipeline, IPrunePipeline, Namespace, PDependency, Pipeline, PNode
from ._processor import IProcessor, Provider

T = TypeVar("T", covariant=True)  # output mapping of processors
M = Mapping[str, T]  # mapping for processor inputs and outputs


# WIP!!


class DataSplitter(IProcessor[T]):
    def __init__(self, num_folds: int) -> None:
        assert num_folds > 0

        super().__init__()
        self._num_folds = num_folds

    def process(self, X: Any = None, Y: Any = None) -> M[T]:
        return super().process()

    @property
    def num_folds(self) -> int:
        return self._num_folds


class XValTrain(IExpandPipeline):
    _pipeline: Pipeline
    _data_splitter: DataSplitter[T]
    _summary: Provider[T]

    def __init__(self, num_folds: int, data_splitter: DataSplitter[T], pipeline: Pipeline) -> None:
        super().__init__()
        self._data_splitter = data_splitter
        self._summary = Provider()
        self._pipeline = pipeline

    def expand(self) -> Pipeline:
        kfolds = []
        datasplit = PNode("data_splitter")
        tail_dependencies: tuple[PDependency, ...] = ()
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

        folds_pipeline: Pipeline = sum(kfolds, start=Pipeline())  # merge kfold
        tail = PNode("summary")  # create new tail for xval_train pipeline
        datasplit_and_tail_pipeline = Pipeline(  # create new pipeline w/ datasplit and summary
            {datasplit: self._data_splitter, tail: self._summary},
            {datasplit: self._pipeline.external_dependencies, tail: tail_dependencies},
        )

        return folds_pipeline + datasplit_and_tail_pipeline

    @property
    def num_folds(self) -> int:
        return self._data_splitter.num_folds


class XValEval(IPrunePipeline):
    _xval_train: Pipeline
    _summary: Provider[T]

    def __init__(self, xval_train: Pipeline) -> None:
        super().__init__()
        self._xval_train = xval_train
        self._summary = Provider()

    def prune(self) -> Pipeline:
        prune_pipeline: tuple[Pipeline, ...] = ()
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
