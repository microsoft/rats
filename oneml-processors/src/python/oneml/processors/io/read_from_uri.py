from abc import abstractmethod
from collections.abc import Mapping
from typing import Generic, Protocol, TypeVar

from furl import furl
from typing_extensions import TypedDict

from oneml.io import IReadData, RWDataUri
from oneml.services import IProvideServices, ServiceId

from ..ux import UPipeline, UPipelineBuilder
from .type_rw_mappers import IGetReadServicesForType

DataType = TypeVar("DataType")


class ReadFromUriProcessorOutput(TypedDict):
    data: DataType


class ReadFromUriProcessor(Generic[DataType]):
    _service_provider: IProvideServices
    _read_service_ids: Mapping[str, ServiceId[IReadData[DataType]]]
    _uri: RWDataUri

    def __init__(
        self,
        service_provider: IProvideServices,
        read_service_ids: Mapping[str, ServiceId[IReadData[DataType]]],
        uri: str,
    ) -> None:
        self._service_provider = service_provider
        self._read_service_ids = read_service_ids
        self._uri = RWDataUri(uri)

    def process(self) -> ReadFromUriProcessorOutput:
        scheme = furl(self._uri.uri).scheme
        read_service_id = self._read_service_ids.get(scheme, None)
        if read_service_id is None:
            raise ValueError(f"Unsupported scheme: {scheme}")
        reader = self._service_provider.get_service(read_service_id)

        return dict(data=reader.read(self._uri))


class IReadFromUrlPipelineBuilder(Protocol):
    @abstractmethod
    def build(self, data_type: type[DataType], uri: str | None = None) -> UPipeline:
        ...


class ReadFromUrlPipelineBuilder(IReadFromUrlPipelineBuilder):
    _service_provider_service_id: ServiceId[IProvideServices]
    _get_read_services_for_type: IGetReadServicesForType

    def __init__(
        self,
        service_provider_service_id: ServiceId[IProvideServices],
        get_read_services_for_type: IGetReadServicesForType,
    ) -> None:
        self._service_provider_service_id = service_provider_service_id
        self._get_read_services_for_type = get_read_services_for_type

    def build(self, data_type: type[DataType], uri: str | None = None) -> UPipeline:
        read_service_ids = self._get_read_services_for_type.get_read_service_ids(data_type)
        config = {
            k: v
            for k, v in dict(
                read_service_ids=read_service_ids,
                uri=uri,
            ).items()
            if v is not None
        }
        task = UPipelineBuilder.task(
            processor_type=ReadFromUriProcessor,
            config=config,
            services=dict(service_provider=self._service_provider_service_id),
        )
        return task
