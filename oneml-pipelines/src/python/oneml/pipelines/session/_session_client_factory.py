import uuid
from typing import Tuple

from oneml.pipelines.dag import PipelineClient, PipelineNode

from ._executable import CallableExecutable
from ._node_execution import PipelineNodeExecutablesClient
from ._node_state import PipelineNodeState, PipelineNodeStateClient
from ._session import PipelineSession
from ._session_client import PipelineSessionClient
from ._session_data_client import (
    IManagePipelineData,
    PipelineDataClient,
    PipelineNodeDataClientFactory,
    PipelineNodeInputDataClientFactory,
    ReadProxyPipelineDataClient,
)
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
    _session_plugin_client: IActivatePipelineSessionPlugins

    def __init__(self, session_plugin_client: IActivatePipelineSessionPlugins) -> None:
        self._session_plugin_client = session_plugin_client

    def get_instance_with_external_data(
        self,
        pipeline_client: PipelineClient,
        external_storage: IManagePipelineData,
        external_nodes: Tuple[PipelineNode, ...],
    ) -> PipelineSessionClient:
        session_id = str(uuid.uuid4())

        node_client = pipeline_client.node_client()
        node_dependencies_client = pipeline_client.node_dependencies_client()
        data_dependencies_client = pipeline_client.data_dependencies_client()

        # TODO: move these clients to private properties + constructor args
        session_state_client = PipelineSessionStateClient()
        node_state_client = PipelineNodeStateClient()
        primary_data_client = PipelineDataClient()
        pipeline_data_client = ReadProxyPipelineDataClient(
            primary_client=primary_data_client,
            proxy_client=external_storage,
            proxied_nodes=external_nodes,
        )
        node_executables_client = PipelineNodeExecutablesClient()
        node_input_data_client_factory = PipelineNodeInputDataClientFactory(
            data_dependencies_client=data_dependencies_client,
            data_client=pipeline_data_client,
        )

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
            node_input_data_client_factory=node_input_data_client_factory,
        )
        # Not sure if this activation belongs somewhere else.
        self._session_plugin_client.activate_all(session_client)
        return session_client

    def get_instance(self, pipeline_client: PipelineClient) -> PipelineSessionClient:
        session_id = str(uuid.uuid4())

        node_client = pipeline_client.node_client()
        node_dependencies_client = pipeline_client.node_dependencies_client()
        data_dependencies_client = pipeline_client.data_dependencies_client()

        # TODO: move these clients to private properties + constructor args
        session_state_client = PipelineSessionStateClient()
        node_state_client = PipelineNodeStateClient()
        pipeline_data_client = PipelineDataClient()
        node_executables_client = PipelineNodeExecutablesClient()
        node_input_data_client_factory = PipelineNodeInputDataClientFactory(
            data_dependencies_client=data_dependencies_client,
            data_client=pipeline_data_client,
        )

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
            node_input_data_client_factory=node_input_data_client_factory,
        )
        # Not sure if this activation belongs somewhere else.
        self._session_plugin_client.activate_all(session_client)
        return session_client
