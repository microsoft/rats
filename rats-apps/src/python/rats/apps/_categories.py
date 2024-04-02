from collections.abc import Container

from ._ids import ConfigId, ServiceId, T_ConfigType, T_ServiceType


class ProviderCategories:
    SERVICE = ServiceId[T_ServiceType]("service")
    GROUP = ServiceId[T_ServiceType]("group")
    CONTAINER = ServiceId[Container]("container")
    CONFIG = ConfigId[T_ConfigType]("config")

    FALLBACK_SERVICE = ServiceId[T_ServiceType]("fallback-service")
    FALLBACK_GROUP = ServiceId[T_ServiceType]("fallback-group")
    FALLBACK_CONFIG = ConfigId[T_ConfigType]("fallback-config")
