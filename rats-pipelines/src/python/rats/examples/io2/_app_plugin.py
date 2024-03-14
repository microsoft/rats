from rats.app import RatsApp
from rats.app_api import AppPlugin
from rats.services import IManageServices

from ._di_container import Io2ExampleDiContainer, Io2ExampleServices


class Io2ExamplePlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(Io2ExampleDiContainer(app))


def main() -> None:
    app = RatsApp.default()
    app.run_pipeline(Io2ExampleServices.PIPELINE)
