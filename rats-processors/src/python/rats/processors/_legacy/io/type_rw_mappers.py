from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from rats.io import IReadData, IWriteData
from rats.services import ServiceId

DataType = TypeVar("DataType")


class IRegisterReadServiceForType:
    @abstractmethod
    def register(
        self,
        scheme: str,
        type_filter: Callable[[type[DataType]], bool],
        service_id: ServiceId[IReadData[DataType]],
    ) -> None: ...


class IRegisterWriteServiceForType:
    @abstractmethod
    def register(
        self,
        scheme: str,
        type_filter: Callable[[type[DataType]], bool],
        service_id: ServiceId[IWriteData[DataType]],
    ) -> None: ...


class IGetReadServicesForType:
    @abstractmethod
    def get_read_service_ids(
        self, data_type: type[DataType]
    ) -> Mapping[str, ServiceId[IReadData[DataType]]]: ...


class IGetWriteServicesForType:
    @abstractmethod
    def get_write_service_ids(
        self, data_type: type[DataType]
    ) -> Mapping[str, ServiceId[IWriteData[DataType]]]: ...


class TypeToReadServiceMapper(IRegisterReadServiceForType, IGetReadServicesForType):
    _per_schema_filters: defaultdict[
        str, list[tuple[Callable[[type[Any]], bool], ServiceId[IReadData[Any]]]]
    ]

    def __init__(self) -> None:
        self._per_schema_filters = defaultdict(list)

    def register(
        self,
        scheme: str,
        type_filter: Callable[[type[Any]], bool],
        service_id: ServiceId[IReadData[Any]],
    ) -> None:
        self._per_schema_filters[scheme].append((type_filter, service_id))

    def _get_service_id(
        self, scheme: str, data_type: type[DataType]
    ) -> ServiceId[IReadData[DataType]]:
        filters = self._per_schema_filters[scheme]
        for type_filter, service_id in filters[::-1]:
            if type_filter(data_type):
                return service_id
        raise ValueError(f"No read service registered for scheme {scheme} and type {data_type}")

    def get_read_service_ids(
        self, data_type: type[DataType]
    ) -> Mapping[str, ServiceId[IReadData[DataType]]]:
        service_ids = {
            scheme: self._get_service_id(scheme, data_type)
            for scheme in self._per_schema_filters.keys()
        }
        return service_ids


class TypeToWriteServiceMapper(IRegisterWriteServiceForType, IGetWriteServicesForType):
    _per_schema_filters: defaultdict[
        str, list[tuple[Callable[[type[Any]], bool], ServiceId[IWriteData[Any]]]]
    ]

    def __init__(self) -> None:
        self._per_schema_filters = defaultdict(list)

    def register(
        self,
        scheme: str,
        type_filter: Callable[[type[Any]], bool],
        service_id: ServiceId[IWriteData[Any]],
    ) -> None:
        self._per_schema_filters[scheme].append((type_filter, service_id))

    def _get_service_id(
        self, scheme: str, data_type: type[DataType]
    ) -> ServiceId[IWriteData[DataType]]:
        filters = self._per_schema_filters[scheme]
        for type_filter, service_id in filters[::-1]:
            if type_filter(data_type):
                return service_id
        raise ValueError(f"No write service registered for scheme {scheme} and type {data_type}")

    def get_write_service_ids(
        self, data_type: type[DataType]
    ) -> Mapping[str, ServiceId[IWriteData[DataType]]]:
        service_ids = {
            scheme: self._get_service_id(scheme, data_type)
            for scheme in self._per_schema_filters.keys()
        }
        return service_ids
