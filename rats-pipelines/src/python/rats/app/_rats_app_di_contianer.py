import logging

from rats.app_api import AppEntryPointPluginRelay, InitializePluginsExe
from rats.services import (
    ContextClient,
    IManageServices,
    IProvideServices,
    service_group,
    service_provider,
)

from ._rats_app_services import PrivateRatsAppServiceGroups, RatsAppServices

logger = logging.getLogger(__name__)


class RatsAppDiContainer:
    _app: IManageServices

    def __init__(self, app: IManageServices) -> None:
        self._app = app

    @service_group(PrivateRatsAppServiceGroups.APP_PLUGINS)
    def entry_point_plugin(self) -> AppEntryPointPluginRelay:
        return AppEntryPointPluginRelay(group="rats.app_plugins")

    @service_provider(RatsAppServices.APP_CONTEXT_CLIENT)
    def app_context_client(self) -> ContextClient:
        return ContextClient()

    @service_provider(RatsAppServices.SERVICE_MANAGER)
    def service_manager(self) -> IManageServices:
        return self._app

    @service_provider(RatsAppServices.SERVICE_CONTAINER)
    def service_container(self) -> IProvideServices:
        return self._app

    @service_provider(RatsAppServices.SERVICE_FACTORY)
    def service_factory(self) -> IManageServices:
        return self._app

    @service_provider(RatsAppServices.PLUGIN_LOAD_EXE)
    def plugin_init_exe(self) -> InitializePluginsExe:
        return InitializePluginsExe(
            app=self._app,
            group=lambda: self._app.get_service_group(PrivateRatsAppServiceGroups.APP_PLUGINS),
        )


# TODO: Document how we can promote a private service as public by adding a second decorator
