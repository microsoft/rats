from __future__ import annotations

from typing import TypedDict

from oneml.processors import (
    InParameter,
    IProcessor,
    PDependency,
    Pipeline,
    PNode,
    PNodeProperties,
    Provider,
)
from oneml.processors._estimator import EstimatorPipelineFromTrainAndEval, WrapEstimatorPipeline
from oneml.processors._viz import dag_to_svg


class Array(object):
    def __repr__(self) -> str:
        return "Array"


StandardizeTrainOutput = TypedDict(
    "StandardizeTrainOutput", {"X": Array, "mu": Array, "scale": Array}
)


class StandardizeTrain(IProcessor):
    def process(self, X: Array) -> StandardizeTrainOutput:
        return StandardizeTrainOutput({"X": X, "mu": Array(), "scale": Array()})


StandardizeEvalOutput = TypedDict("StandardizeEvalOutput", {"X": Array})


class StandardizeEval(IProcessor):
    def __init__(self, mu: Array, scale: Array) -> None:
        super().__init__()
        self._mu = mu
        self._scale = scale

    def process(self, X: Array) -> StandardizeEvalOutput:
        return StandardizeEvalOutput({"X": X})


ModelTrainOutput = TypedDict("ModelTrainOutput", {"acc": Array, "model": Array})


class ModelTrain(IProcessor):
    def process(self, X: Array, Y: Array) -> ModelTrainOutput:
        return ModelTrainOutput({"acc": Array(), "model": Array()})


ModelEvalOutput = TypedDict("ModelEvalOutput", {"probs": Array})


class ModelEval(IProcessor):
    def __init__(self, model: Array) -> None:
        super().__init__()
        self.model = model

    def process(self, X: Array = Array(), Y: Array = Array()) -> ModelEvalOutput:
        return {"probs": X}


def estimator_from_multiple_nodes_pipeline() -> None:
    train_nodes = set((PNode("stz"), PNode("model")))
    train_dps: dict[PNode, set[PDependency]] = {
        PNode("stz"): set((PDependency(PNode("data"), InParameter("X", Array)),)),
        PNode("model"): set(
            (
                PDependency(PNode("stz"), InParameter("X", Array)),
                PDependency(PNode("data"), InParameter("Y", Array)),
            )
        ),
    }

    train_props: dict[PNode, PNodeProperties] = {
        PNode("stz"): PNodeProperties(Provider(StandardizeTrain)),
        PNode("model"): PNodeProperties(Provider(ModelTrain)),
    }
    eval_nodes = train_nodes
    eval_dps = train_dps
    eval_props: dict[PNode, PNodeProperties] = {
        PNode("stz"): PNodeProperties(Provider(StandardizeEval)),
        PNode("model"): PNodeProperties(Provider(ModelEval)),
    }

    train_pipeline: Pipeline = Pipeline(train_nodes, train_dps, train_props)
    eval_pipeline: Pipeline = Pipeline(eval_nodes, eval_dps, eval_props)

    pipeline = EstimatorPipelineFromTrainAndEval(train_pipeline, eval_pipeline).expand()

    svg = dag_to_svg(pipeline)
    with open("pipeline1.svg", "wb") as f:
        f.write(svg)


def concatenate_estimators_pipeline() -> None:
    train_nodeA = set((PNode("stz"),))
    train_nodeB = set((PNode("model"),))
    train_dpsA: dict[PNode, set[PDependency]] = {PNode("stz"): set()}
    train_dpsB: dict[PNode, set[PDependency]] = {PNode("model"): set()}
    train_propsA: dict[PNode, PNodeProperties] = {
        PNode("stz"): PNodeProperties(Provider(StandardizeTrain))
    }

    train_propsB: dict[PNode, PNodeProperties] = {
        PNode("model"): PNodeProperties(Provider(ModelTrain))
    }

    train_pipelineA: Pipeline = Pipeline(train_nodeA, train_dpsA, train_propsA)
    train_pipelineB: Pipeline = Pipeline(train_nodeB, train_dpsB, train_propsB)

    eval_nodeA = train_nodeA
    eval_nodeB = train_nodeB
    eval_dpsA: dict[PNode, set[PDependency]] = train_dpsA
    eval_dpsB: dict[PNode, set[PDependency]] = train_dpsB
    eval_propsA: dict[PNode, PNodeProperties] = {
        PNode("stz"): PNodeProperties(Provider(StandardizeEval))
    }

    eval_propsB: dict[PNode, PNodeProperties] = {
        PNode("model"): PNodeProperties(Provider(ModelEval))
    }

    eval_pipelineA: Pipeline = Pipeline(eval_nodeA, eval_dpsA, eval_propsA)
    eval_pipelineB: Pipeline = Pipeline(eval_nodeB, eval_dpsB, eval_propsB)

    estimatorA = EstimatorPipelineFromTrainAndEval(train_pipelineA, eval_pipelineA).expand()
    estimatorB = EstimatorPipelineFromTrainAndEval(train_pipelineB, eval_pipelineB).expand()

    p = WrapEstimatorPipeline.wrap_estimator_pipeline_in_namespace(estimatorA, "p")
    q = WrapEstimatorPipeline.wrap_estimator_pipeline_in_namespace(estimatorB, "q")

    svg = dag_to_svg(p)
    with open("p.svg", "wb") as f:
        f.write(svg)

    svg = dag_to_svg(q)
    with open("q.svg", "wb") as f:
        f.write(svg)


if __name__ == "__main__":
    estimator_from_multiple_nodes_pipeline()
    concatenate_estimators_pipeline()
