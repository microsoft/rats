from __future__ import annotations

from itertools import chain
from typing import Any, Iterable, Iterator, Mapping

from oneml.app import OnemlApp
from oneml.processors.dag import DagSubmitter, IProcess
from oneml.processors.utils import frozendict

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


def build_output_collector(
    output_storage: dict[str, Ref | Mapping[str, Ref]],
    pipeline: UPipeline,
) -> UPipeline:
    for k in pipeline.outputs:
        output_storage[k] = Ref()
    for k0, col in pipeline.out_collections._asdict().items():
        col_s = dict[str, Ref]()
        output_storage[k0] = col_s
        for k1 in col:
            col_s[k1] = Ref()

    output_populators = [
        UTask(
            name=f"PopulateOutputValue_{k}",
            processor_type=PopulateOutputValue,
            config=frozendict(storage=output_storage[k]),
        ).rename_inputs({"data": k})
        for k in pipeline.outputs
    ]
    output_collection_populators = [
        UTask(
            name=f"PopulateOutputCollectionValue_{k0}_{k1}",
            processor_type=PopulateOutputValue,
            config=frozendict(storage=output_storage[k0][k1]),  # type: ignore
        ).rename_inputs({"data": f"{k0}.{k1}"})
        for k0, col in pipeline.out_collections._asdict().items()
        for k1 in col
    ]

    output_collector: UPipeline = CombinedPipeline(
        name="OutputCollector",
        pipelines=output_populators + output_collection_populators,
    )
    return output_collector


class SessionOutputsGetter(Iterable[str]):
    _storage: Mapping[str, Ref | Mapping[str, Ref]]

    def __init__(self, storage: Mapping[str, Ref | Mapping[str, Ref]]) -> None:
        self._storage = storage

    def __getitem__(self, key: str) -> Any | SessionOutputsGetter:
        v = self._storage[key]
        if isinstance(v, Ref):
            return v.get()
        else:
            return SessionOutputsGetter(v)

    def __getattr__(self, key: str) -> Any | SessionOutputsGetter:
        return self[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._storage


class PipelineRunnerFactory:
    _app: OnemlApp
    _dag_submitter: DagSubmitter

    def __init__(self, app: OnemlApp, dag_submitter: DagSubmitter):
        self._app = app
        self._dag_submitter = dag_submitter

    def __call__(self, pipeline: UPipeline) -> PipelineRunner:
        return PipelineRunner(
            app=self._app,
            dag_submitter=self._dag_submitter,
            pipeline=pipeline,
        )


class PipelineRunner:
    _app: OnemlApp
    _dag_submitter: DagSubmitter
    _pipeline: UPipeline

    def __init__(self, app: OnemlApp, dag_submitter: DagSubmitter, pipeline: UPipeline) -> None:
        self._app = app
        self._dag_submitter = dag_submitter
        self._pipeline = pipeline

    def _add_inputs_and_collect_outputs(
        self, inputs: Mapping[str, Any], output_storage: dict[str, Ref | Mapping[str, Ref]]
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
            for k0, col in data_provider_pipeline.out_collections._asdict().items():
                for k1 in col:
                    dependencies.append(
                        data_provider_pipeline.out_collections[k0][k1]
                        >> self._pipeline.in_collections[k0][k1]
                    )
        if len(self._pipeline.out_collections) > 0 or len(self._pipeline.outputs) > 0:
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
        required_inputs = set(chain(pipeline.required_inputs, pipeline.required_in_collections))
        if len(required_inputs) > 0:
            raise ValueError(f"Missing pipeline inputs: {required_inputs}.")
        if len(tuple(*pipeline.out_collections, *pipeline.outputs)) > 0:
            raise ValueError("UPipeline outputs should have been collected.")
        return pipeline

    def __call__(self, inputs: Mapping[str, Any] = {}) -> SessionOutputsGetter:
        output_storage = dict[str, Ref | Mapping[str, Ref]]()
        pipeline = self._add_inputs_and_collect_outputs(inputs, output_storage)
        dag_submitter = self._dag_submitter
        self._app.run(lambda: dag_submitter.submit_dag(pipeline._dag))
        return SessionOutputsGetter(output_storage)
