import random
import string
from typing import Dict

from oneml.lorenzo.pipelines2 import IPipelineNode, IProvidePipelineNodes

from ._pipeline_output import PipelineOutput


class Mira:
    _data: Dict[str, str]

    def __init__(self, data: Dict[str, str]):
        self._data = data

    def count(self) -> int:
        return len(self._data.keys())


class LoadMiraNode(IPipelineNode):

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

        self._output_client.add(Mira, Mira(data=result))


class LoadMiraNodeProvider(IProvidePipelineNodes[LoadMiraNode]):
    _output_client: PipelineOutput
    _seed: str

    def __init__(self, output_client: PipelineOutput):
        self._output_client = output_client
        self._seed = "abc"

    def get_pipeline_node(self) -> LoadMiraNode:
        return LoadMiraNode(self._output_client, self._seed)
