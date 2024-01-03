from oneml.pipelines.session import (
    OnemlSessionContexts,
    PipelineNodeExecutablesClient,
    PipelineNodeStateClient,
    PipelineSessionClient,
    PipelineSessionFrameClient,
    PipelineSessionStateClient,
)
from oneml.services import IProvideServices, executable, service_provider

from ._oneml_app_services import OnemlAppServices
from ._session_services import OnemlSessionExecutables, OnemlSessionServices


class OnemlSessionDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(OnemlSessionServices.SESSION_CLIENT)
    def session_client(self) -> PipelineSessionClient:
        exe_client = self._app.get_service(OnemlAppServices.EXE_CLIENT)
        state = self._app.get_service(OnemlSessionServices.SESSION_STATE_CLIENT)
        return PipelineSessionClient(
            session_frame=executable(lambda: exe_client.execute_id(OnemlSessionExecutables.FRAME)),
            session_state_client=state,
        )

    @service_provider(OnemlSessionExecutables.FRAME)
    def session_frame_exe(self) -> PipelineSessionFrameClient:
        """Session frame execution client.

        TODO: revisit this
        I think this provider can only be called when within a session, so it has to be used with
        get_service_provider(). I'm not sure if this is a bad pattern yet or not.
        """
        exe_client = self._app.get_service(OnemlAppServices.EXE_CLIENT)
        return PipelineSessionFrameClient(
            context_client=self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT),
            session_state_client=self._app.get_service(OnemlSessionServices.SESSION_STATE_CLIENT),
            node_state_client=self._app.get_service(OnemlSessionServices.NODE_STATE_CLIENT),
            dag_client=self._app.get_service(OnemlAppServices.PIPELINE_DAG_CLIENT),
            execute_node=executable(lambda: exe_client.execute_id(OnemlSessionExecutables.NODE)),
        )

    @service_provider(OnemlSessionServices.SESSION_STATE_CLIENT)
    def session_state_client(self) -> PipelineSessionStateClient:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return PipelineSessionStateClient(
            context=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
        )

    @service_provider(OnemlSessionServices.NODE_STATE_CLIENT)
    def node_state_client(self) -> PipelineNodeStateClient:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return PipelineNodeStateClient(
            context=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
        )

    @service_provider(OnemlSessionServices.NODE_EXECUTABLES_CLIENT)
    def session_node_exe_client(self) -> PipelineNodeExecutablesClient:
        return self._app.get_service(OnemlSessionExecutables.NODE)

    @service_provider(OnemlSessionExecutables.NODE)
    def session_node_exe(self) -> PipelineNodeExecutablesClient:
        # TODO: node execution does not belong to a session
        #       there is more than one way for a node to progress between states
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return PipelineNodeExecutablesClient(
            namespace=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
            node_ctx=context_client.get_context_provider(OnemlSessionContexts.NODE),
        )
