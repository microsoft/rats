from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping

from oneml.pipelines.session import PipelinePort, PipelineSessionClient

from ._client import P2Pipeline, ParamsRegistry, PipelineSessionProvider
from ._frozendict import frozendict
from ._pipeline import PNode
from ._processor import IProcess, OutParameter
from .ml import Estimator
from .ux._client import CombinedWorkflow, Task
from .ux._workflow import Workflow


class InputDataProcessor(IProcess):
    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data = data

    def process(self) -> Mapping[str, Any]:
        return self._data

    @staticmethod
    def get_return_annotation(**inputs: Any) -> Mapping[str, OutParameter]:
        return {k: OutParameter(k, type(v)) for k, v in inputs.items()}


class SessionOutputsGetter(Iterable[str]):
    def __init__(self, workflow: Workflow, session: PipelineSessionClient) -> None:
        self._workflow = workflow
        self._session = session

    def __getitem__(self, key: str) -> Any:
        def get_param(node: PNode, param: OutParameter) -> Any:
            pipeline_node = P2Pipeline.node(node)
            pipeline_port = PipelinePort[Any](param.name)
            output_client = self._session.node_data_client_factory().get_instance(pipeline_node)
            return output_client.get_data(pipeline_port)

        out_params = self._workflow.outputs[key]
        if len(out_params) == 1:
            p = next(iter(out_params.values()))
            return get_param(p.node, p.param)
        else:
            return {repr(p.node): get_param(p.node, p.param) for p in out_params.values()}

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._workflow.outputs


class WorkflowRunner:
    def __init__(
        self, workflow: Workflow, params_registry: ParamsRegistry = ParamsRegistry()
    ) -> None:
        self._workflow = workflow
        self._params_registry = params_registry

    def _data_estimator(
        self, train_inputs: dict[str, Any], eval_inputs: dict[str, Any]
    ) -> Workflow:
        wfs = tuple(
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
            Estimator(name="data", train_wf=wfs[0], eval_wf=wfs[1])
            if train_inputs and eval_inputs
            else Workflow("data")
        )

    def __call__(
        self, name: str = "wf", train_inputs: dict[str, Any] = {}, eval_inputs: dict[str, Any] = {}
    ) -> SessionOutputsGetter:
        data_estimator = self._data_estimator(train_inputs, eval_inputs)
        workflow = CombinedWorkflow(
            data_estimator,
            self._workflow,
            inputs={},
            outputs=self._workflow.outputs,
            dependencies=(
                tuple(
                    getattr(data_estimator.outputs, param) >> getattr(self._workflow.inputs, param)
                    for param in train_inputs
                )
            ),
            name=name,
        )
        session = PipelineSessionProvider.get_session(workflow.pipeline, self._params_registry)
        session.run()
        return SessionOutputsGetter(workflow, session)
