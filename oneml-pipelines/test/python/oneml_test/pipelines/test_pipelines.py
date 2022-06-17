import pytest

from oneml.pipelines import (
    DeferredPipeline,
    ITickablePipeline,
    NullPipeline,
    PipelineChain,
    PipelineSession,
)


class StopPipelineError(RuntimeError):
    pass


class FakePipeline(ITickablePipeline):

    ticks: int

    def __init__(self):
        self.ticks = 0

    def tick(self) -> None:
        self.ticks += 1

        if self.ticks == 50:
            raise StopPipelineError()


class TestNullPipeline:

    def test_basics(self) -> None:
        pipeline = NullPipeline()

        with pytest.raises(RuntimeError):
            pipeline.tick()


class TestPipelineSession:

    _pipeline: FakePipeline
    _session: PipelineSession

    def setup(self) -> None:
        self._pipeline = FakePipeline()
        self._session = PipelineSession(self._pipeline)

    def test_basics(self) -> None:
        assert self._pipeline.ticks == 0

        try:
            self._session.run_pipeline()
        except StopPipelineError:
            assert self._pipeline.ticks == 50

    def test_set_pipeline(self) -> None:
        assert self._pipeline.ticks == 0
        other_pipeline = FakePipeline()

        self._session.set_pipeline(other_pipeline)

        try:
            self._session.run_pipeline()
        except StopPipelineError:
            assert self._pipeline.ticks == 0
            assert other_pipeline.ticks == 50

    def test_stop_pipeline(self) -> None:
        assert self._pipeline.ticks == 0

        self._session.stop_pipeline()
        # This looks like a weird API. Probably need to change it.
        self._session.run_pipeline()
        assert self._pipeline.ticks == 0

    def test_get_pipeline(self) -> None:
        assert self._session.get_pipeline() == self._pipeline


class TestPipelineChain:

    _pipeline1: FakePipeline
    _pipeline2: FakePipeline
    _chain: PipelineChain

    def setup(self) -> None:
        self._pipeline1 = FakePipeline()
        self._pipeline2 = FakePipeline()

        self._chain = PipelineChain(tuple([
            self._pipeline1,
            self._pipeline2,
        ]))

    def test_basics(self) -> None:
        assert self._pipeline1.ticks == 0
        assert self._pipeline2.ticks == 0

        self._chain.tick()

        assert self._pipeline1.ticks == 1
        assert self._pipeline2.ticks == 1


class TestDeferredPipeline:

    _fake_provider_count: int
    _pipeline: DeferredPipeline

    def setup(self) -> None:
        self._fake_provider_count = 0
        self._pipeline = DeferredPipeline(self._fake_provider)

    def _fake_provider(self) -> FakePipeline:
        self._fake_provider_count += 1
        return FakePipeline()

    def test_basics(self) -> None:
        assert self._fake_provider_count == 0
        self._pipeline.tick()
        assert self._fake_provider_count == 1
        self._pipeline.tick()
        assert self._fake_provider_count == 2
