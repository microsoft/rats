from rats.app import RatsAppServices, RatsIo2Services
from rats.services import IProvideServices, ServiceId, scoped_service_ids, service_provider

from ._data import SimpleMessage
from ._fake_agent import FakeAgent
from ._pipeline import Io2ExamplePipeline
from ._user_input import UserInput


@scoped_service_ids
class Io2ExampleServices:
    PIPELINE = ServiceId[Io2ExamplePipeline]("pipeline")
    USER_INPUT_EXE = ServiceId[UserInput]("user-input-exe")
    FAKE_AGENT_EXE = ServiceId[FakeAgent]("fake-agent-exe")


class Io2ExampleDiContainer:
    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(Io2ExampleServices.PIPELINE)
    def example_pipeline(self) -> Io2ExamplePipeline:
        return Io2ExamplePipeline(
            builder_client=self._app.get_service(RatsAppServices.PIPELINE_BUILDER),
            json_storage=self._app.get_service(RatsIo2Services.LOCAL_JSON_SETTINGS),
            local_io_settings=self._app.get_service(RatsIo2Services.LOCAL_IO_SETTINGS),
            user_input_exe=self._app.get_service(Io2ExampleServices.USER_INPUT_EXE),
            fake_agent_exe=self._app.get_service(Io2ExampleServices.FAKE_AGENT_EXE),
        )

    @service_provider(Io2ExampleServices.USER_INPUT_EXE)
    def user_input_exe(self) -> UserInput:
        return UserInput(
            prompt_ctx=lambda: SimpleMessage(
                "Welcome to a fake LLM experience. How can I pretend to " + "help?",
            ),
            pipeline_data=self._app.get_service(RatsIo2Services.PIPELINE_DATA),
        )

    @service_provider(Io2ExampleServices.FAKE_AGENT_EXE)
    def fake_agent_exe(self) -> FakeAgent:
        return FakeAgent(
            prompt_ctx=lambda: SimpleMessage(
                "Welcome to a fake LLM experience. How can I pretend to " + "help?",
            ),
            pipeline_data=self._app.get_service(RatsIo2Services.PIPELINE_DATA),
        )
