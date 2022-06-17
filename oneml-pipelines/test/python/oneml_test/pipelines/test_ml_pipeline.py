from oneml.pipelines import (
    IExecutable,
    IManagePipelines,
    ITickablePipeline,
    MlPipeline,
    MlPipelineConfig,
    MlPipelineProvider,
    PipelineNode,
)


class FakeCommand(IExecutable):

    calls: int

    def __init__(self):
        self.calls = 0

    def execute(self) -> None:
        self.calls += 1


class FakeSession(IManagePipelines):

    stopped: int

    def __init__(self):
        self.stopped = 0

    def run_pipeline(self) -> None:
        raise NotImplementedError()

    def stop_pipeline(self) -> None:
        self.stopped += 1

    def set_pipeline(self, pipeline: ITickablePipeline) -> None:
        raise NotImplementedError()

    def get_pipeline(self) -> ITickablePipeline:
        raise NotImplementedError()


class TestMlPipeline:

    _open_frame_command: FakeCommand
    _execute_frame_command: FakeCommand
    _close_frame_command: FakeCommand
    _ml_pipeline: MlPipeline

    def setup(self) -> None:
        self._open_frame_command = FakeCommand()
        self._execute_frame_command = FakeCommand()
        self._close_frame_command = FakeCommand()

        self._ml_pipeline = MlPipeline(
            open_frame_command=self._open_frame_command,
            execute_frame_command=self._execute_frame_command,
            close_frame_command=self._close_frame_command,
        )

    def test_basics(self) -> None:
        # Just testing that the three commands get called on every tick
        assert self._open_frame_command.calls == 0
        assert self._execute_frame_command.calls == 0
        assert self._close_frame_command.calls == 0
        self._ml_pipeline.tick()
        assert self._open_frame_command.calls == 1
        assert self._execute_frame_command.calls == 1
        assert self._close_frame_command.calls == 1
        self._ml_pipeline.tick()
        assert self._open_frame_command.calls == 2
        assert self._execute_frame_command.calls == 2
        assert self._close_frame_command.calls == 2


class TestMlPipelineProvider:
    """
    Since the pipeline provider initializes a bunch of objects, it's a lot of
    work to fake/mock its dependencies. We use integration tests to make sure
    everything works together.
    """

    _command1: FakeCommand
    _command2: FakeCommand
    _session: FakeSession
    _provider: MlPipelineProvider

    def setup(self) -> None:
        self._command1 = FakeCommand()
        self._command2 = FakeCommand()

        self._session = FakeSession()

        config = MlPipelineConfig(
            executables_provider=lambda: {
                PipelineNode("fake-1"): lambda: self._command1,
                PipelineNode("fake-2"): lambda: self._command2,
            },
            dependencies_provider=lambda: {
                PipelineNode("fake-1"): tuple([PipelineNode("fake-2")])
            },
            session_provider=lambda: self._session,
        )
        self._provider = MlPipelineProvider(pipeline_config=config)

    def test_basics(self) -> None:
        pipeline = self._provider.get_pipeline()

        assert self._command1.calls == 0
        assert self._command2.calls == 0

        pipeline.tick()

        assert self._command1.calls == 0
        assert self._command2.calls == 1

        pipeline.tick()

        assert self._command1.calls == 1
        assert self._command2.calls == 1
