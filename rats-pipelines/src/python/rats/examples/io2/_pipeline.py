from pathlib import Path

from rats.io2 import LocalIoSettings, LocalJsonIoSettings
from rats.pipelines.building import PipelineBuilderClient
from rats.services import IExecutable

from ._fake_agent import AGENT_RESPONSE_PORT, FakeAgent
from ._user_input import UserInput


class Io2ExamplePipeline(IExecutable):
    _builder: PipelineBuilderClient
    _json_storage: LocalJsonIoSettings
    _local_io_settings: LocalIoSettings
    _user_input_exe: UserInput
    _fake_agent_exe: FakeAgent

    def __init__(
        self,
        builder_client: PipelineBuilderClient,
        json_storage: LocalJsonIoSettings,
        local_io_settings: LocalIoSettings,
        user_input_exe: UserInput,
        fake_agent_exe: FakeAgent,
    ) -> None:
        self._builder = builder_client
        self._json_storage = json_storage
        self._local_io_settings = local_io_settings
        self._user_input_exe = user_input_exe
        self._fake_agent_exe = fake_agent_exe

    def execute(self) -> None:
        self._local_io_settings.set_data_path(Path(".tmp/example-pipelines"))

        user_input = self._builder.node("user-input")
        fake_agent = self._builder.node("fake-agent")

        self._builder.add_node(user_input)
        self._builder.add_node(fake_agent)

        self._builder.add_dependency(fake_agent, user_input)

        self._builder.set_executable(user_input, self._user_input_exe)
        self._builder.set_executable(fake_agent, self._fake_agent_exe)

        self._json_storage.register_port(fake_agent, AGENT_RESPONSE_PORT)
