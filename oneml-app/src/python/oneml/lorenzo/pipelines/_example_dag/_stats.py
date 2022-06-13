from abc import ABC, abstractmethod

from oneml.lorenzo.pipelines import PipelineDataReader

from ._mira import Mira
from ._repertoire import Repertoire


class SampleStatsTaskPresenter(ABC):

    @abstractmethod
    def on_stats_ready(self, total_samples: int) -> None:
        pass


class SampleStatsTask:

    _presenter: SampleStatsTaskPresenter
    _repertoire: Repertoire
    _mira: Mira

    def __init__(self, presenter: SampleStatsTaskPresenter, repertoire: Repertoire, mira: Mira):
        self._presenter = presenter
        self._repertoire = repertoire
        self._mira = mira

    def execute(self) -> None:
        total_samples = self._repertoire.count() + self._mira.count()
        self._presenter.on_stats_ready(total_samples)


class SampleStatsTaskFactory:
    _presenter: SampleStatsTaskPresenter
    _storage: PipelineDataReader

    def get_instance(self) -> SampleStatsTask:
        return SampleStatsTask(
            self._presenter,
            self._storage.load(Repertoire),
            self._storage.load(Mira),
        )
