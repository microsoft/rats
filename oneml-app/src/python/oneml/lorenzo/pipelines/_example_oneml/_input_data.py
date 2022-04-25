from oneml.lorenzo.pipelines import PipelineStep, PipelineDataWriter
from ._matrix import RealsMatrix
from ._vector import RealsVector


class InputLabelsStep(PipelineStep):

    _storage: PipelineDataWriter

    def __init__(self, storage: PipelineDataWriter):
        self._storage = storage

    def execute(self) -> None:
        data = tuple([
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            1.0,
            0.0,
        ])
        self._storage.save(RealsVector, RealsVector(data=data))


class InputDataStep(PipelineStep):

    _storage: PipelineDataWriter

    def __init__(self, storage: PipelineDataWriter):
        self._storage = storage

    def execute(self) -> None:
        data = tuple([
            tuple([0.0, 0.0, 0.0, 1.0, 0.0]),
            tuple([0.0, 1.0, 0.0, 1.0, 0.0]),
            tuple([1.0, 0.0, 0.0, 1.0, 0.0]),
            tuple([0.0, 0.0, 0.0, 1.0, 1.0]),
            tuple([0.0, 0.0, 1.0, 1.0, 0.0]),
            tuple([0.0, 0.0, 0.0, 0.0, 0.0]),
            tuple([0.0, 0.0, 0.0, 1.0, 0.0]),
        ])
        self._storage.save(RealsMatrix, RealsMatrix(data=data))
