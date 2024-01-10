from typing import Any

from typing_extensions import NamedTuple

from oneml.pipelines.dag import PipelineNode, PipelinePort
from oneml.services import ContextId, scoped_context_ids


class PipelineSession(NamedTuple):
    # A unique ID for the pipeline session we are running.
    id: str


@scoped_context_ids
class OnemlSessionContexts:
    PIPELINE = ContextId[PipelineSession]("pipeline")
    NODE = ContextId[PipelineNode]("pipeline-node")
    PORT = ContextId[PipelinePort[Any]]("pipeline-port")
