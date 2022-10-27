from __future__ import annotations

from typing import Any, Iterable, Iterator, Mapping

from oneml.pipelines.session import PipelinePort, PipelineSessionClient

from ._client import P2Pipeline, ParamsRegistry, PipelineSessionProvider
from ._frozendict import frozendict
from ._processor import IProcess, OutParameter
from ._ux import Workflow, WorkflowClient


class InputDataProcessor(IProcess):
    def __init__(self, data: Any):
        self._data = data

    def process(self) -> Mapping[str, Any]:
        return dict(data=self._data)


class SessionOutputsGetter(Iterable[str]):
    def __init__(self, workflow: Workflow, session: PipelineSessionClient) -> None:
        self._workflow = workflow
        self._session = session

    def __getitem__(self, key: str) -> Any:
        task_param = self._workflow._output_sources[key]
        pipeline_node = P2Pipeline.node(task_param.node)
        pipeline_port = PipelinePort[Any](task_param.param)
        output_client = self._session.node_data_client_factory().get_instance(pipeline_node)
        val = output_client.get_data(pipeline_port)
        return val

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._workflow.ret


class WorkflowRunner:
    def __init__(self, workflow: Workflow, params_registry: ParamsRegistry) -> None:
        self._workflow = workflow
        self._params_registry = params_registry

    def __call__(self, name: str = "runnable_wf", **inputs: Any) -> SessionOutputsGetter:
        input_workflows = tuple(
            WorkflowClient.single_task(
                name,
                InputDataProcessor,
                frozendict(data=input),
                return_annotation=dict(data=OutParameter("data", type(input))),
            )
            for name, input in inputs.items()
        )
        workflow = WorkflowClient.compose_workflow(
            name,
            input_workflows + (self._workflow,),
            tuple(i.ret.data >> self._workflow.sig[i.name] for i in input_workflows),
        )
        session = PipelineSessionProvider.get_session(workflow.pipeline, self._params_registry)
        session.run()
        return SessionOutputsGetter(workflow, session)
