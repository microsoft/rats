from rats.adocli_next._di_container import RatsAdocliDiContainer
from rats.app_api import AppPlugin
from rats.services import IManageServices


class RatsAdocliPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(RatsAdocliDiContainer(app))
