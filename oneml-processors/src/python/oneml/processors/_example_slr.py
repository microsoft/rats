from __future__ import annotations

from typing import TypedDict

from oneml.processors import (
    InMethod,
    InParameter,
    IProcess,
    Namespace,
    OutParameter,
    PDependency,
    Pipeline,
    PNode,
    ProcessorProps,
    dag_to_svg,
    oset,
)


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

    def process(self, X: Array = Array(), Y: Array = Array()) -> ModelEvalOutput:
        return {"probs": X}


def estimator_from_multiple_nodes_pipeline() -> None:
    train_stz = PNode("train", namespace=Namespace("stz"))
    train_model = PNode("train", namespace=Namespace("model"))
    data = PNode("data")
    train_nodes = {
        train_stz: ProcessorProps(StandardizeTrain),
        train_model: ProcessorProps(ModelTrain),
    }
    train_dps = {
        train_stz: oset((PDependency(data, InParameter("X", Array, InMethod.process)),)),
        train_model: oset(
            (
                PDependency(
                    train_stz, InParameter("X", Array, InMethod.process), OutParameter("Z", Array)
                ),
                PDependency(data, InParameter("Y", Array, InMethod.process)),
            )
        ),
    }

    eval_stz = PNode("eval", namespace=Namespace("stz"))
    eval_model = PNode("eval", namespace=Namespace("model"))
    eval_dps = {
        eval_stz: oset((PDependency(data, InParameter("X", Array, InMethod.process)),)),
        eval_model: oset(
            (
                PDependency(
                    eval_stz, InParameter("X", Array, InMethod.process), OutParameter("Z", Array)
                ),
                PDependency(data, InParameter("Y", Array, InMethod.process)),
            )
        ),
    }
    eval_nodes = {
        eval_stz: ProcessorProps(StandardizeEval),
        eval_model: ProcessorProps(ModelEval),
    }

    train_pipeline = Pipeline(train_nodes, train_dps)
    eval_pipeline = Pipeline(eval_nodes, eval_dps)
    new_pipeline = train_pipeline + eval_pipeline

    svg = dag_to_svg(new_pipeline)
    with open("pipeline1.svg", "wb") as f:
        f.write(svg)


def concatenate_estimators_pipeline() -> None:
    train_nodeA = PNode("train", namespace=Namespace("stz"))
    train_nodeB = PNode("train", namespace=Namespace("model"))
    train_dpsA: dict[PNode, oset[PDependency]] = {train_nodeA: oset()}
    train_dpsB: dict[PNode, oset[PDependency]] = {train_nodeB: oset()}
    train_nodesA = {train_nodeA: ProcessorProps(StandardizeTrain)}
    train_nodesB = {train_nodeB: ProcessorProps(ModelTrain)}

    train_pipelineA = Pipeline(train_nodesA, train_dpsA)
    train_pipelineB = Pipeline(train_nodesB, train_dpsB)

    eval_nodeA = PNode("eval", namespace=Namespace("stz"))
    eval_nodeB = PNode("eval", namespace=Namespace("model"))
    eval_dpsA: dict[PNode, oset[PDependency]] = {eval_nodeA: oset()}
    eval_dpsB: dict[PNode, oset[PDependency]] = {eval_nodeB: oset()}
    eval_nodesA: dict[PNode, ProcessorProps] = {eval_nodeA: ProcessorProps(StandardizeEval)}
    eval_nodesB: dict[PNode, ProcessorProps] = {eval_nodeB: ProcessorProps(ModelEval)}

    eval_pipelineA = Pipeline(eval_nodesA, eval_dpsA)
    eval_pipelineB = Pipeline(eval_nodesB, eval_dpsB)

    estimatorA = train_pipelineA + eval_pipelineA
    estimatorB = train_pipelineB + eval_pipelineB

    p = estimatorA.decorate("p")
    q = estimatorB.decorate("q")

    svg = dag_to_svg(p)
    with open("p.svg", "wb") as f:
        f.write(svg)

    svg = dag_to_svg(q)
    with open("q.svg", "wb") as f:
        f.write(svg)


if __name__ == "__main__":
    estimator_from_multiple_nodes_pipeline()
    concatenate_estimators_pipeline()
