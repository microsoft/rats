from collections.abc import Iterator, Mapping
from typing import TypeVar

from rats.services import IProvideServices, ServiceId

T_ServiceType = TypeVar("T_ServiceType")


class ServiceMapping(Mapping[str, T_ServiceType]):
    _services_provider: IProvideServices
    _service_ids_map: Mapping[str, ServiceId[T_ServiceType]]

    def __init__(
        self,
        services_provider: IProvideServices,
        service_ids_map: Mapping[str, ServiceId[T_ServiceType]],
    ) -> None:
        self._services_provider = services_provider
        self._service_ids_map = service_ids_map

    def __getitem__(self, key: str) -> T_ServiceType:
        return self._services_provider.get_service(self._service_ids_map[key])

    def __contains__(self, key: object) -> bool:
        return key in self._service_ids_map

    def __iter__(self) -> Iterator[str]:
        return iter(self._service_ids_map)

    def __len__(self) -> int:
        return len(self._service_ids_map)
