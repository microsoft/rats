"""Library for config <-> object transformations."""

from ._service_ids import Services
from ._configuration import (
    IGetConfigurationFromObject,
    IFactoryToFactoryWithConfig,
    IConfigurationToObject,
    Configuration,
    FactoryConfiguration,
)
from ._decorators import config_factory_service, autoid_config_factory_service
from ._container import ConfigFactoryContainer
from ._plugin import PluginContainer

__all__ = [
    "ConfigFactoryContainer",
    "config_factory_service",
    "autoid_config_factory_service",
    "Configuration",
    "FactoryConfiguration",
    "PluginContainer",
    "IGetConfigurationFromObject",
    "IFactoryToFactoryWithConfig",
    "IConfigurationToObject",
    "Services",
]
