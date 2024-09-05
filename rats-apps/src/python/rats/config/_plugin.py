from rats import apps
from ._configuration import (
    GetConfigurationFromObject,
    FactoryToFactoryWithConfig,
    ConfigurationToObject,
    ToConfigYaml,
    FromConfigYaml,
)
from ._service_ids import Services


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(Services.GET_CONFIGURATION_FROM_OBJECT)
    def _get_configuration_from_object(self) -> GetConfigurationFromObject:
        return GetConfigurationFromObject()

    @apps.service(Services.FACTORY_TO_FACTORY_WITH_CONFIG)
    def _factory_to_factory_with_config(self) -> FactoryToFactoryWithConfig:
        return FactoryToFactoryWithConfig(self.get(Services.GET_CONFIGURATION_FROM_OBJECT))

    @apps.service(Services.CONFIGURATION_TO_OBJECT)
    def _configuration_to_object(self) -> ConfigurationToObject:
        return ConfigurationToObject(self._app)

    @apps.service(Services.TO_CONFIG_YAML)
    def _to_config_yaml(self) -> ToConfigYaml:
        return ToConfigYaml(self.get(Services.GET_CONFIGURATION_FROM_OBJECT))

    @apps.service(Services.FROM_CONFIG_YAML)
    def _from_config_yaml(self) -> FromConfigYaml:
        return FromConfigYaml(self.get(Services.CONFIGURATION_TO_OBJECT))
