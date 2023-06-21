from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from typing import Iterable

from oneml.services import (
    IManageServices,
    ServiceContainer,
    ServiceFactory,
    ServiceId,
    ServiceProvider,
    ServiceType,
)

from ._oneml_app_di_contianer import OnemlAppDiContainer
from ._oneml_app_services import OnemlAppServiceGroups, OnemlAppServices
from ._structs import PipelineContext

logger = logging.getLogger(__name__)


class OnemlApp(IManageServices):
    _app_factory: ServiceFactory
    _app_container: ServiceContainer

    @staticmethod
    def default() -> OnemlApp:
        # The factory is always expected to return new values on every call
        app_factory = ServiceFactory()
        # This container is expected to always return the same value on every call
        app_container = ServiceContainer(app_factory)

        app = OnemlApp(app_factory, app_container)

        app_di_container = OnemlAppDiContainer(app)
        app.parse_service_container(app_di_container)
        app.add_services(  # type: ignore
            (OnemlAppServices.SERVICE_MANAGER, lambda: app),
            (OnemlAppServices.SERVICE_CONTAINER, lambda: app_container),
            (OnemlAppServices.SERVICE_FACTORY, lambda: app_factory),
        )

        # We initialize plugins here so all services are available when trying to execute pipelines
        app.initialize_app_plugins()

        return app

    def __init__(self, app_factory: ServiceFactory, app_container: ServiceContainer) -> None:
        self._app_factory = app_factory
        self._app_container = app_container

    def execute_pipeline(self, name: str) -> None:
        context_client = self.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        context_value = PipelineContext(id=str(uuid.uuid4()), name=name)

        with context_client.open_context(OnemlAppServices.PIPELINE_CONTEXT_ID, context_value):
            logger.debug(f"executing oneml pipeline: {context_value}")
            self._initialize_pipeline_plugins()
            pipeline_registry = self.get_service(OnemlAppServices.PIPELINE_REGISTRY)
            # TODO: exposing the PipelineSessionClient directly is probably not a good idea
            session = pipeline_registry.create_session(name)
            session.run()

    @lru_cache()  # caching so we only initialize plugins once even if we run many pipelines
    def initialize_app_plugins(self) -> None:
        for plugin in self.get_service_group(OnemlAppServiceGroups.APP_PLUGINS):
            plugin.load_plugin(self)

    def _initialize_pipeline_plugins(self) -> None:
        for plugin in self.get_service_group(OnemlAppServiceGroups.PIPELINE_REGISTRY_PLUGINS):
            plugin.load_plugin()  # type: ignore

    def get_service_provider(
        self,
        service_id: ServiceId[ServiceType],
    ) -> ServiceProvider[ServiceType]:
        return self._app_container.get_service_provider(service_id)

    def get_service(self, service_id: ServiceId[ServiceType]) -> ServiceType:
        return self._app_container.get_service(service_id)

    def get_service_group_providers(
        self,
        group_id: ServiceId[ServiceType],
    ) -> Iterable[ServiceProvider[ServiceType]]:
        return self._app_container.get_service_group_providers(group_id)

    def add_service(
        self,
        service_id: ServiceId[ServiceType],
        provider: ServiceProvider[ServiceType],
    ) -> None:
        self._app_factory.add_service(service_id, provider)

    def add_group(
        self,
        group_id: ServiceId[ServiceType],
        provider: ServiceProvider[ServiceType],
    ) -> None:
        self._app_factory.add_group(group_id, provider)
