from __future__ import annotations

from inspect import Parameter
from typing import Any, Mapping, TypedDict, TypeVar

from oneml.processors import IProcessor, PDependency, Pipeline, PNode, PNodeProperties, Provider
from oneml.processors._estimator import EstimatorPipelineFromTrainAndEval, WrapEstimatorPipeline
from oneml.processors._viz import dag_to_svg

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)
TDict = Mapping[str, Any]


class Array(object):
    def __repr__(self) -> str:
        return "Array"


StandardizeTrainOutput = TypedDict(
    "StandardizeTrainOutput", {"X": Array, "mu": Array, "scale": Array}
)


class StandardizeTrain(IProcessor[StandardizeTrainOutput]):
    def process(self, X: Array = Array()) -> StandardizeTrainOutput:
        return StandardizeTrainOutput({"X": X, "mu": Array(), "scale": Array()})


StandardizeEvalOutput = TypedDict("StandardizeEvalOutput", {"X": Array})


class StandardizeEval(IProcessor[StandardizeEvalOutput]):
    def __init__(self, mu: Array, scale: Array) -> None:
        super().__init__()
        self._mu = mu
        self._scale = scale

    def process(self, X: Array = Array()) -> StandardizeEvalOutput:
        return StandardizeEvalOutput({"X": X})


ModelTrainOutput = TypedDict("ModelTrainOutput", {"acc": Array, "model": Array})


class ModelTrain(IProcessor[ModelTrainOutput]):
    def process(self, X: Array = Array(), Y: Array = Array()) -> ModelTrainOutput:
        return ModelTrainOutput({"acc": Array(), "model": Array()})


ModelEvalOutput = TypedDict("ModelEvalOutput", {"probs": Array})


class ModelEval(IProcessor[ModelEvalOutput]):
    def __init__(self, model: Array) -> None:
        super().__init__()
        self.model = model

    def process(self, X: Array = Array(), Y: Array = Array()) -> ModelEvalOutput:
        return {"probs": X}


def estimator_from_multiple_nodes_pipeline() -> None:
    train_nodes = set((PNode("stz"), PNode("model")))
    train_dps: dict[PNode, set[PDependency]] = {
        PNode("stz"): set(
            (
                PDependency(
                    PNode("data"),
                    Parameter("X", Parameter.POSITIONAL_OR_KEYWORD, annotation=Array),
                ),
            )
        ),
        PNode("model"): set(
            (
                PDependency(
                    PNode("stz"), Parameter("X", Parameter.POSITIONAL_OR_KEYWORD, annotation=Array)
                ),
                PDependency(
                    PNode("data"),
                    Parameter("Y", Parameter.POSITIONAL_OR_KEYWORD, annotation=Array),
                ),
            )
        ),
    }

    train_props: dict[PNode, PNodeProperties[TDict]] = {
        PNode("stz"): PNodeProperties(Provider(StandardizeTrain)),
        PNode("model"): PNodeProperties(Provider(ModelTrain)),
    }
    eval_nodes = train_nodes
    eval_dps = train_dps
    eval_props: dict[PNode, PNodeProperties[TDict]] = {
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
    train_propsA: dict[PNode, PNodeProperties[TDict]] = {
        PNode("stz"): PNodeProperties(Provider(StandardizeTrain))
    }

    train_propsB: dict[PNode, PNodeProperties[TDict]] = {
        PNode("model"): PNodeProperties(Provider(ModelTrain))
    }

    train_pipelineA: Pipeline = Pipeline(train_nodeA, train_dpsA, train_propsA)
    train_pipelineB: Pipeline = Pipeline(train_nodeB, train_dpsB, train_propsB)

    eval_nodeA = train_nodeA
    eval_nodeB = train_nodeB
    eval_dpsA: dict[PNode, set[PDependency]] = train_dpsA
    eval_dpsB: dict[PNode, set[PDependency]] = train_dpsB
    eval_propsA: dict[PNode, PNodeProperties[TDict]] = {
        PNode("stz"): PNodeProperties(Provider(StandardizeEval))
    }

    eval_propsB: dict[PNode, PNodeProperties[TDict]] = {
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
