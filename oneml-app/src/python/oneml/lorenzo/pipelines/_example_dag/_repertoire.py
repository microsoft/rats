import random
import string
from abc import ABC, abstractmethod
from typing import Dict


class Repertoire:
    _data: Dict[str, str]

    def __init__(self, data: Dict[str, str]):
        self._data = data

    def count(self) -> int:
        return len(self._data.keys())


class RepertoireLabels:
    _data: Dict[str, str]

    def __init__(self, data: Dict[str, str]):
        self._data = data

    def count(self) -> int:
        return len(self._data.keys())


class LoadRepertoireTaskPresenter(ABC):

    @abstractmethod
    def on_repertoire_ready(self, repertoires: Repertoire) -> None:
        pass

    @abstractmethod
    def on_labels_ready(self, labels: RepertoireLabels) -> None:
        pass


class LoadRepertoireTask:

    _presenter: LoadRepertoireTaskPresenter
    _seed: str

    def __init__(self, presenter: LoadRepertoireTaskPresenter, seed: str):
        self._presenter = presenter
        self._seed = seed

    def execute(self) -> None:
        result = {}
        random.seed(self._seed)
        num_repertoires = random.randint(5, 30)
        letters = string.ascii_uppercase

        for x in range(num_repertoires):
            key = ''.join(random.choice(letters) for _ in range(10))
            value = ''.join(random.choice(letters) for _ in range(10))
            result[key] = value

        self._presenter.on_repertoire_ready(Repertoire(data=result))
        self._presenter.on_labels_ready(RepertoireLabels(data=result))


class LoadRepertoireTaskFactory:
    _presenter: LoadRepertoireTaskPresenter
    _seed: str

    def get_instance(self) -> LoadRepertoireTask:
        return LoadRepertoireTask(self._presenter, self._seed)
