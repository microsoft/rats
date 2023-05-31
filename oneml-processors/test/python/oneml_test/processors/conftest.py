import logging
from pathlib import Path
from typing import Any

import pytest
from hydra.core.config_store import ConfigStore

from oneml.pipelines._client import SimplePipelineFactory
from oneml.pipelines.building import (
    DefaultDataTypeIOManagerMapper,
    DefaultDataTypeMapper,
    IPipelineBuilderFactory,
)
from oneml.pipelines.context._client import ContextClient, IManageExecutionContexts
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._local_data_client import IOManagerIds, LocalDataClient
from oneml.pipelines.data._serialization import DillSerializer, SerializationClient, SerializerIds
from oneml.pipelines.session import IOManagerRegistry, PipelineSessionClient, ServicesRegistry
from oneml.pipelines.session._session_client import PipelineSessionContext
from oneml.processors import PersistFittedEvalPipeline, PipelineRunnerFactory
from oneml.processors.dag import PipelineSessionProvider
from oneml.processors.schemas import register_configs
from oneml.processors.services import GetActiveNodeKey, OnemlProcessorServices
from oneml.processors.ux import Pipeline, register_resolvers

from .mock_data import Array, ArraySerializer, DataTypeIds, Model, ModelSerializer

logger = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def services_registry(
    pipeline_session_context: PipelineSessionContext, iomanager_registry: IOManagerRegistry
) -> ServicesRegistry:
    services = ServicesRegistry()
    services.register_service(
        OnemlProcessorServices.GetActiveNodeKey, GetActiveNodeKey(pipeline_session_context)
    )
    services.register_service(OnemlProcessorServices.IOManagerRegistry, lambda: iomanager_registry)
    services.register_service(
        OnemlProcessorServices.SessionId,
        lambda: pipeline_session_context.get_context().session_id(),
    )
    return services


@pytest.fixture(scope="package")
def iomanager_registry(local_pipeline_data_client: LocalDataClient) -> IOManagerRegistry:
    from oneml.pipelines.session import IOManagerId

    registry = IOManagerRegistry()
    registry.register(IOManagerIds.LOCAL, local_pipeline_data_client)
    return registry


@pytest.fixture(scope="package")
def serialization_client() -> SerializationClient:
    serializer = SerializationClient()
    serializer.register(type_id=DataTypeIds.ARRAY, serializer=ArraySerializer())
    serializer.register(type_id=DataTypeIds.MODEL, serializer=ModelSerializer())
    serializer.register(type_id=SerializerIds.DILL, serializer=DillSerializer())
    return serializer


@pytest.fixture(scope="package")
def type_mapping() -> MappedPipelineDataClient:
    return MappedPipelineDataClient()


@pytest.fixture(scope="package")
def default_datatype_mapper() -> DefaultDataTypeMapper:
    mapper = DefaultDataTypeMapper()
    mapper.register(type_=Array, type_id=DataTypeIds.ARRAY)
    mapper.register(type_=Model, type_id=DataTypeIds.MODEL)
    mapper.register(type_=Pipeline, type_id=SerializerIds.DILL)
    return mapper


@pytest.fixture(scope="package")
def tmp_path(tmp_path_factory: Any) -> Path:
    return Path(tmp_path_factory.mktemp(".tmp"))


@pytest.fixture(scope="package")
def local_pipeline_data_client(
    tmp_path: Path,
    serialization_client: SerializationClient,
    type_mapping: MappedPipelineDataClient,
    pipeline_session_context: PipelineSessionContext,
) -> LocalDataClient:
    return LocalDataClient(
        tmp_path=tmp_path,
        serializer=serialization_client,
        type_mapping=type_mapping,
        session_context=pipeline_session_context,
    )


@pytest.fixture(scope="package")
def pipeline_session_context() -> IManageExecutionContexts[PipelineSessionClient]:
    return ContextClient()



@pytest.fixture(scope="package")
def pipeline_node_context() -> IManageExecutionContexts[PipelineNode]:
    return ContextClient()


@pytest.fixture(scope="package")
def pipeline_builder_factory(
    services_registry: ServicesRegistry,
    iomanager_registry: IOManagerRegistry,
    default_datatype_mapper: DefaultDataTypeMapper,
    pipeline_session_context: IManageExecutionContexts[PipelineSessionClient],
    pipeline_node_context: IManageExecutionContexts[PipelineNode],
) -> SimplePipelineFactory:
    return SimplePipelineFactory(
        services=services_registry,
        iomanagers=iomanager_registry,
        default_datatype_mapper=default_datatype_mapper,
        session_context=pipeline_session_context,
        node_context=pipeline_node_context,
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


@pytest.fixture(scope="package")
def default_datatype_iomanager_mapper() -> DefaultDataTypeIOManagerMapper:
    from oneml.pipelines.session import IOManagerId

    default_datatype_iomanager_mapper = DefaultDataTypeIOManagerMapper()
    default_datatype_iomanager_mapper.register(type_=Model, iomanager_id=IOManagerId("local"))
    default_datatype_iomanager_mapper.register(type_=Array, iomanager_id=IOManagerId("local"))
    return default_datatype_iomanager_mapper


@pytest.fixture(scope="package")
def persist_fitted_eval_pipeline(
    default_datatype_iomanager_mapper: DefaultDataTypeIOManagerMapper,
) -> PersistFittedEvalPipeline:
    return PersistFittedEvalPipeline(type_to_io_manager_mapping=default_datatype_iomanager_mapper)
