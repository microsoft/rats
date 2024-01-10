from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from typing import Any, cast
from uuid import uuid4

from typing_extensions import NamedTuple

from oneml.app_api import App
from oneml.pipelines.session import OnemlSessionContexts, PipelineSession
from oneml.services import (
    ContextClient,
    ContextId,
    ExecutablesClient,
    IExecutable,
    IManageContexts,
    IManageServices,
    ServiceContainer,
    ServiceFactory,
    ServiceId,
    ServiceProvider,
    T_ContextType,
    T_ExecutableType,
    T_ServiceType,
    TypedServiceContainer,
    executable,
    scoped_context_ids,
)

from ._building_di_container import OnemlBuildingDiContainer
from ._dag_di_container import OnemlDagDiContainer
from ._io2_di_container import OnemlIo2DiContainer
from ._io_di_container import OnemlIoDiContainer
from ._oneml_app_di_contianer import OnemlAppDiContainer
from ._oneml_app_services import OnemlAppServices
from ._session_di_container import OnemlSessionDiContainer
from ._session_services import OnemlSessionServices

logger = logging.getLogger(__name__)


class ExecutableContext(NamedTuple):
    uuid: str
    executable_id: ServiceId[IExecutable]


@scoped_context_ids
class OnemlServiceContexts:
    EXECUTABLE = ContextId[ExecutableContext]("executable")


class OnemlApp(App, IManageServices, IManageContexts):
    _app_factory: ServiceFactory
    _app_container: ServiceContainer
    _exe_container: ExecutablesClient

    @staticmethod
    def default() -> OnemlApp:
        # The factory is always expected to return new values on every call
        app_factory = ServiceFactory()
        # This container is expected to always return the same value on every call
        app_container = ServiceContainer(app_factory)
        exe_container = ExecutablesClient(TypedServiceContainer(app_container))

        app = OnemlApp(
            app_factory,
            app_container,
            exe_container,
        )

        app.add_service(OnemlAppServices.EXE_CLIENT, lambda: exe_container)

        # This is effectively loading some internal plugins
        app.parse_service_container(OnemlAppDiContainer(app))
        app.parse_service_container(OnemlBuildingDiContainer(app))
        app.parse_service_container(OnemlSessionDiContainer(app))
        app.parse_service_container(OnemlIoDiContainer(app))
        app.parse_service_container(OnemlIo2DiContainer(app))
        app.parse_service_container(OnemlDagDiContainer(app))

        # We initialize plugins here so all services are available when trying to execute pipelines
        app.execute(OnemlAppServices.PLUGIN_LOAD_EXE)

        return app

    def __init__(
        self,
        app_factory: ServiceFactory,
        app_container: ServiceContainer,
        exe_container: ExecutablesClient,
    ) -> None:
        self._app_factory = app_factory
        self._app_container = app_container
        self._exe_container = exe_container

    def run_pipeline(self, service_id: ServiceId[T_ExecutableType]) -> None:
        self.run(lambda: self._exe_container.execute_id(service_id))

    def run(self, callback: Callable[[], None]) -> None:
        # TODO: I'm not sure if these are the right data structures to use here
        #       is it the right executable id?
        #       do we need the pipeline context if we have an executable context already?
        #       should the pipeline context be inside the executable context instead?
        ctx = PipelineSession(str(uuid4()))
        with self.open_context(OnemlSessionContexts.PIPELINE, ctx):
            self._exe_container.execute(OnemlAppServices.PIPELINE_EXECUTABLE, executable(callback))
            session = self.get_service(OnemlSessionServices.SESSION_CLIENT)
            session.run()

    def execute(self, exe_id: ServiceId[T_ExecutableType]) -> None:
        ctx = ExecutableContext(
            str(uuid4()),
            cast(ServiceId[IExecutable], exe_id),
        )
        with self.open_context(OnemlServiceContexts.EXECUTABLE, ctx):
            self._exe_container.execute_id(exe_id)

    def get_service_ids(self) -> frozenset[ServiceId[Any]]:
        return self._app_factory.get_service_ids()

    def get_service_provider(
        self,
        service_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[T_ServiceType]:
        return self._app_container.get_service_provider(service_id)

    def get_service(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        return self._app_container.get_service(service_id)

    def get_service_group_provider(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[Iterable[T_ServiceType]]:
        return self._app_container.get_service_group_provider(group_id)

    def get_service_group_providers(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        return self._app_container.get_service_group_providers(group_id)

    def add_service(
        self,
        service_id: ServiceId[T_ServiceType],
        provider: ServiceProvider[T_ServiceType],
    ) -> None:
        self._app_factory.add_service(service_id, provider)

    def add_group(
        self,
        group_id: ServiceId[T_ServiceType],
        provider: ServiceProvider[T_ServiceType],
    ) -> None:
        self._app_factory.add_group(group_id, provider)

    def open_context(
        self,
        context_id: ContextId[T_ContextType],
        value: T_ContextType,
    ) -> AbstractContextManager[None]:
        return self._context_client().open_context(context_id, value)

    def get_context(self, context_id: ContextId[T_ContextType]) -> T_ContextType:
        return self._context_client().get_context(context_id)

    def _context_client(self) -> ContextClient:
        return cast(
            ContextClient,
            self._app_container.get_service(OnemlAppServices.APP_CONTEXT_CLIENT),
        )
