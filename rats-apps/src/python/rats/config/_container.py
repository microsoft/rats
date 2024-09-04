from rats import apps
from ._configuration import (
    GetConfigurationFromObject,
    FactoryToFactoryWithConfig,
    FactoryProviderToFactoryWithConfigProvider,
)
from ._annotations import find_configured_object_factory_methods_in_class
from typing import Iterator


@apps.autoscope
class PrivateServices:
    PROCESS_FACTORY_PROVIDER = apps.ServiceId[FactoryProviderToFactoryWithConfigProvider](
        "process-factory-provider"
    )


class Container(apps.Container):
    __initialization_complete: bool = False

    @apps.service(PrivateServices.PROCESS_FACTORY_PROVIDER)
    def _process_factory_provider(self) -> FactoryProviderToFactoryWithConfigProvider:
        return FactoryProviderToFactoryWithConfigProvider(
            FactoryToFactoryWithConfig(GetConfigurationFromObject())
        )

    def _process_all_factory_providers(self) -> None:
        process_method = self.get(PrivateServices.PROCESS_FACTORY_PROVIDER)
        method_names = find_configured_object_factory_methods_in_class(self.__class__)
        for method_name in method_names:
            method = getattr(self, method_name)
            processed_method = process_method(method)
            setattr(self, method_name, processed_method)

    def _complete_initialization(self) -> None:
        if not self.__initialization_complete:
            self._process_all_factory_providers()
            self.__initialization_complete = True

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: apps.ServiceId[apps.T_ServiceType],
    ) -> Iterator[apps.T_ServiceType]:
        self._complete_initialization()
        super().get_namespaced_group(namespace, group_id)
