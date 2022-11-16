from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping

from oneml.pipelines.session import PipelinePort, PipelineSessionClient

from ..dag._client import P2Pipeline, ParamsRegistry, PipelineSessionProvider
from ..dag._dag import DagNode
from ..dag._processor import IProcess, OutProcessorParam
from ..ml import Estimator
from ..utils._frozendict import frozendict
from ._client import CombinedPipeline, Task
from ._pipeline import Pipeline


class InputDataProcessor(IProcess):
    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data = data

    def process(self) -> Mapping[str, Any]:
        return self._data

    @staticmethod
    def get_return_annotation(**inputs: Any) -> Mapping[str, OutProcessorParam]:
        return {k: OutProcessorParam(k, type(v)) for k, v in inputs.items()}


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
            return get_param(p.node, p.param)
        else:
            return {repr(p.node): get_param(p.node, p.param) for p in out_params.values()}

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

    def _data_estimator(
        self, train_inputs: dict[str, Any], eval_inputs: dict[str, Any]
    ) -> Pipeline:
        pls = tuple(
            Task(
                InputDataProcessor,
                name=k,
                params_getter=frozendict(data=inputs),
                return_annotation=InputDataProcessor.get_return_annotation(**inputs),
            )
            for k, inputs in (("train", train_inputs), ("eval", eval_inputs))
            if train_inputs and eval_inputs
        )
        return (
            Estimator(name="data", train_pipeline=pls[0], eval_pipeline=pls[1])
            if train_inputs and eval_inputs
            else Pipeline("data")
        )

    def __call__(
        self, name: str = "pl", train_inputs: dict[str, Any] = {}, eval_inputs: dict[str, Any] = {}
    ) -> SessionOutputsGetter:
        data_estimator = self._data_estimator(train_inputs, eval_inputs)
        pipeline = CombinedPipeline(
            data_estimator,
            self._pipeline,
            inputs={},
            outputs=self._pipeline.outputs,
            dependencies=(
                tuple(
                    getattr(data_estimator.outputs, param) >> getattr(self._pipeline.inputs, param)
                    for param in train_inputs
                )
            ),
            name=name,
        )
        session = PipelineSessionProvider.get_session(pipeline.dag, self._params_registry)
        session.run()
        return SessionOutputsGetter(pipeline, session)
