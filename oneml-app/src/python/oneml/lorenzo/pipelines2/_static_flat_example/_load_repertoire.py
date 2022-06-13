import random
import string
from abc import ABC, abstractmethod
from typing import Dict

from oneml.lorenzo.pipelines2 import IPipelineNode, IProvidePipelineNodes

from ._pipeline_output import PipelineOutput


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


class LoadRepertoireNode(IPipelineNode):

    _output_client: PipelineOutput
    _seed: str

    def __init__(self, output_client: PipelineOutput, seed: str):
        self._output_client = output_client
        self._seed = seed

    def execute_node(self) -> None:
        result = {}
        random.seed(self._seed)
        num_repertoires = random.randint(5, 30)
        letters = string.ascii_uppercase

        for x in range(num_repertoires):
            key = ''.join(random.choice(letters) for _ in range(10))
            value = ''.join(random.choice(letters) for _ in range(10))
            result[key] = value

        self._output_client.add(Repertoire, Repertoire(data=result))
        self._output_client.add(RepertoireLabels, RepertoireLabels(data=result))


class LoadRepertoireNodeProvider(IProvidePipelineNodes[LoadRepertoireNode]):
    _output_client: PipelineOutput
    _seed: str

    def __init__(self, output_client: PipelineOutput):
        self._output_client = output_client
        self._seed = "abc"

    def get_pipeline_node(self) -> LoadRepertoireNode:
        return LoadRepertoireNode(self._output_client, self._seed)
