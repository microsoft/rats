from rats import processors as rp
from rats.examples_sklearn import Services as ExamplePipelineServices


class TestLRExamplePipelines:
    _app: rp.NotebookApp

    def setup_method(self) -> None:
        self._app = rp.NotebookApp()

    def test_build_train_pipeline(self) -> None:
        pipeline = self._app.get(ExamplePipelineServices.TRAIN_PIPELINE)
        assert set(pipeline.inputs) == set(["category_names", "x", "y"])
        assert set(pipeline.outputs) == set(
            ["model", "number_of_labels_in_training", "number_of_samples_in_training"]
        )

    def test_build_prediction_pipeline(self) -> None:
        pipeline = self._app.get(ExamplePipelineServices.PREDICT_PIPELINE)
        assert set(pipeline.inputs) == set(["model", "x"])
        assert set(pipeline.outputs) == set(["logits"])
