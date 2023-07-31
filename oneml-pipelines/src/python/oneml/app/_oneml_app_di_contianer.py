import logging

from oneml.app_api import AppEntryPointPluginRelay, InitializePluginsExe
from oneml.services import (
    ContextClient,
    IManageServices,
    IProvideServices,
    service_group,
    service_provider,
)

from ._oneml_app_services import OnemlAppServices, PrivateOnemlAppServiceGroups

logger = logging.getLogger(__name__)


class OnemlAppDiContainer:
    _app: IManageServices

    def __init__(self, app: IManageServices) -> None:
        self._app = app

    @service_group(PrivateOnemlAppServiceGroups.APP_PLUGINS)
    def entry_point_plugin(self) -> AppEntryPointPluginRelay:
        return AppEntryPointPluginRelay(group="oneml.app_plugins")

    @service_provider(OnemlAppServices.APP_CONTEXT_CLIENT)
    def app_context_client(self) -> ContextClient:
        return ContextClient()

    @service_provider(OnemlAppServices.SERVICE_MANAGER)
    def service_manager(self) -> IManageServices:
        return self._app

    @service_provider(OnemlAppServices.SERVICE_CONTAINER)
    def service_container(self) -> IProvideServices:
        return self._app

    @service_provider(OnemlAppServices.SERVICE_FACTORY)
    def service_factory(self) -> IManageServices:
        return self._app

    @service_provider(OnemlAppServices.PLUGIN_LOAD_EXE)
    def plugin_init_exe(self) -> InitializePluginsExe:
        return InitializePluginsExe(
            app=self._app,
            group=lambda: self._app.get_service_group(PrivateOnemlAppServiceGroups.APP_PLUGINS),
        )


"""
TODO: Document how we can promote a private service as public by adding a second decorator
"""
