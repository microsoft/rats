from typing import Generic, TypeVar

from typing_extensions import NamedTuple

ServiceType = TypeVar("ServiceType")


class ServiceId(NamedTuple, Generic[ServiceType]):
    name: str
