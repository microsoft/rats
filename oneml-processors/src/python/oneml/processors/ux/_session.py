from __future__ import annotations

from itertools import chain
from typing import Any, Iterable, Iterator, Mapping
from uuid import uuid4

from oneml.app import OnemlApp, OnemlAppServices

from ..dag._client import PipelineSessionProvider
from ..dag._processor import IProcess
from ..utils._frozendict import frozendict
from ._builder import CombinedPipeline, DependencyOp, Task
from ._pipeline import Pipeline


class FixedOutputProcessor(IProcess):
    def __init__(self, data: Any) -> None:
        self._data = data

    def process(self) -> Mapping[str, Any]:
        return dict(data=self._data)


def build_data_provider_pipeline_from_objects(data: Mapping[str, Any]) -> Pipeline:
    tasks = {
        k: Task(
            name=k,
            processor_type=FixedOutputProcessor,
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
    pipeline: Pipeline,
) -> Pipeline:
    for k in pipeline.outputs:
        output_storage[k] = Ref()
    for k0, col in pipeline.out_collections.items():
        col_s = dict[str, Ref]()
        output_storage[k0] = col_s
        for k1 in col:
            col_s[k1] = Ref()

    output_populators = [
        Task(
            name=f"PopulateOutputValue_{k}",
            processor_type=PopulateOutputValue,
            config=frozendict(storage=output_storage[k]),
        ).rename_inputs({"data": k})
        for k in pipeline.outputs.keys()
    ]
    output_collection_populators = [
        Task(
            name=f"PopulateOutputCollectionValue_{k0}_{k1}",
            processor_type=PopulateOutputValue,
            config=frozendict(storage=output_storage[k0][k1]),  # type: ignore
        ).rename_inputs({"data": f"{k0}.{k1}"})
        for k0, col in pipeline.out_collections.items()
        for k1 in col
    ]

    output_collector = CombinedPipeline(
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
    _pipeline_session_provider: PipelineSessionProvider

    def __init__(self, app: OnemlApp, pipeline_session_provider: PipelineSessionProvider):
        self._app = app
        self._pipeline_session_provider = pipeline_session_provider

    def __call__(self, pipeline: Pipeline) -> PipelineRunner:
        return PipelineRunner(
            app=self._app,
            pipeline_session_provider=self._pipeline_session_provider,
            pipeline=pipeline,
        )


class PipelineRunner:
    _app: OnemlApp
    _pipeline_session_provider: PipelineSessionProvider
    _pipeline: Pipeline

    def __init__(
        self, app: OnemlApp, pipeline_session_provider: PipelineSessionProvider, pipeline: Pipeline
    ) -> None:
        self._app = app
        self._pipeline_session_provider = pipeline_session_provider
        self._pipeline = pipeline

    def _add_inputs_and_collect_outputs(
        self, inputs: Mapping[str, Any], output_storage: dict[str, Ref | Mapping[str, Ref]]
    ) -> Pipeline:
        pipelines = [self._pipeline]
        dependencies = list[DependencyOp]()
        if len(set(inputs)) > 0:
            data_provider_pipeline = build_data_provider_pipeline_from_objects(inputs)
            if self._pipeline.name == data_provider_pipeline.name:
                data_provider_pipeline = data_provider_pipeline.decorate(
                    data_provider_pipeline.name + "_"
                )
            pipelines.append(data_provider_pipeline)
            for k in data_provider_pipeline.outputs:
                dependencies.append(data_provider_pipeline.outputs[k] >> self._pipeline.inputs[k])
            for k0, col in data_provider_pipeline.out_collections.items():
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
        pipeline = CombinedPipeline(
            name="run",
            pipelines=pipelines,
            dependencies=dependencies,
        )
        required_inputs = set(chain(pipeline.required_inputs, pipeline.required_in_collections))
        if len(required_inputs) > 0:
            raise ValueError(f"Missing pipeline inputs: {required_inputs}.")
        if len(tuple(*pipeline.out_collections, *pipeline.outputs)) > 0:
            raise ValueError("Pipeline outputs should have been collected.")
        return pipeline

    def __call__(self, inputs: Mapping[str, Any] = {}) -> SessionOutputsGetter:
        output_storage = dict[str, Ref | Mapping[str, Ref]]()
        name = f"{self._pipeline.name}_{uuid4()}"
        pipeline = self._add_inputs_and_collect_outputs(inputs, output_storage)
        pipeline_registry = self._app.get_service(OnemlAppServices.PIPELINE_REGISTRY)
        pipeline_session_provider = self._pipeline_session_provider
        pipeline_registry.register_pipeline_provider(
            name, lambda: pipeline_session_provider.get_session(pipeline._dag)
        )
        self._app.execute_pipeline(name)
        return SessionOutputsGetter(output_storage)
