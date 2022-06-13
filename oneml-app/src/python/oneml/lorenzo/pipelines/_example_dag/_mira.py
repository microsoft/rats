import random
import string
from abc import ABC, abstractmethod
from typing import Dict


class Mira:
    _data: Dict[str, str]

    def __init__(self, data: Dict[str, str]):
        self._data = data

    def count(self) -> int:
        return len(self._data.keys())


class LoadMiraTaskPresenter(ABC):

    @abstractmethod
    def on_mira_ready(self, miras: Mira) -> None:
        pass


class LoadMiraTask:

    _presenter: LoadMiraTaskPresenter
    _seed: str

    def __init__(self, presenter: LoadMiraTaskPresenter, seed: str):
        self._presenter = presenter
        self._seed = seed

    def execute(self) -> None:
        result = {}
        random.seed(self._seed)
        num_miras = random.randint(5, 30)
        letters = string.ascii_uppercase

        for x in range(num_miras):
            key = ''.join(random.choice(letters) for _ in range(10))
            value = ''.join(random.choice(letters) for _ in range(10))
            result[key] = value

        self._presenter.on_mira_ready(Mira(data=result))


class LoadMiraTaskFactory:
    _presenter: LoadMiraTaskPresenter
    _seed: str

    def get_instance(self) -> LoadMiraTask:
        return LoadMiraTask(self._presenter, self._seed)
