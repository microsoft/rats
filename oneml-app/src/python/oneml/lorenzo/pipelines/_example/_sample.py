from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ExampleSample:
    name: str


class ExampleSamplesCollection:
    _samples: Tuple[ExampleSample, ...]

    def __init__(self, samples: Tuple[ExampleSample, ...]):
        self._samples = samples

    def get_names(self) -> Tuple[str, ...]:
        names = [sample.name for sample in self._samples]
        return tuple(names)
