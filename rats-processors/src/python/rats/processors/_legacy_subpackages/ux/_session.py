from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from rats.app import RatsApp
from rats.processors._legacy_subpackages.dag import DagSubmitter, IProcess
from rats.processors._legacy_subpackages.utils import frozendict, namedcollection

from ._builder import CombinedPipeline, DependencyOp, UTask
from ._pipeline import UPipeline


class ExposeGivenOutputsProcessor(IProcess):
    def __init__(self, data: Any) -> None:
        self._data = data

    def process(self) -> Mapping[str, Any]:
        return dict(data=self._data)


def build_data_provider_pipeline_from_objects(data: Mapping[str, Any]) -> UPipeline:
    tasks = {
        k: UTask(
            name=k,
            processor_type=ExposeGivenOutputsProcessor,
            config=frozendict(data=v),
            return_annotation=dict(data=type(v)),
        ).rename_outputs({"data": k})
        for k, v in data.items()
    }
    return CombinedPipeline(list(tasks.values()), name="DataProvider")


class Ref:
    _v: Any | None

    def set(self, v: Any) -> None:
        self._v = v

    def get(self) -> Any:
        return self._v


class PopulateOutputValue:
    _storage: Ref

    def __init__(self, storage: Ref):
        self._storage = storage

    def process(self, data: Any) -> None:
        self._storage.set(data)


def build_output_collector(output_storage: dict[str, Ref], pipeline: UPipeline) -> UPipeline:
    for k in pipeline.outputs._asdict():
        output_storage[k] = Ref()

    output_populators = [
        UTask(
            name=f"""PopulateOutputValue_{k.replace(".", "_")}""",
            processor_type=PopulateOutputValue,
            config=frozendict(storage=output_storage[k]),
        ).rename_inputs({"data": k})
        for k in pipeline.outputs._asdict()
    ]

    return CombinedPipeline(name="OutputCollector", pipelines=output_populators)


class SessionOutputsGetter(Mapping[str, Any]):
    _storage: namedcollection[Ref]

    def __init__(self, storage: Mapping[str, Ref]) -> None:
        self._storage = namedcollection(storage)

    def __getitem__(self, key: str) -> Any:
        v = self._storage[key]
        if isinstance(v, Ref):
            return v.get()
        else:
            return SessionOutputsGetter(v._asdict())

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._storage

    def __len__(self) -> int:
        return len(self._storage)


class PipelineRunnerFactory:
    _app: RatsApp
    _dag_submitter: DagSubmitter

    def __init__(self, app: RatsApp, dag_submitter: DagSubmitter):
        self._app = app
        self._dag_submitter = dag_submitter

    def __call__(self, pipeline: UPipeline) -> PipelineRunner:
        return PipelineRunner(app=self._app, dag_submitter=self._dag_submitter, pipeline=pipeline)


class PipelineRunner:
    _app: RatsApp
    _dag_submitter: DagSubmitter
    _pipeline: UPipeline

    def __init__(self, app: RatsApp, dag_submitter: DagSubmitter, pipeline: UPipeline) -> None:
        self._app = app
        self._dag_submitter = dag_submitter
        self._pipeline = pipeline

    def _add_inputs_and_collect_outputs(
        self, inputs: Mapping[str, Any], output_storage: dict[str, Ref]
    ) -> UPipeline:
        pipelines = [self._pipeline]
        dependencies = list[DependencyOp[Any]]()
        if len(set(inputs)) > 0:
            data_provider_pipeline = build_data_provider_pipeline_from_objects(inputs)
            if self._pipeline.name == data_provider_pipeline.name:
                data_provider_pipeline = data_provider_pipeline.decorate(
                    data_provider_pipeline.name + "_"
                )
            pipelines.append(data_provider_pipeline)
            for k in data_provider_pipeline.outputs:
                dependencies.append(data_provider_pipeline.outputs[k] >> self._pipeline.inputs[k])

        if len(self._pipeline.outputs) > 0:
            output_pipeline = build_output_collector(output_storage, self._pipeline)
            if self._pipeline.name == output_pipeline.name:
                output_pipeline = output_pipeline.decorate(output_pipeline.name + "_")
            pipelines.append(output_pipeline)
            dependencies.append(self._pipeline >> output_pipeline)
        pipeline: UPipeline = CombinedPipeline(
            name="run",
            pipelines=pipelines,
            dependencies=dependencies,
        )
        required_inputs = set(pipeline.required_inputs)
        if len(required_inputs) > 0:
            raise ValueError(f"Missing pipeline inputs: {required_inputs}.")
        if len(pipeline.outputs) > 0:
            raise ValueError("UPipeline outputs should have been collected.")
        return pipeline

    def __call__(self, inputs: Mapping[str, Any] = {}) -> SessionOutputsGetter:
        output_storage = dict[str, Ref]()
        pipeline = self._add_inputs_and_collect_outputs(inputs, output_storage)
        dag_submitter = self._dag_submitter
        self._app.run(lambda: dag_submitter.submit_dag(pipeline._dag))
        return SessionOutputsGetter(output_storage)
