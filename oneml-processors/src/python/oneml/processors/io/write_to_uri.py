from abc import abstractmethod
from typing import Any, Generic, Mapping, Protocol, TypeVar, TypedDict

from furl import furl

from oneml.io import IWriteData, RWDataUri
from oneml.pipelines.session import OnemlSessionContexts
from oneml.processors.ux import UPipeline, UPipelineBuilder
from oneml.services import IGetContexts, IProvideServices, ServiceId
from .type_rw_mappers import IGetWriteServicesForType

DataType = TypeVar("DataType")

WriteToUriProcessorOutput = TypedDict("WriteToUriProcessorOutput", {"uri": str})


class WriteToUriProcessorBase(Generic[DataType]):
    _service_provider: IProvideServices
    _write_service_ids: Mapping[str, ServiceId[IWriteData[DataType]]]
    _uri: RWDataUri

    def __init__(
        self,
        service_provider: IProvideServices,
        write_service_ids: Mapping[str, ServiceId[IWriteData[DataType]]],
        uri: RWDataUri,
    ) -> None:
        self._service_provider = service_provider
        self._write_service_ids = write_service_ids
        self._uri = uri

    def process(self, data: DataType) -> WriteToUriProcessorOutput:
        scheme = furl(self._uri.uri).scheme
        write_service_id = self._write_service_ids.get(scheme, None)
        if write_service_id is None:
            raise ValueError(f"Unsupported scheme: {scheme}")
        writer = self._service_provider.get_service(write_service_id)
        writer.write(self._uri, data)
        return WriteToUriProcessorOutput(uri=self._uri.uri)


class WriteToUriProcessor(WriteToUriProcessorBase[DataType]):
    pass


class IWriteToUriPipelineBuilder(Protocol):
    @abstractmethod
    def build(self, uri: str, data_type: type[DataType]) -> UPipeline:
        ...


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

    def build(self, uri: str, data_type: type[DataType]) -> UPipeline:
        write_service_ids = self._get_write_services_for_type.get_write_service_ids(data_type)
        task = UPipelineBuilder.task(
            processor_type=WriteToUriProcessor,
            config=dict(uri=RWDataUri(uri), write_service_ids=write_service_ids),
            services=dict(service_provider=self._service_provider_service_id),
        )
        return task


class WriteToNodeBasedUriProcessor(WriteToUriProcessorBase[DataType]):
    def __init__(
        self,
        service_provider: IProvideServices,
        context_provider: IGetContexts,
        write_service_ids: Mapping[str, ServiceId[IWriteData[DataType]]],
        output_base_uri: str,
    ) -> None:
        session_id = context_provider.get_context(OnemlSessionContexts.PIPELINE).id
        node_id = context_provider.get_context(OnemlSessionContexts.NODE).key
        uri = RWDataUri(str(furl(output_base_uri) / f"{session_id}/{node_id}"))
        super().__init__(
            service_provider=service_provider, write_service_ids=write_service_ids, uri=uri
        )


class IWriteToNodeBasedUriPipelineBuilder(Protocol):
    @abstractmethod
    def build(self, data_type: type[DataType], node_name: str) -> UPipeline:
        ...


T_IGetContexts = TypeVar("T_IGetContexts", bound=IGetContexts)


class WriteToNodeBasedUriPipelineBuilder(IWriteToNodeBasedUriPipelineBuilder):
    _service_provider_service_id: ServiceId[IProvideServices]
    _context_provider_service_id: ServiceId[Any]
    _get_write_services_for_type: IGetWriteServicesForType

    def __init__(
        self,
        service_provider_service_id: ServiceId[IProvideServices],
        context_provider_service_id: ServiceId[T_IGetContexts],
        get_write_services_for_type: IGetWriteServicesForType,
    ) -> None:
        self._service_provider_service_id = service_provider_service_id
        self._context_provider_service_id = context_provider_service_id
        self._get_write_services_for_type = get_write_services_for_type

    def build(self, data_type: type[DataType], node_name: str) -> UPipeline:
        write_service_ids = self._get_write_services_for_type.get_write_service_ids(data_type)
        task = UPipelineBuilder.task(
            name=node_name,
            processor_type=WriteToNodeBasedUriProcessor,
            config=dict(
                write_service_ids=write_service_ids,
            ),
            services=dict(
                service_provider=self._service_provider_service_id,
                context_provider=self._context_provider_service_id,
            ),
        )
        return task
