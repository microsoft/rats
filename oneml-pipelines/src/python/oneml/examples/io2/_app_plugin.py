from oneml.app import OnemlApp
from oneml.app_api import AppPlugin
from oneml.services import IManageServices

from ._di_container import Io2ExampleDiContainer, Io2ExampleServices


class Io2ExamplePlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(Io2ExampleDiContainer(app))


def main() -> None:
    app = OnemlApp.default()
    app.run_pipeline(Io2ExampleServices.PIPELINE)
