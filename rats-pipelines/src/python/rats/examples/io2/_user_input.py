from rats.io2 import IPublishNodeData
from rats.pipelines.dag import PipelinePort
from rats.services import ContextProvider, IExecutable

from ._data import SimpleMessage

USER_RESPONSE_PORT = PipelinePort[SimpleMessage]("response")


class UserInput(IExecutable):
    _pipeline_data: IPublishNodeData

    def __init__(
        self,
        prompt_ctx: ContextProvider[SimpleMessage],
        pipeline_data: IPublishNodeData,
    ) -> None:
        self._prompt_ctx = prompt_ctx
        self._pipeline_data = pipeline_data

    def execute(self) -> None:
        # user_msg = input(f"{self._prompt_ctx().value}\n").strip()
        print(self._prompt_ctx().text)
        user_msg = "fake user input"
        self._pipeline_data.publish_port(port=USER_RESPONSE_PORT, data=SimpleMessage(user_msg))
