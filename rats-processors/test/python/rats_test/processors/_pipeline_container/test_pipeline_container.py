from rats import processors as rp
from rats_test.processors._pipeline_container import example
from rats_test.processors._pipeline_container.example import (
    ExamplePipelineServices,
    Model,
    SubModel,
)


class TestPipelineContainer:
    _app: example.ExampleApp

    def setup_method(self) -> None:
        self._app = example.ExampleApp()

    def test_p1(self) -> None:
        prf = self._app.get(rp.ProcessorsServices.PIPELINE_RUNNER_FACTORY)
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

    def test_train_pipeline(self) -> None:
        prf = self._app.get(rp.ProcessorsServices.PIPELINE_RUNNER_FACTORY)
        pipeline = self._app.get(ExamplePipelineServices.TRAIN_PIPELINE)
        pr = prf(pipeline)
        model = Model(
            model_name="linear",
            num_layers=21,
            sub_model=SubModel(
                gamma=0.1,
            ),
        )
        assert not model.trained
        inputs = dict(
            url="blob://data",
            epochs=2,
            model=model,
        )
        outputs = pr(inputs)
        expected_message = (
            f"Training model\n\tdata: Data from blob://data\n\tepochs: {2}\n"
            f"\tmodel: Model(model_name=linear, num_layers=21, sub_model=SubModel(gamma=0.1), "
            "status=untrained)"
        )
        assert outputs["message"] == expected_message
        model = outputs["model"]
        assert model.model_name == "linear"
        assert model.num_layers == 21
        assert model.sub_model.gamma == 0.1
        assert model.trained

    def test_train_and_test_pipeline(self) -> None:
        prf = self._app.get(rp.ProcessorsServices.PIPELINE_RUNNER_FACTORY)
        pipeline = self._app.get(ExamplePipelineServices.TRAIN_AND_TEST_PIPELINE)
        pr = prf(pipeline)
        model = Model(
            model_name="linear",
            num_layers=21,
            sub_model=SubModel(
                gamma=0.1,
            ),
        )
        assert not model.trained
        inputs = {
            "url.train": "blob://train_data",
            "url.test": "blob://test_data",
            "epochs": 2,
            "model": model,
        }
        outputs = pr(inputs)
        expected_train_message = (
            f"Training model\n\tdata: Data from blob://train_data\n\tepochs: {2}\n"
            f"\tmodel: Model(model_name=linear, num_layers=21, sub_model=SubModel(gamma=0.1), "
            "status=untrained)"
        )
        expected_test_message = (
            "Testing model\n\tdata: Data from blob://test_data\n"
            "\tmodel: Model(model_name=linear, num_layers=21, sub_model=SubModel(gamma=0.1), "
            "status=trained)"
        )
        assert outputs["message.train"] == expected_train_message
        assert outputs["message.test"] == expected_test_message

    def static_checks(self) -> None:
        # Does not run;
        # Static type checkers (mypy, pyright) will verify that static types of the pipelines
        # are correct.
        load_data = self._app.get(ExamplePipelineServices.LOAD_DATA)
        train_model = self._app.get(ExamplePipelineServices.TRAIN_MODEL)
        train_pipeline = self._app.get(ExamplePipelineServices.TRAIN_PIPELINE)

        # verify typing of tasks
        load_data.outputs.data >> train_model.inputs.data  # ok
        load_data.outputs.data >> train_model.inputs.epochs  # type: ignore[operator]  wrong type
        load_data.outputs.data << train_model.inputs.data  # type: ignore[operator]  wrong direction

        # verify typing of pipeline
        train_model.outputs.message >> train_pipeline.inputs.url  # ok
        train_pipeline.outputs.length >> train_pipeline.inputs.num_layers  # ok

    def test_registry(self) -> None:
        registered_pipelines = self._app.get(rp.ProcessorsServices.EXECUTABLE_PIPELINES)
        assert len(registered_pipelines) == 2
        registered_pipelines_dict = {p["name"]: p for p in registered_pipelines}
        train_pipeline_1 = self._app.get(ExamplePipelineServices.TRAIN_PIPELINE)
        train_pipeline_2 = self._app.get(registered_pipelines_dict["train_pipeline"]["service_id"])
        assert train_pipeline_1 is train_pipeline_2
        train_and_test_pipeline_1 = self._app.get(ExamplePipelineServices.TRAIN_AND_TEST_PIPELINE)
        train_and_test_pipeline_2 = self._app.get(
            registered_pipelines_dict["train_and_test_pipeline"]["service_id"]
        )
        assert train_and_test_pipeline_1 is train_and_test_pipeline_2
