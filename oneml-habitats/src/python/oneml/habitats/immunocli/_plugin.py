import logging
from typing import cast

from immunodata.cli import CliCommand, OnCommandRegistrationEvent
from immunodata.core.immunocli import OnPackageResourceRegistrationEvent
from immunodata.immunocli.next import BasicCliPlugin, OnPluginConfigurationEvent

from oneml.habitats._services import OnemlHabitatsServices
from oneml.processors.services import OnemlProcessorServices

from ._di_container import OnemlHabitatsDiContainer

logger = logging.getLogger(__name__)


class OnemlHabitatsCliPlugin(BasicCliPlugin[None]):
    component_name = "oneml-habitats"
    component_config_cls = None
    _container: OnemlHabitatsDiContainer

    def __post_init__(self) -> None:
        logger.debug("registered immunocli plugin for oneml-habitats")

        self._container = OnemlHabitatsDiContainer(self.app)
        self.app.register_container(OnemlHabitatsDiContainer, self._container)

        self.app.event_dispatcher.add_listener(OnPluginConfigurationEvent, self._configure_plugin)
        self.app.event_dispatcher.add_listener(OnCommandRegistrationEvent, self._register_commands)
        self.app.event_dispatcher.add_listener(
            OnPackageResourceRegistrationEvent, self._register_package_resources
        )

    def _configure_plugin(self, event: OnPluginConfigurationEvent) -> None:
        pipelines_container = self._container.pipelines_container()

        registry = self._container.session_registry()
        services = self._container.services_registry()

        services.register_service(OnemlHabitatsServices.DI_LOCATOR, lambda: self.app)
        services.register_service(
            OnemlHabitatsServices.NODE_PUBLISHER,
            pipelines_container.node_publisher,
        )
        services.register_service(
            OnemlHabitatsServices.SINGLE_PORT_PUBLISHER,
            pipelines_container.single_port_publisher,
        )
        services.register_service(
            OnemlProcessorServices.GetActiveNodeKey, 
            self._container.get_active_node_key_service()
        )
        services.register_service(
            OnemlProcessorServices.IOManagerRegistry,
            pipelines_container.iomanager_registry
        )
        services.register_service(
            OnemlProcessorServices.SessionId,
            lambda: pipelines_container.pipeline_session_context().get_context().session_id()
        )

        hello_example = self._container.example_hello_world()
        diamond_example = self._container.example_diamond()
        registry.register_session_provider("hello-world", hello_example.get_local_session)
        registry.register_session_provider("diamond", diamond_example.get)

    def _register_commands(self, event: OnCommandRegistrationEvent) -> None:
        for provider in self._container.container_search().get_providers(CliCommand):
            logger.debug(f"auto registering CliCommand: {provider}")
            event.add_command(cast(CliCommand, provider()))

    def _register_package_resources(self, event: OnPackageResourceRegistrationEvent) -> None:
        event.add_locator("oneml-habitats", self._container.resources_locator())
