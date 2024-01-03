from __future__ import annotations

from typing import TypedDict

from oneml.processors.dag import (
    DAG,
    DagDependency,
    DagNode,
    InMethod,
    InProcessorParam,
    IProcess,
    Namespace,
    OutProcessorParam,
    ProcessorProps,
    dag_to_svg,
)
from oneml.processors.utils import orderedset


class Array(object):
    def __repr__(self) -> str:
        return "Array"


class Model(object):
    def __repr__(self) -> str:
        return "Model"


StandardizeTrainOutput = TypedDict(
    "StandardizeTrainOutput", {"Z": Array, "mu": Array, "scale": Array}
)


class StandardizeTrain(IProcess):
    def process(self, X: Array) -> StandardizeTrainOutput:
        return StandardizeTrainOutput({"Z": X, "mu": Array(), "scale": Array()})


StandardizeEvalOutput = TypedDict("StandardizeEvalOutput", {"Z": Array})


class StandardizeEval(IProcess):
    def __init__(self, mu: Array, scale: Array) -> None:
        super().__init__()
        self._mu = mu
        self._scale = scale

    def process(self, X: Array) -> StandardizeEvalOutput:
        return StandardizeEvalOutput({"Z": X})


ModelTrainOutput = TypedDict("ModelTrainOutput", {"acc": Array, "model": Model})


class ModelTrain(IProcess):
    def process(self, X: Array, Y: Array) -> ModelTrainOutput:
        return ModelTrainOutput({"acc": Array(), "model": Model()})


ModelEvalOutput = TypedDict("ModelEvalOutput", {"probs": Array})


class ModelEval(IProcess):
    def __init__(self, model: Model) -> None:
        super().__init__()
        self.model = model

    def process(self, X: Array, Y: Array) -> ModelEvalOutput:
        return {"probs": X}


def estimator_from_multiple_nodes_dag() -> None:
    train_stz = DagNode("train", namespace=Namespace("stz"))
    train_model = DagNode("train", namespace=Namespace("model"))
    data = DagNode("data")
    train_nodes = {
        train_stz: ProcessorProps(StandardizeTrain),
        train_model: ProcessorProps(ModelTrain),
    }
    train_dps = {
        train_stz: orderedset(
            (DagDependency(data, InProcessorParam("X", Array, InMethod.process)),)
        ),
        train_model: orderedset(
            (
                DagDependency(
                    train_stz,
                    InProcessorParam("X", Array, InMethod.process),
                    OutProcessorParam("Z", Array),
                ),
                DagDependency(data, InProcessorParam("Y", Array, InMethod.process)),
            )
        ),
    }

    eval_stz = DagNode("eval", namespace=Namespace("stz"))
    eval_model = DagNode("eval", namespace=Namespace("model"))
    eval_dps = {
        eval_stz: orderedset(
            (DagDependency(data, InProcessorParam("X", Array, InMethod.process)),)
        ),
        eval_model: orderedset(
            (
                DagDependency(
                    eval_stz,
                    InProcessorParam("X", Array, InMethod.process),
                    OutProcessorParam("Z", Array),
                ),
                DagDependency(data, InProcessorParam("Y", Array, InMethod.process)),
            )
        ),
    }
    eval_nodes = {
        eval_stz: ProcessorProps(StandardizeEval),
        eval_model: ProcessorProps(ModelEval),
    }

    train_dag = DAG(train_nodes, train_dps)
    eval_dag = DAG(eval_nodes, eval_dps)
    new_dag = train_dag + eval_dag
    assert new_dag

    # svg = dag_to_svg(new_dag)
    # with open("dag1.svg", "wb") as f:
    #     f.write(svg)


def concatenate_estimators_dag() -> None:
    train_nodeA = DagNode("train", namespace=Namespace("stz"))
    train_nodeB = DagNode("train", namespace=Namespace("model"))
    train_dpsA: dict[DagNode, orderedset[DagDependency]] = {train_nodeA: orderedset()}
    train_dpsB: dict[DagNode, orderedset[DagDependency]] = {train_nodeB: orderedset()}
    train_nodesA = {train_nodeA: ProcessorProps(StandardizeTrain)}
    train_nodesB = {train_nodeB: ProcessorProps(ModelTrain)}

    train_dagA = DAG(train_nodesA, train_dpsA)
    train_dagB = DAG(train_nodesB, train_dpsB)

    eval_nodeA = DagNode("eval", namespace=Namespace("stz"))
    eval_nodeB = DagNode("eval", namespace=Namespace("model"))
    eval_dpsA: dict[DagNode, orderedset[DagDependency]] = {eval_nodeA: orderedset()}
    eval_dpsB: dict[DagNode, orderedset[DagDependency]] = {eval_nodeB: orderedset()}
    eval_nodesA: dict[DagNode, ProcessorProps] = {eval_nodeA: ProcessorProps(StandardizeEval)}
    eval_nodesB: dict[DagNode, ProcessorProps] = {eval_nodeB: ProcessorProps(ModelEval)}

    eval_dagA = DAG(eval_nodesA, eval_dpsA)
    eval_dagB = DAG(eval_nodesB, eval_dpsB)

    estimatorA = train_dagA + eval_dagA
    estimatorB = train_dagB + eval_dagB

    assert estimatorA
    assert estimatorB

    # p = estimatorA.decorate("p")
    # q = estimatorB.decorate("q")

    # svg = dag_to_svg(p)
    # with open("p.svg", "wb") as f:
    #     f.write(svg)

    # svg = dag_to_svg(q)
    # with open("q.svg", "wb") as f:
    #     f.write(svg)


def test_dag_example() -> None:
    estimator_from_multiple_nodes_dag()
    concatenate_estimators_dag()
