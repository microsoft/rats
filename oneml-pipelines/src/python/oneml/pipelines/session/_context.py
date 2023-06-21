from oneml.pipelines.dag import PipelineNodeId, PipelineSessionId
from oneml.services import scoped_service_ids
from oneml.services._context import ContextId


@scoped_service_ids
class OnemlSessionContextIds:
    SESSION_ID = ContextId[PipelineSessionId]("session-id")
    NODE_ID = ContextId[PipelineNodeId]("node-id")
