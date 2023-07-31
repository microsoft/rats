from typing import NamedTuple

from oneml.pipelines.dag import PipelineNode
from oneml.services import ContextId, scoped_context_ids


class PipelineContext(NamedTuple):
    # A unique ID for the pipeline session we are running.
    id: str


class PipelineNodeContext(NamedTuple):
    id: str
    node: PipelineNode


@scoped_context_ids
class OnemlSessionContexts:
    PIPELINE = ContextId[PipelineContext]("pipeline")
    PIPELINE_NODE = ContextId[PipelineNodeContext]("pipeline-node")
