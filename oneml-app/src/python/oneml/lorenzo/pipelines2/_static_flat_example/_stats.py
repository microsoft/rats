from abc import ABC, abstractmethod

from oneml.lorenzo.pipelines2 import IPipelineNode, IProvidePipelineNodes

from ...pipelines import PipelineDataReader
from ._load_mira import Mira
from ._load_repertoire import Repertoire
from ._pipeline_output import PipelineOutput


class SampleStatsTaskPresenter(ABC):

    @abstractmethod
    def on_stats_ready(self, total_samples: int) -> None:
        pass


class SampleStatsNode(IPipelineNode):

    _output_client: PipelineOutput
    _repertoire: Repertoire
    _mira: Mira

    def __init__(self, output_client: PipelineOutput, repertoire: Repertoire, mira: Mira):
        self._output_client = output_client
        self._repertoire = repertoire
        self._mira = mira

    def execute_node(self) -> None:
        total_samples = self._repertoire.count() + self._mira.count()
        self._output_client.add(int, total_samples)


class SampleStatsNodeProvider(IProvidePipelineNodes[SampleStatsNode]):
    _output_client: PipelineOutput
    _storage: PipelineDataReader

    def __init__(self, output_client: PipelineOutput, storage: PipelineDataReader):
        self._output_client = output_client
        self._storage = storage

    def get_pipeline_node(self) -> SampleStatsNode:
        return SampleStatsNode(
            output_client=self._output_client,
            repertoire=self._storage.load(Repertoire),
            mira=self._storage.load(Mira),
        )
