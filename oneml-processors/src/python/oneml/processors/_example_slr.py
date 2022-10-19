from __future__ import annotations

from typing import TypedDict

from ._estimator import EstimatorPipelineFromTrainAndEval, WrapEstimatorPipeline
from ._pipeline import PDependency, Pipeline, PNode, ProcessorProps
from ._processor import InParameter, InParameterTargetMethod, IProcess
from ._viz import dag_to_svg


class Array(object):
    def __repr__(self) -> str:
        return "Array"


class Model(object):
    def __repr__(self) -> str:
        return "Model"


StandardizeTrainOutput = TypedDict(
    "StandardizeTrainOutput", {"X": Array, "mu": Array, "scale": Array}
)


class StandardizeTrain(IProcess):
    def process(self, X: Array) -> StandardizeTrainOutput:
        return StandardizeTrainOutput({"X": X, "mu": Array(), "scale": Array()})


StandardizeEvalOutput = TypedDict("StandardizeEvalOutput", {"X": Array})


class StandardizeEval(IProcess):
    def __init__(self, mu: Array, scale: Array) -> None:
        super().__init__()
        self._mu = mu
        self._scale = scale

    def process(self, X: Array) -> StandardizeEvalOutput:
        return StandardizeEvalOutput({"X": X})


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
    train_stz = PNode("stz")
    train_model = PNode("model")
    data = PNode("data")
    train_nodes = {
        train_stz: ProcessorProps(StandardizeTrain),
        train_model: ProcessorProps(ModelTrain),
    }
    train_dps = {
        train_stz: set((PDependency(data, InParameter("X", Array, InParameterTargetMethod.Process)),)),
        train_model: set(
            (
                PDependency(train_stz, InParameter("X", Array, InParameterTargetMethod.Process)),
                PDependency(data, InParameter("Y", Array, InParameterTargetMethod.Process)),
            )
        ),
    }

    eval_stz = train_stz
    eval_model = train_model
    eval_dps = {
        eval_stz: set((PDependency(data, InParameter("X", Array, InParameterTargetMethod.Process)),)),
        eval_model: set(
            (
                PDependency(train_stz, InParameter("X", Array, InParameterTargetMethod.Process)),
                PDependency(data, InParameter("Y", Array, InParameterTargetMethod.Process)),
            )
        ),
    }
    eval_nodes = {
        eval_stz: ProcessorProps(StandardizeEval),
        eval_model: ProcessorProps(ModelEval),
    }

    train_pipeline = Pipeline(train_nodes, train_dps)
    eval_pipeline = Pipeline(eval_nodes, eval_dps)

    pipeline = EstimatorPipelineFromTrainAndEval(train_pipeline, eval_pipeline).expand()

    svg = dag_to_svg(pipeline)
    with open("pipeline1.svg", "wb") as f:
        f.write(svg)


def concatenate_estimators_pipeline() -> None:
    train_nodeA = PNode("stz")
    train_nodeB = PNode("model")
    train_dpsA: dict[PNode, set[PDependency]] = {train_nodeA: set()}
    train_dpsB: dict[PNode, set[PDependency]] = {train_nodeB: set()}
    train_nodesA = {train_nodeA: ProcessorProps(StandardizeTrain)}
    train_nodesB = {train_nodeB: ProcessorProps(ModelTrain)}

    train_pipelineA = Pipeline(train_nodesA, train_dpsA)
    train_pipelineB = Pipeline(train_nodesB, train_dpsB)

    eval_nodeA = train_nodeA
    eval_nodeB = train_nodeB
    eval_dpsA: dict[PNode, set[PDependency]] = train_dpsA
    eval_dpsB: dict[PNode, set[PDependency]] = train_dpsB
    eval_nodesA: dict[PNode, ProcessorProps] = {eval_nodeA: ProcessorProps(StandardizeEval)}
    eval_nodesB: dict[PNode, ProcessorProps] = {eval_nodeB: ProcessorProps(ModelEval)}

    eval_pipelineA: Pipeline = Pipeline(eval_nodesA, eval_dpsA)
    eval_pipelineB: Pipeline = Pipeline(eval_nodesB, eval_dpsB)

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
