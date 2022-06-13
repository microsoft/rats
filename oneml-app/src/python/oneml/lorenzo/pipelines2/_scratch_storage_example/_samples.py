import random
import string
from dataclasses import dataclass
from typing import Any, Dict

from oneml.lorenzo.pipelines2 import IPipelineNode, IProvidePipelineNodes

from ._pipeline_output import PipelineOutput


@dataclass(frozen=True)
class Samples:
    data: Dict[Any, Any]
    foo_column: str
    bar_column: str


class LoadSamplesNode(IPipelineNode):

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

        self._output_client.add(Samples, Samples(data=result, bar_column="123", foo_column="456"))


class LoadSamplesNodeProvider(IProvidePipelineNodes[LoadSamplesNode]):
    _output_client: PipelineOutput
    _seed: str

    def __init__(self, output_client: PipelineOutput):
        self._output_client = output_client
        self._seed = "abc"

    def get_pipeline_node(self) -> LoadSamplesNode:
        return LoadSamplesNode(self._output_client, self._seed)
