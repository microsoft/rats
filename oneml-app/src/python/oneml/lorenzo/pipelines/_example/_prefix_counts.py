from functools import lru_cache
from typing import Dict, Tuple

from dataclasses import dataclass

from oneml.lorenzo.pipelines import PipelineStep, PipelineDataWriter
from ._sample import ExampleSamplesCollection


@dataclass(frozen=True)
class SamplePrefixCountStepConfig:
    prefix_length: int


class SamplePrefixCountStep(PipelineStep):

    _storage: PipelineDataWriter
    _prefix_length: int
    _samples: ExampleSamplesCollection

    def __init__(self, storage: PipelineDataWriter, prefix_length: int, samples: ExampleSamplesCollection):
        self._storage = storage
        self._prefix_length = prefix_length
        self._samples = samples

    def execute(self) -> None:
        counts: Dict[str, int] = {}
        for name in self._samples.get_names():
            prefix = name[:self._prefix_length]
            counts[prefix] = counts.get(prefix, 0) + 1

        tup = ((k, v) for k, v in counts.items())
        result = SamplePrefixCounts(data=tuple(tup))
        self._storage.save(SamplePrefixCounts, result)


@dataclass(frozen=True)
class SampleLetterCountStepConfig:
    prefix_length: int
    letters_to_count: Tuple[str, ...]


class SampleLetterCountStep(PipelineStep):

    _storage: PipelineDataWriter
    _prefix_length: int
    _letters_to_count: Tuple[str, ...]
    _samples: ExampleSamplesCollection

    def __init__(
            self,
            storage: PipelineDataWriter,
            prefix_length: int,
            letters_to_count: Tuple[str, ...],
            samples: ExampleSamplesCollection):
        self._storage = storage
        self._prefix_length = prefix_length
        self._letters_to_count = letters_to_count
        self._samples = samples

    def execute(self) -> None:
        counts: Dict[str, int] = {}
        for name in self._samples.get_names():
            prefix = name[:self._prefix_length].lower()
            for letter in prefix:
                if letter in self._letters_to_count:
                    counts[letter] = counts.get(letter, 0) + 1

        tup = ((k, v) for k, v in counts.items())
        result = SamplePrefixCounts(data=tuple(tup))
        self._storage.save(SamplePrefixCounts, result)


class SamplePrefixCounts:
    _data: Tuple[Tuple[str, int], ...]

    def __init__(self, data: Tuple[Tuple[str, int], ...]):
        self._data = data

    def top(self, num: int) -> Tuple[Tuple[str, int], ...]:
        return self._sorted()[:num]

    @lru_cache()
    def _sorted(self) -> Tuple[Tuple[str, int], ...]:
        return tuple(sorted(self._data, key=lambda item: item[1], reverse=True))


# If we have a config object for a given iteration, how do we modify it slightly for iteration +1?
# maybe Jabran is a good user to test some of this on
# 
