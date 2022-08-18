import uuid

from ._executable import CallableExecutable
from ._node_execution import PipelineNodeExecutablesClient
from ._node_state import PipelineNodeState, PipelineNodeStateClient
from ._session import PipelineSession
from ._session_client import PipelineSessionClient
from ._session_data_client import PipelineDataClient, PipelineNodeDataClientFactory
from ._session_frame import PipelineSessionFrame, BasicPipelineSessionFrameCommands
from ._session_plugins import IActivatePipelineSessionPlugins
from oneml.pipelines.dag import PipelineClient
from ._session_state import PipelineSessionStateClient


class PipelineSessionClientFactory:

    # TODO: How do I inject these without the builder component knowing about them?
    #       Is it ok for the builder to know about all of these?
    #       If we want to inject them, we should inject providers.
    #       So two calls to get_instance() result in new state instances.
    # _session_state_client: PipelineSessionStateClient
    # _node_state_client: PipelineNodeStateClient
    _session_plugin_client: IActivatePipelineSessionPlugins

    def __init__(self, session_plugin_client: IActivatePipelineSessionPlugins) -> None:
        self._session_plugin_client = session_plugin_client

    def get_instance(self, pipeline_client: PipelineClient) -> PipelineSessionClient:
        session_id = str(uuid.uuid4())

        node_client = pipeline_client.node_client()
        node_dependencies_client = pipeline_client.node_dependencies_client()
        # node_executables_client = components.node_executables_client()

        # TODO: move these clients to private properties + constructor args
        session_state_client = PipelineSessionStateClient()
        node_state_client = PipelineNodeStateClient()
        pipeline_data_client = PipelineDataClient()
        node_executables_client = PipelineNodeExecutablesClient()

        node_data_client_factory = PipelineNodeDataClientFactory(pipeline_data_client)

        for node in node_client.get_nodes():
            node_state_client.set_node_state(node, PipelineNodeState.REGISTERED)

        # TODO: frame logic should come from another layer of abstraction for better control.
        frame_commands = BasicPipelineSessionFrameCommands(
            session_state_client=session_state_client,
            node_state_client=node_state_client,
            node_dependencies_client=node_dependencies_client,
            node_executables_client=node_executables_client,
        )

        frame = PipelineSessionFrame(tuple([
            CallableExecutable(frame_commands.promote_registered_nodes),
            CallableExecutable(frame_commands.promote_queued_nodes),
            CallableExecutable(frame_commands.execute_pending_nodes),
            CallableExecutable(frame_commands.check_pipeline_completion),
        ]))

        session = PipelineSession(
            session_state_client=session_state_client,
            session_frame=frame,
        )

        session_client = PipelineSessionClient(
            session_id=session_id,
            session_client=session,
            session_frame=frame,
            session_state_client=session_state_client,
            pipeline_data_client=pipeline_data_client,
            session_executables_client=node_executables_client,
            node_state_client=node_state_client,
            node_data_client_factory=node_data_client_factory,
            node_executables_client=node_executables_client,
        )
        # Not sure if this activation belongs somewhere else.
        self._session_plugin_client.activate_all(session_client)
        return session_client
