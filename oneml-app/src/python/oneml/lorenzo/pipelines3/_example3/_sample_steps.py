import logging
from typing import Tuple

from oneml.pipelines.building import IPipelineSessionExecutable
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.session import (
    IExecutable,
    PipelineNodeDataClient,
    PipelineDataNode,
    PipelineNodeDataClientFactory,
    PipelineSessionClient,
)

logger = logging.getLogger(__name__)


class ExampleSamples:
    _samples: Tuple[str, ...]

    def __init__(self, samples: Tuple[str, ...]):
        self._samples = samples

    def samples(self) -> Tuple[str, ...]:
        return self._samples


class ProduceExampleSamples(IExecutable):
    _node_data_client: PipelineNodeDataClient

    def __init__(self, node_data_client: PipelineNodeDataClient):
        self._node_data_client = node_data_client

    def execute(self) -> None:
        logger.info(f"Executing! {self}")
        self._node_data_client.publish_data(
            PipelineDataNode[ExampleSamples]("example-samples"),
            ExampleSamples(tuple(["one", "two", "three"])),
        )


class ProduceExampleSamplesFactory:

    _node_data_client_factory: PipelineNodeDataClientFactory

    def __init__(self, node_data_client_factory: PipelineNodeDataClientFactory) -> None:
        self._node_data_client_factory = node_data_client_factory

    def get_instance(self, node: PipelineNode) -> ProduceExampleSamples:
        return ProduceExampleSamples(
            node_data_client=self._node_data_client_factory.get_instance(node)
        )


class FooBarExecutable(IPipelineSessionExecutable):
    def execute(self, session_client: PipelineSessionClient) -> None:
        logging.warning("EXECUTING FOOBAREXECUTABLE!")
