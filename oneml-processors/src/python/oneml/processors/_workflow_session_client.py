from typing import Any, Hashable, Iterable, Iterator

from oneml.pipelines.session import PipelinePort, PipelineSessionClient

from ._client import P2Pipeline, PipelineSessionProvider
from ._environment_singletons import IRegistryOfSingletonFactories
from ._input_data import InputDataProcessorProps
from ._ux import Workflow, WorkflowClient


class WorkflowSessionProvider:
    @classmethod
    def get_session(
        cls, workflow: Workflow, environment_singletons_registry: IRegistryOfSingletonFactories
    ) -> PipelineSessionClient:
        session = PipelineSessionProvider.get_session(
            workflow.pipeline, environment_singletons_registry
        )
        return session


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
    def __init__(
        self, workflow: Workflow, environment_singletons_registry: IRegistryOfSingletonFactories
    ) -> None:
        self._workflow = workflow
        self._environment_singletons_registry = environment_singletons_registry

    def __call__(self, **kwrgs: Hashable) -> SessionOutputsGetter:
        input_workflows = tuple(
            WorkflowClient.single_task_from_props(param_name, InputDataProcessorProps(param_value))
            for param_name, param_value in kwrgs.items()
        )
        workflow = WorkflowClient.compose_workflow(
            "runnable",
            input_workflows + (self._workflow,),
            tuple(i.ret.data >> self._workflow.sig[i.name] for i in input_workflows),
        )
        session = WorkflowSessionProvider.get_session(
            workflow, self._environment_singletons_registry
        )
        session.run()
        return SessionOutputsGetter(workflow, session)
