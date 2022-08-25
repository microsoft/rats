# type: ignore
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, Generic, List, Protocol, Tuple, TypeVar

from hydra.utils import instantiate
from omegaconf import DictConfig

from oneml.lorenzo.pipelines3._example._gui import DagSvg, DotDag
from oneml.pipelines import IExecutable, PipelineNodeState, StorageClient, StorageItemKey

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class Namespace:
    key: str = ""

    def __add__(self, namespace: Namespace) -> Namespace:
        return Namespace(self.key + ("/" if self.key and namespace.key else "") + namespace.key)

    def __contains__(self, namespace: Namespace) -> bool:
        return namespace.key in self.key

    def __post_init__(self) -> None:
        if len(self.key) > 0:
            assert self.key[0] != "/" and self.key[-1] != "/", """No leading nor trailing "/"."""

    def __repr__(self) -> str:
        return "/" + self.key + ("/" if self.key else "")

    def to_node(self) -> PipelineNode:
        names = self.key.split("/")
        assert len(self.key) > 0, """Root namespace "/" cannot be converted to node."""
        return PipelineNode(names[-1], Namespace("/".join(names[:-1])))


@dataclass(frozen=True)
class PipelineNode:
    key: str
    namespace: Namespace = Namespace()

    def __repr__(self) -> str:
        return repr(self.namespace) + self.key

    def decorate(self, namespace: Namespace) -> PipelineNode:
        return PipelineNode(key=self.key, namespace=namespace + self.namespace)


@dataclass(frozen=True)
class PipelineData(Generic[T]):
    name: str

    def __repr__(self) -> str:
        return self.name


@dataclass(frozen=True)
class NodeDependency(Generic[T]):
    node: PipelineNode
    args: Tuple[PipelineData[T], ...] = ()

    def __repr__(self) -> str:
        return repr(self.node) + str(self.args)

    def decorate(self, namespace: Namespace) -> NodeDependency[T]:
        return NodeDependency(self.node.decorate(namespace), self.args)


class NodeProvider(IExecutable):
    _config: DictConfig
    _inputs: List[StorageItemKey[Any]]
    _storage: StorageClient

    def _get_node(self) -> IExecutable:
        loaded_inputs = {k: self._storage.get_storage_item(k) for k in self._inputs}
        return instantiate(self._config, _partial_=True)(**loaded_inputs)

    def execute(self) -> None:
        self._get_node().execute()

    def get_input_schema(self) -> Dict[Any, Any]:
        return {}

    def get_output_schema(self) -> Dict[Any, Any]:
        return {}


@dataclass(frozen=True)
class Pipeline(Generic[T]):
    nodes: Dict[PipelineNode, NodeProvider] = field(default_factory=dict)
    dependencies: Dict[PipelineNode, Tuple[NodeDependency[T], ...]] = field(default_factory=dict)

    def __add__(self, pipeline: Pipeline[T]) -> Pipeline[T]:
        assert all(
            self.nodes[node] == pipeline.nodes[node]
            for node in set(self.nodes.keys()) & set(pipeline.nodes.keys())
        ), "Nodes in both pipelines need to have same NodeProvider."
        new_nodes = {**self.nodes, **pipeline.nodes}  # overloaded nodes point to same NodeProvider
        new_dependencies = self.dependencies.copy()
        for node, dependencies in pipeline.dependencies.items():
            new_dependencies[node] = tuple(set(new_dependencies.get(node, ()) + dependencies))
        return Pipeline(new_nodes, new_dependencies)

    def __sub__(self, pipeline: Pipeline[T]) -> Pipeline[T]:
        new_nodes = {n: p for n, p in self.nodes.items() if n not in pipeline}
        new_dependencies = {n: dps for n, dps in self.dependencies.items() if n not in pipeline}
        return Pipeline(new_nodes, new_dependencies)

    def __contains__(self, node: PipelineNode) -> bool:
        return node in self.nodes

    def __len__(self) -> int:
        return len(self.nodes)

    def __post_init__(self) -> None:
        assert len(self.nodes) >= len(self.dependencies)
        assert all(node in self.nodes for node in self.dependencies.keys())
        for node in set(self.nodes) - set(self.dependencies.keys()):
            self.dependencies[node] = ()

    def __repr__(self) -> str:
        return f"Pipeline(nodes = {tuple(self.nodes.keys())}, dependencies = {self.dependencies})"

    def decorate(self, namespace: Namespace) -> Pipeline[T]:
        nodes: Dict[PipelineNode, NodeProvider] = {}
        dependencies: Dict[PipelineNode, Tuple[NodeDependency[T], ...]] = {}

        for node, provider in self.nodes.items():
            new_node = node.decorate(namespace)
            nodes[new_node] = provider
            dependencies[new_node] = tuple(
                dp.decorate(namespace) if dp not in self.external_dependencies else dp
                for dp in self.dependencies[node]
            )

        return Pipeline(nodes, dependencies)

    # def add_dependency(
    #     self,
    #     dependency: PipelineNode,
    #     condition: Callable[[PipelineNode], bool] = lambda node: True,
    # ) -> Pipeline:
    #     """Adds dependency to nodes that satisfy the specified condition."""
    #     dependencies = self.dependencies.copy()
    #     for node in self.nodes:
    #         if condition(node):
    #           dependencies[node] += (dependency,) if dependency not in dependencies[node] else ()
    #     return Pipeline(self.nodes, dependencies)

    # def sub_dependency(
    #     self,
    #     dependency: PipelineNode,
    #     condition: Callable[[PipelineNode], bool] = lambda node: False,
    # ) -> Pipeline:
    #     """Removes dependency to nodes that satisfy the specified condition."""
    #     dependencies = self.dependencies.copy()
    #     for node in self.nodes:
    #         dependencies[node] = tuple(dp for dp in dependencies[node] if not condition(dp))
    #     return Pipeline(self.nodes, dependencies)

    def substitute_external_dependencies(self, node: PipelineNode) -> Pipeline[T]:
        """Substitute external dependencies of self.start_nodes with node.

        Example:
            A -> B and A -> C, change to A, node -> B, node -> C.

        """
        assert len(set(dp.node for dp in self.external_dependencies)) == 1
        ext_node = self.external_dependencies[0].node
        dependencies = self.dependencies.copy()
        for sn in self.start_nodes:
            dependencies[sn] = tuple(
                dp if ext_node != dp.node else NodeDependency(node, dp.args)
                for dp in dependencies[sn]
            )
        return Pipeline(self.nodes, dependencies)

    def pop(self, node: PipelineNode) -> Pipeline[T]:
        nodes = self.nodes.copy()
        dependencies = self.dependencies.copy()
        nodes.pop(node)
        dependencies.pop(node)
        return Pipeline(nodes, dependencies)

    @cached_property
    def all_dependencies(self) -> Tuple[NodeDependency[T], ...]:
        """All dependencies gathered from all nodes in the pipeline."""
        return tuple(set((dp for dps in self.dependencies.values() for dp in dps)))

    @cached_property
    def external_dependencies(self) -> Tuple[NodeDependency[T], ...]:
        """Dependencies that point to other nodes not from the pipeline."""
        return tuple(dp for dp in self.all_dependencies if dp.node not in self.nodes.keys())

    @cached_property
    def internal_dependencies(self) -> Tuple[NodeDependency[T], ...]:
        """Dependencides that point to other nodes within the pipeline."""
        return tuple(set(self.all_dependencies) - set(self.external_dependencies))

    @cached_property
    def start_nodes(self) -> Tuple[PipelineNode, ...]:
        """Nodes with external dependencies or no dependencies with internal nodes."""
        return tuple(
            n
            for n in self.nodes
            if set(self.external_dependencies) & set(self.dependencies[n])
            or not (set(self.nodes) & set(dp.node for dp in self.dependencies[n]))
        )

    @cached_property
    def end_nodes(self) -> Tuple[PipelineNode, ...]:
        """Nodes that other nodes in the pipeline do not depend on."""
        return tuple(set(self.nodes) - set(dp.node for dp in self.internal_dependencies))

    def get_nodes(self) -> Tuple[PipelineNode, ...]:
        return tuple(self.nodes.keys())

    def get_node_state(self, node: PipelineNode) -> PipelineNodeState:
        return PipelineNodeState.REGISTERED

    def get_node_dependencies(self, node: PipelineNode) -> Tuple[PipelineNode, ...]:
        return tuple(dp.node for dp in self.dependencies[node])


class PipelineExpander(Protocol, Generic[T]):
    def expand(self) -> Pipeline[T]:
        pass


class PipelinePruner(Protocol, Generic[T]):
    def prune(self) -> Pipeline[T]:
        pass


class Estimator(PipelineExpander[T]):
    _train_pipeline: Pipeline[T]
    _eval_pipeline: Pipeline[T]

    def __init__(self, train_pipeline: Pipeline[T], eval_pipeline: Pipeline[T]) -> None:
        super().__init__()
        self._train_pipeline = train_pipeline
        self._eval_pipeline = eval_pipeline

    def expand(self) -> Pipeline[T]:
        train_ns, eval_ns = Namespace("train"), Namespace("eval")
        tail_node = PipelineNode("tail")
        new_train = self._train_pipeline.decorate(train_ns)
        new_eval = self._eval_pipeline.decorate(eval_ns)
        tail_dps: Tuple[NodeDependency[T], ...] = tuple(
            NodeDependency(dp) for dp in new_train.end_nodes + new_eval.end_nodes
        )
        tail = Pipeline(nodes={tail_node: NodeProvider()}, dependencies={tail_node: tail_dps})
        new_pipeline = new_train + new_eval + tail

        for node in self._eval_pipeline.dependencies.keys():
            train_node = node.decorate(train_ns)
            eval_node = node.decorate(eval_ns)
            # create dependency from train node on eval node
            new_pipeline.dependencies[eval_node] += (NodeDependency(train_node),)
            # update existing external train dependencies on eval nodes
            new_pipeline.dependencies[eval_node] = tuple(
                dp.decorate(train_ns) if dp.node in self._train_pipeline else dp
                for dp in new_pipeline.dependencies[eval_node]
            )

        return new_pipeline


class IExecute:
    pass


class DataSplitter(NodeProvider):
    def __init__(self, num_folds: int) -> None:
        assert num_folds > 0

        super().__init__()
        self._num_folds = num_folds

    @property
    def num_folds(self) -> int:
        return self._num_folds


class XValTrain(PipelineExpander[T]):
    _pipeline: Pipeline[T]
    _data_splitter: DataSplitter
    _summary: NodeProvider

    def __init__(self, num_folds: int, data_splitter: DataSplitter, pipeline: Pipeline[T]) -> None:
        super().__init__()
        self._data_splitter = data_splitter
        self._summary = NodeProvider()
        self._pipeline = pipeline

    def expand(self) -> Pipeline[T]:
        kfolds = []
        datasplit = PipelineNode("data_splitter")
        tail_dependencies: Tuple[NodeDependency[T], ...] = ()
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

        folds_pipeline: Pipeline[T] = sum(kfolds, start=Pipeline())  # merge kfold pipelines
        tail = PipelineNode("summary")  # create new tail for xval_train pipeline
        datasplit_and_tail_pipeline = Pipeline(  # create new pipeline w/ datasplit and summary
            {datasplit: self._data_splitter, tail: self._summary},
            {datasplit: self._pipeline.external_dependencies, tail: tail_dependencies},
        )

        return folds_pipeline + datasplit_and_tail_pipeline

    @property
    def num_folds(self) -> int:
        return self._data_splitter.num_folds


class XValEval(PipelinePruner[T]):
    _xval_train: Pipeline[T]
    _summary: NodeProvider

    def __init__(self, xval_train: Pipeline[T]) -> None:
        super().__init__()
        self._xval_train = xval_train
        self._summary = NodeProvider()

    def prune(self) -> Pipeline[T]:
        prune_pipeline: Tuple[Pipeline[T], ...] = ()
        train_ns = Namespace("train")
        for node, provider in self._xval_train.nodes.items():
            if train_ns in node.namespace:
                prune_pipeline += (Pipeline({node: provider}),)

        datasplit = PipelineNode("data_splitter")
        datasplit_dps = self._xval_train.dependencies[datasplit]  # get datasplit dependencies
        new_pipeline = self._xval_train.pop(datasplit)  # remove datasplit
        for node, dps in new_pipeline.dependencies.items():
            if datasplit in (dp.node for dp in dps):
                # remove lingering datasplit depenencies
                newds = tuple(dp for dp in (set(dps) | set(datasplit_dps)) if dp.node != datasplit)
                new_pipeline.dependencies[node] = newds

        return new_pipeline - sum(prune_pipeline, start=Pipeline())


class Array:
    def __repr__(self) -> str:
        return "Array"


class ATrain(NodeProvider):
    def process(self, X: Array) -> Dict[PipelineData[Array], Array]:
        return {PipelineData[Array]("X"): X, PipelineData[Array]("mu"): Array()}


class AEval(NodeProvider):
    def process(self, X: Array, mu: Array) -> Dict[PipelineData[Array], Array]:
        return {PipelineData[Array]("X"): X}


class BTrain(NodeProvider):
    def process(self, X: Array, Y: Array) -> Dict[PipelineData[Array], Array]:
        return {PipelineData[Array]("acc"): Array(), PipelineData[Array]("model"): Array()}


class BEval(NodeProvider):
    def process(self, X: Array, Y: Array, model: Array) -> Dict[PipelineData[Array], Array]:
        return {PipelineData[Array]("X"): X}


train_nodes = {PipelineNode("A"): ATrain(), PipelineNode("B"): BTrain()}
eval_nodes = {PipelineNode("A"): AEval(), PipelineNode("B"): BEval()}
edges: Dict[PipelineNode, Tuple[NodeDependency[Array], ...]] = {
    PipelineNode("A"): (NodeDependency(PipelineNode("data"), args=(PipelineData[Array]("X"),)),),
    PipelineNode("B"): (
        NodeDependency(PipelineNode("A"), args=(PipelineData[Array]("X"),)),
        NodeDependency(PipelineNode("data"), args=(PipelineData[Array]("Y"),)),
    ),
}


def main(
    train_nodes: Dict[PipelineNode, NodeProvider],
    eval_nodes: Dict[PipelineNode, NodeProvider],
    edges: Dict[PipelineNode, Tuple[NodeDependency[T], ...]],
) -> Pipeline[T]:
    pipeline0_train = Pipeline(train_nodes, edges)
    pipeline0_eval = Pipeline(eval_nodes, edges)
    pipeline1 = Estimator(pipeline0_train, pipeline0_eval).expand()
    xval_train = XValTrain(DataSplitter(num_folds=2), pipeline1).expand()
    xval_eval = XValEval(xval_train).prune()
    pipeline2 = Estimator(xval_train, xval_eval).expand()  # noqa: F841

    svg_client = DagSvg(
        DotDag(
            node_client=pipeline1,
            dependencies_client=pipeline1,
            node_state_client=pipeline1,
        )
    )
    with open("pipeline2.svg", "wb") as f:
        f.write(svg_client.svg())

    return pipeline1


if __name__ == "__main__":
    main(train_nodes, eval_nodes, edges)
