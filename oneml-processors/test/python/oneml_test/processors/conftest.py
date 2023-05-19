import logging

import pytest
from hydra.core.config_store import ConfigStore

from oneml.pipelines._client import SimplePipelineFactory
from oneml.pipelines.building import DefaultDataTypeMapper, IPipelineBuilderFactory
from oneml.pipelines.context._client import ContextClient, IManageExecutionContexts
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._local_data_client import IOManagerIds, LocalDataClient
from oneml.pipelines.data._serialization import DillSerializer, SerializationClient, SerializerIds
from oneml.pipelines.session import IOManagerRegistry, PipelineSessionClient, ServicesRegistry
from oneml.pipelines.session._session_client import PipelineSessionContext
from oneml.processors import PipelineRunnerFactory
from oneml.processors.dag import PipelineSessionProvider
from oneml.processors.schemas import register_configs
from oneml.processors.ux import Pipeline, register_resolvers

from .mock_data import DataTypeIds, Model, ModelSerializer

logger = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def services_registry() -> ServicesRegistry:
    return ServicesRegistry()


@pytest.fixture(scope="package")
def iomanager_registry(local_pipeline_data_client: LocalDataClient) -> IOManagerRegistry:
    registry = IOManagerRegistry()
    registry.register(IOManagerIds.LOCAL, local_pipeline_data_client)
    return registry


@pytest.fixture(scope="package")
def serialization_client() -> SerializationClient:
    serializer = SerializationClient()
    serializer.register(type_id=DataTypeIds.MODEL, serializer=ModelSerializer())
    serializer.register(type_id=SerializerIds.DILL, serializer=DillSerializer())
    return serializer


@pytest.fixture(scope="package")
def type_mapping() -> MappedPipelineDataClient:
    return MappedPipelineDataClient()


@pytest.fixture(scope="package")
def default_datatype_mapper() -> DefaultDataTypeMapper:
    mapper = DefaultDataTypeMapper()
    mapper.register(type_=Model, type_id=DataTypeIds.MODEL)
    mapper.register(type_=Pipeline, type_id=SerializerIds.DILL)
    return mapper


@pytest.fixture(scope="package")
def local_pipeline_data_client(
    serialization_client: SerializationClient,
    type_mapping: MappedPipelineDataClient,
    pipeline_session_context: PipelineSessionContext,
) -> LocalDataClient:
    return LocalDataClient(
        serializer=serialization_client,
        type_mapping=type_mapping,
        session_context=pipeline_session_context,
    )


@pytest.fixture(scope="package")
def pipeline_session_context() -> PipelineSessionContext:
    return ContextClient[PipelineSessionClient]()


@pytest.fixture(scope="package")
def node_context() -> IManageExecutionContexts[PipelineNode]:
    return ContextClient()


@pytest.fixture(scope="package")
def pipeline_builder_factory(
    services_registry: ServicesRegistry,
    iomanager_registry: IOManagerRegistry,
    default_datatype_mapper: DefaultDataTypeMapper,
    pipeline_session_context: PipelineSessionContext,
    node_context: IManageExecutionContexts[PipelineNode],
) -> IPipelineBuilderFactory:
    return SimplePipelineFactory(
        services=services_registry,
        iomanagers=iomanager_registry,
        default_datatype_mapper=default_datatype_mapper,
        session_context=pipeline_session_context,
        node_context=node_context,
    )


@pytest.fixture(scope="package")
def pipeline_session_provider(
    pipeline_builder_factory: IPipelineBuilderFactory,
    pipeline_session_context: PipelineSessionContext,
) -> PipelineSessionProvider:
    return PipelineSessionProvider(
        builder_factory=pipeline_builder_factory,
        session_context=pipeline_session_context,
    )


@pytest.fixture(scope="package")
def pipeline_runner_factory(
    pipeline_session_provider: PipelineSessionProvider,
) -> PipelineRunnerFactory:
    return PipelineRunnerFactory(pipeline_session_provider=pipeline_session_provider)


@pytest.fixture(scope="package")
def register_resolvers_and_configs() -> None:
    register_configs(ConfigStore())
    register_resolvers()
