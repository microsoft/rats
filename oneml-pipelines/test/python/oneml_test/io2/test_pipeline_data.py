from typing import NamedTuple

import pytest

from oneml.io2 import DuplicatePipelineDataError, PipelineData, PipelineDataNotFoundError
from oneml.pipelines.dag import PipelineNode, PipelinePort
from oneml.pipelines.session import PipelineSession


class ExampleData(NamedTuple):
    foo: str
    bar: int


class TestPipelineData:
    def setup_method(self) -> None:
        self._example_node = PipelineNode("a")
        self._example_port = PipelinePort[ExampleData]("out")
        self._missing_port = PipelinePort[ExampleData]("missing")
        self._example_data = ExampleData(foo="abc", bar=123)

        self._client = PipelineData(
            namespace=lambda: PipelineSession("fake"),
            node_ctx=lambda: self._example_node,
        )

    def test_basics(self) -> None:
        """
        In its most basic form, the PipelineData class gives a simple API to publish and load data.

        We expect the same data to come out as we put in. Data in a pipeline is tied to
        """
        self._client.publish(self._example_node, self._example_port, self._example_data)
        assert self._client.load(self._example_node, self._example_port) == self._example_data

    def test_duplicate_data_error(self) -> None:
        self._client.publish(self._example_node, self._example_port, self._example_data)

        with pytest.raises(DuplicatePipelineDataError):
            self._client.publish(self._example_node, self._example_port, self._example_data)

    def test_data_not_found_error(self) -> None:
        with pytest.raises(PipelineDataNotFoundError):
            self._client.load(self._example_node, self._example_port)

        self._client.publish(self._example_node, self._example_port, self._example_data)

        with pytest.raises(PipelineDataNotFoundError):
            self._client.load(self._example_node, self._missing_port)

    def test_contextual_node_api(self) -> None:
        """
        Our PipelineData class also implements the IManageNodeData interface.

        This interface is useful for interacting with the data of a single node, so we can shorten
        the API to eliminate the need for the user to specify the node every time.
        """
        self._client.publish_port(self._example_port, self._example_data)
        assert self._client.load_port(self._example_port) == self._example_data
