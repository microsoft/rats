# pyright: reportUninitializedInstanceVariable=false
from oneml.pipelines.session import PipelineSessionState, PipelineSessionStateClient


class TestPipelineSessionStateClient:
    _client: PipelineSessionStateClient

    def setup_method(self) -> None:
        self._client = PipelineSessionStateClient(lambda: 1)

    def test_basics(self) -> None:
        self._client.set_state(PipelineSessionState.RUNNING)
        assert self._client.get_state() == PipelineSessionState.RUNNING
