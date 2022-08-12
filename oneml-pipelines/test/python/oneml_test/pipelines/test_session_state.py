from oneml.pipelines import PipelineSessionState, PipelineSessionStateClient


class TestPipelineSessionStateClient:

    _client: PipelineSessionStateClient

    def setup(self) -> None:
        self._client = PipelineSessionStateClient()

    def test_basics(self) -> None:
        assert self._client.get_state() == PipelineSessionState.PENDING
        self._client.set_state(PipelineSessionState.RUNNING)
        assert self._client.get_state() == PipelineSessionState.RUNNING
