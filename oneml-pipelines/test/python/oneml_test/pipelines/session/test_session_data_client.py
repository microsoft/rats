import pytest

from oneml.pipelines.dag import (
    PipelineDataDependenciesClient,
    PipelineDataDependency,
    PipelineNode,
)
from oneml.pipelines.session import (
    PipelineDataClient,
    PipelineNodeDataClient,
    PipelineNodeDataClientFactory,
    PipelinePort,
    ReadProxyPipelineDataClient,
)
from oneml.pipelines.session._session_data_client import (
    PipelineNodeInputDataClient,
    PipelineNodeInputDataClientFactory,
)


def test_imports() -> None:
    assert 1 == 1


class TestPipelineDataClient:

    _client: PipelineDataClient

    def setup_method(self) -> None:
        self._client = PipelineDataClient()

    def test_basics(self) -> None:
        self._client.publish_data(
            node=PipelineNode("step-1"),
            port=PipelinePort[str]("port-1"),
            data="some-data",
        )

        assert (
            self._client.get_data(
                node=PipelineNode("step-1"),
                port=PipelinePort[str]("port-1"),
            )
            == "some-data"
        )

    def test_validation(self) -> None:
        self._client.publish_data(
            node=PipelineNode("step-1"),
            port=PipelinePort[str]("port-1"),
            data="some-data",
        )

        with pytest.raises(RuntimeError):
            # We can't publish the same key twice
            self._client.publish_data(
                node=PipelineNode("step-1"),
                port=PipelinePort[str]("port-1"),
                data="some-other-data",
            )

        with pytest.raises(RuntimeError):
            # Try to load data that doesn't exist
            self._client.get_data(
                node=PipelineNode("step-2"),
                port=PipelinePort[str]("port-1"),
            )


class TestPipelineNodeDataClient:

    _node: PipelineNode
    _data_client: PipelineDataClient
    _client: PipelineNodeDataClient

    def setup_method(self) -> None:
        self._node = PipelineNode("step-1")
        self._data_client = PipelineDataClient()
        self._client = PipelineNodeDataClient(
            pipeline_data_client=self._data_client,
            node=self._node,
        )

    def test_basics(self) -> None:
        self._client.publish_data(
            port=PipelinePort[str]("port-1"),
            data="some-data",
        )

        assert (
            self._client.get_data(
                port=PipelinePort[str]("port-1"),
            )
            == "some-data"
        )

        assert (
            self._data_client.get_data(
                node=PipelineNode("step-1"),
                port=PipelinePort[str]("port-1"),
            )
            == "some-data"
        )


class TestReadProxyPipelineDataClient:

    _primary_data_client: PipelineDataClient
    _proxy_data_client: PipelineDataClient
    _client: ReadProxyPipelineDataClient

    def setup_method(self) -> None:
        self._primary_data_client = PipelineDataClient()
        self._proxy_data_client = PipelineDataClient()
        self._client = ReadProxyPipelineDataClient(
            primary_client=self._primary_data_client,
            proxy_client=self._proxy_data_client,
            proxied_nodes=tuple(
                [
                    PipelineNode("proxied-step-1"),
                ]
            ),
        )

    def test_basics(self) -> None:
        # you can publish data normally
        self._client.publish_data(
            node=PipelineNode("step-1"),
            port=PipelinePort[str]("port-1"),
            data="some-data",
        )
        # and you can retrieve data normally
        assert (
            self._client.get_data(
                node=PipelineNode("step-1"),
                port=PipelinePort[str]("port-1"),
            )
            == "some-data"
        )

    def test_proxy_reads(self) -> None:
        self._primary_data_client.publish_data(
            node=PipelineNode("step-1"),
            port=PipelinePort[str]("port-1"),
            data="primary-data",
        )
        self._proxy_data_client.publish_data(
            node=PipelineNode("step-1"),
            port=PipelinePort[str]("port-1"),
            data="proxied-data",
        )

        self._primary_data_client.publish_data(
            node=PipelineNode("proxied-step-1"),
            port=PipelinePort[str]("port-1"),
            data="primary-data",
        )
        self._proxy_data_client.publish_data(
            node=PipelineNode("proxied-step-1"),
            port=PipelinePort[str]("port-1"),
            data="proxied-data",
        )

        # This data should come from the primary client
        assert (
            self._client.get_data(
                node=PipelineNode("step-1"),
                port=PipelinePort[str]("port-1"),
            )
            == "primary-data"
        )

        # This data should come from the proxy client
        assert (
            self._client.get_data(
                node=PipelineNode("proxied-step-1"),
                port=PipelinePort[str]("port-1"),
            )
            == "proxied-data"
        )

    def test_we_cannot_publish_to_proxy_nodes(self) -> None:
        self._client.publish_data(
            node=PipelineNode("step-1"),
            port=PipelinePort[str]("port-1"),
            data="some-data",
        )

        with pytest.raises(RuntimeError):
            self._client.publish_data(
                node=PipelineNode("proxied-step-1"),
                port=PipelinePort[str]("port-2"),
                data="some-data",
            )


class TestPipelineNodeInputDataClient:

    _data_client: PipelineDataClient
    _client: PipelineNodeInputDataClient

    def setup_method(self) -> None:
        self._data_client = PipelineDataClient()
        self._client = PipelineNodeInputDataClient(
            data_client=self._data_client,
            data_mapping={
                PipelinePort("input-port-1"): (PipelineNode("step-1"), PipelinePort("port-1")),
            },
        )

    def test_basics(self) -> None:
        self._data_client.publish_data(
            node=PipelineNode("step-1"),
            port=PipelinePort[str]("port-1"),
            data="some-data",
        )

        assert self._client.get_data(PipelinePort("input-port-1")) == "some-data"


class TestFactories:
    def test_basics(self) -> None:
        node_1 = PipelineNode("step-1")
        node_2 = PipelineNode("step-2")
        data_client = PipelineDataClient()
        data_dependencies_client = PipelineDataDependenciesClient()
        data_dependencies_client.register_data_dependencies(
            node_2,
            (
                PipelineDataDependency(
                    node=node_1,
                    output_port=PipelinePort("step-1"),
                    input_port=PipelinePort("input-step-1"),
                ),
            ),
        )

        node_data_client_factory = PipelineNodeDataClientFactory(pipeline_data_client=data_client)
        node_data_client_instance = node_data_client_factory.get_instance(node_1)
        assert isinstance(node_data_client_instance, PipelineNodeDataClient)

        node_input_data_client_factory = PipelineNodeInputDataClientFactory(
            data_dependencies_client=data_dependencies_client,
            data_client=data_client,
        )
        node_input_data_client_instance = node_input_data_client_factory.get_instance(node_2)
        assert isinstance(node_input_data_client_instance, PipelineNodeInputDataClient)
