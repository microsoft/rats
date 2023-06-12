import os
import uuid

from oneml.io._pipeline_data import IPipelineDataManager
from oneml.pipelines.dag import PipelineClient
from ._executable import CallableExecutable
from ._node_execution import PipelineNodeExecutablesClient
from ._node_state import PipelineNodeState, PipelineNodeStateClient
from ._services import IProvideServices
from ._session_client import PipelineSessionClient
from ._session_frame import BasicPipelineSessionFrameCommands, PipelineSessionFrame
from ._session_plugins import IActivatePipelineSessionPlugins
from ._session_state import PipelineSessionStateClient


class PipelineSessionClientFactory:
    # TODO: How do I inject these without the builder component knowing about them?
    #       Is it ok for the builder to know about all of these?
    #       If we want to inject them, we should inject providers.
    #       So two calls to get_instance() result in new state instances.
    # _session_state_client: PipelineSessionStateClient
    # _node_state_client: PipelineNodeStateClient
    _services: IProvideServices
    _pipeline_data_client: IPipelineDataManager
    _session_plugin_client: IActivatePipelineSessionPlugins

    def __init__(
        self,
        services: IProvideServices,
        pipeline_data_client: IPipelineDataManager,
        session_plugin_client: IActivatePipelineSessionPlugins,
    ) -> None:
        self._services = services
        self._pipeline_data_client = pipeline_data_client
        self._session_plugin_client = session_plugin_client

    def get_instance(self, pipeline_client: PipelineClient) -> PipelineSessionClient:
        # TODO: we should move logic for creating a app id to a separate class.
        #       otherwise this method behaves differently on drivers and executors.
        session_id = os.environ.get("PIPELINE_SESSION_ID", str(uuid.uuid4()))

        node_client = pipeline_client.node_client()
        node_dependencies_client = pipeline_client.node_dependencies_client()
        data_dependencies_client = pipeline_client.data_dependencies_client()

        # TODO: move these clients to private properties + constructor args
        session_state_client = PipelineSessionStateClient()
        node_state_client = PipelineNodeStateClient()
        pipeline_data_client = self._pipeline_data_client
        node_executables_client = PipelineNodeExecutablesClient()

        for node in node_client.get_nodes():
            node_state_client.set_node_state(node, PipelineNodeState.REGISTERED)

        # TODO: frame logic should come from another layer of abstraction for better control.
        frame_commands = BasicPipelineSessionFrameCommands(
            session_state_client=session_state_client,
            node_state_client=node_state_client,
            node_dependencies_client=node_dependencies_client,
            node_executables_client=node_executables_client,
        )

        frame = PipelineSessionFrame(
            tuple(
                [
                    CallableExecutable(frame_commands.promote_registered_nodes),
                    CallableExecutable(frame_commands.promote_queued_nodes),
                    CallableExecutable(frame_commands.execute_pending_nodes),
                    CallableExecutable(frame_commands.check_pipeline_completion),
                ]
            )
        )

        session_client = PipelineSessionClient(
            session_id=session_id,
            services=self._services,
            session_frame=frame,
            session_state_client=session_state_client,
            pipeline_data_client=self._pipeline_data_client,
            session_executables_client=node_executables_client,
            node_state_client=node_state_client,
            node_executables_client=node_executables_client,
        )
        # Not sure if this activation belongs somewhere else.
        self._session_plugin_client.activate_all(session_client)
        return session_client
