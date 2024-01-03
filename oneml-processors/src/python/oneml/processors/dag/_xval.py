# type: ignore
from collections.abc import Mapping
from typing import Any

from ._dag import DAG, DagDependency, DagNode, IExpandDag, IPruneDag, Namespace
from ._processor import IProcess, Provider

T = Mapping[str, Any]  # mapping for processor inputs and outputs


class DataSplitter(IProcess):
    def __init__(self, num_folds: int) -> None:
        assert num_folds > 0

        super().__init__()
        self._num_folds = num_folds

    def process(self, X: Any, Y: Any) -> T:
        return super().process()

    @property
    def num_folds(self) -> int:
        return self._num_folds


class XValTrain(IExpandDag):
    _dag: DAG
    _data_splitter: DataSplitter
    _summary: Provider

    def __init__(self, num_folds: int, data_splitter: DataSplitter, dag: DAG) -> None:
        super().__init__()
        self._data_splitter = data_splitter
        self._summary = Provider()
        self._dag = dag

    def expand(self) -> DAG:
        kfolds = []
        datasplit = DagNode("data_splitter")
        tail_dependencies: tuple[DagDependency, ...] = ()
        # insert datasplit onto external dependencies
        new_pipeline = self._dag.substitute_external_dependencies(datasplit)
        for k in range(self.num_folds):
            ns = Namespace(f"fold{k}")
            new_kfold = new_pipeline.decorate(ns)  # decorate each kfold
            # remove tail if last node exists and accumulate tail_dependencies
            if len(new_kfold.end_nodes) == 1 and new_kfold.end_nodes[0].key == "tail":
                tail_dependencies += new_kfold.dependencies[new_kfold.end_nodes[0]]
                new_kfold = new_kfold.pop(new_kfold.end_nodes[0])
            kfolds.append(new_kfold)

        folds_pipeline: DAG = sum(kfolds, start=DAG())  # merge kfold
        tail = DagNode("summary")  # create new tail for xval_train dag
        datasplit_and_tail_pipeline = DAG(  # create new dag w/ datasplit and summary
            {datasplit: self._data_splitter, tail: self._summary},
            {datasplit: self._dag.external_dependencies, tail: tail_dependencies},
        )

        return folds_pipeline + datasplit_and_tail_pipeline

    @property
    def num_folds(self) -> int:
        return self._data_splitter.num_folds


class XValEval(IPruneDag):
    _xval_train: DAG
    _summary: Provider

    def __init__(self, xval_train: DAG) -> None:
        super().__init__()
        self._xval_train = xval_train
        self._summary = Provider()

    def prune(self) -> DAG:
        prune_pipeline: tuple[DAG, ...] = ()
        train_ns = Namespace("train")
        for node, provider in self._xval_train.nodes.items():
            if train_ns in node.namespace:
                prune_pipeline += (DAG({node: provider}),)

        datasplit = DagNode("data_splitter")
        datasplit_dps = self._xval_train.dependencies[datasplit]  # get datasplit dependencies
        new_pipeline = self._xval_train.pop(datasplit)  # remove datasplit
        for node, dps in new_pipeline.dependencies.items():
            if datasplit in (dp.node for dp in dps):
                # remove lingering datasplit depenencies
                newds = tuple(dp for dp in (set(dps) | set(datasplit_dps)) if dp.node != datasplit)
                new_pipeline.dependencies[node] = newds

        return new_pipeline - sum(prune_pipeline, start=DAG())
