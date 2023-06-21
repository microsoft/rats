import os
import uuid

from oneml.services._context import ContextClient

from ...services import IProvideServices
from ..dag import PipelineClient, PipelineSessionId
from ._executable import CallableExecutable
from ._node_execution import PipelineNodeExecutablesClient
from ._node_state import PipelineNodeState, PipelineNodeStateClient
from ._running_session_registry import RunningSessionRegistry
from ._session_client import PipelineSessionClient
from ._session_data import SessionDataClient
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
    _running_session_registry: RunningSessionRegistry
    _services: IProvideServices
    _context_client: ContextClient
    _session_data_client: SessionDataClient

    def __init__(
        self,
        running_session_registry: RunningSessionRegistry,
        services: IProvideServices,
        context_client: ContextClient,
        session_data_client: SessionDataClient,
    ) -> None:
        self._running_session_registry = running_session_registry
        self._services = services
        self._context_client = context_client
        self._session_data_client = session_data_client

    def get_instance(
        self,
        pipeline_client: PipelineClient,
        session_plugin_client: IActivatePipelineSessionPlugins,
    ) -> PipelineSessionClient:
        # TODO: we should move logic for creating a app id to a separate class.
        #       otherwise this method behaves differently on drivers and executors.
        session_id = PipelineSessionId(os.environ.get("PIPELINE_SESSION_ID", str(uuid.uuid4())))

        node_client = pipeline_client.node_client()
        node_dependencies_client = pipeline_client.node_dependencies_client()
        data_dependencies_client = pipeline_client.data_dependencies_client()
        loaders, publishers = self._session_data_client.configure_loaders_and_publishers(
            session_id, node_client, data_dependencies_client
        )

        # TODO: move these clients to private properties + constructor args
        session_state_client = PipelineSessionStateClient()
        node_state_client = PipelineNodeStateClient()
        node_executables_client = PipelineNodeExecutablesClient()

        for node in node_client.get_nodes():
            node_state_client.set_node_state(node, PipelineNodeState.REGISTERED)

        # TODO: frame logic should come from another layer of abstraction for better control.
        frame_commands = BasicPipelineSessionFrameCommands(
            context_client=self._context_client,
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
            running_session_registry=self._running_session_registry,
            session_id=session_id,
            services=self._services,
            context_client=self._context_client,
            session_frame=frame,
            session_state_client=session_state_client,
            session_executables_client=node_executables_client,
            node_state_client=node_state_client,
            node_executables_client=node_executables_client,
            pipeline_loader_getter=loaders,
            pipeline_publisher_getter=publishers,
        )
        # Not sure if this activation belongs somewhere else.
        session_plugin_client.activate_all(session_client)
        return session_client
