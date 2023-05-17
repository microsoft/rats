import pytest

from oneml.pipelines.dag import (
    PipelineDataDependenciesClient,
    PipelineDataDependency,
    PipelineNode,
)
from oneml.pipelines.data._memory_data_client import InMemoryDataClient
from oneml.pipelines.session import (
    IOManagerClient,
    IOManagerRegistry,
    PipelineNodeDataClient,
    PipelineNodeDataClientFactory,
    PipelineNodeInputDataClient,
    PipelineNodeInputDataClientFactory,
    PipelinePort,
    ReadProxyPipelineDataClient,
)


def test_imports() -> None:
    assert 1 == 1


class TestInMemoryDataClient:
    _client: InMemoryDataClient

    def setup_method(self) -> None:
        self._client = InMemoryDataClient()

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
    _iomanager_client: IOManagerClient
    _client: PipelineNodeDataClient

    def setup_method(self) -> None:
        self._node = PipelineNode("step-1")
        self._iomanager_client = IOManagerClient(IOManagerRegistry(), InMemoryDataClient())
        self._client = PipelineNodeDataClient(
            iomanager_client=self._iomanager_client,
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

        node = PipelineNode("step-1")
        port = PipelinePort[str]("port-1")
        assert (
            self._iomanager_client.get_dataclient(node, port).get_data(node, port) == "some-data"
        )


class TestReadProxyInMemoryDataClient:
    _primary_data_client: InMemoryDataClient
    _proxy_data_client: InMemoryDataClient
    _client: ReadProxyPipelineDataClient

    def setup_method(self) -> None:
        self._primary_data_client = InMemoryDataClient()
        self._proxy_data_client = InMemoryDataClient()
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
    _iomanager_client: IOManagerClient
    _client: PipelineNodeInputDataClient

    def setup_method(self) -> None:
        self._iomanager_client = IOManagerClient(IOManagerRegistry(), InMemoryDataClient())
        self._client = PipelineNodeInputDataClient(
            iomanager_client=self._iomanager_client,
            data_mapping={
                PipelinePort("input-port-1"): (PipelineNode("step-1"), PipelinePort("port-1")),
            },
        )

    def test_basics(self) -> None:
        node = PipelineNode("step-1")
        port = PipelinePort[str]("port-1")
        self._iomanager_client.get_dataclient(node, port).publish_data(
            node, port, data="some-data"
        )

        assert self._client.get_data(PipelinePort("input-port-1")) == "some-data"


class TestFactories:
    def test_basics(self) -> None:
        node_1 = PipelineNode("step-1")
        node_2 = PipelineNode("step-2")
        iomanager_registry = IOManagerRegistry()
        default_data_client = InMemoryDataClient()
        iomanager_client = IOManagerClient(iomanager_registry, default_data_client)
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

        node_data_client_factory = PipelineNodeDataClientFactory(iomanager_client=iomanager_client)
        node_data_client_instance = node_data_client_factory.get_instance(node_1)
        assert isinstance(node_data_client_instance, PipelineNodeDataClient)

        node_input_data_client_factory = PipelineNodeInputDataClientFactory(
            data_dependencies_client=data_dependencies_client,
            iomanager_client=iomanager_client,
        )
        node_input_data_client_instance = node_input_data_client_factory.get_instance(node_2)
        assert isinstance(node_input_data_client_instance, PipelineNodeInputDataClient)
