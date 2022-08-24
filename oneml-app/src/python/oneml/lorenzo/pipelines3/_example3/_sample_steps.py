import logging
from typing import Tuple, Dict

from oneml.pipelines.building import IPipelineSessionExecutable
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.dag._data_dependencies_client import PipelineDataDependenciesClient, PipelinePortDataType
from oneml.pipelines.session import (
    IExecutable,
    PipelinePort,
    PipelineNodeDataClient,
    PipelineSessionClient, PipelineDataClient,
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
            PipelinePort[ExampleSamples]("example-samples"),
            ExampleSamples(tuple(["one", "two", "three"])),
        )


class ProduceExampleSamplesRunner(IPipelineSessionExecutable):
    _node: PipelineNode

    def __init__(self, node: PipelineNode) -> None:
        self._node = node

    def execute(self, session_client: PipelineSessionClient) -> None:
        logging.warning("EXECUTING ProduceExampleSamplesRunner!")
        data_factory = session_client.node_data_client_factory()
        step_data = data_factory.get_instance(self._node)
        step = ProduceExampleSamples(node_data_client=step_data)
        step.execute()


class LogExampleSamples(IExecutable):

    _data: ExampleSamples

    def __init__(self, data: ExampleSamples):
        self._data = data

    def execute(self) -> None:
        logger.warning(f"Number of samples: {len(self._data.samples())}")
        for sample in self._data.samples():
            logger.warning(f"Sample: {sample}")


class LogExampleSamplesRunner(IPipelineSessionExecutable):
    _input_node: PipelineNode

    def __init__(self, input_node: PipelineNode) -> None:
        self._input_node = input_node

    def execute(self, session_client: PipelineSessionClient) -> None:
        logging.warning("EXECUTING LogExampleSamplesRunner!")
        data_factory = session_client.node_data_client_factory()
        data_node = PipelinePort[ExampleSamples]("example-samples")

        input_data = data_factory.get_instance(self._input_node).get_data(data_node)

        step = LogExampleSamples(data=input_data)
        step.execute()


class LogExampleSamplesRunner2(IPipelineSessionExecutable):
    _node: PipelineNode

    def __init__(self, node: PipelineNode) -> None:
        self._node = node

    def execute(self, session_client: PipelineSessionClient) -> None:
        logging.warning("EXECUTING LogExampleSamplesRunner!")
        input_data_factory = session_client.node_input_data_client_factory()
        node_input_data = input_data_factory.get_instance(self._node)
        # A:example-samples -> B:input-samples
        step = LogExampleSamples(
            data=node_input_data.get_data(
                PipelinePort[ExampleSamples]("input-samples")))
        step.execute()
