from oneml.pipelines.session import (
    OnemlSessionContexts,
    PipelineNodeExecutablesClient,
    PipelineNodeStateClient,
    PipelineSessionClient,
    PipelineSessionFrameClient,
    PipelineSessionStateClient,
)
from oneml.services import IProvideServices, service_provider

from ._oneml_app_services import OnemlAppServices
from ._session_services import OnemlSessionServices


class OnemlSessionDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(OnemlSessionServices.SESSION_CLIENT)
    def session_client(self) -> PipelineSessionClient:
        frame = self._app.get_service(OnemlSessionServices.SESSION_FRAME_CLIENT)
        state = self._app.get_service(OnemlSessionServices.SESSION_STATE_CLIENT)
        return PipelineSessionClient(
            session_frame=frame,
            session_state_client=state,
        )

    @service_provider(OnemlSessionServices.SESSION_FRAME_CLIENT)
    def frame_client(self) -> PipelineSessionFrameClient:
        """
        TODO: revisit this
        I think this provider can only be called when within a session, so it has to be used with
        get_service_provider(). I'm not sure if this is a bad pattern yet or not.
        """
        return PipelineSessionFrameClient(
            context_client=self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT),  # type: ignore
            session_state_client=self._app.get_service(OnemlSessionServices.SESSION_STATE_CLIENT),
            node_state_client=self._app.get_service(OnemlSessionServices.NODE_STATE_CLIENT),
            node_executables_client=self._app.get_service(
                OnemlSessionServices.NODE_EXECUTABLES_CLIENT,
            ),
            dag_client=self._app.get_service(OnemlAppServices.PIPELINE_DAG_CLIENT),
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
        # TODO: node execution does not belong to a session
        #       there is more than one way for a node to progress between states
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return PipelineNodeExecutablesClient(
            context=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
        )
