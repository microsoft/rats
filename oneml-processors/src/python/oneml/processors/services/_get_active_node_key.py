# type: ignore

class GetActiveNodeKey:
    _pipeline_session_context: "PipelineSessionContext"

    def __init__(self, pipeline_session_context: "PipelineSessionContext"):
        self._pipeline_session_context = pipeline_session_context

    def __call__(self) -> str:
        pipeline_session_client = self._pipeline_session_context.get_context()
        node_executables_client = pipeline_session_client.node_executables_client()
        node = node_executables_client.get_active_node()
        key = node.key
        return key
