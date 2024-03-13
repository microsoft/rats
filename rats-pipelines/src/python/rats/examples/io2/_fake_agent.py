from typing import NamedTuple

from rats.io2 import IPublishNodeData
from rats.pipelines.dag import PipelinePort
from rats.services import ContextProvider, IExecutable

from ._data import SimpleMessage, SimpleMetrics

AGENT_RESPONSE_PORT = PipelinePort[SimpleMessage]("response")
AGENT_METRICS_PORT = PipelinePort[SimpleMetrics]("metrics")


class FakeResponse(NamedTuple):
    goal_complexity: float
    message: str


class FakeAgent(IExecutable):
    _prompt_ctx: ContextProvider[SimpleMessage]
    _pipeline_data: IPublishNodeData

    def __init__(
        self,
        prompt_ctx: ContextProvider[SimpleMessage],
        pipeline_data: IPublishNodeData,
    ) -> None:
        self._prompt_ctx = prompt_ctx
        self._pipeline_data = pipeline_data

    def execute(self) -> None:
        response = SimpleMessage("as a fake large language model, i don't know how to help you.")
        print(response.text)

        self._pipeline_data.publish_port(
            port=AGENT_RESPONSE_PORT,
            data=response,
        )
