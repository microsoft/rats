from rats import pipelines_app as rpa
from rats_test.pipelines_app import example
from rats_test.pipelines_app.example._pipeline1 import ExamplePipelineServices


class TestPipelineContainer:
    _app: example.ExampleApp

    def setup_method(self) -> None:
        self._app = example.ExampleApp()

    def test_p1(self) -> None:
        prf = self._app.get(rpa.PipelineServices.PIPELINE_RUNNER_FACTORY)
        pipeline = self._app.get(ExamplePipelineServices.P1)
        pr = prf(pipeline)
        inputs = dict(
            url="http://example.com",
            model_type="linear",
            num_layers=2,
        )
        outputs = pr(inputs)
        assert (
            outputs["message"]
            == "Training model with data: Data from http://example.com with config linear, 2"
        )
        assert "length" in outputs
