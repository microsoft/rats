from rats import apps

from ._configuration import (
    IGetConfigurationFromObject,
    IFactoryToFactoryWithConfig,
    IConfigurationToObject,
    ToConfigYaml,
    FromConfigYaml,
)


@apps.autoscope
class Services:
    GET_CONFIGURATION_FROM_OBJECT = apps.ServiceId[IGetConfigurationFromObject](
        "get-configuration-from-object"
    )
    FACTORY_TO_FACTORY_WITH_CONFIG = apps.ServiceId[IFactoryToFactoryWithConfig](
        "factory-to-factory-with-config"
    )
    CONFIGURATION_TO_OBJECT = apps.ServiceId[IConfigurationToObject]("configuration-to-object")
    TO_CONFIG_YAML = apps.ServiceId[ToConfigYaml]("to-config-yaml")
    FROM_CONFIG_YAML = apps.ServiceId[FromConfigYaml]("from-config-yaml")
