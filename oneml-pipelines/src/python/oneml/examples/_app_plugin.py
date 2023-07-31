from oneml.app_api import AppPlugin
from oneml.services import IManageServices

from ._di_container import OnemlExamplesDiContainer


class OnemlExamplesPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(OnemlExamplesDiContainer(app))
