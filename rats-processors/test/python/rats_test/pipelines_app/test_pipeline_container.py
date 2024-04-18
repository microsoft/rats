from rats import pipelines_app as rpa
from rats_test.pipelines_app import example
from rats_test.pipelines_app.example import ExamplePipelineServices


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

    def test_p2(self) -> None:
        prf = self._app.get(rpa.PipelineServices.PIPELINE_RUNNER_FACTORY)
        pipeline = self._app.get(ExamplePipelineServices.P2)
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

    def test_p3(self) -> None:
        prf = self._app.get(rpa.PipelineServices.PIPELINE_RUNNER_FACTORY)
        pipeline = self._app.get(ExamplePipelineServices.P2)
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

    def static_checks(self) -> None:
        # Does not run;
        # Static type checkers (mypy, pyright) will verify that static types of the pipelines
        # are correct.
        load_data = self._app.get(ExamplePipelineServices.LOAD_DATA)
        train_model = self._app.get(ExamplePipelineServices.TRAIN_MODEL)
        p2 = self._app.get(ExamplePipelineServices.P2)

        # verify typing of tasks
        load_data.outputs.data >> train_model.inputs.data  # ok
        load_data.outputs.data >> train_model.inputs.num_layers  # type: ignore[operator]  wrong type
        load_data.outputs.data << train_model.inputs.data  # type: ignore[operator]  wrong direction

        # verify typing of pipeline
        train_model.outputs.message >> p2.inputs.url  # ok
        p2.outputs.length >> p2.inputs.num_layers  # ok
