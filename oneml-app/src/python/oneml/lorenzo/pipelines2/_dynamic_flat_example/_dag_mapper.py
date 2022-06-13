from typing import Type

from oneml.lorenzo.pipelines2 import IProvidePipelineNodes, PipelineNodeType


class PipelineDagClient:

    def add_node(
            self,
            key: Type[PipelineNodeType],
            value: IProvidePipelineNodes[PipelineNodeType]) -> None:
        pass
