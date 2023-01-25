from __future__ import annotations

from itertools import chain
from typing import Any, Iterable, Iterator, Mapping

from oneml.pipelines.session import PipelinePort, PipelineSessionClient

from ..dag._client import P2Pipeline, ParamsRegistry, PipelineSessionProvider
from ..dag._dag import DagNode
from ..dag._processor import IProcess, OutProcessorParam
from ..utils._frozendict import frozendict
from ._builder import CombinedPipeline, Task
from ._pipeline import OutEntry, Outputs, Pipeline


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

        out_params: OutEntry | Outputs = (
            self._pipeline.outputs[key]
            if key in self._pipeline.outputs
            else self._pipeline.out_collections[key]
        )
        if isinstance(out_params, OutEntry):
            if len(out_params) == 1:
                return get_param(out_params[0].node, out_params[0].param)
            else:
                return [get_param(p.node, p.param) for p in out_params]
        else:
            d = {}
            for k, entry in out_params.items():
                if len(entry) == 1:
                    d[k] = get_param(entry[0].node, entry[0].param)
                else:
                    d[k] = [get_param(p.node, p.param) for p in entry]
            return frozendict(d)

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __iter__(self) -> Iterator[str]:
        yield from chain(self._pipeline.outputs, self._pipeline.out_collections)


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
                    for k in inputs
                    if k.count(".") == 0
                )
                + tuple(
                    pipeline.in_collections[k0][k1]
                    << data_provider_pipeline.out_collections[k0][k1]
                    for k in inputs
                    if k.count(".") == 1
                    for k0, k1 in [k.split(".")]
                ),
            )
        if len(set(chain(pipeline.inputs, pipeline.in_collections))) > 0:
            raise ValueError(f"Missing pipeline inputs: {set(pipeline.inputs)}.")
        session = PipelineSessionProvider.get_session(pipeline._dag, self._params_registry)
        session.run()
        return SessionOutputsGetter(pipeline, session)
