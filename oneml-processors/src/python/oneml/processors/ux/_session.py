from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping

from oneml.pipelines.session import PipelinePort, PipelineSessionClient

from ..dag._client import P2Pipeline, ParamsRegistry, PipelineSessionProvider
from ..dag._dag import DagNode
from ..dag._processor import IProcess, OutProcessorParam
from ..utils._frozendict import frozendict
from ._client import CombinedPipeline, Task
from ._pipeline import Pipeline


class InputDataProcessor(IProcess):
    def __init__(self, data: Any) -> None:
        self._data = data

    def process(self) -> Mapping[str, Any]:
        return dict(data=self._data)


def build_data_provider_pipeline_from_objects(data: Mapping[str, Any]) -> Pipeline:
    tasks = {
        k: Task(
            name=k,
            processor_type=InputDataProcessor,
            params_getter=frozendict(data=v),
            return_annotation=dict(data=type(v)),
        )
        for k, v in data.items()
    }
    outputs = {k: t.outputs.data for k, t in tasks.items()}
    return CombinedPipeline(*tasks.values(), name="DataProvider", outputs=outputs)


class SessionOutputsGetter(Iterable[str]):
    def __init__(self, pipeline: Pipeline, session: PipelineSessionClient) -> None:
        self._pipeline = pipeline
        self._session = session

    def __getitem__(self, key: str) -> Any:
        def get_param(node: DagNode, param: OutProcessorParam) -> Any:
            pipeline_node = P2Pipeline.node(node)
            pipeline_port = PipelinePort[Any](param.name)
            output_client = self._session.node_data_client_factory().get_instance(pipeline_node)
            return output_client.get_data(pipeline_port)

        out_params = self._pipeline.outputs[key]
        if len(out_params) == 1:
            p = next(iter(out_params.values()))
            return get_param(p[0].node, p[0].param)
        else:
            return frozendict({k: get_param(p[0].node, p[0].param) for k, p in out_params.items()})

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._pipeline.outputs


class PipelineRunner:
    def __init__(
        self, pipeline: Pipeline, params_registry: ParamsRegistry = ParamsRegistry()
    ) -> None:
        self._pipeline = pipeline
        self._params_registry = params_registry

    def __call__(self, inputs: Mapping[str, Any] = {}) -> SessionOutputsGetter:
        pipeline = self._pipeline
        if len(set(inputs)) > 0:
            data_provider_pipeline = build_data_provider_pipeline_from_objects(inputs)
            if pipeline.name == data_provider_pipeline.name:
                data_provider_pipeline = data_provider_pipeline.decorate(
                    data_provider_pipeline.name + "_"
                )
            pipeline = CombinedPipeline(
                data_provider_pipeline,
                pipeline,
                name="run",
                dependencies=tuple(
                    pipeline.inputs[k] << data_provider_pipeline.outputs[k]
                    for k in pipeline.inputs
                ),
            )
        if len(set(pipeline.inputs)) > 0:
            raise ValueError(f"Missing pipeline inputs: {set(pipeline.inputs)}.")
        session = PipelineSessionProvider.get_session(pipeline.dag, self._params_registry)
        session.run()
        return SessionOutputsGetter(pipeline, session)
