from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, Protocol, TypedDict, TypeVar

from furl import furl

from rats.io import IWriteData, RWDataUri
from rats.pipelines.session import RatsSessionContexts
from rats.processors._legacy_subpackages.ux import UPipeline, UPipelineBuilder
from rats.services import IGetContexts, IProvideServices, ServiceId

from .type_rw_mappers import IGetWriteServicesForType

DataType = TypeVar("DataType")


class WriteToUriProcessorOutput(TypedDict):
    uri: str


class WriteToUriProcessor(Generic[DataType]):
    _service_provider: IProvideServices
    _write_service_ids: Mapping[str, ServiceId[IWriteData[DataType]]]
    _uri: str

    def __init__(
        self,
        service_provider: IProvideServices,
        write_service_ids: Mapping[str, ServiceId[IWriteData[DataType]]],
        uri: str,
    ) -> None:
        self._service_provider = service_provider
        self._write_service_ids = write_service_ids
        self._uri = uri

    def process(self, data: DataType) -> WriteToUriProcessorOutput:
        scheme = furl(self._uri).scheme
        if scheme is None:
            raise ValueError(f"Invalid uri: {self._uri}")
        write_service_id = self._write_service_ids.get(scheme, None)
        if write_service_id is None:
            raise ValueError(f"Unsupported scheme: {scheme}")
        writer = self._service_provider.get_service(write_service_id)
        writer.write(RWDataUri(self._uri), data)
        return WriteToUriProcessorOutput(uri=self._uri)


class IWriteToUriPipelineBuilder(Protocol):
    @abstractmethod
    def build(self, data_type: type[DataType], uri: str | None = None) -> UPipeline: ...


class WriteToUriPipelineBuilder(IWriteToUriPipelineBuilder):
    _service_provider_service_id: ServiceId[IProvideServices]
    _get_write_services_for_type: IGetWriteServicesForType

    def __init__(
        self,
        service_provider_service_id: ServiceId[IProvideServices],
        get_write_services_for_type: IGetWriteServicesForType,
    ) -> None:
        self._service_provider_service_id = service_provider_service_id
        self._get_write_services_for_type = get_write_services_for_type

    def build(self, data_type: type[DataType], uri: str | None = None) -> UPipeline:
        write_service_ids = self._get_write_services_for_type.get_write_service_ids(data_type)
        task = UPipelineBuilder.task(
            processor_type=WriteToUriProcessor,
            config={
                k: v
                for k, v in dict(
                    write_service_ids=write_service_ids,
                    uri=uri,
                ).items()
                if v is not None
            },
            services=dict(service_provider=self._service_provider_service_id),
        )
        return task


class ComputeOutputUriFromRelativePathProcessor:
    def __init__(
        self,
        relative_path: str,
        output_base_uri: str,
    ):
        self._relative_path = relative_path
        self._output_base_uri = output_base_uri

    def process(self) -> WriteToUriProcessorOutput:
        uri = str(furl(self._output_base_uri) / self._relative_path)
        return WriteToUriProcessorOutput(uri=uri)


class IWriteToRelativePathPipelineBuilder(Protocol):
    @abstractmethod
    def build(self, data_type: type[DataType], relative_path: str) -> UPipeline: ...


class WriteToRelativePathPipelineBuilder(IWriteToRelativePathPipelineBuilder):
    _write_to_uri_pipeline_builder: IWriteToUriPipelineBuilder

    def __init__(
        self,
        write_to_uri_pipeline_builder: IWriteToUriPipelineBuilder,
    ) -> None:
        self._write_to_uri_pipeline_builder = write_to_uri_pipeline_builder

    def build(self, data_type: type[DataType], relative_path: str) -> UPipeline:
        compute_uri = UPipelineBuilder.task(
            processor_type=ComputeOutputUriFromRelativePathProcessor,
            config=dict(relative_path=relative_path),
        )
        write = self._write_to_uri_pipeline_builder.build(data_type)
        pl = UPipelineBuilder.combine(
            [compute_uri, write],
            name="write_to_relative_path",
            dependencies=(compute_uri.outputs.uri >> write.inputs.uri,),
        )
        return pl


class ComputeNodeBasedOutputUriProcessor:
    def __init__(
        self,
        context_provider: IGetContexts,
        output_base_uri: str,
    ):
        self._context_provider = context_provider
        self._output_base_uri = output_base_uri

    def process(self) -> WriteToUriProcessorOutput:
        session_id = self._context_provider.get_context(RatsSessionContexts.PIPELINE).id
        node_id = self._context_provider.get_context(RatsSessionContexts.NODE).key
        uri = str(furl(self._output_base_uri) / session_id / node_id)
        return WriteToUriProcessorOutput(uri=uri)


class IWriteToNodeBasedUriPipelineBuilder(Protocol):
    @abstractmethod
    def build(self, data_type: type[DataType]) -> UPipeline: ...


T_IGetContexts = TypeVar("T_IGetContexts", bound=IGetContexts)


class WriteToNodeBasedUriPipelineBuilder(IWriteToNodeBasedUriPipelineBuilder):
    _write_to_uri_pipeline_builder: IWriteToUriPipelineBuilder
    _context_provider_service_id: ServiceId[Any]

    def __init__(
        self,
        write_to_uri_pipeline_builder: IWriteToUriPipelineBuilder,
        context_provider_service_id: ServiceId[T_IGetContexts],
    ) -> None:
        self._write_to_uri_pipeline_builder = write_to_uri_pipeline_builder
        self._context_provider_service_id = context_provider_service_id

    def build(self, data_type: type[DataType]) -> UPipeline:
        compute_uri = UPipelineBuilder.task(
            processor_type=ComputeNodeBasedOutputUriProcessor,
            services=dict(context_provider=self._context_provider_service_id),
        )
        write = self._write_to_uri_pipeline_builder.build(data_type)
        pl = UPipelineBuilder.combine(
            [compute_uri, write],
            name="write_to_node_based_uri",
            dependencies=(compute_uri.outputs.uri >> write.inputs.uri,),
        )
        return pl
