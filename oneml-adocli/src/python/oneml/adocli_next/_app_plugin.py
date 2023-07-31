from oneml.adocli_next._di_container import OnemlAdocliDiContainer
from oneml.app_api import AppPlugin
from oneml.services import IManageServices


class OnemlAdocliPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(OnemlAdocliDiContainer(app))
